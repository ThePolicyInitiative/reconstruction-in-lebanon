"""Exhaust CDR pagination, refresh changed lots, and queue source-specific alerts."""
from __future__ import annotations

import argparse
import concurrent.futures
import http.cookiejar
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from .build_dashboard import build
from .cdr_parser import BASE, START, STAGES, combine_project, listing, parse_detail
from .monitor import fetch_html, read_json, save_json
from .ppa_parser import now

ROOT = Path(__file__).resolve().parent


class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def fetch(self, url, post=False):
        headers = {'User-Agent': 'Mona2asat-Tender-Monitor/1.0 (+https://github.com/ThePolicyInitiative/mona2asat)',
                   'Referer': START, 'Accept': 'text/html'}
        if post:
            headers.update({'X-Requested-With': 'XMLHttpRequest',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, data=b'' if post else None, headers=headers)
                with self.opener.open(request, timeout=40) as response:
                    return response.read().decode('utf-8-sig')
            except (OSError, urllib.error.URLError) as exc:
                if isinstance(exc, urllib.error.HTTPError) and exc.code in (401, 403, 404):
                    raise
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)


def collect_listing(fetch, page_size=100):
    """Check the visible first page against AJAX; require an explicit empty end."""
    result = {}
    summary = {}
    for stage in STAGES:
        first = listing(fetch(START + '&stage=' + stage), stage)
        if not first:
            # CDR's AJAX endpoint falls back to Ongoing for an empty Others section.
            # Only the actual section page can establish that this section is empty.
            summary[stage] = {'rows': 0, 'pages': 1}
            continue
        stage_rows = []
        seen = set()
        first_batch = None
        for page in range(1000):
            url = BASE + f'/CDR/Pages/LoadMore/LoadMoreProcurments.aspx?1=1&stage={stage}&Limit={page_size}&Offset={page * page_size}'
            batch = listing(fetch(url, post=True), stage, fragment=True)
            if first_batch is None:
                first_batch = batch
                if [r['key'] for r in first] != [r['key'] for r in batch[:len(first)]]:
                    raise ValueError(f'CDR {stage} pagination disagrees with the visible section')
            if not batch:
                break
            if len(batch) > page_size:
                raise ValueError('CDR returned more rows than requested')
            for row in batch:
                if row['key'] in seen:
                    raise ValueError('CDR pagination shifted or repeated rows; no state advanced')
                seen.add(row['key'])
                stage_rows.append(row)
        else:
            raise ValueError('CDR pagination never terminated')
        verify_url = BASE + f'/CDR/Pages/LoadMore/LoadMoreProcurments.aspx?1=1&stage={stage}&Limit={page_size}&Offset=0'
        if listing(fetch(verify_url, post=True), stage, fragment=True) != first_batch:
            raise ValueError('CDR first page changed during scan; no state advanced')
        summary[stage] = {'rows': len(stage_rows), 'pages': page + 1}
        for row in stage_rows:
            if row['key'] in result:
                result[row['key']]['stages'].append(stage)
            else:
                result[row['key']] = row
    if not result:
        raise ValueError('All CDR sections unexpectedly empty; preserving saved data')
    return list(result.values()), summary


