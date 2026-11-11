"""Automatic rebuilding, headline collection, publishing and page refresh."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from auto_update import AutoUpdater, collect, publish, rebuild
from auto_update.ui import content_revision, headlines_html, status_lines
from tests.support import offline_tender_feed

ROOT = Path(__file__).resolve().parents[1]
RSS = """<?xml version="1.0"?><rss><channel>
<item><title>France pledges $75 million for Lebanon reconstruction</title><link>https://example.org/a</link>
<pubDate>Tue, 10 Nov 2026 09:00:00 GMT</pubDate><description>&lt;p&gt;Details&lt;/p&gt;</description></item>
<item><title>إعادة إعمار غزة تبدأ قريباً</title><link>https://example.org/b</link></item>
<item><title>Rain expected on Friday</title><link>https://example.org/c</link></item>
<item><title>Rebuild &lt;script&gt;alert(1)&lt;/script&gt; in Beirut</title><link>javascript:alert(1)</link></item>
</channel></rss>""".encode()


def old(path, seconds=60):
    moment = time.time() - seconds
    os.utime(path, (moment, moment))


class HeadlineTests(unittest.TestCase):
    def test_only_lebanon_recovery_headlines_are_kept_and_sorted_into_pages(self):
        names = {'countries': ['France'], 'parties': ['Hezbollah']}
        self.assertEqual(collect.classify('France pledges $75 million for Lebanon reconstruction', '', True, names), (['countries'], ['France']))
        self.assertEqual(collect.classify('Hezbollah MP says reconstruction cannot wait', '', True, names), (['parties'], ['Hezbollah']))
        self.assertEqual(collect.classify('بلدية حولا تمنع ترميم المنازل المتضررة')[0], ['barriers'])
        self.assertEqual(collect.classify('موازنة 2027 تخصص 100 مليار لإعادة الإعمار')[0], ['budget', 'losses'])
        self.assertEqual(collect.classify('إعادة إعمار غزة تبدأ قريباً'), ([], []))
        self.assertEqual(collect.classify('Minister opens radio studio', 'He also mentioned reconstruction in Lebanon.'), ([], []))
        self.assertEqual(collect.classify('Reconstruction talks resume', '', False), ([], []))

    def test_collection_saves_new_headlines_once_and_survives_failed_feeds(self):
        def fetcher(url):
            if 'nna-leb.gov.lb/en' in url:
                return RSS
            raise OSError('offline')
        with tempfile.TemporaryDirectory() as folder:
            root, state = Path(folder), {}
            (root / 'data').mkdir()
            collect.run(root, state, 1000, fetcher)
            saved = json.loads((root / collect.OUTPUT).read_text(encoding='utf-8'))
            self.assertEqual([item['url'] for item in saved['items']], ['https://example.org/a'])
            self.assertEqual(saved['items'][0]['published'], '2026-11-10T09:00:00+00:00')
            self.assertIn('Not reviewed', saved['note'])
            self.assertEqual(state['added'], 1)
            self.assertIn('Naharnet', state['failures'])
            self.assertEqual(state['next_check'], 1000 + collect.INTERVAL)
            before = (root / collect.OUTPUT).read_bytes()
            collect.run(root, state, 1001, fetcher)  # Not due yet.
            collect.run(root, state, 1000 + collect.INTERVAL, fetcher)
            self.assertEqual((root / collect.OUTPUT).read_bytes(), before)
            self.assertEqual(state['added'], 0)

    def test_headlines_are_escaped_and_labelled_unreviewed(self):
        html = headlines_html([{'title': '<b>x</b>', 'url': 'https://example.org/?a=1&b=2', 'publisher': 'P',
                                'published': '2026-11-10T09:00:00+00:00', 'first_seen': '', 'mentions': []}])
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', html)
        self.assertIn('href="https://example.org/?a=1&amp;b=2"', html)
        self.assertIn('not reviewed', html)


class RebuildTests(unittest.TestCase):
    def test_saved_input_reruns_its_script_and_failures_are_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            root, state, calls = Path(folder), {}, []
            (root / 'data').mkdir()
            (root / 'data' / 'economic_losses.json').write_text('{"source_sha256": "x"}', encoding='utf-8')
            source = root / 'data' / 'input.json'
            source.write_text('1', encoding='utf-8')
            old(source)
            rules = [('political', ['data/input.json'], lambda root: calls.append('built'))]
            rebuild.run(root, state, 1, rules)
            self.assertEqual(calls, [])  # First sight is the baseline.
            rebuild.run(root, state, 2, rules)
            self.assertEqual(calls, [])
            source.write_text('22', encoding='utf-8')
            rebuild.run(root, state, 3, rules)
            self.assertEqual(calls, [])  # Still being saved.
            old(source, 30)
            rebuild.run(root, state, 4, rules)
            self.assertEqual(calls, ['built'])
            self.assertTrue(state['political']['ok'])

            attempts = []

            def broken(root):
                attempts.append(1)
                raise AssertionError('unknown source')
            source.write_text('333', encoding='utf-8')
            old(source, 20)
            rebuild.run(root, state, 5, [('political', ['data/input.json'], broken)])
            self.assertFalse(state['political']['ok'])
            self.assertIn('unknown source', state['political']['message'])
            rebuild.run(root, state, 6, [('political', ['data/input.json'], broken)])
            self.assertEqual(attempts, [1])  # Not retried until the file is saved again.

    def test_changed_reviewed_workbook_is_flagged_not_imported(self):
        with tempfile.TemporaryDirectory() as folder:
            root, state, imported = Path(folder), {}, []
            (root / 'data').mkdir()
            (root / 'data' / 'economic_losses.json').write_text('{"source_sha256": "x"}', encoding='utf-8')
            workbook = root / 'data' / 'new.xlsx'
            workbook.write_bytes(b'workbook')
            (root / 'data' / '~$new.xlsx').write_bytes(b'lock')
            old(workbook)
            old(root / 'data' / '~$new.xlsx')

            def refuse(path):
                imported.append(path.name)
                raise ValueError("Review changed general cells before importing: ['B4']")
            rebuild.import_workbook(root, state, 1, refuse)
            rebuild.import_workbook(root, state, 2, refuse)  # The same file is not retried.
            self.assertEqual(imported, ['new.xlsx'])
            self.assertTrue(state['workbook']['review'])
            self.assertIn('B4', state['workbook']['message'])
            warnings = [text for kind, text in status_lines({'rebuild': state, 'collect': {}, 'publish': {}}) if kind == 'warn']
            self.assertTrue(any('new.xlsx' in text and 'B4' in text for text in warnings))

    def test_current_workbook_is_already_imported(self):
        state = {}
        with patch('scripts.import_economic_losses.main') as importer:
            rebuild.import_workbook(ROOT, state, 1)
        importer.assert_not_called()
        self.assertNotIn('workbook', state)


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.folder = self.enterContext(tempfile.TemporaryDirectory(ignore_cleanup_errors=True))
        self.root, self.remote = Path(self.folder) / 'site', Path(self.folder) / 'remote.git'
        self.root.mkdir()
        subprocess.run([publish.git_executable(), 'init', '--bare', '-b', 'main', str(self.remote)], check=True, capture_output=True)
        for args in (['init', '-b', 'main'], ['config', 'user.name', 'Test'], ['config', 'user.email', 'test@example.org'],
                     ['config', 'commit.gpgsign', 'false'], ['remote', 'add', 'origin', str(self.remote)]):
            subprocess.run([publish.git_executable(), *args], cwd=self.root, check=True, capture_output=True)
        (self.root / 'a.txt').write_text('1', encoding='utf-8')
        publish.git(self.root, 'add', '-A')
        publish.git(self.root, 'commit', '-m', 'first')
        publish.git(self.root, 'push', '-u', 'origin', 'main')

    def remote_head(self):
        return publish.git(self.remote, 'log', '-1', '--format=%s', 'main').strip()

    def run_publish(self, state, now, passed=True):
        ran = []

        def checks(root):
            ran.append(1)
            return passed, 'FAIL: test_x'
        publish.run(self.root, state, now, checks=checks, every=0)
        return ran

    def test_git_is_found_when_the_launcher_path_omits_it(self):
        real = publish.git_executable()
        programs = Path(self.folder) / 'programs'
        (programs / 'Git' / 'cmd').mkdir(parents=True)
        (programs / 'Git' / 'cmd' / 'git.exe').write_bytes(b'')
        with patch.object(publish.shutil, 'which', return_value=None):
            with patch.dict(os.environ, {'ProgramFiles': str(programs)}):
                self.assertEqual(publish.git_executable(), str(programs / 'Git' / 'cmd' / 'git.exe'))
            empty = {name: str(Path(self.folder) / 'none') for name in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)', 'LocalAppData')}
            with patch.dict(os.environ, empty):
                state = {}
                publish.run(self.root, state, 0, every=0)
                self.assertEqual(state['status'], 'unavailable')
                self.assertIn('Git was not found', state['detail'])
        self.assertTrue(Path(real).is_file())

    def test_publishes_only_after_quiet_period_and_passing_checks(self):
        state = {}
        self.run_publish(state, 0)
        self.assertEqual(state['status'], 'idle')
        (self.root / 'data').mkdir()
        (self.root / 'data' / 'b.json').write_text('{}', encoding='utf-8')
        self.assertEqual(self.run_publish(state, 10), [])
        self.assertEqual(state['status'], 'waiting')
        self.assertEqual(self.run_publish(state, 10 + publish.QUIET - 1), [])
        self.assertEqual(self.run_publish(state, 10 + publish.QUIET, passed=False), [1])
        self.assertEqual(state['status'], 'checks_failed')
        self.assertEqual(self.remote_head(), 'first')
        self.assertEqual(self.run_publish(state, 20 + publish.QUIET), [])  # The same failing files are not re-tested.
        (self.root / 'data' / 'b.json').write_text('{"fixed": true}', encoding='utf-8')
        self.run_publish(state, 1000)
        self.assertEqual(self.run_publish(state, 1000 + publish.QUIET), [1])
        self.assertEqual(state['status'], 'published')
        self.assertEqual(self.remote_head(), 'Auto-update: 1 file (data)')
        self.assertEqual(publish.changed_paths(self.root), [])

    def test_rejected_push_is_reported_and_never_forced(self):
        state = {}
        other = Path(self.folder) / 'other'
        subprocess.run([publish.git_executable(), 'clone', str(self.remote), str(other)], check=True, capture_output=True)
        for args in (['config', 'user.name', 'Other'], ['config', 'user.email', 'other@example.org'], ['config', 'commit.gpgsign', 'false']):
            subprocess.run([publish.git_executable(), *args], cwd=other, check=True, capture_output=True)
        (other / 'c.txt').write_text('remote', encoding='utf-8')
        publish.git(other, 'add', '-A')
        publish.git(other, 'commit', '-m', 'someone else')
        publish.git(other, 'push', 'origin', 'main')
        (self.root / 'a.txt').write_text('2', encoding='utf-8')
        self.run_publish(state, 0)
        self.run_publish(state, publish.QUIET)
        self.assertEqual(state['status'], 'push_failed')
        self.assertEqual(self.remote_head(), 'someone else')

    def test_updater_runs_every_job_even_when_one_fails(self):
        updater = AutoUpdater(root=self.root, directory=Path(self.folder) / 'cache', publish=True)
        with patch('auto_update.rebuild.run', side_effect=RuntimeError('boom')), patch('auto_update.collect.run') as collected, \
                patch('auto_update.publish.run') as published:
            self.assertTrue(updater.tick())
        collected.assert_called_once()
        published.assert_called_once()
        state = json.loads((Path(self.folder) / 'cache' / 'state.json').read_text(encoding='utf-8'))
        self.assertIn('boom', state['rebuild']['error'])


class PageTests(unittest.TestCase):
    def test_revision_changes_when_a_data_file_is_saved(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'data').mkdir()
            first = content_revision(root)
            (root / 'data' / 'x.json').write_text('{}', encoding='utf-8')
            self.assertNotEqual(content_revision(root), first)

    def test_pages_show_unreviewed_headlines_and_status_without_starting_work(self):
        self.enterContext(offline_tender_feed())
        with patch('auto_update.ui.get_process_updater') as started:
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=60).run()
            self.assertFalse(app.exception)
            labels = [expander.label for expander in app.expander]
            self.assertIn('Latest headlines — collected automatically, not reviewed', labels)
            self.assertTrue(any(label.startswith('Automatic updates') for label in labels))
            arabic = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=60)
            arabic.query_params['lang'] = 'ar'
            arabic.run()
            self.assertFalse(arabic.exception)
            self.assertIn('آخر العناوين — تُجمع تلقائياً ولم تُراجع', [expander.label for expander in arabic.expander])
        started.assert_not_called()


if __name__ == '__main__':
    unittest.main()
