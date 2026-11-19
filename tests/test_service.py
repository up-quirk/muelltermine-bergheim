import tempfile
import unittest
from unittest.mock import patch
from datetime import date
from pathlib import Path

try:
    from muelltermine.service import Service
    from muelltermine.sources import discover_links
except ImportError:
    Service = discover_links = None

FIXTURES = Path(__file__).parent / 'fixtures'


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(Service, 'Calendar service is not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_discovery_uses_district_context_and_changed_filenames(self):
        html = '''<h2>Abfallkalender 2027</h2><p>Abfallkalender Bergheim und Kenten 2027
        <a href="/uploads/new_2027_v3.pdf">PDF</a> <a href="/uploads/new_2027.ics">iCal</a></p>
        <p>Abfallkalender Glessen 2027 <a href="/uploads/glessen_2027.pdf">PDF</a></p>'''
        links = discover_links(html, 'https://swbm.de/calendar/', 'Bergheim und Kenten', 2027)
        self.assertEqual(links['pdf'], ['https://swbm.de/uploads/new_2027_v3.pdf'])
        self.assertEqual(links['ics'], ['https://swbm.de/uploads/new_2027.ics'])

    def test_discovery_reads_district_and_year_from_anchor_text(self):
        links = discover_links('<p><a href="/new-v3.pdf">Abfallkalender Bergheim und Kenten 2027</a></p>',
                               'https://swbm.de/', 'Bergheim und Kenten', 2027)
        self.assertEqual(links['pdf'], ['https://swbm.de/new-v3.pdf'])

    def test_source_preview_uses_unsaved_area_and_filters_without_activating(self):
        service = Service(Path(self.temp.name), fetch=lambda _: b'<p>Ahe 2027 <a href="/ahe-2027-v2.pdf">PDF</a><a href="/ahe-2027-old.pdf">Alt</a></p>')
        cfg = service.config()
        cfg.update(district='Ahe', link_pattern='v2', pdf_url_pattern='https://example.org/plan_{year}.pdf')
        result = service.preview_sources(cfg, 2027)
        self.assertEqual(result['discovered']['pdf'], ['https://swbm.de/ahe-2027-v2.pdf'])
        self.assertEqual(result['fallback']['pdf'], ['https://example.org/plan_2027.pdf'])
        self.assertEqual(service.config()['district'], 'Bergheim und Kenten')
        self.assertEqual(service.documents(), [])
        cfg['link_pattern'] = '['
        with self.assertRaises(ValueError):
            service.preview_sources(cfg, 2027)

    def test_source_preview_keeps_fallback_visible_when_overview_is_unavailable(self):
        def offline(_):
            raise OSError('HTTP 404')
        service = Service(Path(self.temp.name), fetch=offline)
        cfg = service.config()
        cfg['pdf_url_pattern'] = 'https://example.org/calendar_{year}.pdf'
        result = service.preview_sources(cfg, 2027)
        self.assertEqual(result['discovered']['pdf'], [])
        self.assertEqual(result['fallback']['pdf'], ['https://example.org/calendar_2027.pdf'])
        self.assertTrue(result['warnings'])

    def test_same_multiyear_ics_preserves_both_years(self):
        content = b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20260106\r\nSUMMARY:Hausm\xc3\xbcll\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20270105\r\nSUMMARY:Hausm\xc3\xbcll\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'
        service = Service(Path(self.temp.name))
        service.add_document(content, 2026, 'ics', active=True)
        service.add_document(content, 2027, 'ics', active=True)
        self.assertEqual(service.status()['active_years'], [2026, 2027])
        self.assertEqual([e['date'] for e in service.events()], ['2026-01-06', '2027-01-05'])

    def test_failed_activation_keeps_previous_source_and_survives_restart(self):
        def calendar(summary):
            return f'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nDTSTART;VALUE=DATE:20270105\r\nSUMMARY:{summary}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'.encode()
        service = Service(Path(self.temp.name))
        original = service.add_document(calendar('a'), 2027, 'ics', active=True)
        cfg = service.config()
        cfg['rules'] = [{'id': 'test', 'name': 'Test', 'pattern': '(a|aa)+$', 'enabled': True}]
        service.save_config(cfg)
        with self.assertRaises(ValueError):
            service.add_document(calendar('a' * 1000 + '!'), 2027, 'ics', active=True)
        self.assertEqual([d['id'] for d in service.documents() if d['active']], [original['id']])
        self.assertEqual(len(Service(Path(self.temp.name)).events()), 1)

    def test_index_write_failure_does_not_replace_in_memory_calendar(self):
        import muelltermine.service as module
        service = self.make_service()
        service.refresh()
        before_documents, before_events = service.documents(), service.events()
        real_save = module.save_json
        def failing_save(path, value):
            if path.name == 'documents.json':
                raise OSError('disk full')
            return real_save(path, value)
        # Same dated data, changed bytes/source hash: exercise a real replacement.
        original = (FIXTURES / 'bergheim-2027.ics').read_bytes()
        with patch.object(module, 'save_json', side_effect=failing_save):
            with self.assertRaises(OSError):
                service.add_document(original, 2027, 'ics', active=True)
        self.assertEqual(service.documents(), before_documents)
        self.assertEqual(service.events(), before_events)

    def make_service(self, fail_next=False):
        def fetch(url):
            if url.endswith('/calendar/'):
                return b'<p>Bergheim und Kenten 2027 <a href="/2027.pdf">PDF</a></p><p>Bergheim und Kenten 2026 <a href="/2026.pdf">PDF</a></p>'
            if fail_next and '2027' in url:
                raise OSError('Not published yet')
            return (FIXTURES / ('bergheim-2027.pdf' if '2027' in url else 'bergheim-2026.pdf')).read_bytes()
        service = Service(Path(self.temp.name), fetch=fetch, today=lambda: date(2026, 11, 18))
        config = service.config()
        config['overview_url'] = 'https://swbm.de/calendar/'
        service.save_config(config)
        return service

    def test_preview_does_not_change_active_rules_and_save_persists(self):
        service = self.make_service()
        service.refresh()
        before = service.config()
        document = next(d for d in service.documents() if d['year'] == 2027)
        draft = [dict(r) for r in before['rules']]
        draft[0]['pattern'] = 'Biotonne'
        preview = service.preview(document['id'], draft)
        self.assertEqual(preview['counts']['rest'], 43)
        self.assertEqual(service.config(), before)
        self.assertEqual(sum(e['rule_id'] == 'rest' and e['date'].startswith('2027') for e in service.events()), 26)
        service.save_config({**before, 'rules': draft})
        restored = Service(Path(self.temp.name))
        self.assertEqual(restored.config()['rules'][0]['pattern'], 'Biotonne')
        self.assertEqual(sum(e['rule_id'] == 'rest' and e['date'].startswith('2027') for e in restored.events()), 43)

    def test_unpublished_next_year_keeps_current_year(self):
        service = self.make_service(fail_next=True)
        service.refresh()
        self.assertEqual(len(service.events()), 109)
        self.assertTrue(service.status()['errors'])

    def test_failed_refresh_retains_last_good_documents(self):
        service = self.make_service()
        service.refresh()
        before = service.events()
        service.fetch = lambda url: (_ for _ in ()).throw(OSError('offline'))
        service.refresh()
        self.assertEqual(service.events(), before)
        self.assertTrue(service.status()['errors'])


if __name__ == '__main__':
    unittest.main()
