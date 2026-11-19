from copy import deepcopy
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
from threading import Lock, RLock
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import logging

import regex

from .models import Record
from .parsers import parse_pdf, parse_ics
from .rules import default_rules, evaluate, validate_rules
from .render import render_page
from .sources import discover_links, download, template_urls, MAX_BYTES
from .store import atomic_write, load_json, save_json
from .mqtt import DEFAULT_MQTT, validate_mqtt

LOG = logging.getLogger(__name__)
DEFAULT_CONFIG = {
    'district': 'Bergheim und Kenten',
    'overview_url': 'https://swbm.de/geschaeftsfelder/abfallentsorgung/abfallkalender/',
    'source_format': 'pdf', 'pdf_url_pattern': '', 'ics_url_pattern': '',
    'link_pattern': '', 'next_year_month': 10, 'rules': default_rules(),
    'mqtt': DEFAULT_MQTT,
}


def validate_config(config):
    if not isinstance(config, dict):
        raise ValueError('Ungültige Konfiguration.')
    value = {key: deepcopy(config.get(key, default)) for key, default in DEFAULT_CONFIG.items()}
    if not isinstance(value['district'], str) or not 1 <= len(value['district'].strip()) <= 100:
        raise ValueError('Bitte einen Stadtteil angeben.')
    value['district'] = value['district'].strip()
    if value['source_format'] not in ('pdf', 'ics', 'auto'):
        raise ValueError('Unbekanntes Datenformat.')
    if type(value['next_year_month']) is not int or not 1 <= value['next_year_month'] <= 12:
        raise ValueError('Startmonat muss zwischen 1 und 12 liegen.')
    for key in ('overview_url', 'pdf_url_pattern', 'ics_url_pattern'):
        url = value[key]
        if not isinstance(url, str) or len(url) > 2048:
            raise ValueError('Ungültige URL-Einstellung.')
        if url:
            parsed = urlparse(url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ValueError('Bitte öffentliche HTTPS-URLs ohne Zugangsdaten verwenden.')
        if key.endswith('_pattern'):
            template_urls(url, 2027)
    pattern = value['link_pattern']
    if not isinstance(pattern, str) or len(pattern) > 500:
        raise ValueError('Link-Suchmuster darf höchstens 500 Zeichen haben.')
    try:
        regex.compile(pattern)
    except regex.error as exc:
        raise ValueError(f'Ungültiges Link-Suchmuster: {exc}') from exc
    validate_rules(value['rules'])
    value['mqtt'] = validate_mqtt(value['mqtt'])
    return value


class Service:
    def __init__(self, data_dir, fetch=download, today=None):
        self.root = Path(data_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.fetch = fetch
        self.today = today or (lambda: datetime.now(ZoneInfo('Europe/Berlin')).date())
        self.lock = RLock()
        self.refresh_lock = Lock()
        self._config = validate_config(load_json(self.root / 'config.json', DEFAULT_CONFIG))
        self._index = load_json(self.root / 'documents.json', {})
        self._status = load_json(self.root / 'status.json', {'last_attempt': None, 'last_success': None, 'errors': [], 'refreshing': False})
        self._status['refreshing'] = False
        self._records = {}
        self._events = self._calculate(self._config)

    def config(self, include_secrets=False):
        with self.lock:
            config = deepcopy(self._config)
            if not include_secrets:
                config['mqtt']['password_set'] = bool(config['mqtt'].pop('password'))
            return config

    def status(self):
        with self.lock:
            active_years = sorted({d['year'] for d in self._index.values() if d.get('active')})
            return {**deepcopy(self._status), 'active_years': active_years, 'event_count': len(self._events)}

    def documents(self):
        with self.lock:
            return sorted((deepcopy(v) for v in self._index.values()), key=lambda d: (-d['year'], d['format'], d['id']))

    def _read_records(self, item):
        key = item['id']
        if key not in self._records:
            self._records[key] = [Record(**r) for r in load_json(self.root / f'{key}.records.json', [])]
        return self._records[key]

    def document_bytes(self, key):
        with self.lock:
            if key not in self._index:
                raise ValueError('Unbekanntes Dokument.')
            item = self._index[key]
            return (self.root / f"{key}.{item['format']}").read_bytes(), item['format']

    def page_image(self, key, number):
        content, kind = self.document_bytes(key)
        if kind != 'pdf' or not 1 <= number <= 12:
            raise ValueError('Keine gültige PDF-Seite ausgewählt.')
        path = self.root / f'{key}.page{number}.png'
        if not path.exists():
            atomic_write(path, render_page(content, number))
        return path.read_bytes()

    def add_document(self, content, year, kind='pdf', source='Upload', active=False, district=None):
        if kind not in ('pdf', 'ics') or type(year) is not int or not 2000 <= year <= 2100:
            raise ValueError('Ungültiges Dateiformat oder Kalenderjahr.')
        if len(content) > MAX_BYTES:
            raise ValueError('Die Datei ist größer als 20 MB.')
        records = (parse_pdf if kind == 'pdf' else parse_ics)(content, year)
        document_district = district or self.config()['district']
        identity = f'\0{year}\0{kind}\0{document_district}'.encode('utf-8')
        key = sha256(content + identity).hexdigest()[:24]
        item = {'id': key, 'year': year, 'format': kind, 'source': source, 'active': active,
                'district': document_district, 'record_count': len(records),
                'page_count': max((r.page or 0 for r in records), default=0),
                'fetched_at': datetime.now(timezone.utc).isoformat()}
        with self.lock:
            # An upload of the same file must not deactivate a production source.
            if key in self._index and self._index[key].get('active') and not active:
                return deepcopy(self._index[key])
            candidate_index = deepcopy(self._index)
            if active:
                for previous in candidate_index.values():
                    if previous['year'] == year and previous['district'] == item['district']:
                        previous['active'] = False
            candidate_index[key] = item
            self._records[key] = records
            candidate_events = self._calculate(self._config, candidate_index)
            atomic_write(self.root / f'{key}.{kind}', content)
            save_json(self.root / f'{key}.records.json', [r.as_dict() for r in records])
            save_json(self.root / 'documents.json', candidate_index)
            self._index, self._events = candidate_index, candidate_events
        return deepcopy(item)

    def _calculate(self, config, index=None):
        records = []
        for item in (self._index if index is None else index).values():
            if item.get('active') and item.get('district') == config['district']:
                records.extend(self._read_records(item))
        return evaluate(records, config['rules'])['events']

    def events(self):
        with self.lock:
            return deepcopy(self._events)

    def preview(self, document_id, rules):
        with self.lock:
            if document_id not in self._index:
                raise ValueError('Bitte zuerst ein Dokument auswählen.')
            records = list(self._read_records(self._index[document_id]))
        return {**evaluate(records, rules), 'record_count': len(records)}

    def preview_sources(self, config, year):
        value = validate_config(config)
        if type(year) is not int or not 2000 <= year <= 2100:
            raise ValueError('Bitte ein gültiges Kalenderjahr wählen.')
        warnings = []
        try:
            html = self.fetch(value['overview_url']).decode('utf-8', errors='replace') if value['overview_url'] else ''
        except (OSError, ValueError) as exc:
            html = ''
            warnings.append(f'Übersichtsseite konnte nicht geladen werden: {exc}')
        return {'district': value['district'], 'year': year,
                'warnings': warnings,
                'discovered': discover_links(html, value['overview_url'], value['district'], year, value['link_pattern']),
                'fallback': {kind: template_urls(value[f'{kind}_url_pattern'], year) for kind in ('pdf', 'ics')}}

    def save_config(self, config):
        with self.lock:
            candidate = deepcopy(config)
            if isinstance(candidate, dict) and isinstance(candidate.get('mqtt'), dict):
                candidate['mqtt'].setdefault('password', self._config['mqtt']['password'])
            value = validate_config(candidate)
            connection_fields = ('mode', 'host', 'port', 'tls')
            changed = any(value['mqtt'][k] != self._config['mqtt'][k] for k in connection_fields)
            ledger = load_json(self.root / 'mqtt.json', {})
            if changed and (self._config['mqtt']['enabled'] or ledger.get('topics')):
                raise ValueError('Zum Wechsel der MQTT-Verbindung zuerst die Sensorbereitstellung ausschalten, speichern und die Bereinigung abwarten.')
            events = self._calculate(value)
            save_json(self.root / 'config.json', value)
            self._config, self._events = value, events
        return self.config()

    def refresh(self):
        if not self.refresh_lock.acquire(blocking=False):
            return self.status()
        errors, successful = [], []
        try:
            config = self.config()
            with self.lock:
                self._status['refreshing'] = True
            try:
                html = self.fetch(config['overview_url']).decode('utf-8', errors='replace') if config['overview_url'] else ''
            except (OSError, ValueError) as exc:
                html = ''
                errors.append(f'Übersichtsseite: {exc}')
            now = self.today()
            years = [now.year] + ([now.year + 1] if now.month >= config['next_year_month'] else [])
            for year in years:
                try:
                    links = discover_links(html, config['overview_url'], config['district'], year, config['link_pattern'])
                    formats = ['ics', 'pdf'] if config['source_format'] == 'auto' else [config['source_format']]
                    attempts = []
                    loaded = False
                    for kind in formats:
                        candidates = links[kind] + template_urls(config[f'{kind}_url_pattern'], year)
                        for url in dict.fromkeys(candidates):
                            try:
                                content = self.fetch(url)
                                self.add_document(content, year, kind, url, active=True, district=config['district'])
                                successful.append(year)
                                loaded = True
                                break
                            except (OSError, ValueError) as exc:
                                attempts.append(f'{url}: {exc}')
                        if loaded:
                            break
                    if not loaded:
                        detail = '; '.join(attempts[-3:]) or 'Noch keine passende Datei auf der Übersichtsseite gefunden.'
                        errors.append(f'{year}: {detail}')
                except (ValueError, TimeoutError) as exc:
                    errors.append(f'{year}: {exc}')
            with self.lock:
                timestamp = datetime.now(timezone.utc).isoformat()
                self._status.update(last_attempt=timestamp, errors=errors, refreshing=False)
                if successful:
                    self._status['last_success'] = timestamp
                save_json(self.root / 'status.json', self._status)
            for error in errors:
                LOG.warning('Kalenderabruf: %s', error)
            return self.status()
        finally:
            with self.lock:
                self._status['refreshing'] = False
            self.refresh_lock.release()
