"""Read retained Memo automation exports without changing its source or labels."""
from __future__ import annotations

from datetime import date, datetime, timezone
import gzip
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
YEARS = ('2026', '2025', '2024')
SITE_URL = 'https://lebanon-gazette-observatory.tpichatgpt.chatgpt.site'
DEFAULT_MEMO_EXPORT = Path.home() / 'Desktop' / 'Memo automation' / 'sites' / 'gazette-dashboard' / 'work' / 'dashboard.json'
FIELDS = ('id', 'date', 'type', 'number', 'title', 'nature', 'admin_function', 'major', 'sub', 'method', 'status', 'url', 'review_reasons', 'doc_date')


def source_paths():
    return [Path(__file__).parent / 'data' / 'snapshot.json.gz',
            ROOT / '.cache' / 'gazette' / 'cloud.json',
            Path(os.environ.get('GAZETTE_MEMO_EXPORT', str(DEFAULT_MEMO_EXPORT)))]


def fingerprint(paths=None):
    result = []
    for path in paths or source_paths():
        try:
            stat = path.stat()
            result.append((str(path), stat.st_mtime_ns, stat.st_size))
        except OSError:
            result.append((str(path), None, None))
    return tuple(result)


def validate(payload):
    records = payload.get('records')
    if not isinstance(records, list) or not records:
        raise ValueError('Empty Gazette export')
    seen = set()
    for row in records:
        if not isinstance(row, dict) or any(key not in row for key in FIELDS):
            raise ValueError('Incomplete Gazette record')
        if not isinstance(row['id'], str) or row['id'] in seen:
            raise ValueError('Duplicate Gazette record')
        seen.add(row['id'])
        date.fromisoformat(row['date'])
        if row['type'] not in ('قرار', 'مرسوم', 'قانون'):
            raise ValueError('Unsupported Gazette document type')
        if any(not isinstance(row[k], str) for k in FIELDS if k != 'doc_date'):
            raise ValueError('Invalid Gazette source field')
        link = urlsplit(row['url'])
        if link.scheme != 'https' or link.netloc != 'jo.pcm.gov.lb':
            raise ValueError('Unexpected Gazette source URL')
    return payload


def build_time(payload):
    try:
        return datetime.fromisoformat(payload['built_at'].replace('Z', '+00:00')).astimezone(timezone.utc)
    except (KeyError, ValueError, TypeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def read_snapshot(path):
    raw = path.read_bytes()
    if path.suffix == '.gz':
        raw = gzip.decompress(raw)
    return validate(json.loads(raw))


def load_snapshot(paths=None):
    """Newest saved field values win; retain newly collected cloud-only IDs.

    Source reads are atomic from the consumer's perspective: malformed/in-progress
    exports are ignored as a whole. A valid retained export stays available.
    No login token or portal credential is part of these snapshots.
    """
    snapshots, failed = [], []
    for path in paths or source_paths():
        if not path.exists():
            continue
        try:
            snapshots.append(read_snapshot(path))
        except (OSError, ValueError, TypeError, KeyError, EOFError):
            failed.append(path.name)
    if not snapshots:
        raise ValueError('No valid Memo automation export is available')
    records = {}
    revisions = []
    snapshots.sort(key=build_time)
    for snapshot in snapshots:
        for row in snapshot['records']:
            if row['date'][:4] in YEARS:
                records[row['id']] = dict(row)
        if snapshot.get('revision') not in revisions:
            revisions.append(snapshot.get('revision'))
    latest = snapshots[-1]
    ordered = sorted(records.values(), key=lambda r: (r['date'], int(r['id']) if r['id'].isdigit() else 0), reverse=True)
    return {'records': ordered, 'latest_publication': max((r['date'] for r in ordered), default=None),
            'built_at': latest.get('built_at'), 'revisions': revisions, 'invalid_exports': failed,
            'refresh_schedule': latest.get('refresh_schedule', 'Monday 09:00 Asia/Beirut')}
