"""Keep reviewed country additions when refreshing the original local archive."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADDITIONS = ROOT / 'data' / 'country_additions.json'


def add_reviewed_countries(original):
    data = deepcopy(original)
    if not ADDITIONS.exists():
        return data
    additions = json.loads(ADDITIONS.read_text(encoding='utf-8'))
    for group in ('parties', 'actors', 'statements'):
        records = {row['id']: row for row in data[group]}
        records.update({row['id']: row for row in additions[group]})
        data[group] = list(records.values())
    data['methodology']['gaps'][:2] = additions['coverage_notes']
    if additions.get('checked'):
        data['checked'] = additions['checked']
    if additions.get('freshness'):
        data['methodology']['freshness'] = additions['freshness']
    return data


def update_saved_page():
    directory = ROOT / 'imported' / 'countries'
    path = directory / 'index.html'
    page = path.read_text(encoding='utf-8')
    marker = 'window.RECONSTRUCTION_DATA ='
    start = page.index(marker) + len(marker)
    start += len(page[start:]) - len(page[start:].lstrip())
    archive, length = json.JSONDecoder().raw_decode(page[start:])
    archive['international'] = add_reviewed_countries(archive['international'])
    serialized = json.dumps(archive, ensure_ascii=False).replace('</', '<\\/')
    path.write_text(page[:start] + serialized + page[start + length:], encoding='utf-8')
    data = archive['international']
    (directory / 'country-statements.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    provenance_path = directory / 'provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    provenance.update({
        'countries': len(data['parties']), 'statements': len(data['statements']),
        'additions_file': 'data/country_additions.json',
        'additions_sha256': hashlib.sha256(ADDITIONS.read_bytes()).hexdigest(),
        'additions_reviewed': json.loads(ADDITIONS.read_text(encoding='utf-8'))['reviewed'],
    })
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'countries': len(data['parties']), 'statements': len(data['statements'])}


if __name__ == '__main__':
    print(json.dumps(update_saved_page()))
