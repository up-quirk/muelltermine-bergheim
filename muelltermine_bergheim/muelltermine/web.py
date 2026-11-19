"""Ingress editor and a separate, read-only calendar listener."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread, Event
from urllib.parse import urlparse, parse_qs
import json
import logging
import mimetypes
import re
import signal

from .calendar import render_ics
from .sources import MAX_BYTES

LOG = logging.getLogger(__name__)
STATIC = Path(__file__).parent / 'static'


def make_server(service, host='127.0.0.1', port=8099, editor=True, ingress_only=False):
    class Handler(BaseHTTPRequestHandler):
        server_version = 'Muelltermine/0.1'

        def log_message(self, fmt, *args):
            LOG.debug(fmt, *args)

        def send(self, data, content_type='application/json; charset=utf-8', status=200):
            if isinstance(data, (dict, list)):
                data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            elif isinstance(data, str):
                data = data.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; object-src 'none'; base-uri 'self'")
            self.end_headers()
            self.wfile.write(data)

        def allowed(self):
            if editor and ingress_only and self.client_address[0] != '172.30.32.2':
                self.send({'error': 'Die Oberfläche ist nur über Home Assistant Ingress erreichbar.'}, status=403)
                return False
            return True

        def do_GET(self):
            if not self.allowed():
                return
            path = urlparse(self.path).path
            try:
                if path == '/healthz':
                    self.send({'ok': True})
                elif path == '/calendar.ics':
                    self.send(render_ics(service.events()), 'text/calendar; charset=utf-8')
                elif path == '/api/calendar':
                    self.send({'events': service.events(), 'status': service.status()})
                elif not editor:
                    self.send({'error': 'Nicht gefunden.'}, status=404)
                elif path == '/api/state':
                    self.send({'config': service.config(), 'documents': service.documents(), 'status': service.status(),
                               'mqtt': service.mqtt.status() if hasattr(service, 'mqtt') else {'connected': False, 'message': 'Nicht gestartet.', 'sensor_count': 0}})
                elif path.startswith('/api/documents/'):
                    image = re.fullmatch(r'/api/documents/([0-9a-f]{24})/page/([0-9]{1,2})\.png', path)
                    if image:
                        self.send(service.page_image(image[1], int(image[2])), 'image/png')
                    else:
                        data, kind = service.document_bytes(path.rsplit('/', 1)[-1])
                        self.send(data, 'application/pdf' if kind == 'pdf' else 'text/calendar; charset=utf-8')
                elif path in ('/', '/index.html', '/app.js', '/style.css'):
                    name = 'index.html' if path == '/' else path[1:]
                    self.send((STATIC / name).read_bytes(), mimetypes.guess_type(name)[0] + '; charset=utf-8')
                else:
                    self.send({'error': 'Nicht gefunden.'}, status=404)
            except ValueError as exc:
                self.send({'error': str(exc)}, status=400)
            except (OSError, TypeError):
                LOG.exception('Datei konnte nicht geladen werden')
                self.send({'error': 'Datei konnte nicht geladen werden.'}, status=500)

        def do_POST(self):
            if not self.allowed():
                return
            if not editor:
                self.send({'error': 'Dieser Anschluss ist ausschließlich lesend.'}, status=405)
                return
            origin = self.headers.get('Origin')
            permitted = {self.headers.get('Host'), self.headers.get('X-Forwarded-Host')}
            if self.headers.get('Sec-Fetch-Site') == 'cross-site' or (origin and urlparse(origin).netloc not in permitted):
                self.send({'error': 'Anfrage aus fremder Seite abgelehnt.'}, status=403)
                return
            parsed = urlparse(self.path)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                limit = MAX_BYTES if parsed.path == '/api/upload' else 128 * 1024
                if not 0 < length <= limit:
                    self.send({'error': f'Anfrage darf höchstens {limit // 1024} KB enthalten.'}, status=413)
                    return
                self.connection.settimeout(30)
                body = self.rfile.read(length)
                if len(body) != length:
                    raise ValueError('Unvollständige Anfrage.')
                if parsed.path == '/api/upload':
                    year = int(parse_qs(parsed.query).get('year', ['0'])[0])
                    self.send(service.add_document(body, year), status=201)
                    return
                if self.headers.get_content_type() != 'application/json':
                    raise ValueError('JSON-Anfrage erforderlich.')
                payload = json.loads(body)
                if not isinstance(payload, dict):
                    raise ValueError('Ungültige Anfrage.')
                if parsed.path == '/api/preview':
                    self.send(service.preview(payload.get('document_id'), payload.get('rules')))
                elif parsed.path == '/api/sources/preview':
                    self.send(service.preview_sources(payload.get('config'), payload.get('year')))
                elif parsed.path == '/api/config':
                    self.send(service.save_config(payload))
                elif parsed.path == '/api/refresh':
                    Thread(target=safe_refresh, args=(service,), daemon=True).start()
                    self.send({'started': True}, status=202)
                else:
                    self.send({'error': 'Nicht gefunden.'}, status=404)
            except (ValueError, TypeError, KeyError) as exc:
                self.send({'error': str(exc)}, status=400)
            except Exception:
                LOG.exception('Anfrage konnte nicht verarbeitet werden')
                self.send({'error': 'Interner Fehler. Details stehen im App-Protokoll.'}, status=500)

    return ThreadingHTTPServer((host, port), Handler)


def safe_refresh(service):
    try:
        service.refresh()
    except Exception:
        LOG.exception('Kalenderabruf fehlgeschlagen; vorhandene Daten bleiben gespeichert')


def run(service, editor_port=8099, feed_port=8098, ingress_only=True, refresh=True):
    from .mqtt import MqttBridge
    service.mqtt = MqttBridge(service)
    service.mqtt.start()
    def terminate(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, terminate)
    stop = Event()
    bind = '0.0.0.0' if ingress_only else '127.0.0.1'
    editor = make_server(service, bind, editor_port, True, ingress_only)
    feed = make_server(service, bind, feed_port, False)
    Thread(target=feed.serve_forever, daemon=True).start()

    def scheduler():
        while not stop.is_set():
            safe_refresh(service)
            stop.wait(24 * 60 * 60)

    if refresh:
        Thread(target=scheduler, daemon=True).start()
    LOG.info('Editor auf Port %s; lesender Kalender auf Port %s', editor.server_port, feed.server_port)
    try:
        editor.serve_forever()
    finally:
        stop.set()
        service.mqtt.close()
        feed.shutdown()
        feed.server_close()
        editor.server_close()
