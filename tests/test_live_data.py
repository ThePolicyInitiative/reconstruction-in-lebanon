import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from integrated_tenders.live_data import FeedError, TenderFeed


class Reader:
    def __init__(self):
        self.revision = 'a' * 40
        self.head_calls = 0
        self.files = []
        self.offline = False
        self.invalid_cdr = False

    def head(self):
        self.head_calls += 1
        if self.offline:
            raise FeedError('offline')
        return self.revision

    def file(self, path, revision):
        self.files.append((path, revision))
        if path.endswith('dashboard.json'):
            return {'schema_version': 1, 'total': 2 if self.invalid_cdr and '/cdr/' in path else 1,
                    'tenders': [{'id': '1' if revision == 'a' * 40 else '2'}]}
        if path.endswith('status.json'):
            return {'checked_at': '2026-10-09T01:20:00+00:00'}
        return {'id': Path(path).stem, 'revision': revision, 'attachments': []}


class LiveFeedTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory()))
        self.reader = Reader()
        self.now = 0
        self.feed = TenderFeed(cache=self.directory / 'cache', reader=self.reader, clock=lambda: self.now)

    def test_checks_every_minute_and_manual_refresh_is_immediate(self):
        first = self.feed.refresh()
        self.assertTrue(first['live'])
        self.now = 59
        self.feed.refresh()
        self.assertEqual(self.reader.head_calls, 1)
        self.now = 60
        self.feed.refresh()
        self.assertEqual(self.reader.head_calls, 2)
        self.assertEqual(len(self.reader.files), 4, 'Unchanged commits must not redownload all data')
        self.feed.refresh(force=True)
        self.assertEqual(self.reader.head_calls, 3)

    def test_updates_both_sources_and_details_to_the_same_commit(self):
        old = self.feed.refresh()
        self.reader.revision = 'b' * 40
        new = self.feed.refresh(force=True)
        self.assertNotEqual(old['revision'], new['revision'])
        for source, (payload, status) in new['sources'].items():
            self.assertEqual(payload['tenders'][0]['id'], '2')
            detail = self.feed.detail(source, '2', new['revision'])
            self.assertEqual(detail['revision'], new['revision'])
        calls = len(self.reader.files)
        self.feed.detail('ppa', '2', new['revision'])
        self.assertEqual(len(self.reader.files), calls)

    def test_invalid_partial_update_keeps_both_previous_sources(self):
        old = self.feed.refresh()
        self.reader.revision = 'b' * 40
        self.reader.invalid_cdr = True
        failed = self.feed.refresh(force=True)
        self.assertFalse(failed['live'])
        self.assertTrue(failed['error'])
        self.assertEqual(failed['revision'], old['revision'])
        self.assertEqual(failed['sources'], old['sources'])
        restored = TenderFeed(cache=self.directory / 'cache', reader=self.reader)
        self.assertEqual(restored.refresh()['revision'], old['revision'])

    def test_outage_survives_restart_and_recovers(self):
        previous = self.feed.refresh()
        self.reader.offline = True
        restored = TenderFeed(cache=self.directory / 'cache', reader=self.reader)
        cached = restored.refresh()
        self.assertFalse(cached['live'])
        self.assertEqual(cached['sources'], previous['sources'])
        self.reader.offline = False
        self.assertTrue(restored.refresh(force=True)['live'])

    def test_first_connection_failure_uses_bundled_data(self):
        bundled = self.directory / 'fallback'
        for folder in [bundled, bundled / 'cdr']:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / 'dashboard.json').write_text(json.dumps({'schema_version': 1, 'total': 0, 'tenders': []}))
            (folder / 'status.json').write_text(json.dumps({'checked_at': '2026-10-02T01:00:00+00:00'}))
        self.reader.offline = True
        feed = TenderFeed(cache=self.directory / 'empty', bundled=bundled, reader=self.reader)
        result = feed.refresh()
        self.assertIsNone(result['revision'])
        self.assertFalse(result['live'])
        self.assertTrue(result['error'])
        self.assertEqual(result['sources']['ppa'][0]['total'], 0)


if __name__ == '__main__':
    unittest.main()
