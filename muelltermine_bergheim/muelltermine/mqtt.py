"""Optional MQTT Discovery publisher; the calendar remains usable without a broker."""
from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
import json
import logging
import os
import re
from threading import Event, RLock, Thread
from urllib.request import Request, urlopen
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .store import load_json, save_json

LOG = logging.getLogger(__name__)
VERSION = '0.2.0'
DEFAULT_MQTT = {
    'enabled': False, 'mode': 'auto', 'host': '', 'port': 1883,
    'username': '', 'password': '', 'tls': False,
    'discovery_prefix': 'homeassistant', 'birth_topic': 'homeassistant/status',
    'timezone': 'Europe/Berlin',
}


def validate_mqtt(settings):
    if not isinstance(settings, dict):
        raise ValueError('Ungültige MQTT-Einstellungen.')
    value = {key: deepcopy(settings.get(key, default)) for key, default in DEFAULT_MQTT.items()}
    for key in ('enabled', 'tls'):
        if type(value[key]) is not bool:
            raise ValueError('MQTT-Schalter müssen wahr oder falsch sein.')
    if value['mode'] not in ('auto', 'manual'):
        raise ValueError('Unbekannte MQTT-Verbindungsart.')
    if type(value['port']) is not int or not 1 <= value['port'] <= 65535:
        raise ValueError('MQTT-Port muss zwischen 1 und 65535 liegen.')
    for key in ('host', 'username', 'password', 'discovery_prefix', 'birth_topic', 'timezone'):
        if not isinstance(value[key], str) or len(value[key]) > 1024 or '\x00' in value[key]:
            raise ValueError('Ungültige MQTT-Einstellung.')
    if value['enabled'] and value['mode'] == 'manual' and not value['host'].strip():
        raise ValueError('Bitte einen MQTT-Host angeben.')
    for key in ('discovery_prefix', 'birth_topic'):
        if not re.fullmatch(r'[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*', value[key]):
            raise ValueError('MQTT-Themen dürfen keine Platzhalter oder leeren Abschnitte enthalten.')
    try:
        ZoneInfo(value['timezone'])
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError('Unbekannte Zeitzone.') from exc
    return value


def discover_broker():
    token = os.environ.get('SUPERVISOR_TOKEN')
    if not token:
        raise OSError('Supervisor unavailable')
    request = Request('http://supervisor/services/mqtt', headers={'Authorization': f'Bearer {token}'})
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    if result.get('result') != 'ok' or not isinstance(result.get('data'), dict):
        raise ValueError('MQTT service unavailable')
    data = result['data']
    return {'host': data['host'], 'port': int(data['port']),
            'username': data.get('username', ''), 'password': data.get('password', ''),
            'tls': bool(data.get('ssl', False)), 'protocol': data.get('protocol', '3.1.1')}


def make_client(identity):
    import paho.mqtt.client as mqtt
    return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'muelltermine_{identity}')


def sensor_value(events, rule_id, today):
    dates = sorted(e['date'] for e in events if e['rule_id'] == rule_id and e['date'] >= today.isoformat())
    next_date = dates[0] if dates else None
    days = (date.fromisoformat(next_date) - today).days if next_date else None
    state = 'Kein Termin' if days is None else 'Heute' if days == 0 else 'Morgen' if days == 1 else f'in {days} Tagen'
    return {'state': state, 'next_date': next_date, 'days_until': days}


