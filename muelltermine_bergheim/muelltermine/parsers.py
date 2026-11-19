"""Read dated records, without assigning waste types or depending on HA."""
from datetime import date, datetime
from io import BytesIO
import re

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException
from icalendar import Calendar

from .models import Record

WEEKDAYS = {'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'}
MONTHS = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
          'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']


def parse_pdf(content: bytes, year: int) -> list[Record]:
    try:
        return _parse_pdf(content, year)
    except (PdfminerException, OSError, EOFError) as exc:
        raise ValueError('Das PDF ist beschädigt, verschlüsselt oder kann nicht gelesen werden.') from exc


def _parse_pdf(content: bytes, year: int) -> list[Record]:
    if not content.startswith(b'%PDF-'):
        raise ValueError('Die Datei ist kein PDF.')
    records = {}
    with pdfplumber.open(BytesIO(content)) as pdf:
        if len(pdf.pages) > 12:
            raise ValueError('Das PDF hat zu viele Seiten (maximal 12).')
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
        if not re.search(rf'Abfallkalender\s+(?:Januar bis Juni\s+|Juli bis Dezember\s+)?{year}\b', text, re.I):
            # Current PDFs place the year after "Abfallkalender"; fail closed on unknown layouts.
            raise ValueError(f'Das PDF enthält keinen erkennbaren Abfallkalender für {year}.')
        months_seen = set()
        for page_number, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                if not table or max(map(len, table)) not in (17, 18):
                    continue
                header = next((row for row in table if any(
                    (cell or '').strip() in ('Januar', 'Juli') for cell in row)), None)
                if header is None:
                    continue
                first_month = 1 if any((v or '').strip() == 'Januar' for v in header) else 7
                missing_december_day = len(header) == 17
                if missing_december_day and (first_month != 7 or (header[15] or '').strip() != 'Dezember'):
                    continue
                months_seen.update(range(first_month, first_month + 6))
                for row in table:
                    if missing_december_day and len(row) == 17 and (row[0] or '').strip() in WEEKDAYS and (row[15] or '').strip() not in WEEKDAYS:
                        raise ValueError('Dezember-Wochentag fehlt oder ist nicht erkennbar.')
                    if missing_december_day and len(row) == 17 and (row[15] or '').strip() in WEEKDAYS:
                        # Glessen 2027 omits December's day column. Other months
                        # share the same dated row; require agreement and weekday.
                        days = {(row[i] or '').strip() for i in (1, 4, 7, 10, 13)
                                if (row[i] or '').strip().isdigit()}
                        if len(days) != 1:
                            raise ValueError('Dezember-Tag kann nicht eindeutig aus der Tabellenzeile bestimmt werden.')
                        day_text = next(iter(days))
                        when = date(year, 12, int(day_text))
                        if (row[15] or '').strip() != ('Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So')[when.weekday()]:
                            raise ValueError('Dezember-Wochentag passt nicht zum Datum der Tabellenzeile.')
                        row = row[:16] + [day_text] + row[16:]
                    if len(row) != 18:
                        continue
                    for col in range(6):
                        weekday, day, label = row[col * 3:col * 3 + 3]
                        if (weekday or '').strip() not in WEEKDAYS or not (day or '').strip().isdigit():
                            continue
                        try:
                            when = date(year, first_month + col, int(day.strip()))
                        except ValueError:
                            continue
                        value = re.sub(r'\s+', ' ', label or '').strip()
                        if value:
                            records[(when.isoformat(), value)] = Record(when.isoformat(), value, page_number)
        if len(months_seen) != 12 or not records:
            raise ValueError('Keine vollständige Bergheimer Jahrestabelle erkannt. Text-PDF mit sechs Monaten je Seite erforderlich.')
    return sorted(records.values(), key=lambda r: (r.date, r.text))


def parse_ics(content: bytes, year: int) -> list[Record]:
    try:
        calendar = Calendar.from_ical(content)
        records = []
        for event in calendar.walk('VEVENT'):
            when = event.decoded('dtstart')
            if isinstance(when, datetime):
                when = when.date()
            if not isinstance(when, date):
                raise ValueError('Ungültiges Ereignisdatum.')
            if event.get('rrule'):
                raise ValueError('Wiederholungsregeln werden für diese Jahresdateien nicht unterstützt.')
            if when.year == year and event.get('summary'):
                records.append(Record(when.isoformat(), str(event['summary']).strip()))
        if not records:
            raise ValueError(f'Keine Termine für {year} gefunden.')
        return sorted(set(records), key=lambda r: (r.date, r.text))
    except (KeyError, TypeError) as exc:
        raise ValueError('Ungültige iCalendar-Datei.') from exc
