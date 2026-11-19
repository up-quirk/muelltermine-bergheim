"""Download official test inputs; original documents are not redistributed."""
from pathlib import Path
import json
from muelltermine.sources import download

ROOT = Path(__file__).resolve().parents[1] / 'tests' / 'fixtures'
FILES = {
    'glessen-2027.pdf': 'https://swbm.de/wp-content/uploads/2026/11/Abfallkalender_Glessen_2027-neu.pdf',
    'bergheim-2026.pdf': 'https://swbm.de/wp-content/uploads/2026/03/abfallkalender_bergheim2026_v2.pdf',
    'bergheim-2027.pdf': 'https://swbm.de/wp-content/uploads/2026/11/Bergheim_und_Kenten_Abfallkalender_2027.pdf',
    'bergheim-2026.ics': 'https://swbm.de/wp-content/uploads/2025/10/Bergheim2026.ics',
    'bergheim-2027.ics': 'https://swbm.de/wp-content/uploads/2026/11/Bergheim_Abfallkalender_2027.ics',
}
if __name__ == '__main__':
    ROOT.mkdir(parents=True, exist_ok=True)
    FILES.update({area['file']: area['url'] for area in json.loads((ROOT / 'areas-2027.json').read_text(encoding='utf-8'))})
    for name, url in FILES.items():
        (ROOT / name).write_bytes(download(url))
        print(f'Downloaded {name}')
