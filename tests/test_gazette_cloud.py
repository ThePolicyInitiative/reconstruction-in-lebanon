from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

from integrated_gazette.data_feed import ROOT, SITE_URL, read_snapshot
from integrated_gazette.live_data import CloudGazetteFeed, SiteReader, GazetteFeedError, NoRedirect, STATUS_PATH, DATA_PATH, atomic_json


class GazetteCloudTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cache = Path(self.tmp.name)
        data = read_snapshot(ROOT / 'integrated_gazette/data/snapshot.json.gz')
        owner = next(r for r in data['records'] if r['method'] == 'owner-workbook')
        other = next(r for r in data['records'] if r['method'] != 'owner-workbook')
        self.old = {**data, 'revision': 'old', 'records': [owner, other]}
        atomic_json(self.cache / 'cloud.json', self.old)
        self.reader = Mock()
        self.now = 0
        self.feed = CloudGazetteFeed(self.reader, self.cache, clock=lambda: self.now)

    def status(self, payload):
        return {'dashboard': {'revision': payload['revision'], 'records': len(payload['records'])},
                'source_configured': True, 'new_records_pending': 0, 'memos_pending': 0}

    def test_new_records_download_once_then_small_status_checks_each_minute(self):
        new = deepcopy(self.old)
        new['revision'] = 'new'
        row = {**new['records'][1], 'id': '999999', 'date': '2026-10-15', 'url': 'https://jo.pcm.gov.lb/desc.php?table=div1&id=999999'}
        new['records'].append(row)
        self.reader.get.side_effect = [self.status(new), new, self.status(new)]
        result = self.feed.refresh()
        self.assertTrue(result['live'])
        self.assertEqual(len(result['snapshot']['records']), 3)
        self.assertEqual([c.args[0] for c in self.reader.get.call_args_list], [STATUS_PATH, DATA_PATH])
        self.now = 59
        self.feed.refresh()
        self.assertEqual(self.reader.get.call_count, 2)
        self.now = 61
        self.feed.refresh()
        self.assertEqual(self.reader.get.call_count, 3)
        self.assertEqual(read_snapshot(self.cache / 'cloud.json')['revision'], 'new')

    def test_changed_owner_labels_or_partial_exports_do_not_replace_cache(self):
        before = (self.cache / 'cloud.json').read_bytes()
        for mutation in ('owner', 'partial', 'count'):
            changed = deepcopy(self.old)
            changed['revision'] = 'new'
            if mutation == 'owner':
                changed['records'][0]['admin_function'] = 'Unapproved new wording'
            elif mutation == 'partial':
                changed['records'][1].pop('title')
            status = self.status(changed)
            if mutation == 'count':
                status['dashboard']['records'] = 1000
            self.reader.get.side_effect = [status, changed]
            result = self.feed.refresh(force=True)
            self.assertFalse(result['live'])
            self.assertTrue(result['error'])
            self.assertEqual(result['snapshot']['revisions'], ['old'])
            self.assertEqual((self.cache / 'cloud.json').read_bytes(), before)

    def test_restart_offline_fallback_and_automatic_recovery(self):
        self.reader.get.side_effect = GazetteFeedError('Connection unavailable')
        first = self.feed.refresh()
        self.assertFalse(first['live'])
        self.assertEqual(first['snapshot']['revisions'], ['old'])
        restarted = CloudGazetteFeed(self.reader, self.cache, clock=lambda: self.now)
        self.assertEqual(restarted.refresh()['snapshot']['revisions'], ['old'])
        self.now = 61
        self.reader.get.side_effect = [self.status(self.old)]
        recovered = restarted.refresh()
        self.assertTrue(recovered['live'])
        self.assertIsNone(recovered['error'])
        self.assertTrue(recovered['connected_at'])

    def test_cloud_update_during_download_requires_matching_readback(self):
        new = {**deepcopy(self.old), 'revision': 'new'}
        self.reader.get.side_effect = [self.status({**new, 'revision': 'intermediate'}), new, self.status(new)]
        result = self.feed.refresh()
        self.assertTrue(result['live'])
        self.assertEqual(result['revision'], 'new')
        self.assertEqual(self.reader.get.call_count, 3)

    def test_corrupt_connection_metadata_cannot_replace_valid_saved_records(self):
        for bad in ([], {'revision': 'wrong', 'snapshot': {'records': []}}, {'revision': 'old', 'snapshot': {'records': []}}):
            atomic_json(self.cache / 'connection.json', bad)
            self.reader.get.side_effect = GazetteFeedError('Offline')
            feed = CloudGazetteFeed(self.reader, self.cache)
            result = feed.refresh()
            self.assertEqual(len(result['snapshot']['records']), 2)
            self.assertEqual(result['snapshot']['revisions'], ['old'])

    def test_site_reader_is_get_only_fixed_origin_and_hides_auth_failures(self):
        reader = SiteReader(lambda: 'private-test-token')
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b'{"dashboard": {}}'
        reader.opener = Mock()
        reader.opener.open.return_value = response
        reader.get(STATUS_PATH)
        request = reader.opener.open.call_args.args[0]
        self.assertEqual(request.full_url, SITE_URL + STATUS_PATH)
        self.assertEqual(request.get_method(), 'GET')
        self.assertNotIn('private-test-token', request.full_url)
        with self.assertRaises(GazetteFeedError):
            reader.get('https://unrelated.example/api')
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, 'https://unrelated.example'))
        reader.opener.open.side_effect = HTTPError(SITE_URL, 403, 'private-test-token', {}, io.BytesIO(b'private-test-token'))
        with self.assertRaises(GazetteFeedError) as error:
            reader.get(STATUS_PATH)
        self.assertNotIn('private-test-token', str(error.exception))


if __name__ == '__main__':
    unittest.main()
