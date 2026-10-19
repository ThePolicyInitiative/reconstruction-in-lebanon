"""Integration checks for the three imported pages and their saved evidence."""
import json
from pathlib import Path
import unittest

from streamlit.testing.v1 import AppTest
from scripts.import_requested_pages import LocalReferences
from tests.support import offline_tender_feed

ROOT = Path(__file__).resolve().parents[1]


class ImportedPageTests(unittest.TestCase):
    def test_gallery_keeps_every_local_image_and_report(self):
        directory = ROOT / 'imported' / 'evidence'
        parser = LocalReferences()
        parser.feed((directory / 'index.html').read_text(encoding='utf-8'))
        self.assertGreater(len(parser.paths), 90)
        for asset in parser.paths:
            with self.subTest(asset=asset):
                self.assertTrue((directory / asset).is_file())
                self.assertGreater((directory / asset).stat().st_size, 0)

    def test_tender_details_and_statement_archive_are_preserved(self):
        manifest = json.loads((ROOT / 'imported' / 'manifest.json').read_text())
        for source, relative in [('ppa', ''), ('cdr', 'cdr')]:
            directory = ROOT / 'integrated_tenders' / 'data' / relative
            payload = json.loads((directory / 'dashboard.json').read_text(encoding='utf-8'))
            self.assertEqual(len(payload['tenders']), manifest['tenders']['counts'][source])
            for row in payload['tenders']:
                self.assertTrue((directory / 'tenders' / f'{row["id"]}.json').is_file())
        parties = json.loads((ROOT / 'imported' / 'parties' / 'reconstruction-statements.json').read_text(encoding='utf-8'))
        additions = json.loads((ROOT / 'data' / 'party_additions_2026_10_12.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(len(parties['statements']), 61 + len(additions['statements']))
        self.assertTrue({s['id'] for s in additions['statements']} <= {s['id'] for s in parties['statements']})
        actor_ids = {actor['id'] for actor in parties['actors']}
        for statement in parties['statements']:
            self.assertIn(statement['actor'], actor_ids)
            self.assertTrue(statement['url'].startswith('https://'))

    def test_tender_search_and_programme_filter(self):
        self.enterContext(offline_tender_feed())
        app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=60).run()
        self.assertFalse(app.exception)
        app.session_state['reconstruction_section'] = 'Tenders'
        app.run()
        # AppTest does not serialize stateful tab containers yet; supply the
        # active label on each run, as the browser does with widget updates.
        def run_tenders():
            app.session_state['reconstruction_section'] = 'Tenders'
            app.run()

        app.text_input(key='search').set_value('no-such-procurement-8fe6721')
        run_tenders()
        self.assertFalse(app.exception)
        filtered = [metric.value for metric in app.metric if metric.label == 'Filtered tenders']
        self.assertEqual(filtered, ['0', '0'])
        app.text_input(key='search').set_value('')
        run_tenders()
        app.selectbox(key='tender_category').set_value('LEAP')
        run_tenders()
        self.assertFalse(app.exception)
        filtered = [int(metric.value.replace(',', '')) for metric in app.metric if metric.label == 'Filtered tenders']
        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(count > 0 for count in filtered))
        app.session_state['reconstruction_section'] = 'What parties are saying'
        app.run()
        app.session_state['reconstruction_section'] = 'Tenders'
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='tender_category').value, 'LEAP')

    def test_other_tabs_do_not_wait_for_the_tender_feed(self):
        from unittest.mock import patch
        self.enterContext(patch('integrated_tenders.get_monitor'))
        with patch('integrated_tenders.get_feed', side_effect=AssertionError('Tender feed must not run on other tabs')):
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run()
            self.assertFalse(app.exception)
            for label, component in [('What parties are saying', 'party_statements'), ('What countries are saying', 'country_statements'), ('Evidence of destruction', 'destruction_evidence')]:
                app.session_state['reconstruction_section'] = label
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any(component in item.proto.component_name for item in app.get('component_instance')))


if __name__ == '__main__':
    unittest.main()
