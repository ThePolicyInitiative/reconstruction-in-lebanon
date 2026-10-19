from copy import deepcopy
import unittest
from integrated_gazette.analytics import subject_breakdown, monthly_breakdown, year_comparison, classification_breakdown


def row(identifier, date, subjects=(), dtype='قرار', major='Government Operations', status='automated-proposal'):
    return {'id': identifier, 'date': date, 'subjects': list(subjects), 'type': dtype,
            'major': major, 'status': status, 'nature': 'Administrative'}


class GazetteChartTests(unittest.TestCase):
    def test_subject_overlap_uses_unique_record_denominators(self):
        rows = [row('1', '2024-01-01', ['Roads', 'Reconstruction']), row('2', '2024-02-01', ['Roads'], dtype='قانون'),
                row('3', '2025-01-01', [])]
        segments, totals, matrix = subject_breakdown(rows)
        roads = next(r for r in totals if r['subject'] == 'Roads')
        self.assertEqual(roads['count'], 2)
        self.assertAlmostEqual(roads['share'], 2/3)
        year = next(r for r in segments if r['subject'] == 'Roads' and r['year'] == '2024')
        self.assertEqual(year['year_share'], 1)
        self.assertEqual(sum(r['count'] for r in matrix if r['subject'] == 'Roads'), roads['count'])

    def test_missing_month_is_not_a_filtered_zero_and_future_months_are_absent(self):
        all_rows = [row('1', '2026-01-01'), row('2', '2026-03-12')]
        months = {r['month']: r for r in monthly_breakdown([all_rows[1]], all_rows, ['2026'])}
        self.assertEqual(months['2026-01']['count'], 0)
        self.assertIsNone(months['2026-02']['count'])
        self.assertEqual(months['2026-03']['count'], 1)
        self.assertNotIn('2026-04', months)

    def test_annual_comparison_uses_same_calendar_cutoff(self):
        rows = [row('1', '2024-02-29'), row('2', '2024-12-15'),
                row('3', '2025-10-15'), row('4', '2025-12-15'), row('5', '2026-10-15')]
        comparable = year_comparison(rows, rows)
        self.assertEqual([r['count'] for r in comparable], [1, 1, 1])
        self.assertEqual([r['through'] for r in comparable], ['2024-10-15', '2025-10-15', '2026-10-15'])
        self.assertEqual([r['count'] for r in year_comparison(rows, rows, same_window=False)], [2, 2, 1])
        self.assertEqual(year_comparison([], rows, ['2026'])[0]['count'], 0)

    def test_classification_case_groups_do_not_change_source_fields(self):
        rows = [row('1', '2026-01-01'), row('2', '2026-02-01', major=' Government operations ', status='needs-source-review')]
        before = deepcopy(rows)
        groups = classification_breakdown(rows, 'major')
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['count'], 2)
        self.assertEqual(groups[0]['share'], 1)
        self.assertEqual(groups[0]['needs_review'], 1)
        self.assertEqual(rows, before)


if __name__ == '__main__':
    unittest.main()
