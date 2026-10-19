"""Import the supplied Countries archive without changing the Parties archive."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.request import urlopen

from scripts.import_requested_pages import embed_page
from scripts.install_localization import install
from scripts.country_content import add_reviewed_countries, update_saved_page

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = 'http://127.0.0.1:8787/?view=countries'


def import_countries(source):
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', source, re.S)
    data_script = next(script for script in scripts if 'window.RECONSTRUCTION_DATA =' in script)
    archive, _ = json.JSONDecoder().raw_decode(data_script.split('=', 1)[1].lstrip())
    countries = add_reviewed_countries(archive['international'])
    if not countries['parties'] or not countries['statements']:
        raise ValueError('The source must contain country and statement records.')
    for statement in countries['statements']:
        if not statement['url'].startswith('https://'):
            raise ValueError('Missing source link in a country statement.')

    page = source.replace('data-view="comparison"', 'data-view="countries"', 1)
    # The adjacent Streamlit tab already provides the Lebanese-party archive.
    # Keep these IDs for the original navigation script, but hide duplicate links.
    page = page.replace('</head>', '<style>#comparison-link,#source-scope{display:none!important}</style></head>')
    directory = ROOT / 'imported' / 'countries'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'index.html').write_text(embed_page(page), encoding='utf-8')
    (directory / 'country-statements.json').write_text(json.dumps(countries, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provenance = {
        'source_url': SOURCE_URL,
        'imported_at': datetime.now(timezone.utc).isoformat(),
        'source_sha256': hashlib.sha256(source.encode('utf-8')).hexdigest(),
        'research_checked': countries['checked'],
        'countries': len(countries['parties']),
        'statements': len(countries['statements']),
    }
    (directory / 'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    update_saved_page()
    install()
    return provenance


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', type=Path, help='Import a previously saved copy of the supplied page.')
    args = parser.parse_args()
    if args.file:
        source = args.file.read_text(encoding='utf-8')
    else:
        with urlopen(SOURCE_URL, timeout=20) as response:
            source = response.read().decode('utf-8')
    print(json.dumps(import_countries(source), ensure_ascii=False))
