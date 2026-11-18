from datetime import date, datetime, timedelta, timezone
from hashlib import sha256

from icalendar import Calendar, Event


def render_ics(events):
    calendar = Calendar()
    calendar.add('prodid', '-//up-quirk//Mülltermine Bergheim//DE')
    calendar.add('version', '2.0')
    calendar.add('x-wr-calname', 'Mülltermine Bergheim')
    for item in events:
        when = date.fromisoformat(item['date'])
        event = Event()
        event.add('uid', sha256(f"{item['date']}:{item['rule_id']}".encode()).hexdigest()[:32] + '@muelltermine-bergheim')
        event.add('dtstamp', datetime.now(timezone.utc))
        event.add('dtstart', when)
        event.add('dtend', when + timedelta(days=1))
        event.add('summary', item['name'])
        event.add('description', item['text'])
        calendar.add_component(event)
    return calendar.to_ical()
