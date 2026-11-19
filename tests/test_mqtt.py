import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from muelltermine.service import Service
try:
    from muelltermine.mqtt import MqttBridge, sensor_value
except ImportError:
    MqttBridge = sensor_value = None


class Transport:
    """Network boundary: keep real payload construction and persistence in tests."""
    def __init__(self):
        self.messages = []
        self.connected = False
    def publish(self, topic, payload, qos=0, retain=False):
        self.messages.append((topic, payload, qos, retain))
        class Ack:
            rc = 0
            def wait_for_publish(self, timeout):
                return None
            def is_published(self):
                return True
        return Ack()
    def subscribe(self, topic, qos=0):
        self.subscription = topic
    def connect_async(self, host, port, keepalive):
        self.host = host
    def loop_start(self):
        pass
    def loop_stop(self):
        pass
    def disconnect(self):
        self.connected = False
    def will_set(self, topic, payload, qos, retain):
        self.will = (topic, payload, qos, retain)
    def username_pw_set(self, username, password):
        pass
    def tls_set(self):
        pass
    def reconnect_delay_set(self, min_delay, max_delay):
        pass


class MqttTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = Service(Path(self.temp.name), today=lambda: date(2026, 11, 18))

    def test_date_selection_ignores_past_and_other_bins(self):
        self.assertIsNotNone(sensor_value, 'MQTT sensor calculation is missing')
        events = [{'date': '2026-11-17', 'rule_id': 'gelb'},
                  {'date': '2026-11-18', 'rule_id': 'bio'},
                  {'date': '2026-11-25', 'rule_id': 'gelb'}]
        for today, state, days in [(date(2026, 11, 18), 'in 7 Tagen', 7),
                                    (date(2026, 11, 24), 'Morgen', 1),
                                    (date(2026, 11, 25), 'Heute', 0),
                                    (date(2026, 11, 26), 'Kein Termin', None)]:
            value = sensor_value(events, 'gelb', today)
            self.assertEqual(value['state'], state)
            self.assertEqual(value['days_until'], days)
        self.assertEqual(sensor_value(events, 'gelb', date(2026, 11, 18))['next_date'], '2026-11-25')

    def test_credentials_preserved_but_redacted_and_settings_validated(self):
        cfg = self.service.config()
        cfg['mqtt'] = {'enabled': True, 'mode': 'manual', 'host': 'localhost',
                       'port': 1883, 'username': 'user', 'password': 'private-secret'}
        result = self.service.save_config(cfg)
        self.assertNotIn('private-secret', json.dumps(result))
        self.assertTrue(result['mqtt']['password_set'])
        result['district'] = 'Ahe'
        self.service.save_config(result)
        self.assertEqual(self.service.config(include_secrets=True)['mqtt']['password'], 'private-secret')
        for field, bad in [('port', 0), ('enabled', 'yes'), ('discovery_prefix', '#'), ('timezone', 'Missing/Zone')]:
            cfg = self.service.config()
            cfg['mqtt'][field] = bad
            with self.assertRaises(ValueError):
                self.service.save_config(cfg)

    def bridge(self):
        self.assertIsNotNone(MqttBridge, 'MQTT publisher is missing')
        cfg = self.service.config()
        cfg['mqtt'] = {'enabled': True, 'mode': 'manual', 'host': 'localhost'}
        self.service.save_config(cfg)
        self.transport = Transport()
        bridge = MqttBridge(self.service, client_factory=lambda _: self.transport,
                            today=lambda _: date(2026, 11, 18))
        bridge.tick()
        self.transport.on_connect(self.transport, None, None, 0, None)
        bridge.tick()
        return bridge

    def test_discovery_groups_sensors_and_republishes_after_birth_and_reconnect(self):
        bridge = self.bridge()
        configs = [(t, json.loads(p)) for t,p,_,_ in self.transport.messages if t.endswith('/config') and p]
        self.assertEqual(len(configs), 4)
        identifiers = [p['device']['identifiers'] for _,p in configs]
        self.assertTrue(all(i == identifiers[0] for i in identifiers))
        gelb = next(p for _,p in configs if p['name'] == 'Gelbe Tonne')
        self.assertEqual(gelb['default_entity_id'], 'sensor.muelltermine_bergheim_gelb_mqtt')
        self.assertEqual(self.transport.will[1:], ('offline', 1, True))
        self.assertEqual(self.transport.subscription, 'homeassistant/status')
        self.assertTrue(all(q == 1 and r for _,_,q,r in self.transport.messages))
        self.transport.messages.clear()
        message = type('Message', (), {'topic': 'homeassistant/status', 'payload': b'online'})()
        self.transport.on_message(self.transport, None, message)
        bridge.tick()
        self.assertEqual(sum(t.endswith('/config') for t,_,_,_ in self.transport.messages), 4)
        self.transport.messages.clear()
        self.transport.on_disconnect(self.transport, None, None, 1, None)
        self.assertFalse(bridge.status()['connected'])
        self.transport.on_connect(self.transport, None, None, 0, None)
        bridge.tick()
        self.assertEqual(sum(t.endswith('/config') for t,_,_,_ in self.transport.messages), 4)
        before = gelb['unique_id']
        bridge.close()
        again = self.bridge()
        gelb2 = next(json.loads(p) for t,p,_,_ in self.transport.messages if t.endswith('/config') and p and json.loads(p)['name'] == 'Gelbe Tonne')
        self.assertEqual(gelb2['unique_id'], before)
        again.close()

    def test_removed_rules_and_disable_clear_retained_discovery(self):
        bridge = self.bridge()
        original = [t for t,p,_,_ in self.transport.messages if t.endswith('/config') and p]
        self.transport.messages.clear()
        cfg = self.service.config()
        cfg['rules'][1]['enabled'] = False
        self.service.save_config(cfg)
        bridge.tick()
        self.assertEqual(sum(t.endswith('/config') and p == '' for t,p,_,_ in self.transport.messages), 1)
        self.transport.messages.clear()
        cfg['mqtt']['enabled'] = False
        self.service.save_config(cfg)
        bridge.tick()
        self.assertEqual(sum(t in original and p == '' for t,p,_,_ in self.transport.messages), 3)
        bridge.close()

    def test_missing_supervisor_broker_does_not_break_calendar(self):
        self.assertIsNotNone(MqttBridge, 'MQTT publisher is missing')
        cfg = self.service.config()
        cfg['mqtt'] = {'enabled': True}
        self.service.save_config(cfg)
        def missing():
            raise OSError('secret-should-not-be-logged')
        bridge = MqttBridge(self.service, discover=missing)
        bridge.tick()
        self.assertFalse(bridge.status()['connected'])
        self.assertNotIn('secret', json.dumps(bridge.status()))
        self.assertEqual(self.service.events(), [])
        bridge.close()

    def test_broker_change_requires_cleanup_first(self):
        bridge = self.bridge()
        cfg = self.service.config()
        cfg['mqtt']['host'] = 'other-broker'
        with self.assertRaises(ValueError):
            self.service.save_config(cfg)
        cfg = self.service.config()
        cfg['mqtt']['enabled'] = False
        self.service.save_config(cfg)
        cfg['mqtt']['host'] = 'other-broker'
        with self.assertRaises(ValueError):
            self.service.save_config(cfg)
        bridge.tick()
        self.service.save_config(cfg)
        bridge.close()

    def test_reconnect_failed_publish_retries_without_another_calendar_change(self):
        bridge = self.bridge()
        self.transport.messages.clear()
        self.transport.on_connect(self.transport, None, None, 0, None)
        original = bridge._publish
        def fail(topic, payload):
            raise OSError('unacknowledged')
        bridge._publish = fail
        bridge.tick()
        bridge._publish = original
        bridge.tick()
        self.assertEqual(sum(t.endswith('/config') for t,_,_,_ in self.transport.messages), 4)
        bridge.close()

    def test_rotated_credentials_preserve_topic_ownership_for_cleanup(self):
        bridge = self.bridge()
        cfg = self.service.config()
        cfg['mqtt']['password'] = 'rotated-password'
        self.service.save_config(cfg)
        bridge.tick()
        self.transport.on_connect(self.transport, None, None, 0, None)
        self.transport.messages.clear()
        cfg = self.service.config()
        cfg['rules'][1]['enabled'] = False
        self.service.save_config(cfg)
        bridge.tick()
        self.assertEqual(sum(t.endswith('/gelb/config') and p == '' for t,p,_,_ in self.transport.messages), 1)
        bridge.close()

    def test_rule_color_changes_are_published_without_recreating_sensors(self):
        bridge = self.bridge()
        def yellow_state():
            return next(json.loads(p) for t,p,_,_ in reversed(self.transport.messages)
                        if t.endswith('/gelb/state') and p)
        self.assertEqual(yellow_state().get('color'), '#d99a0b')
        original_config = next(json.loads(p) for t,p,_,_ in self.transport.messages
                               if t.endswith('/gelb/config') and p)
        cfg = self.service.config()
        cfg['rules'][1]['color'] = '#fcdd07'
        self.service.save_config(cfg)
        self.transport.messages.clear()
        bridge.tick()
        self.assertEqual(yellow_state()['color'], '#fcdd07')
        updated = next(json.loads(p) for t,p,_,_ in self.transport.messages
                       if t.endswith('/gelb/config') and p)
        self.assertEqual(updated['unique_id'], original_config['unique_id'])
        self.assertIn('value_json.color', updated['json_attributes_template'])
        bridge.close()
