import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

try:
    from muelltermine.web import make_server
    from muelltermine.service import Service
except ImportError:
    make_server = Service = None


class WebTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(make_server, 'HTTP endpoints are not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = Service(Path(self.temp.name))
        self.editor = make_server(self.service, '127.0.0.1', 0, editor=True)
        self.feed = make_server(self.service, '127.0.0.1', 0, editor=False)
        for server in (self.editor, self.feed):
            threading.Thread(target=server.serve_forever, daemon=True).start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)

    def request(self, server, path, data=None, headers=None):
        url = f'http://127.0.0.1:{server.server_port}{path}'
        return urlopen(Request(url, data=data, headers=headers or {}), timeout=5)

    def test_feed_does_not_expose_editor_or_writes(self):
        self.assertIn(b'VCALENDAR', self.request(self.feed, '/calendar.ics').read())
        for path, data in [('/api/state', None), ('/api/config', b'{}'), ('/', None)]:
            with self.assertRaises(HTTPError) as caught:
                self.request(self.feed, path, data)
            self.assertIn(caught.exception.code, (404, 405))

    def test_preview_is_isolated_until_explicit_save(self):
        source = (Path(__file__).parent / 'fixtures/bergheim-2027.pdf').read_bytes()
        doc = self.service.add_document(source, 2027, active=True)
        cfg = self.service.config()
        cfg['rules'][0]['pattern'] = 'Biotonne'
        payload = json.dumps({'document_id': doc['id'], 'rules': cfg['rules']}).encode()
        result = json.load(self.request(self.editor, '/api/preview', payload, {'Content-Type': 'application/json'}))
        self.assertEqual(result['counts']['rest'], 43)
        self.assertEqual(sum(e['rule_id'] == 'rest' for e in self.service.events()), 26)
        self.request(self.editor, '/api/config', json.dumps(cfg).encode(), {'Content-Type': 'application/json'}).close()
        self.assertEqual(sum(e['rule_id'] == 'rest' for e in self.service.events()), 43)

    def test_original_pdf_page_is_rendered_as_browser_independent_image(self):
        content = (Path(__file__).parent / 'fixtures/bergheim-2027.pdf').read_bytes()
        doc = self.service.add_document(content, 2027)
        response = self.request(self.editor, f"/api/documents/{doc['id']}/page/1.png")
        self.assertEqual(response.headers['Content-Type'], 'image/png')
        self.assertTrue(response.read().startswith(b'\x89PNG\r\n\x1a\n'))

    def test_source_preview_returns_links_without_saving_settings(self):
        self.service.fetch = lambda _: b'<p>Ahe 2027 <a href="/ahe_2027.pdf">PDF</a></p>'
        cfg = self.service.config()
        cfg['district'] = 'Ahe'
        payload = json.dumps({'config': cfg, 'year': 2027}).encode()
        result = json.load(self.request(self.editor, '/api/sources/preview', payload, {'Content-Type': 'application/json'}))
        self.assertEqual(result['discovered']['pdf'], ['https://swbm.de/ahe_2027.pdf'])
        self.assertEqual(self.service.config()['district'], 'Bergheim und Kenten')
        self.assertEqual(self.service.documents(), [])

    def test_cross_origin_writes_and_bad_uploads_are_rejected(self):
        for path, content, headers in [
            ('/api/config', b'{}', {'Content-Type': 'application/json', 'Origin': 'https://elsewhere.example'}),
            ('/api/upload?year=2027', b'not a pdf', {'Content-Type': 'application/pdf'}),
        ]:
            with self.assertRaises(HTTPError) as caught:
                self.request(self.editor, path, content, headers)
            self.assertIn(caught.exception.code, (400, 403))


if __name__ == '__main__':
    unittest.main()
