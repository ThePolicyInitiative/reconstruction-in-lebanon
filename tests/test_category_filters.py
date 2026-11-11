"""Combined subject/programme filters and dependent Gazette classifications."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from tests.support import OfflineFeed
from integrated_tenders.categories import ANY_SUBJECT, NO_SUBJECT
from integrated_gazette.data_feed import load_snapshot

ROOT = Path(__file__).resolve().parents[1]


class CategoryFilterTests(unittest.TestCase):
    def test_tender_programme_combines_with_subject_and_no_match(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))
        snapshot = OfflineFeed().refresh()
        for payload, _ in snapshot['sources'].values():
            template = payload['tenders'][0]
            payload['tenders'] = [{**deepcopy(template), 'id':str(i), 'title':title,
                                  'summary':'', 'topic_evidence':[], 'program_evidence':[],
                                  'announcement_date':'2026-01-01'}
                                 for i, title in enumerate(('LEAP procurement specialist',
                                                           'LEAP road rehabilitation', 'Office supplies'))]
        feed = self.enterContext(patch('integrated_tenders.get_feed'))
        feed.return_value.refresh.return_value = snapshot
        feed.return_value.detail.return_value = None
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'), default_timeout=60).run()

        def run():
            app.session_state['reconstruction_section'] = 'Tenders'
            app.run()
            self.assertFalse(app.exception)

        run()
        app.selectbox(key='tender_programme').set_value('LEAP')
        app.selectbox(key='tender_category').set_value(ANY_SUBJECT)
        run()
        self.assertEqual([m.value for m in app.metric if m.label == 'Filtered tenders'], ['1','1'])
        app.selectbox(key='tender_category').set_value(NO_SUBJECT)
        run()
        self.assertEqual([m.value for m in app.metric if m.label == 'Filtered tenders'], ['1','1'])
        for element in app.dataframe:
            if 'Tender' in element.value.columns:
                self.assertEqual(element.value['Tender'].tolist(), ['LEAP procurement specialist'])

    def test_gazette_subcategories_follow_main_category_and_survive_language_switch(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))
        snapshot = load_snapshot([ROOT/'integrated_gazette/data/snapshot.json.gz'])
        base = snapshot['records'][0]
        snapshot['records'] = [{**base, 'id':str(i), 'title':'Office supplies',
                                'major':major, 'sub':sub}
                               for i, (major, sub) in enumerate((('Government Operations', 'Appointments'),
                                                                (' government operations ', 'appointments'),
                                                                ('Education', 'Higher'), ('', '')))]
        feed = self.enterContext(patch('integrated_gazette.get_feed'))
        feed.return_value.refresh.return_value = {'snapshot':snapshot, 'error':None}
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'), default_timeout=60).run()

        def run(section='Gazette'):
            app.session_state['reconstruction_section'] = section
            app.run()
            self.assertFalse(app.exception)

        run()
        self.assertEqual(len(app.multiselect(key='gazette_majors').options), 3)
        app.multiselect(key='gazette_majors').set_value(['Government Operations'])
        run()
        self.assertEqual(app.multiselect(key='gazette_subs').options, ['Appointments'])
        app.multiselect(key='gazette_subs').set_value(['Appointments'])
        run()
        self.assertEqual([m.value for m in app.metric if m.label == 'Matching records'], ['2'])
        app.multiselect(key='gazette_majors').set_value(['Education'])
        run()
        self.assertEqual(app.multiselect(key='gazette_subs').value, [])
        self.assertEqual(app.multiselect(key='gazette_subs').options, ['Higher'])
        app.multiselect(key='gazette_subs').set_value(['Higher'])
        run()
        app.session_state['reconstruction_section'] = 'Gazette'
        app.button(key='language_toggle').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.multiselect(key='gazette_subs__ar').value, ['Higher'])
        app.multiselect(key='gazette_majors__ar').set_value(['Not specified'])
        run('الجريدة الرسمية')
        self.assertEqual(app.multiselect(key='gazette_subs__ar').value, [])
        self.assertEqual([m.value for m in app.metric if m.label == 'السجلات المطابقة'], ['1'])


if __name__ == '__main__':
    unittest.main()
