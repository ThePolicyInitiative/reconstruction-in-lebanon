"""Read Mona2asat's monitored GitHub data without running a second monitor."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

REPOSITORY = 'ThePolicyInitiative/mona2asat'
BRANCH = 'master'
ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parent / '.cache' / 'mona2asat'


class FeedError(RuntimeError):
    """A user-safe connection error; never includes credentials or HTTP bodies."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def github_token():
    """Use an existing sign-in, in memory only; never prompt or persist a token."""
    token = os.environ.get('MONA2ASAT_GITHUB_TOKEN', '').strip()
    if token:
        return token
    try:
        import streamlit as st
        token = str(st.secrets.get('MONA2ASAT_GITHUB_TOKEN', '')).strip()
        if token:
            return token
    except (FileNotFoundError, KeyError):
        pass
    executable = shutil.which('git')
    if not executable:
        raise FeedError('GitHub read access is not configured on this computer.')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_TRACE', 'GCM_TRACE'))}
    env.update(GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    try:
        result = subprocess.run(
            [executable, '-c', 'credential.interactive=never', 'credential', 'fill'],
            input='protocol=https\nhost=github.com\n\n', text=True,
            capture_output=True, env=env, timeout=25,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.TimeoutExpired):
        raise FeedError('The saved GitHub sign-in could not be read.') from None
    credential = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if result.returncode or not credential.get('password'):
        raise FeedError('The saved GitHub sign-in is unavailable.')
    return credential['password']


class GitHubReader:
    def __init__(self):
        self._token = None
        self._token_time = 0
        self._auth_lock = threading.Lock()

    def get(self, path, raw=False):
        with self._auth_lock:
            if not self._token or time.monotonic() - self._token_time > 900:
                self._token = github_token()
                self._token_time = time.monotonic()
            token = self._token
        request = Request('https://api.github.com/repos/' + REPOSITORY + path, headers={
            'Authorization': 'Bearer ' + token,
            'Accept': 'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
            'User-Agent': 'Reconstruction-in-Lebanon',
        })
        try:
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            if exc.code in (401, 403, 404):
                self._token = None
                raise FeedError('GitHub could not provide this Mona2asat record. Check repository access or its original source link.') from None
            raise FeedError('GitHub is temporarily unavailable.') from None
        except (OSError, URLError, ValueError):
            raise FeedError('Mona2asat could not be reached. The saved data remains available.') from None

    def head(self):
        return self.get('/git/ref/heads/' + quote(BRANCH, safe=''))['object']['sha']

    def file(self, path, revision):
        return self.get('/contents/' + quote(path, safe='/') + '?ref=' + revision, raw=True)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.' + uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def validate_source(payload, status):
    rows = payload.get('tenders')
    if payload.get('schema_version') != 1 or not isinstance(rows, list) or payload.get('total') != len(rows):
        raise FeedError('Mona2asat returned incomplete data; keeping the last successful version.')
    if not isinstance(status, dict) or not status.get('checked_at'):
        raise FeedError('Mona2asat returned an invalid monitor status.')
    if len({str(row['id']) for row in rows}) != len(rows):
        raise FeedError('Mona2asat returned duplicate records; keeping the last successful version.')


class TenderFeed:
    def __init__(self, cache=CACHE, bundled=ROOT / 'data', reader=None, clock=time.monotonic):
        self.cache, self.bundled = Path(cache), Path(bundled)
        self.reader = reader or GitHubReader()
        self.clock = clock
        self._lock = threading.Lock()
        self._last_attempt = None
        self._last_success = None
        self._error = None
        self._snapshot = None
        self._restore()

    def _restore(self):
        try:
            pointer = json.loads((self.cache / 'current.json').read_text(encoding='utf-8'))
            revision = pointer['revision']
            if not re.fullmatch(r'[0-9a-f]{40}', revision):
                return
            sources = {}
            for source in ('ppa', 'cdr'):
                directory = self.cache / revision / source
                payload = json.loads((directory / 'dashboard.json').read_text(encoding='utf-8'))
                status = json.loads((directory / 'status.json').read_text(encoding='utf-8'))
                validate_source(payload, status)
                sources[source] = (payload, status)
            self._snapshot = {'revision': revision, 'sources': sources}
            self._last_success = pointer.get('connected_at')
        except (OSError, ValueError, KeyError, TypeError, FeedError):
            pass

    def _fallback(self):
        sources = {}
        for source, directory in [('ppa', self.bundled), ('cdr', self.bundled / 'cdr')]:
            payload = json.loads((directory / 'dashboard.json').read_text(encoding='utf-8'))
            status = json.loads((directory / 'status.json').read_text(encoding='utf-8'))
            validate_source(payload, status)
            sources[source] = (payload, status)
        return {'revision': None, 'sources': sources}

    def refresh(self, force=False):
        with self._lock:
            now = self.clock()
            if force or self._last_attempt is None or now - self._last_attempt >= 60:
                self._last_attempt = now
                try:
                    revision = self.reader.head()
                    if not re.fullmatch(r'[0-9a-f]{40}', revision):
                        raise FeedError('Mona2asat returned an invalid data revision.')
                    if not self._snapshot or revision != self._snapshot['revision']:
                        paths = {f'{source}/{kind}': f'data/{"cdr/" if source == "cdr" else ""}{kind}.json'
                                 for source in ('ppa', 'cdr') for kind in ('dashboard', 'status')}
                        with ThreadPoolExecutor(max_workers=4) as pool:
                            jobs = {key: pool.submit(self.reader.file, path, revision) for key, path in paths.items()}
                            received = {key: job.result() for key, job in jobs.items()}
                        sources = {}
                        for source in ('ppa', 'cdr'):
                            payload, status = received[f'{source}/dashboard'], received[f'{source}/status']
                            validate_source(payload, status)
                            sources[source] = (payload, status)
                        # Publish a revision only after both datasets and statuses validate.
                        for key, value in received.items():
                            write_json(self.cache / revision / (key + '.json'), value)
                        connected_at = utc_now()
                        write_json(self.cache / 'current.json', {'revision': revision, 'connected_at': connected_at})
                        self._snapshot = {'revision': revision, 'sources': sources}
                    self._last_success = utc_now()
                    self._error = None
                except (FeedError, OSError, ValueError, KeyError, TypeError):
                    self._error = 'Unable to refresh from Mona2asat. Showing the last saved data; automatic retries continue every minute.'
            snapshot = self._snapshot or self._fallback()
            return {**snapshot, 'connected_at': self._last_success, 'error': self._error,
                    'live': self._snapshot is not None and self._error is None}

    def detail(self, source, identifier, revision):
        if source not in ('ppa', 'cdr') or not re.fullmatch(r'\d+', str(identifier)):
            raise FeedError('Invalid tender identifier.')
        if revision is None:
            directory = self.bundled / ('cdr' if source == 'cdr' else '')
            return json.loads((directory / 'tenders' / f'{identifier}.json').read_text(encoding='utf-8'))
        if not re.fullmatch(r'[0-9a-f]{40}', revision):
            raise FeedError('Invalid tender data revision.')
        path = self.cache / revision / source / 'tenders' / f'{identifier}.json'
        if path.exists():
            return json.loads(path.read_text(encoding='utf-8'))
        record = self.reader.file(f'data/{"cdr/" if source == "cdr" else ""}tenders/{identifier}.json', revision)
        if not isinstance(record, dict):
            raise FeedError('The complete tender record is unavailable.')
        write_json(path, record)
        return record
