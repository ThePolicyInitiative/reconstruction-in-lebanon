"""Retain a validated Memo dashboard export for this local Streamlit website.

Usage: python -m scripts.import_gazette_export PATH_TO_DASHBOARD_JSON
This reads an existing export only; it does not scrape or classify Gazette items.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from integrated_gazette.data_feed import ROOT, YEARS, SITE_URL, read_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('export', type=Path)
    args = parser.parse_args()
    payload = read_snapshot(args.export)
    output = {key: payload.get(key) for key in ('schema_version', 'revision', 'built_at', 'latest_publication', 'refresh_schedule')}
    output.update(records=[row for row in payload['records'] if row['date'][:4] in YEARS],
                  source='Memo automation / Lebanon Gazette Observatory', source_url=SITE_URL,
                  source_sha256=hashlib.sha256(args.export.read_bytes()).hexdigest())
    if not output['records']:
        raise ValueError('Export contains no records published in 2024–2026')
    target = ROOT / 'integrated_gazette/data/snapshot.json.gz'
    target.parent.mkdir(exist_ok=True)
    temp = target.with_suffix('.tmp')
    temp.write_bytes(gzip.compress(json.dumps(output, ensure_ascii=False, separators=(',', ':')).encode('utf-8'), mtime=0))
    temp.replace(target)
    print(json.dumps({'records': len(output['records']), 'latest_publication': output['latest_publication'], 'revision': output['revision']}))


if __name__ == '__main__':
    main()
