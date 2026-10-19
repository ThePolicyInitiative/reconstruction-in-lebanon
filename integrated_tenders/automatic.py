"""Collect public PPA/CDR notices in the running app, independently of GitHub Actions."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import threading
import time

from .live_data import ROOT, FeedError, TenderFeed, validate_source, write_json

CACHE = ROOT.parent / '.cache' / 'tender-monitor'
SOURCES = ('ppa', 'cdr')
INTERVAL = 30 * 60
RETRY_INTERVAL = 5 * 60
LOG = logging.getLogger(__name__)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def stamp(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


@contextmanager
def scan_lock(directory):
    """An OS lock is released even if the server exits during collection."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / 'scan.lock').open('a+b') as handle:
        handle.seek(0, 2)
        if not handle.tell():
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        acquired = False
        try:
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (OSError, BlockingIOError):
                pass
            yield acquired
        finally:
            if acquired:
                handle.seek(0)
                if os.name == 'nt':
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(handle, fcntl.LOCK_UN)


class SnapshotStore:
    """Immutable objects keep each table, detail view and download consistent."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self._object_lock = threading.Lock()

    def put(self, value):
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        key = hashlib.sha256(raw.encode('utf-8')).hexdigest()
        path = self.directory / 'objects' / (key + '.json')
        with self._object_lock:
            if not path.exists():
                write_json(path, value)
        return key

    def get(self, key):
        if not re.fullmatch(r'[0-9a-f]{64}', key):
            raise FeedError('Invalid tender data revision.')
        return read_json(self.directory / 'objects' / (key + '.json'))

    def manifest(self, revision=None):
        if revision is None:
            pointer = self.directory / 'current.json'
            if not pointer.exists():
                return {'sources': {}}
            revision = read_json(pointer)['revision']
        if not re.fullmatch(r'local-[0-9a-f]{64}', revision):
            raise FeedError('Invalid tender data revision.')
        return self.get(revision[6:])

    def prepare(self, directory, status):
        payload = read_json(directory / 'dashboard.json')
        validate_source(payload, status)
        details = {}
        for row in payload['tenders']:
            identifier = str(row['id'])
            if not re.fullmatch(r'\d+', identifier):
                raise FeedError('Invalid tender identifier.')
            record = read_json(directory / 'tenders' / (identifier + '.json'))
            if str(record.get('id')) != identifier:
                raise FeedError('The complete tender record is unavailable.')
            details[identifier] = self.put(record)
        return {'dashboard': self.put(payload), 'status': status, 'details': details}

    def publish(self, sources):
        revision = 'local-' + self.put({'sources': sources})
        write_json(self.directory / 'current.json', {'revision': revision})
        return revision

    def snapshot(self):
        pointer = self.directory / 'current.json'
        if not pointer.exists():
            return None
        revision = read_json(pointer)['revision']
        manifest = self.manifest(revision)
        sources = {}
        for source, item in manifest['sources'].items():
            payload = self.get(item['dashboard'])
            validate_source(payload, item['status'])
            sources[source] = (payload, item['status'])
        return {'revision': revision, 'sources': sources}

    def detail(self, source, identifier, revision):
        if source not in SOURCES or not re.fullmatch(r'\d+', str(identifier)):
            raise FeedError('Invalid tender identifier.')
        try:
            key = self.manifest(revision)['sources'][source]['details'][str(identifier)]
            return self.get(key)
        except KeyError:
            raise FeedError('The complete tender record is unavailable.') from None


def bootstrap(directory, source, bundled):
    """Rebuild collector state from packaged full records on a fresh installation."""
    if (directory / 'state.json').exists():
        return
    from .collectors.monitor import compact_index
    from .collectors.cdr_parser import combine_project

    original = bundled / ('cdr' if source == 'cdr' else '')
    directory.mkdir(parents=True, exist_ok=True)
    shutil.copytree(original / 'tenders', directory / 'tenders', dirs_exist_ok=True)
    index, known, listings, refreshed = [], [], {}, {}
    for path in sorted((directory / 'tenders').glob('*.json')):
        record = read_json(path)
        known.append(str(record['id']))
        if source == 'ppa':
            index.append(compact_index(record))
        else:
            _, item = combine_project(record['lots'])
            index.append(item)
            for lot in record['lots']:
                listing = lot['listing']
                key = listing['key']
                write_json(directory / 'lots' / (key + '.json'), lot)
                listings[key] = listing
                refreshed[key] = lot.get('scraped_at_utc', '')[:10]
    for filename in ('dashboard.json', 'status.json'):
        shutil.copyfile(original / filename, directory / filename)
    write_json(directory / 'index.json', index)
    write_json(directory / 'alerts.json', {})  # The notification module is not included.
    state = {'schema_version': 1, 'known_ids': known}
    if source == 'ppa':
        state['pending_details'] = {}
    else:
        state.update(listings=listings, refreshed_on=refreshed, pending_lots={})
    write_json(directory / 'state.json', state)  # Commit initialization last.


def collect(source, directory):
    from .collectors import monitor, cdr_monitor, build_dashboard
    if source == 'ppa':
        records, pages = monitor.collect_listing()
        status = monitor.process_scan(directory, records, pages, max_new=50)
        build_dashboard.build(directory)
    else:
        client = cdr_monitor.Client()
        records, stages = cdr_monitor.collect_listing(client.fetch)
        status = cdr_monitor.process_scan(directory, records, stages, max_details=50)
    # Record each real completed listing check, including checks without new notices.
    status.update(checked_at=stamp(time.time()), collection_method='direct')
    write_json(directory / 'status.json', status)
    return status


class LocalMonitor:
    def __init__(self, directory=CACHE, bundled=ROOT / 'data', collector=collect, clock=time.time):
        self.directory, self.bundled = Path(directory), Path(bundled)
        self.store = SnapshotStore(self.directory)
        self.collector, self.clock = collector, clock
        self._thread = None
        self._thread_lock = threading.Lock()
        self._wake = threading.Event()
        self._stop = threading.Event()

    def working(self, source):
        return self.directory / 'working' / ('cdr' if source == 'cdr' else '')

    def state(self):
        try:
            return read_json(self.directory / 'worker-state.json')
        except (OSError, ValueError):
            return {'sources': {}}

    def request(self):
        # A request remains pending across reruns and process restarts.
        write_json(self.directory / 'request.json', {'requested_at': self.clock()})
        self._wake.set()

    def tick(self):
        with scan_lock(self.directory) as acquired:
            if not acquired:
                return False
            state = self.state()
            now = self.clock()
            try:
                request = read_json(self.directory / 'request.json')['requested_at']
            except (OSError, ValueError, KeyError):
                request = 0
            forced = request > state.get('handled_request', 0)
            due = [s for s in SOURCES if forced or now >= state['sources'].get(s, {}).get('next_check', 0)]
            state.update(worker_heartbeat=stamp(now), worker_pid=os.getpid(), running=due)
            write_json(self.directory / 'worker-state.json', state)
            if not due:
                return False
            published = self.store.manifest()['sources']

            def run(source):
                directory = self.working(source)
                bootstrap(directory, source, self.bundled)
                status = self.collector(source, directory)
                item = self.store.prepare(directory, status)
                return item

            with ThreadPoolExecutor(max_workers=2) as pool:
                jobs = {pool.submit(run, source): source for source in due}
                for job in as_completed(jobs):
                    source = jobs[job]
                    previous = state['sources'].get(source, {})
                    try:
                        item = job.result()
                        # Publish each source independently; a failed source retains its old data.
                        candidate = {**published, source: item}
                        self.store.publish(candidate)
                        published = candidate
                        incomplete = bool(item['status'].get('pending_details') or item['status'].get('detail_failures'))
                        state['sources'][source] = {
                            'last_success': item['status']['checked_at'], 'error': None,
                            'next_check': self.clock() + (RETRY_INTERVAL if incomplete else INTERVAL),
                        }
                    except Exception as exc:
                        # Do not expose HTTP response bodies or arbitrary source text in the UI.
                        LOG.warning('Tender %s collection failed (%s)', source, type(exc).__name__)
                        state['sources'][source] = {**previous, 'error': 'collection_failed',
                                                  'next_check': self.clock() + RETRY_INTERVAL}
                    state['sources'][source]['last_attempt'] = stamp(now)
                    state['running'] = [s for s in state['running'] if s != source]
                    state['worker_heartbeat'] = stamp(self.clock())
                    write_json(self.directory / 'worker-state.json', state)
            state.update(running=[], handled_request=request, worker_heartbeat=stamp(self.clock()))
            write_json(self.directory / 'worker-state.json', state)
            return True

    def _run(self):
        while not self._stop.is_set():
            self._wake.clear()
            try:
                self.tick()
            except Exception as exc:
                LOG.warning('Tender background worker retrying after %s', type(exc).__name__)
            self._wake.wait(60)

    def start(self):
        with self._thread_lock:
            if self._thread is None or not self._thread.is_alive():
                self._stop.clear()
                self._thread = threading.Thread(target=self._run, daemon=True, name='tender-monitor')
                self._thread.start()
        return self

    def stop(self):
        self._stop.set()
        self._wake.set()


_process_monitor = None
_process_lock = threading.Lock()


def get_process_monitor():
    """Share one thread between the launcher and all Streamlit sessions/reruns."""
    global _process_monitor
    with _process_lock:
        if _process_monitor is None:
            _process_monitor = LocalMonitor()
        return _process_monitor.start()


class AutomaticTenderFeed:
    def __init__(self, monitor=None, fallback=None, clock=time.time):
        self.monitor = monitor or LocalMonitor()
        self.fallback = fallback or TenderFeed()
        self.clock = clock

    def start(self):
        self.monitor.start()
        return self

    def refresh(self, force=False):
        if force:
            self.monitor.request()
        local = self.monitor.store.snapshot()
        state = self.monitor.state()
        # Keep checking GitHub even after local data exists. The cloud archive can
        # contain notices discovered and withdrawn while this computer was off.
        base = self.fallback.refresh(force=force)
        sources, revisions, origins = {}, {}, {}
        current_cloud_sources = set()
        for source in SOURCES:
            remote = base['sources'][source]
            try:
                checked = datetime.fromisoformat(remote[1]['checked_at'])
                age = self.clock() - checked.timestamp() if checked.tzinfo else float('inf')
            except (KeyError, ValueError, TypeError):
                age = float('inf')
            cloud_current = base['revision'] is not None and -300 <= age <= 36 * 3600
            if cloud_current:
                current_cloud_sources.add(source)
            if cloud_current or not local or source not in local['sources']:
                sources[source], revisions[source] = remote, base['revision']
                origins[source] = 'cloud' if base['revision'] else 'bundled'
            else:
                sources[source], revisions[source] = local['sources'][source], local['revision']
                origins[source] = 'local'
        failures = [s.upper() for s, item in state['sources'].items()
                    if item.get('error') and s not in current_cloud_sources]
        error = (' / '.join(failures) + ': automatic collection failed. Saved records remain available; another attempt is scheduled in five minutes.') if failures else None
        if not error and any(origin != 'local' for origin in origins.values()):
            error = base.get('error')
        return {'sources': sources, 'revision': local['revision'] if local else base['revision'],
                'revisions': revisions, 'origins': origins, 'live': not error and ('cloud' in origins.values() or bool(local)),
                'connected_at': state.get('worker_heartbeat'), 'error': error,
                'collecting': state.get('running', [])}

    def detail(self, source, identifier, revision):
        if isinstance(revision, str) and revision.startswith('local-'):
            return self.monitor.store.detail(source, identifier, revision)
        return self.fallback.detail(source, identifier, revision)
