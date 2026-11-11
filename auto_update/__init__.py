"""Keep the website current without manual commands.

One background thread per computer (an OS lock prevents duplicates) does three
jobs while the server is running:

* rebuild  – re-runs the import/build scripts when their input files change;
* collect  – saves new reconstruction headlines from public feeds, unreviewed;
* publish  – commits and pushes to GitHub once the checks pass (local launcher only).

Open pages refresh themselves through ``auto_update.ui``.
"""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import threading
import time

from integrated_tenders.automatic import scan_lock
from integrated_tenders.live_data import write_json

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache' / 'auto-update'
TICK = 5
LOG = logging.getLogger(__name__)


def stamp(seconds=None):
    return datetime.fromtimestamp(time.time() if seconds is None else seconds, timezone.utc).isoformat(timespec='seconds')


def read_state(directory=CACHE):
    try:
        state = json.loads((Path(directory) / 'state.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        state = {}
    for section in ('rebuild', 'collect', 'publish'):
        state.setdefault(section, {})
    return state


def enabled():
    """Tests and one-off scripts set RECONSTRUCTION_AUTO_UPDATE=0."""
    return os.environ.get('RECONSTRUCTION_AUTO_UPDATE', '1') != '0'


class AutoUpdater:
    def __init__(self, root=ROOT, directory=CACHE, publish=False, clock=time.time):
        self.root, self.directory = Path(root), Path(directory)
        self.publish, self.clock = publish, clock
        self._thread = None
        self._thread_lock = threading.Lock()
        self._stop = threading.Event()

    def tick(self):
        """Run every job once. Each job records its own outcome; none stops the others."""
        from . import collect, publish, rebuild
        with scan_lock(self.directory) as acquired:
            if not acquired:
                return False
            state = read_state(self.directory)
            before = json.dumps(state, sort_keys=True)
            jobs = [('rebuild', rebuild.run), ('collect', collect.run)]
            if self.publish:
                jobs.append(('publish', publish.run))
            for name, job in jobs:
                try:
                    job(self.root, state[name], self.clock())
                except Exception as exc:  # A failed job must never stop the website.
                    LOG.warning('Automatic %s failed (%s)', name, type(exc).__name__)
                    state[name].update(error=f'{type(exc).__name__}: {exc}'[:300], error_at=stamp(self.clock()))
            state['publish']['enabled'] = self.publish
            if json.dumps(state, sort_keys=True) != before:
                write_json(self.directory / 'state.json', state)
            return True

    def _run(self):
        while not self._stop.is_set():
            try:
                self.tick()
            except Exception as exc:
                LOG.warning('Automatic updates retrying after %s', type(exc).__name__)
            self._stop.wait(TICK)

    def start(self):
        with self._thread_lock:
            if enabled() and (self._thread is None or not self._thread.is_alive()):
                self._stop.clear()
                self._thread = threading.Thread(target=self._run, daemon=True, name='auto-update')
                self._thread.start()
        return self

    def stop(self):
        self._stop.set()


_process_updater = None
_process_lock = threading.Lock()


def get_process_updater(publish=False):
    """Share one thread between the launcher and all Streamlit sessions.

    Only the local launcher (run_website.py) asks for publishing, so a hosted
    copy of the site never tries to commit or push.
    """
    global _process_updater
    with _process_lock:
        if _process_updater is None:
            _process_updater = AutoUpdater(publish=publish)
        elif publish:
            _process_updater.publish = True
        return _process_updater.start()
