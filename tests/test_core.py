import unittest
from collections import Counter
from datetime import date
from pathlib import Path

try:
    from muelltermine.parsers import parse_pdf, parse_ics
    from muelltermine.rules import evaluate, default_rules
    from muelltermine.calendar import render_ics
except ImportError:
    parse_pdf = parse_ics = evaluate = default_rules = render_ics = None

FIXTURES = Path(__file__).parent / 'fixtures'


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(parse_pdf, 'Core parser is not implemented')

    def test_official_pdf_dates_and_bin_counts(self):
        for year, bio in [(2026, 44), (2027, 43)]:
            records = parse_pdf((FIXTURES / f'bergheim-{year}.pdf').read_bytes(), year)
            result = evaluate(records, default_rules())
            self.assertEqual(Counter(e['rule_id'] for e in result['events']),
                             {'rest': 26, 'gelb': 26, 'bio': bio, 'papier': 13})
        rest = [e['date'] for e in result['events'] if e['rule_id'] == 'rest' and e['date'].startswith('2027-01')]
        self.assertEqual(rest, ['2027-01-05', '2027-01-19'])
        self.assertEqual({e['rule_id'] for e in result['events'] if e['date'] == '2027-01-14'}, {'bio', 'papier'})

    def test_wrong_year_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '2027'):
            parse_pdf((FIXTURES / 'bergheim-2026.pdf').read_bytes(), 2027)

    def test_broken_pdf_has_an_actionable_validation_error(self):
        with self.assertRaises(ValueError):
            parse_pdf(b'%PDF-1.7\ninvalid', 2027)

    def test_ics_and_pdf_produce_same_collections(self):
        for year in (2026, 2027):
            pdf = evaluate(parse_pdf((FIXTURES / f'bergheim-{year}.pdf').read_bytes(), year), default_rules())
            ics = evaluate(parse_ics((FIXTURES / f'bergheim-{year}.ics').read_bytes(), year), default_rules())
            key = lambda r: {(e['date'], e['rule_id']) for e in r['events']}
            self.assertEqual(key(pdf), key(ics))

    def test_invalid_and_empty_patterns_are_rejected(self):
        for pattern in ('[', ''):
            with self.assertRaises(ValueError):
                evaluate([], [{'id': 'test', 'name': 'Test', 'pattern': pattern, 'enabled': True}])

    def test_export_uses_stable_uids_and_exclusive_end_date(self):
        from icalendar import Calendar
        events = [{'date': '2027-01-05', 'rule_id': 'rest', 'name': 'Restmüll', 'text': 'Hausmüll', 'page': 1}]
        a, b = render_ics(events), render_ics(events)
        ca, cb = Calendar.from_ical(a), Calendar.from_ical(b)
        ea, eb = ca.walk('VEVENT')[0], cb.walk('VEVENT')[0]
        self.assertEqual(ea.decoded('dtstart'), date(2027, 1, 5))
        self.assertEqual(ea.decoded('dtend'), date(2027, 1, 6))
        self.assertEqual(ea['uid'], eb['uid'])


if __name__ == '__main__':
    unittest.main()
