"""Read Memo's existing cloud pipeline; collection stays in its cloud schedule."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPRedirectHandler, build_opener
from uuid import uuid4

from .credentials import site_token
from .data_feed import ROOT, SITE_URL, YEARS, validate, read_snapshot, load_snapshot

CACHE = ROOT / '.cache' / 'gazette'
STATUS_PATH = '/api/pipeline?action=status'
DATA_PATH = '/api/data'


class GazetteFeedError(RuntimeError):
    """Safe UI error; HTTP bodies, headers and credentials are never included."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Site credentials must never follow a redirect to another service.
        return None


class SiteReader:
    def __init__(self, token_provider=site_token):
        self.token_provider = token_provider
        self.opener = build_opener(NoRedirect())

    def get(self, path):
        if path not in (STATUS_PATH, DATA_PATH):
            raise GazetteFeedError('Unsupported Gazette feed request.')
        try:
            token = self.token_provider()
        except (OSError, ValueError):
            token = ''
        if not token:
            raise GazetteFeedError('The private Gazette connection is not configured. Saved records remain available.')
        request = Request(SITE_URL + path, headers={
            'OAI-Sites-Authorization': 'Bearer ' + token,
            'Accept': 'application/json', 'User-Agent': 'Reconstruction-in-Lebanon-Gazette',
        }, method='GET')
        limit = 40_000_000 if path == DATA_PATH else 250_000
        try:
            with self.opener.open(request, timeout=45 if path == DATA_PATH else 20) as response:
                raw = response.read(limit + 1)
            if len(raw) > limit:
                raise ValueError('Oversized response')
            value = json.loads(raw)
            if not isinstance(value, dict):
                raise ValueError('Unexpected response')
            return value
        except HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308, 401, 403):
                raise GazetteFeedError('Memo automation could not authenticate the Gazette connection. Saved records remain available; the connection needs attention.') from None
            raise GazetteFeedError('Memo automation is temporarily unavailable. The Gazette connection will retry automatically.') from None
        except (OSError, URLError, ValueError):
            raise GazetteFeedError('The Gazette cloud feed could not be read. Saved records remain available while the connection retries.') from None


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)


def protect_owner_fields(previous, incoming):
    lookup = {r['id']: r for r in incoming['records']}
    for row in previous.get('records', []):
        if row.get('method') != 'owner-workbook':
            continue
        new = lookup.get(row['id'])
        keys = ('nature', 'admin_function', 'major', 'sub', 'method')
        if not new or any(row[k] != new[k] for k in keys):
            raise ValueError('Owner-supplied classification differs')


def dashboard_snapshot(payload):
    rows = sorted((r for r in payload['records'] if r['date'][:4] in YEARS),
                  key=lambda r: (r['date'], int(r['id']) if r['id'].isdigit() else 0), reverse=True)
    return {'records': rows, 'latest_publication': max((r['date'] for r in rows), default=None),
            'built_at': payload.get('built_at'), 'revisions': [payload.get('revision')],
            'invalid_exports': [], 'refresh_schedule': payload.get('refresh_schedule')}


class CloudGazetteFeed:
    def __init__(self, reader=None, cache=CACHE, clock=time.monotonic):
        self.reader = reader or SiteReader()
        self.cache = Path(cache)
        self.clock = clock
        self.lock = threading.Lock()
        self.next_check = 0
        self.payload = None
        self.state = {}
        self.error = None
        self.live = False
        try:
            self.payload = read_snapshot(self.cache / 'cloud.json')
            saved_state = json.loads((self.cache / 'connection.json').read_text(encoding='utf-8'))
            if isinstance(saved_state, dict) and saved_state.get('revision') == self.payload.get('revision'):
                self.state = {key: saved_state.get(key) for key in (
                    'connected_at', 'revision', 'records', 'latest_publication',
                    'source_configured', 'pending_records', 'pending_memos')}
        except (OSError, ValueError, TypeError, KeyError, EOFError):
            pass

    def refresh(self, force=False):
        with self.lock:
            if force or self.clock() >= self.next_check:
                self.next_check = self.clock() + 60
                try:
                    status = self.reader.get(STATUS_PATH)
                    dashboard = status.get('dashboard', {})
                    revision = dashboard.get('revision')
                    if not isinstance(revision, str) or not revision or not isinstance(dashboard.get('records'), int):
                        raise ValueError('Invalid cloud status')
                    changed = not self.payload or self.payload.get('revision') != revision
                    if changed:
                        incoming = validate(self.reader.get(DATA_PATH))
                        if incoming.get('revision') != revision:
                            # A collection can finish between status and data requests.
                            status = self.reader.get(STATUS_PATH)
                            dashboard = status.get('dashboard', {})
                        if incoming.get('revision') != dashboard.get('revision') or len(incoming['records']) != dashboard.get('records'):
                            raise ValueError('Cloud revision changed during read')
                        protected = self.payload
                        if protected is None:
                            protected = read_snapshot(ROOT / 'integrated_gazette/data/snapshot.json.gz')
                        protect_owner_fields(protected, incoming)
                        atomic_json(self.cache / 'cloud.json', incoming)
                        self.payload = incoming
                    elif len(self.payload['records']) != dashboard['records']:
                        raise ValueError('Cloud record count does not match revision')
                    checked = datetime.now(timezone.utc).isoformat()
                    self.state = {'connected_at': checked, 'revision': self.payload['revision'],
                                  'records': len(self.payload['records']),
                                  'latest_publication': self.payload.get('latest_publication'),
                                  'source_configured': status.get('source_configured'),
                                  'pending_records': status.get('new_records_pending'),
                                  'pending_memos': status.get('memos_pending')}
                    atomic_json(self.cache / 'connection.json', self.state)
                    self.live, self.error = True, None
                except GazetteFeedError as exc:
                    self.live, self.error = False, str(exc)
                except (OSError, ValueError, TypeError, KeyError):
                    self.live = False
                    self.error = 'The new Gazette data could not be verified. The last valid records remain available and the connection will retry.'
                finally:
                    self.next_check = self.clock() + 60
            snapshot = dashboard_snapshot(self.payload) if self.payload else load_snapshot()
            return {'snapshot': snapshot, 'live': self.live, 'error': self.error, **self.state}