def process_scan(data_dir, records, stages, fetch=fetch_html, baseline=False, max_details=50, workers=3):
    state_path = data_dir / 'state.json'
    if baseline:
        if state_path.exists():
            raise ValueError('CDR baseline already exists; refusing to reset alert history')
        state = {'schema_version': 1, 'known_ids': sorted({r['id'] for r in records}, key=int),
                 'listings': {}, 'pending_lots': {}, 'refreshed_on': {}}
        save_json(data_dir / 'alerts.json', {})
        save_json(data_dir / 'index.json', [])
    else:
        if not state_path.exists():
            raise RuntimeError('Missing CDR baseline. Run cdr_monitor.py --baseline first.')
        state = read_json(state_path)
    if state.get('schema_version') != 1 or not isinstance(state.get('known_ids'), list):
        raise ValueError('Invalid CDR baseline state')
    stamp = now()
    pending = state['pending_lots']
    known = set(state['known_ids'])
    for row in records:
        key = row['key']
        changed = state['listings'].get(key) != row
        state['listings'][key] = row
        if changed or not (data_dir / 'lots' / (key + '.json')).exists():
            pending[key] = row
        elif 'Ongoing' in row['stages'] and state['refreshed_on'].get(key) != stamp[:10]:
            pending[key] = row  # Daily refresh of active-lot documents and extensions.
    save_json(state_path, state)
    outbox = read_json(data_dir / 'alerts.json')
    index = {r['id']: r for r in read_json(data_dir / 'index.json')}
    batch = sorted(pending.values(), key=lambda r: (r['id'] in known, int(r['id']), int(r['lot'])))[:max_details]
    failures, updated = [], []
    def get_detail(row):
        detail = parse_detail(row, fetch(row['source_url']))
        if not detail['title']:
            english_row = dict(row, source_url=row['source_url'].replace('/ar/', '/en-us/'))
            english = parse_detail(english_row, fetch(english_row['source_url']))
            detail['english_version'] = english
            detail['title'] = english['title'] or f"CDR procurement {row['id']} (title not supplied)"
            detail['lot_title'] = detail['lot_title'] or english['lot_title']
            detail['source_url'] = english['source_url']
            detail['full_text'] += '\n\nEnglish version: ' + english['full_text']
            urls = {a['url'] for a in detail['attachments']}
            detail['attachments'] += [a for a in english['attachments'] if a['url'] not in urls]
        return detail
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        jobs = {pool.submit(get_detail, row): row for row in batch}
        for future in concurrent.futures.as_completed(jobs):
            row = jobs[future]
            try:
                detail = future.result()
                path = data_dir / 'lots' / (row['key'] + '.json')
                previous = read_json(path) if path.exists() else None
                if previous:
                    unchanged = dict(detail, scraped_at_utc=previous['scraped_at_utc'])
                    if unchanged == previous:
                        detail = previous
                save_json(path, detail)
                state['refreshed_on'][row['key']] = stamp[:10]
                del pending[row['key']]
                updated.append(row['key'])
            except Exception as exc:
                failures.append({'lot': row['key'], 'error': str(exc)})
    groups = {}
    for row in state['listings'].values():
        groups.setdefault(row['id'], []).append(row['key'])
    added = []
    for ident, keys in groups.items():
        paths = [data_dir / 'lots' / (key + '.json') for key in keys]
        # Publish complete projects only; keep the previous snapshot during retries.
        if any(key in pending for key in keys) or not all(path.exists() for path in paths):
            continue
        record, item = combine_project([read_json(path) for path in paths])
        save_json(data_dir / 'tenders' / (ident + '.json'), record)
        index[ident] = item
        if ident not in known:
            outbox.setdefault(ident, {'created_at': stamp, 'status': 'pending'})
            known.add(ident)
            added.append(ident)
    save_json(data_dir / 'index.json', sorted(index.values(), key=lambda r: int(r['id']), reverse=True))
    save_json(data_dir / 'alerts.json', outbox)
    state['known_ids'] = sorted(known, key=int)
    save_json(state_path, state)
    build(data_dir, source=START)
    summary = {'checked_at': stamp, 'stages': stages, 'listed_lots': len(records),
               'listed_tenders': len({r['id'] for r in records}), 'saved_tenders': len(index),
               'new_ids': sorted(added, key=int), 'updated_lots': len(updated),
               'pending_details': len(pending), 'detail_failures': failures}
    path = data_dir / 'status.json'
    previous = read_json(path) if path.exists() else {}
    if updated or failures or previous.get('scan_error') or previous.get('checked_at', '')[:10] != stamp[:10] or previous.get('stages') != stages or previous.get('pending_details') != len(pending):
        save_json(path, summary)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=ROOT / 'data' / 'cdr')
    parser.add_argument('--baseline', action='store_true')
    parser.add_argument('--max-details', type=int, default=50)
    args = parser.parse_args()
    client = Client()
    try:
        records, stages = collect_listing(client.fetch)
    except Exception as exc:
        path = args.data_dir / 'status.json'
        if path.exists():
            status = read_json(path)
            status.update(scan_error=str(exc), failed_at=now())
            save_json(path, status)
        raise
    summary = process_scan(args.data_dir, records, stages, baseline=args.baseline, max_details=args.max_details)
    print(json.dumps(summary, ensure_ascii=False))
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as stream:
            stream.write(f"\n## CDR check\n\nSaved {summary['saved_tenders']} procurements from {len(records)} listed lots. "
                         f"New procurements: {len(summary['new_ids'])}. Pending lot details: {summary['pending_details']}.\n")
    if summary['detail_failures']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
