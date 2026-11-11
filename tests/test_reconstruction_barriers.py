"""Protect attribution, dated funding scope and bilingual tab navigation."""
from datetime import date
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

from lxml import html as html_parser
from streamlit.testing.v1 import AppTest

from dashboard_data import load_data
from i18n import TAB_LABELS, translate
from reconstruction_barriers import (
    ROOT, RESTRICTION_GROUPS, barriers_html, case_group, dated,
    load_barriers, sources_html, local_funding_html, ui, all_cases_html,
)


class PageText(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.text = []
        self.links = []
        self.feed(html)

    def handle_data(self, value):
        self.text.append(value)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs)['href'])


class ReconstructionBarriersTests(unittest.TestCase):
    def test_rationale_and_status_limits_are_visible_before_expanding(self):
        data = load_barriers()
        for lang in ('en', 'ar'):
            tree = html_parser.fromstring(all_cases_html(data, lang))
            self.assertEqual(tree.xpath('.//div[@class="restriction-overview"]/div/strong/text()'), ['2', '7', '3'])
            for record in data['physical']:
                summary = tree.xpath(f'.//article[@data-case="{record["id"]}"]/details/summary')[0]
                self.assertIn(record['rationale'][lang], summary.text_content())
                self.assertIn(record['limit'][lang], summary.text_content())
            houla = tree.xpath('.//article[@data-case="houla_return"]/details/summary')[0]
            self.assertIn(ui('return_reported', lang), houla.text_content())

    def test_cases_have_dated_attribution_and_explicit_limits(self):
        data = load_barriers()
        reviewed = date.fromisoformat(data['reviewed_on'])
        self.assertEqual(data['scope'], 'lebanese_authorities_only')
        self.assertEqual(len({item['id'] for item in data['physical']}), len(data['physical']))
        for record in data['physical']:
            self.assertLessEqual(date.fromisoformat(record['date']), reviewed)
            self.assertNotEqual(record['status'], 'active_ban')
            self.assertIn(record['date_kind'], ('notice_date', 'report_date', 'statement_date', 'document_date'))
            for field in ('title', 'place', 'actor', 'blocked', 'action', 'limit'):
                self.assertEqual(set(record[field]), {'en', 'ar'})
                self.assertTrue(all(record[field].values()))
            self.assertTrue(record['sources'])
            for key in record['sources']:
                source = data['sources'][key]
                self.assertTrue(source['url'].startswith('https://'))
                self.assertTrue(source['access']['en'])
        for field in ('updates', 'budget_history'):
            for record in data[field]:
                self.assertIn(record['source'], data['sources'])
                self.assertLessEqual(date.fromisoformat(record['date']), reviewed)

    def test_local_gaps_do_not_convert_unknown_allocations_into_zero(self):
        data = load_barriers()
        self.assertEqual(len({row['id'] for row in data['funding_cases']}), len(data['funding_cases']))
        for row in data['funding_cases']:
            self.assertIsNone(row['allocation_usd'])
            self.assertIn(row['evidence'], ('reported_unmet_need', 'reported_uncovered_cost', 'fee_relief_missing'))
            self.assertEqual(row['date_kind'], 'report_date')
            self.assertLessEqual(date.fromisoformat(row['date']), date.fromisoformat(data['reviewed_on']))
            for field in ('title', 'place', 'actor', 'activity', 'action', 'limit'):
                self.assertEqual(set(row[field]), {'en', 'ar'})
                self.assertTrue(all(row[field].values()))
            for key in row['sources']:
                self.assertIn(key, data['sources'])
        hosh = next(row for row in data['funding_cases'] if row['id'] == 'hosh_residual_debris')
        self.assertEqual(hosh['household_cost_usd'], 1500)
        for lang in ('en', 'ar'):
            page = local_funding_html(data, lang)
            self.assertEqual(page.count(ui('not_quantified', lang)), len(data['funding_cases']))
            self.assertNotIn('$0', page)
            self.assertIn(ui('household_cost', lang), page)
            self.assertIn('$1,500', page)

    def test_zero_is_scoped_to_initial_programme_and_totals_reconcile(self):
        data = load_barriers()
        funding = data['funding']
        self.assertEqual(funding['basis'], 'initial_programme_financing')
        self.assertEqual(funding['as_of'], data['sources'][funding['source']]['date'])
        self.assertEqual(sum(row['available'] for row in funding['rows']), 250)
        self.assertEqual(sum(row['gap'] for row in funding['rows']), 750)
        self.assertEqual([row['code'] for row in funding['rows'] if row['available'] == 0], ['C3b'])
        government = {row['code']: row for row in load_data()['allocations']}
        for row in funding['rows']:
            self.assertEqual(row['available'], government[row['code']]['available_m'])
            self.assertEqual(row['gap'], government[row['code']]['gap_m'])

    def test_rendering_preserves_sources_and_every_case_in_both_languages(self):
        data = load_barriers()
        for lang in ('en', 'ar'):
            page = barriers_html(data, lang)
            parsed = PageText(page)
            text = ' '.join(parsed.text)
            for record in data['physical']:
                for field in ('title', 'place', 'actor', 'blocked', 'action', 'limit'):
                    self.assertIn(record[field][lang], text)
                self.assertIn(ui(record['date_kind'], lang), text)
                self.assertIn('data-case="' + record['id'] + '"', page)
            for record in data['funding_cases']:
                for field in ('title', 'place', 'actor', 'activity', 'action', 'limit'):
                    self.assertIn(record[field][lang], text)
                self.assertIn('data-funding-case="' + record['id'] + '"', page)
            self.assertIn('dir="' + ('rtl' if lang == 'ar' else 'ltr') + '"', page)
            sources = PageText(sources_html(data, lang))
            self.assertEqual(set(sources.links), {source['url'] for source in data['sources'].values()})
            self.assertTrue(set(parsed.links).issubset(set(sources.links)))
            self.assertNotIn('NaN', page)

    def test_focused_sections_separate_stoppages_rules_and_funding(self):
        data = load_barriers()
        grouped = {key: [row for row in data['physical'] if case_group(row) == key]
                   for key in RESTRICTION_GROUPS}
        self.assertEqual({key: len(rows) for key, rows in grouped.items()},
                         {'stopped': 2, 'roads': 2, 'return': 5, 'conditions': 3})
        for lang in ('en', 'ar'):
            for group, records in grouped.items():
                page = barriers_html(data, lang, 'restrictions', group)
                self.assertEqual(page.count('data-case='), len(records))
                for row in data['physical']:
                    self.assertEqual('data-case="' + row['id'] + '"' in page, row in records)
                self.assertNotIn('data-funding-case=', page)
            for group in ('leap', 'local', 'budget'):
                page = barriers_html(data, lang, 'funding', group)
                self.assertIn('data-group="' + group + '"', page)
                self.assertNotIn('data-case=', page)
                if group == 'local':
                    self.assertEqual(page.count('data-funding-case='), 4)
                    self.assertNotIn('$0', page)
                if group == 'budget':
                    self.assertIn(ui('budget_answer', lang), page)
                    for record in data['budget_history']:
                        self.assertIn(record['date'], page)
        self.assertEqual(dated('2026-10-19', 'ar'), '19 تشرين الأول 2026')

    def test_infographic_keeps_required_fields_outside_collapsed_details(self):
        data = load_barriers()
        for lang in ('en', 'ar'):
            root = html_parser.fromstring(barriers_html(data, lang))
            for detail in root.xpath('.//details[not(@open)]'):
                for child in list(detail):
                    if child.tag != 'summary':
                        detail.remove(child)
            for record in data['physical']:
                card = root.xpath(f'.//article[@data-case="{record["id"]}"]')[0]
                visible = ' '.join(card.itertext())
                for key in ('place', 'actor', 'blocked'):
                    self.assertIn(record[key][lang], visible)
                self.assertEqual(card.xpath('.//time/@datetime'), [record['date']])
                self.assertIn(ui(record['date_kind'], lang), visible)
                self.assertNotIn(record['action'][lang], visible)
            for record in data['funding_cases']:
                card = root.xpath(f'.//article[@data-funding-case="{record["id"]}"]')[0]
                visible = ' '.join(card.itertext())
                for key in ('place', 'actor', 'activity'):
                    self.assertIn(record[key][lang], visible)
                self.assertEqual(card.xpath('.//time/@datetime'), [record['date']])
                self.assertIn(ui('not_quantified', lang), visible)
                self.assertNotIn('$0', visible)
                if record.get('household_cost_usd'):
                    self.assertIn('$1,500', visible)
                    self.assertIn(ui('household_cost', lang), visible)
                else:
                    self.assertIn(ui('amount_unknown', lang), visible)

    def test_all_cases_show_without_selectors_in_both_languages(self):
        with patch('integrated_tenders.get_monitor'):
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run()
            label = 'Restrictions & funding gaps'
            app.session_state['reconstruction_section'] = label
            app.run()
            for lang in ('en', 'ar'):
                if lang == 'ar':
                    app.session_state['reconstruction_section'] = label
                    app.button(key='language_toggle').click().run()
                self.assertFalse(app.exception)
                self.assertFalse(any((widget.key or '').startswith('barriers_') for widget in app.selectbox))
                html = ''.join(node.proto.body for node in app.get('html'))
                root = html_parser.fromstring(html)
                for record in load_barriers()['physical']:
                    self.assertEqual(len(root.xpath(f'.//article[@data-case="{record["id"]}"]')), 1)
                for record in load_barriers()['funding_cases']:
                    self.assertEqual(len(root.xpath(f'.//article[@data-funding-case="{record["id"]}"]')), 1)
                self.assertIn(ui('not_quantified', lang), html)

    def test_all_case_summaries_keep_required_fields_and_sources(self):
        data = load_barriers()
        for lang in ('en', 'ar'):
            root = html_parser.fromstring(all_cases_html(data, lang))
            for funding, records in ((False, data['physical']), (True, data['funding_cases'])):
                for record in records:
                    attribute = 'data-funding-case' if funding else 'data-case'
                    card = root.xpath(f'.//article[@{attribute}="{record["id"]}"]')[0]
                    summary = card.xpath('./details/summary')[0]
                    visible = ' '.join(summary.itertext())
                    for field in ('place', 'actor', 'activity' if funding else 'blocked'):
                        self.assertIn(record[field][lang], visible)
                    self.assertEqual(summary.xpath('.//time/@datetime'), [record['date']])
                    self.assertIn(ui(record['date_kind'], lang), visible)
                    self.assertEqual(set(card.xpath('.//a/@href')),
                                     {data['sources'][key]['url'] for key in record['sources']})
                    for field in ('action', 'limit'):
                        self.assertIn(record[field][lang], ' '.join(card.itertext()))
                    if funding:
                        self.assertIn(ui('not_quantified', lang), visible)
                        self.assertNotIn('$0', visible)
                        if record.get('household_cost_usd'):
                            self.assertIn('$1,500', visible)
                            self.assertIn(ui('household_cost', lang), visible)

    def test_new_tab_renders_and_survives_language_switch(self):
        with patch('integrated_tenders.get_monitor'):
            app = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=30).run()
            self.assertFalse(app.exception)
            self.assertEqual([tab.label for tab in app.tabs], TAB_LABELS)
            label = 'Restrictions & funding gaps'
            app.session_state['reconstruction_section'] = label
            app.run()
            self.assertFalse(app.exception)
            self.assertTrue(any('barriers-page' in node.proto.body for node in app.get('html')))
            # AppTest does not model clicks on stateful tabs; supply the active
            # tab with each simulated interaction, as in test_i18n.py.
            app.session_state['reconstruction_section'] = label
            app.button(key='language_toggle').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['reconstruction_section'], translate(label, 'ar'))
            html = ''.join(node.proto.body for node in app.get('html'))
            self.assertIn('القيود وفجوات التمويل', html)
            self.assertIn('dir="rtl"', html)
            app.session_state['reconstruction_section'] = translate(label, 'ar')
            app.button(key='language_toggle').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['reconstruction_section'], label)


if __name__ == '__main__':
    unittest.main()
