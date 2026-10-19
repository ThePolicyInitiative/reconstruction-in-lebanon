import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import threading
import time
from unittest.mock import patch

from integrated_tenders.automatic import (
    AutomaticTenderFeed, LocalMonitor, SnapshotStore, INTERVAL, RETRY_INTERVAL,
    bootstrap, scan_lock,
)
from integrated_tenders.live_data import FeedError, write_json


class AutomaticTenderTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.now = 1000
        self.version = 1
        self.fail = set()
        self.calls = []
        self.monitor = LocalMonitor(self.directory, collector=self.collect, clock=lambda: self.now)
        for source in ('ppa', 'cdr'):
            write_json(self.monitor.working(source) / 'state.json', {})

    def collect(self, source, directory):
        self.calls.append(source)
        write_json(directory / 'tenders/1.json', {'id': '1', 'version': self.version})
        if source in self.fail:
            raise ValueError('Simulate failure after modifying working details')
        write_json(directory / 'dashboard.json', {'schema_version': 1, 'total': 1,
                                                 'tenders': [{'id': '1', 'version': self.version}]})
        return {'checked_at': str(self.now), 'pending_details': 0}

    def test_schedule_survives_restart_and_manual_check_is_queued(self):
        self.assertTrue(self.monitor.tick())
        self.assertCountEqual(self.calls, ['ppa', 'cdr'])
        self.calls.clear()
        self.now += INTERVAL - 1
        restarted = LocalMonitor(self.directory, collector=self.collect, clock=lambda: self.now)
        self.assertFalse(restarted.tick())
        self.assertEqual(self.calls, [])
        restarted.request()
        self.assertEqual(self.calls, [], 'Request must not block the UI on network collection')
        self.assertTrue(restarted.tick())
        self.assertCountEqual(self.calls, ['ppa', 'cdr'])
        self.calls.clear()
        self.assertFalse(restarted.tick(), 'Request is consumed once')
        self.now += INTERVAL
        self.assertTrue(restarted.tick())

    def test_failure_retains_immutable_details_and_other_source_updates(self):
        self.monitor.tick()
        old = self.monitor.store.snapshot()
        self.version = 2
        self.fail.add('ppa')
        self.now += INTERVAL
        self.monitor.tick()
        new = self.monitor.store.snapshot()
        self.assertEqual(new['sources']['ppa'], old['sources']['ppa'])
        self.assertEqual(new['sources']['cdr'][0]['tenders'][0]['version'], 2)
        for source in ('ppa', 'cdr'):
            self.assertEqual(self.monitor.store.detail(source, '1', old['revision'])['version'], 1)
        self.assertEqual(self.monitor.store.detail('ppa', '1', new['revision'])['version'], 1)
        self.assertEqual(self.monitor.store.detail('cdr', '1', new['revision'])['version'], 2)
        self.assertEqual(self.monitor.state()['sources']['ppa']['last_success'], '1000')
        self.fail.clear()
        self.calls.clear()
        self.now += RETRY_INTERVAL
        self.monitor.tick()
        self.assertEqual(self.calls, ['ppa'])
        self.assertIsNone(self.monitor.state()['sources']['ppa']['error'])

    def test_lock_prevents_overlapping_processes_and_releases(self):
        with scan_lock(self.directory) as acquired:
            self.assertTrue(acquired)
            self.assertFalse(self.monitor.tick())
            self.assertFalse(self.calls)
        self.assertTrue(self.monitor.tick())

    def test_incomplete_details_retry_without_losing_completed_records(self):
        def incomplete(source, directory):
            return {**self.collect(source, directory), 'pending_details': 1, 'detail_failures': []}
        self.monitor.collector = incomplete
        self.monitor.tick()
        self.assertEqual(self.monitor.store.snapshot()['sources']['ppa'][1]['pending_details'], 1)
        self.assertEqual(self.monitor.state()['sources']['ppa']['next_check'], self.now + RETRY_INTERVAL)

    def test_fast_source_publishes_while_other_source_is_still_waiting(self):
        release = threading.Event()
        def slow_ppa(source, directory):
            if source == 'ppa':
                release.wait(10)
            return self.collect(source, directory)
        self.monitor.collector = slow_ppa
        worker = threading.Thread(target=self.monitor.tick)
        worker.start()
        try:
            deadline = time.monotonic() + 5
            snapshot = None
            while time.monotonic() < deadline:
                snapshot = self.monitor.store.snapshot()
                if snapshot:
                    break
                time.sleep(0.02)
            self.assertIsNotNone(snapshot)
            self.assertEqual(set(snapshot['sources']), {'cdr'})
        finally:
            release.set()
            worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(set(self.monitor.store.snapshot()['sources']), {'ppa', 'cdr'})

    def test_invalid_dashboard_does_not_publish_or_advance_success_time(self):
        self.monitor.tick()
        old = self.monitor.store.snapshot()
        def invalid(source, directory):
            write_json(directory / 'dashboard.json', {'schema_version': 1, 'total': 2, 'tenders': []})
            return {'checked_at': 'wrong'}
        self.monitor.collector = invalid
        self.now += INTERVAL
        self.monitor.tick()
        self.assertEqual(self.monitor.store.snapshot(), old)
        self.assertEqual(self.monitor.state()['sources']['cdr']['last_success'], '1000')

    def test_stale_cloud_uses_local_data_but_keeps_checking_for_recovery(self):
        self.monitor.tick()
        from unittest.mock import Mock
        fallback = Mock()
        fallback.refresh.return_value = {'revision': 'a'*40, 'sources': {
            source: ({'tenders': []}, {'checked_at': '2026-10-01T00:00:00+00:00'}) for source in ('ppa', 'cdr')}, 'error': None}
        feed = AutomaticTenderFeed(self.monitor, fallback)
        result = feed.refresh()
        self.assertTrue(result['live'])
        self.assertTrue(fallback.refresh.called)
        self.assertEqual(feed.detail('ppa', '1', result['revisions']['ppa'])['version'], 1)
        self.assertFalse(fallback.detail.called)
        with self.assertRaises(FeedError):
            feed.detail('ppa', '../state', result['revision'])

    def test_cloud_archive_takes_over_when_checks_resume_after_computer_was_off(self):
        self.monitor.tick()
        from unittest.mock import Mock
        fallback = Mock()
        cloud = {'revision': 'a'*40, 'sources': {
            source: ({'tenders': [{'id': '2'}]}, {'checked_at': '2026-10-19T12:00:00+00:00'})
            for source in ('ppa', 'cdr')}, 'error': None}
        fallback.refresh.return_value = cloud
        from datetime import datetime
        feed = AutomaticTenderFeed(self.monitor, fallback, clock=lambda: datetime.fromisoformat('2026-10-19T12:30:00+00:00').timestamp())
        result = feed.refresh()
        self.assertEqual(result['origins'], {'ppa': 'cloud', 'cdr': 'cloud'})
        self.assertEqual(result['sources'], cloud['sources'])
        feed.detail('ppa', '2', result['revisions']['ppa'])
        fallback.detail.assert_called_once_with('ppa', '2', 'a'*40)
        # A successful local check cannot discard notices archived while the PC was off.
        self.now += INTERVAL
        self.monitor.tick()
        self.assertEqual(feed.refresh()['sources'], cloud['sources'])
        feed.refresh(force=True)
        fallback.refresh.assert_called_with(force=True)

    def test_partial_first_scan_routes_each_source_to_its_own_revision(self):
        self.fail.add('cdr')
        self.monitor.tick()
        from unittest.mock import Mock
        fallback = Mock()
        fallback.refresh.return_value = {'revision': 'a'*40, 'sources': {'ppa': ({}, {}), 'cdr': ({}, {})}}
        feed = AutomaticTenderFeed(self.monitor, fallback)
        result = feed.refresh()
        self.assertTrue(result['revisions']['ppa'].startswith('local-'))
        self.assertEqual(result['revisions']['cdr'], 'a'*40)
        self.assertIn('CDR:', result['error'])

    def test_packaged_full_records_can_bootstrap_both_collectors(self):
        from integrated_tenders.live_data import ROOT
        bundled = self.directory / 'bundled'
        for source in ('ppa', 'cdr'):
            original = ROOT / 'data' / ('cdr' if source == 'cdr' else '')
            target = bundled / ('cdr' if source == 'cdr' else '')
            record_path = next((original / 'tenders').glob('*.json'))
            record = json.loads(record_path.read_text(encoding='utf-8'))
            write_json(target / 'tenders' / record_path.name, record)
            write_json(target / 'dashboard.json', {'schema_version': 1, 'total': 1, 'tenders': [{'id': record['id']}]})
            write_json(target / 'status.json', {'checked_at': '2026-10-02T00:00:00+00:00'})
            working = self.directory / 'fresh' / source
            bootstrap(working, source, bundled)
            state = json.loads((working / 'state.json').read_text(encoding='utf-8'))
            self.assertIn(record['id'], state['known_ids'])
            if source == 'cdr':
                self.assertEqual(len(list((working / 'lots').glob('*.json'))), len(record['lots']))
            self.assertEqual(len(json.loads((working / 'index.json').read_text(encoding='utf-8'))), 1)


if __name__ == '__main__':
    unittest.main()
