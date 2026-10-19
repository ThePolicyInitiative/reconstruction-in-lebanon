import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from budget import PERIODS, allocation_groups, load_budget, parse_amount, primary_lines, totals

ROOT = Path(__file__).resolve().parents[1]


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch('integrated_tenders.get_monitor'))

    def test_totals_exclude_component_rows(self):
        records = load_budget()
        self.assertEqual(len(records), 19)
        self.assertEqual(len(primary_lines(records)), 15)
        self.assertEqual(list(totals(records).values()), [95_776_503, 135_307_229, 135_307_229])
        parent = next(row for row in records if row['code'].endswith('|FAMILY_TOTAL'))
        children = [row for row in records if row['parent'] == parent['code']]
        for period in PERIODS:
            self.assertEqual(sum(row['amounts'][period] for row in children if row['amounts'][period] is not None), parent['amounts'][period])
            grouped = allocation_groups(records, period)
            self.assertEqual(sum(amount for _, amount in grouped if amount is not None), totals(records)[period])

    def test_unavailable_is_not_zero(self):
        self.assertIsNone(parse_amount('n.a.'))
        self.assertEqual(parse_amount('0'), 0)
        groups = dict(allocation_groups(load_budget(), PERIODS[0]))
        self.assertIsNone(groups['Capital works & reconstruction'])
        self.assertEqual(groups['Housing compensation & reconstruction'], 89_385_475)

    def test_draft_difference_reconciles(self):
        by_code = {row['code']: row for row in load_budget()}
        mixed = by_code['1.3.211.1091.14.1.2|D001']['amounts']
        repairs = by_code['1.3.211.1091.14.1.2|D002']['amounts']
        self.assertIsNone(repairs[PERIODS[1]])
        self.assertEqual(mixed[PERIODS[1]] - mixed[PERIODS[2]], 11_173_184)
        self.assertEqual(mixed[PERIODS[2]] + repairs[PERIODS[2]], mixed[PERIODS[1]])

    def test_budget_runs_independently_and_switches_versions(self):
        with patch('integrated_tenders.get_feed', side_effect=AssertionError('Budget must not load the tender feed')):
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py')).run()
            self.assertEqual(app.tabs[1].label, 'Budget')
            app.session_state['reconstruction_section'] = 'Budget'
            app.run()
            self.assertFalse(app.exception)
            html = ''.join(item.proto.body for item in app.get('html'))
            self.assertIn('$135,307,229', html)
            self.assertIn('$95,776,503', html)
            self.assertIn('n.a.', html)
            self.assertNotIn('????', html)
            app.selectbox(key='budget_version').set_value(PERIODS[0])
            # AppTest does not serialize stateful tab widgets; provide the
            # active label alongside the changed selectbox value.
            app.session_state['reconstruction_section'] = 'Budget'
            app.run()
            self.assertFalse(app.exception)
            html = ''.join(item.proto.body for item in app.get('html'))
            self.assertIn('$89.39m', html)


if __name__ == '__main__':
    unittest.main()