class MqttBridge:
    def __init__(self, service, client_factory=make_client, discover=discover_broker, today=None):
        self.service, self.client_factory, self.discover = service, client_factory, discover
        self.today = today or (lambda zone: datetime.now(ZoneInfo(zone)).date())
        self.path = service.root / 'mqtt.json'
        self.ledger = load_json(self.path, {'identity': uuid4().hex[:16], 'topics': [], 'broker': None})
        save_json(self.path, self.ledger)
        self.base = f"muelltermine_bergheim/{self.ledger['identity']}"
        self.client = None
        self.connection_key = None
        self.connected = Event()
        self.resync = Event()
        self.stop = Event()
        self.lock = RLock()
        self.worker = None
        self.last_payload = None
        self.message = 'Sensorbereitstellung ausgeschaltet.'

    def status(self):
        with self.lock:
            return {'connected': self.connected.is_set(), 'message': self.message,
                    'sensor_count': len(self.ledger['topics']) if self.connected.is_set() else 0}

    def start(self):
        def work():
            while not self.stop.is_set():
                self.tick()
                self.stop.wait(2)
        self.worker = Thread(target=work, daemon=True, name='mqtt-discovery')
        self.worker.start()

    def _publish(self, topic, payload):
        result = self.client.publish(topic, payload, qos=1, retain=True)
        result.wait_for_publish(timeout=5)
        if result.rc != 0 or not result.is_published():
            raise OSError('MQTT publish was not acknowledged')

    def _disconnect(self):
        if self.client:
            try:
                if self.connected.is_set():
                    self._publish(f'{self.base}/availability', 'offline')
            finally:
                self.client.disconnect()
                self.client.loop_stop()
                self.client = None
                self.connected.clear()
                self.last_payload = None

    def _connect(self, cfg):
        broker = self.discover() if cfg['mode'] == 'auto' else cfg
        # Passwords are not persisted in the topic ledger or included in messages.
        key = sha256(json.dumps({k: broker.get(k) for k in ('host', 'port', 'tls')}, sort_keys=True).encode()).hexdigest()
        self.connection_key = key
        self.client = client = self.client_factory(self.ledger['identity'])
        if broker.get('username'):
            client.username_pw_set(broker['username'], broker.get('password', ''))
        if broker.get('tls'):
            client.tls_set()
        client.will_set(f'{self.base}/availability', 'offline', qos=1, retain=True)
        client.reconnect_delay_set(min_delay=1, max_delay=60)

        def connected(client, userdata, flags, reason, properties):
            if reason == 0:
                client.subscribe(cfg['birth_topic'], qos=1)
                self.connected.set()
                self.resync.set()

        def disconnected(client, userdata, flags, reason, properties):
            self.connected.clear()

        def message(client, userdata, msg):
            if msg.topic == cfg['birth_topic'] and msg.payload == b'online':
                self.resync.set()

        client.on_connect, client.on_disconnect, client.on_message = connected, disconnected, message
        client.connect_async(broker['host'], broker['port'], keepalive=30)
        client.loop_start()

    def tick(self):
        with self.lock:
            try:
                self._tick()
            except Exception:
                # Exceptions may contain broker credentials: expose only a fixed message.
                self.message = 'MQTT nicht bereit. Broker, Zugangsdaten und Verbindung prüfen; automatischer Neuversuch.'
                if self.client and not self.connected.is_set():
                    self._disconnect()
                LOG.debug('MQTT-Veröffentlichung wird erneut versucht.')

    def _tick(self):
        config = self.service.config(include_secrets=True)
        cfg = config['mqtt']
        if not cfg['enabled'] and not self.ledger['topics']:
            self._disconnect()
            self.message = 'Sensorbereitstellung ausgeschaltet.'
            return
        # Rebuild when edited connection settings change; paho handles transient disconnects.
        settings_key = json.dumps({k: cfg[k] for k in ('mode', 'host', 'port', 'username', 'password', 'tls', 'birth_topic')}, sort_keys=True)
        if self.client and settings_key != getattr(self, '_settings_key', None):
            self._disconnect()
        if not self.client:
            self._connect(cfg)
            self._settings_key = settings_key
            self.message = 'Verbindung zum MQTT-Broker wird hergestellt …'
        if not self.connected.is_set():
            self.message = 'MQTT nicht verbunden; automatischer Neuversuch.'
            return
        rules = [r for r in config['rules'] if r.get('enabled', True)] if cfg['enabled'] else []
        topics = {f"{cfg['discovery_prefix']}/sensor/{self.ledger['identity']}/{r['id']}/config": r for r in rules}
        payload = json.dumps([config['district'], rules, cfg['timezone'], cfg['discovery_prefix'],
                              self.today(cfg['timezone']).isoformat(), self.service.events(), self.service.status()], sort_keys=True)
        force = self.resync.is_set()
        if payload == self.last_payload and not force:
            return
        self.last_payload = None
        self.resync.clear()
        previous = self.ledger['topics'] if self.ledger['broker'] == self.connection_key else []
        # Persist the union before publishing: an interrupted update is cleaned on restart.
        self.ledger.update(topics=sorted(set(previous) | set(topics)), broker=self.connection_key)
        save_json(self.path, self.ledger)
        for topic in set(previous) - set(topics):
            self._publish(topic, '')
            # Only clear a state topic when its rule is actually removed.
            rule_id = topic.split('/')[-2]
            if not any(r['id'] == rule_id for r in rules):
                self._publish(f'{self.base}/{rule_id}/state', '')
        status = self.service.status()
        for topic, rule in topics.items():
            state_topic = f"{self.base}/{rule['id']}/state"
            discovery = {
                'name': rule['name'], 'unique_id': f"muelltermine_{self.ledger['identity']}_{rule['id']}",
                'default_entity_id': f"sensor.muelltermine_bergheim_{rule['id']}_mqtt",
                'icon': 'mdi:trash-can-outline', 'state_topic': state_topic,
                'value_template': '{{ value_json.state }}',
                'json_attributes_topic': state_topic,
                'json_attributes_template': "{{ {'next_date': value_json.next_date, 'days_until': value_json.days_until, 'active_years': value_json.active_years, 'last_success': value_json.last_success, 'errors': value_json.errors} | tojson }}",
                'availability_topic': f'{self.base}/availability',
                'device': {'identifiers': [f"muelltermine_bergheim_{self.ledger['identity']}"],
                           'name': 'Mülltermine Bergheim', 'manufacturer': 'up-quirk',
                           'model': config['district'], 'sw_version': VERSION},
                'origin': {'name': 'Mülltermine Bergheim', 'sw_version': VERSION,
                           'support_url': 'https://github.com/up-quirk/muelltermine-bergheim'},
            }
            self._publish(topic, json.dumps(discovery, ensure_ascii=False))
            value = sensor_value(self.service.events(), rule['id'], self.today(cfg['timezone']))
            value.update({key: status[key] for key in ('active_years', 'last_success', 'errors')})
            self._publish(state_topic, json.dumps(value, ensure_ascii=False))
        self._publish(f'{self.base}/availability', 'online' if rules else 'offline')
        self.ledger['topics'] = sorted(topics)
        save_json(self.path, self.ledger)
        self.last_payload = payload
        self.message = f'{len(rules)} Sensoren in Home Assistant bereitgestellt.' if rules else 'Sensorbereitstellung ausgeschaltet.'
        if not cfg['enabled']:
            self._disconnect()

    def close(self):
        self.stop.set()
        if self.worker:
            self.worker.join(timeout=20)
        with self.lock:
            self._disconnect()
