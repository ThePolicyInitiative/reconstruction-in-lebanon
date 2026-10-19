"""The website's year scope applies before totals, filters and export tables."""
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import unittest

from streamlit.testing.v1 import AppTest
from tests.support import OfflineFeed

ROOT = Path(__file__).resolve().parents[1]


class TenderYearTests(unittest.TestCase):
    def test_scope_and_optional_year_filter(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))
        snapshot = OfflineFeed().refresh()
        dates = ['2023-12-31', '2024-01-01', '2025-06-01', '2026-12-31', '2027-01-01', None]
        for source, (payload, status) in snapshot['sources'].items():
            template = payload['tenders'][0]
            payload['tenders'] = []
            for index, date in enumerate(dates):
                row = deepcopy(template)
                row.update(id=str(index + 1), announcement_date=date,
                           submission_deadline='2020-01-01 00:00:00', deadline_date='2020-01-01')
                payload['tenders'].append(row)
        with patch('integrated_tenders.get_feed') as get_feed:
            get_feed.return_value.refresh.return_value = snapshot
            get_feed.return_value.detail.return_value = None
            app = AppTest.from_file(str(ROOT/'streamlit_app.py'), default_timeout=60).run()
            app.session_state['deadline_open'] = True  # Old sessions must not silently apply the removed filter.
            app.session_state['reconstruction_section'] = 'Tenders'
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual(app.multiselect(key='years_2024_2026').options, ['2026','2025','2024'])
            self.assertEqual([m.value for m in app.metric if m.label=='Total tenders'], ['3','3'])
            self.assertEqual([m.value for m in app.metric if m.label=='Filtered tenders'], ['3','3'])
            tables = [element.value for element in app.dataframe if 'Announced' in element.value.columns]
            self.assertGreaterEqual(len(tables), 2)
            for table in tables:
                self.assertTrue(set(table['Announced']).issubset({'2024-01-01','2025-06-01','2026-12-31'}))
            self.assertNotIn('Future submission deadline only', [c.label for c in app.checkbox])
            self.assertNotIn('GitHub repository ↗', [link.proto.label for link in app.get('link_button')])
            app.multiselect(key='years_2024_2026').set_value(['2025'])
            app.session_state['reconstruction_section'] = 'Tenders'
            app.run()
            self.assertFalse(app.exception)
            self.assertEqual([m.value for m in app.metric if m.label=='Total tenders'], ['3','3'])
            self.assertEqual([m.value for m in app.metric if m.label=='Filtered tenders'], ['1','1'])


if __name__ == '__main__':
    unittest.main()
