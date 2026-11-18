"""One bounded matching engine for both preview and production calendars."""
import regex


def default_rules():
    return [
        {'id': 'rest', 'name': 'Restmüll', 'pattern': r'(?:^| / )Hausmüll(?:$| / )', 'color': '#64748b', 'enabled': True, 'case_sensitive': False},
        {'id': 'gelb', 'name': 'Gelbe Tonne', 'pattern': r'gelbe To(?:nne)?\.?', 'color': '#d99a0b', 'enabled': True, 'case_sensitive': False},
        {'id': 'bio', 'name': 'Biotonne', 'pattern': 'Biotonne', 'color': '#39805b', 'enabled': True, 'case_sensitive': False},
        {'id': 'papier', 'name': 'Papiertonne', 'pattern': 'blaue Tonne', 'color': '#3774bd', 'enabled': True, 'case_sensitive': False},
    ]


def validate_rules(rules):
    if not isinstance(rules, list) or not 1 <= len(rules) <= 30:
        raise ValueError('Bitte 1 bis 30 Tonnenregeln anlegen.')
    compiled = []
    ids = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError('Ungültige Tonnenregel.')
        key, name, pattern = rule.get('id', ''), rule.get('name', ''), rule.get('pattern', '')
        if not isinstance(key, str) or not regex.fullmatch(r'[a-zA-Z0-9_-]{1,40}', key) or key in ids:
            raise ValueError('Jede Tonne benötigt eine eindeutige ID (Buchstaben, Ziffern, _ oder -).')
        if not isinstance(name, str) or not name.strip() or len(name) > 100:
            raise ValueError('Der Tonnenname muss 1 bis 100 Zeichen lang sein.')
        if not isinstance(pattern, str) or not pattern.strip() or len(pattern) > 500:
            raise ValueError(f'{name}: Suchmuster muss 1 bis 500 Zeichen lang sein.')
        for flag in ('enabled', 'case_sensitive'):
            if flag in rule and not isinstance(rule[flag], bool):
                raise ValueError(f'{name}: Ungültige Einstellung {flag}.')
        color = rule.get('color', '#64748b')
        if not isinstance(color, str) or not regex.fullmatch(r'#[0-9a-fA-F]{6}', color):
            raise ValueError(f'{name}: Ungültige Farbe.')
        try:
            expression = regex.compile(pattern, 0 if rule.get('case_sensitive', False) else regex.IGNORECASE)
            if expression.search('', timeout=0.02):
                raise ValueError(f'{name}: Suchmuster darf nicht den leeren Text treffen.')
        except (regex.error, TimeoutError) as exc:
            raise ValueError(f'{name}: Ungültiges oder zu aufwendiges Suchmuster: {exc}') from exc
        ids.add(key)
        compiled.append((rule, expression))
    return compiled


def evaluate(records, rules):
    compiled = validate_rules(rules)
    events = {}
    matches = []
    counts = {rule['id']: 0 for rule in rules}
    for record in records:
        for rule, expression in compiled:
            if not rule.get('enabled', True):
                continue
            try:
                found = list(expression.finditer(record.text, timeout=0.025))
            except TimeoutError as exc:
                raise ValueError(f"{rule['name']}: Suchmuster benötigt zu viel Rechenzeit.") from exc
            if found:
                event = {**record.as_dict(), 'rule_id': rule['id'], 'name': rule['name'], 'color': rule.get('color', '#64748b')}
                events[(record.date, rule['id'])] = event
                matches.append({**event, 'spans': [{'start': m.start(), 'end': m.end()} for m in found if m.end() > m.start()]})
    ordered = sorted(events.values(), key=lambda e: (e['date'], e['rule_id']))
    for event in ordered:
        counts[event['rule_id']] += 1
    return {'events': ordered, 'matches': matches, 'counts': counts}
