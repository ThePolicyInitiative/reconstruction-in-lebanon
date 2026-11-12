"""Gazette source fidelity, subject boundaries and actual dashboard interactions."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from integrated_gazette import saved_data
from integrated_gazette.analytics import (ALL, RELATED, NO_SUBJECT, tag_records, filter_records,
                                         csv_rows, classification_options)
from integrated_gazette.data_feed import FIELDS, ROOT, load_snapshot, read_snapshot


class GazetteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / 'integrated_gazette/data/snapshot.json.gz'
        cls.bundle = read_snapshot(cls.path)

    def test_saved_records_preserve_owner_values_and_year_scope(self):
        snapshot = load_snapshot([self.path])
        records = snapshot['records']
        self.assertEqual(len(records), 5694)
        self.assertEqual(len({r['id'] for r in records}), len(records))
        self.assertEqual({r['date'][:4] for r in records}, {'2024', '2025', '2026'})
        self.assertEqual(sum(r['status'] == 'owner-workbook' for r in records), 493)
        tagged = tag_records(records)
        for original, decorated in zip(records, tagged):
            self.assertEqual(original, {k: decorated[k] for k in original})
        export = csv_rows(tagged)
        for original, row in zip(records, export):
            for key, field in [('nature', 'Nature'), ('admin_function', 'Administrative function'), ('major', 'Main category'), ('sub', 'Subcategory')]:
                self.assertEqual(original[key], row[field])

    def test_bank_names_are_not_reconstruction_and_real_rebuilding_is(self):
        records = {r['id']: r for r in tag_records(self.bundle['records'])}
        for rid in ('190743', '190751'):
            self.assertNotIn('Reconstruction', records[rid]['subjects'])
        self.assertIn('Reconstruction', records['186181']['subjects'])
        self.assertIn('Reconstruction', records['188129']['subjects'])
        matches = filter_records(list(records.values()), years=['2024'], subject='Reconstruction', query='الجنوب')
        self.assertEqual([r['id'] for r in matches], ['186181'])
        self.assertEqual(filter_records(list(records.values()), query='no-such-gazette-item'), [])
        related = filter_records(list(records.values()), subject=RELATED)
        self.assertTrue(related)
        self.assertTrue(all(r['subjects'] for r in related))

    def test_sector_words_alone_are_not_recovery_and_war_damage_measures_are(self):
        records = {r['id']: r for r in tag_records(self.bundle['records'])}
        # Road alignment, an ambassador named Berri, electric cars, vehicle impound fees,
        # a directorate's name and "methods" of payment.
        for rid in ('190098', '190895', '185061', '187122', '187481', '187257', '184188'):
            with self.subTest(rid=rid):
                self.assertEqual(records[rid]['subjects'], [])
        for rid in ('187537', '189141', '190744'):
            with self.subTest(rid=rid):
                self.assertEqual(records[rid]['subjects'], ['Reconstruction'])
                self.assertIn('Recovery link', [e['Category'] for e in records[rid]['subject_evidence']])
        self.assertEqual(records['186693']['subjects'], ['Damage assessment'])
        self.assertEqual(records['189573']['subjects'], [])
        self.assertEqual(records['189573']['programmes'], ['LEAP'])
        self.assertEqual([e['Category'] for e in records['189573']['subject_evidence']], ['LEAP'])

    def test_changed_export_updates_fields_retains_cloud_only_records_and_rejects_partial_write(self):
        row = deepcopy(self.bundle['records'][0])
        second = deepcopy(self.bundle['records'][1])
        old = {'built_at': '2026-10-19T09:00:00Z', 'revision': 'old', 'records': [row, second]}
        newer = deepcopy(old)
        newer.update(built_at='2026-10-19T10:00:00Z', revision='new', records=[deepcopy(row)])
        newer['records'][0]['admin_function'] = ''
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'old.json', Path(tmp)/'new.json'
            a.write_text(json.dumps(old), encoding='utf-8')
            b.write_text(json.dumps(newer), encoding='utf-8')
            saved = load_snapshot([a, b])
            self.assertEqual(len(saved['records']), 2)
            self.assertEqual(next(r for r in saved['records'] if r['id'] == row['id'])['admin_function'], '')
            b.write_text('{"records":', encoding='utf-8')
            fallback = load_snapshot([a, b])
            self.assertEqual(fallback['invalid_exports'], ['new.json'])
            self.assertEqual(len(fallback['records']), 2)
            self.assertEqual(fallback['revisions'], ['old'])

    def test_classification_filters_group_variants_keep_blanks_and_combine(self):
        base = deepcopy(self.bundle['records'][0])
        rows = tag_records([{**base, 'id':'a', 'title':'LEAP procurement specialist',
                             'major':'Government Operations', 'sub':'Appointments', 'nature':'Administrative', 'admin_function':''},
                            {**base, 'id':'b', 'title':'LEAP road works',
                             'major':' government   operations ', 'sub':'appointments', 'nature':'Administrative', 'admin_function':''},
                            {**base, 'id':'c', 'title':'Office supplies',
                             'major':'', 'sub':'', 'nature':'', 'admin_function':''}])
        before = deepcopy(rows)
        self.assertEqual(classification_options(rows, 'major'), ['Government Operations', 'Not specified'])
        self.assertEqual([r['id'] for r in filter_records(rows, majors=['Government Operations'],
                         subs=['Appointments'], natures=['Administrative'], functions=['Not specified'])], ['a','b'])
        self.assertEqual([r['id'] for r in filter_records(rows, majors=['Not specified'])], ['c'])
        self.assertEqual([r['id'] for r in filter_records(rows, subject=NO_SUBJECT, programme='LEAP')], ['a'])
        self.assertEqual([r['id'] for r in filter_records(rows, subject='Roads', programme='LEAP')], ['b'])
        self.assertEqual(rows, before)
        self.assertEqual(csv_rows(rows)[1]['Main category'], ' government   operations ')
        self.assertEqual(csv_rows(rows)[2]['Subcategory'], '')

    def test_gazette_filters_downloads_and_language_switch(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))
        mock_feed = self.enterContext(patch('integrated_gazette.get_feed'))
        mock_feed.return_value.refresh.return_value = {'snapshot': load_snapshot([self.path]), 'live': True, 'error': None}
        saved_data.clear()
        app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=60).run()
        app.session_state['reconstruction_section'] = 'Gazette'
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual([t.label for t in app.tabs][:6], ['Government response', 'Budget', 'Economic losses',
                                                       'Restrictions & funding gaps', 'Tenders', 'Gazette'])
        self.assertEqual(app.multiselect(key='gazette_years').options, ['2026', '2025', '2024'])
        app.selectbox(key='gazette_subject').set_value('Reconstruction')
        app.multiselect(key='gazette_years').set_value(['2024'])
        app.session_state['reconstruction_section'] = 'Gazette'
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual([m.value for m in app.metric if m.label == 'Matching records'], ['1'])
        table = next(v.value for v in app.dataframe if 'Gazette title' in v.value.columns)
        self.assertEqual(table['ID'].tolist(), ['186181'])
        self.assertTrue(any(e.proto.label == 'Download Gazette records · CSV' for e in app.get('download_button')))
        app.session_state['reconstruction_section'] = 'Government response'
        app.run()
        app.session_state['reconstruction_section'] = 'Gazette'
        app.run()
        self.assertEqual(app.selectbox(key='gazette_subject').value, 'Reconstruction')
        app.session_state['reconstruction_section'] = 'Gazette'
        app.button(key='language_toggle').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['reconstruction_section'], 'الجريدة الرسمية')
        self.assertEqual(app.multiselect(key='gazette_years__ar').value, ['2024'])
        self.assertEqual(app.selectbox(key='gazette_subject__ar').value, 'Reconstruction')
        self.assertIn('سجلات الجريدة الرسمية', [m.label for m in app.metric])
        app.text_input(key='gazette_search').set_value('no-such-gazette-item')
        app.session_state['reconstruction_section'] = 'الجريدة الرسمية'
        app.run()
        self.assertFalse(app.exception)
        self.assertTrue(app.info)
        self.assertEqual([m.value for m in app.metric if m.label == 'السجلات المطابقة'], ['0'])


if __name__ == '__main__':
    unittest.main()
