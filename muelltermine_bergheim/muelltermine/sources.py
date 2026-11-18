"""Bounded public HTTPS retrieval and discovery independent of filenames."""
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
import ipaddress
import socket
import unicodedata

import regex

MAX_BYTES = 20 * 1024 * 1024


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold().replace('ß', 'ss')) if c.isalnum())


def validate_url(url):
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError('Ungültige Download-URL.')
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Downloads benötigen eine öffentliche HTTPS-URL ohne Zugangsdaten.')
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f'Download-Host nicht erreichbar: {parsed.hostname}') from exc
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Downloads aus privaten oder lokalen Netzen sind nicht erlaubt.')
    return url


class PublicRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url):
    validate_url(url)
    request = Request(url, headers={'User-Agent': 'Muelltermine-Bergheim/0.1 (+https://github.com/up-quirk/muelltermine-bergheim)'})
    with build_opener(PublicRedirects()).open(request, timeout=30) as response:
        if int(response.headers.get('Content-Length', '0')) > MAX_BYTES:
            raise ValueError('Download ist größer als 20 MB.')
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Download ist größer als 20 MB.')
    return data


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.context = ''
        self.links = []
        self.anchor = None
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignored += 1
        if tag in ('p', 'br', 'li', 'div'):
            self.context = ''
        if tag == 'a':
            self.anchor = [dict(attrs).get('href', ''), self.context, '']

    def handle_data(self, data):
        if self.ignored:
            return
        self.context = (self.context + ' ' + data)[-600:]
        if self.anchor is not None:
            self.anchor[2] += data

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignored = max(0, self.ignored - 1)
        if tag == 'a' and self.anchor is not None:
            self.links.append(tuple(self.anchor))
            self.anchor = None


def discover_links(html, overview_url, district, year, link_pattern=''):
    parser = Links()
    parser.feed(html)
    pattern = regex.compile(link_pattern, regex.I) if link_pattern else None
    found = {'pdf': [], 'ics': []}
    district_key = normalize(district)
    # "Bergheim" filenames cover Bergheim und Kenten; other districts keep their own names.
    alias = 'bergheim' if district_key == 'bergheimundkenten' else district_key
    for href, context, title in parser.links:
        url = urljoin(overview_url, href)
        path = urlparse(url).path.lower()
        kind = 'pdf' if path.endswith('.pdf') else 'ics' if path.endswith('.ics') else None
        if kind is None:
            continue
        context = context + ' ' + title
        haystack = normalize(context)
        filename = normalize(path.rsplit('/', 1)[-1])
        if district_key not in haystack and alias not in filename:
            continue
        if str(year) not in context and str(year) not in path:
            continue
        if pattern and not pattern.search(url, timeout=0.025):
            continue
        if url not in found[kind]:
            found[kind].append(url)
    return found


def template_urls(pattern, year):
    if not pattern:
        return []
    urls = []
    publication_years = [year - 1, year] if '{publication_year}' in pattern else [year - 1]
    months = range(12, 0, -1) if '{month}' in pattern else [11]
    for published in publication_years:
        for month in months:
            try:
                url = pattern.format(year=year, publication_year=published, month=f'{month:02}')
            except (KeyError, ValueError, IndexError) as exc:
                raise ValueError('URL-Muster unterstützt nur {year}, {publication_year} und {month}.') from exc
            if url not in urls:
                urls.append(url)
    return urls
