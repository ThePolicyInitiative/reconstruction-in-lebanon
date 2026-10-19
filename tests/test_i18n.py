"""Language switches preserve the selected page, data values and filter behavior."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from i18n import translate, translate_html
from tests.support import offline_tender_feed

ROOT = Path(__file__).resolve().parents[1]


class ArabicTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))

    def test_translation_keeps_numbers_codes_and_links(self):
        self.assertEqual(translate('Government response', 'ar'), 'استجابة الحكومة')
        self.assertEqual(translate('$135.31M', 'ar'), '$135.31 مليون')
        self.assertEqual(translate('1.3.211.1091.14.1.2|D001', 'ar'), '1.3.211.1091.14.1.2|D001')
        with patch('i18n.language', return_value='ar'):
            html = translate_html('<a href="https://example.org/Budget">Budget</a><style>.Budget{color:black}</style>')
        self.assertIn('href="https://example.org/Budget"', html)
        self.assertIn('>الموازنة</a>', html)
        self.assertIn('.Budget{color:black}', html)

    def test_component_catalogs_match(self):
        from scripts.install_localization import localized_page
        catalog = json.loads((ROOT/'locales/ar.json').read_text(encoding='utf-8'))
        for component in ('parties','countries','evidence'):
            path = ROOT/'imported'/component
            self.assertEqual(json.loads((path/'ar.json').read_text(encoding='utf-8')), catalog)
            self.assertEqual((path/'localize.js').read_bytes(), (ROOT/'assets/component-i18n.js').read_bytes())
            page = (path/'index.html').read_text(encoding='utf-8')
            self.assertEqual(page, localized_page(page, parties=component in ('parties', 'countries')))
            if component in ('parties', 'countries'):
                self.assertIn('class="party-scroll"',page)

    def test_switch_preserves_budget_tab_and_period(self):
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=30).run()
        app.session_state['reconstruction_section'] = 'Budget'
        app.run()
        from budget import PERIODS
        app.selectbox(key='budget_version').set_value(PERIODS[0])
        app.session_state['reconstruction_section'] = 'Budget'
        app.run()
        period = app.selectbox(key='budget_version').value
        app.session_state['reconstruction_section'] = 'Budget'
        app.button(key='language_toggle').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['language'],'ar')
        self.assertEqual(app.session_state['reconstruction_section'],'الموازنة')
        self.assertEqual(app.selectbox(key='budget_version__ar').value,period)
        self.assertEqual(app.query_params['lang'],['ar'])
        app.session_state['reconstruction_section'] = 'الموازنة'
        app.button(key='language_toggle').click().run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['reconstruction_section'],'Budget')

    def test_arabic_tender_filter_uses_original_values(self):
        self.enterContext(offline_tender_feed())
        app = AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60)
        app.query_params['lang'] = 'ar'
        app.run()
        app.session_state['reconstruction_section'] = 'المناقصات'
        app.run()
        self.assertFalse(app.exception)
        app.selectbox(key='tender_category__ar').set_value('LEAP')
        app.session_state['reconstruction_section'] = 'المناقصات'
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox(key='tender_category__ar').value,'LEAP')
        self.assertEqual(app.selectbox(key='tender_category__ar').label,translate('Category','ar'))
        counts=[int(metric.value.replace(',','')) for metric in app.metric if metric.label==translate('Filtered tenders','ar')]
        self.assertEqual(len(counts),2)
        self.assertTrue(all(value>0 for value in counts))


if __name__ == '__main__':
    unittest.main()
