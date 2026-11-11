"""Protect the supplied values, estimate boundaries and bilingual navigation."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from lxml import html
from streamlit.testing.v1 import AppTest

from economic_losses import (
    SOURCE, load_losses, headline_html, channels_html, regions_html,
    gdp_html, source_notes_html, original_cells_html, tr,
    sectors_html, displacement_html,
)
from i18n import TAB_LABELS

ROOT = Path(__file__).resolve().parents[1]


class EconomicLossTests(unittest.TestCase):
    def test_periods_and_provenance_stay_visible_beside_the_figures(self):
        data = load_losses()
        for lang in ('en', 'ar'):
            channels = html.fromstring(channels_html(data, lang))
            self.assertEqual(channels.xpath('.//div[@class="losses-pair"]/span/bdi/text()'), ['2024', '2026', '2024', '2026'])
            self.assertNotIn('2023', ' '.join(channels.xpath('.//*[@role="img"]/@aria-label')))
            self.assertIn(tr('channels_note', lang), channels.text_content())
            self.assertTrue(any('#page=33' in url for url in channels.xpath('.//a/@href')))
            self.assertTrue(any('#page=42' in url for url in channels.xpath('.//a/@href')))
            headline = html.fromstring(headline_html(data, lang))
            self.assertIn(tr('workbook_range', lang), headline.text_content())
            self.assertIn(tr('assessed', lang), headline.text_content())
            self.assertIn(tr('gdp_revision', lang), html.fromstring(gdp_html(data, lang)).text_content())
            self.assertIn(tr('regional_source', lang), html.fromstring(regions_html(data, lang)).text_content())

    def test_gdp_scenarios_reconcile_without_mutating_workbook_snapshot(self):
        data = load_losses()
        for row in data['gdp_comparisons']:
            self.assertAlmostEqual(row['no_war_pct'] - row['growth_pct'], row['lost_pp'])
        published = next(row for row in data['gdp_comparisons'] if row['year'] == 2024)
        workbook = next(row for row in data['gdp'] if row['year'] == 2024)
        self.assertEqual((published['growth_pct'], published['lost_pp']), (-5.7, 6.6))
        self.assertEqual(published['source'], 'WB-FALL24')
        self.assertEqual((workbook['growth_pct'], workbook['lost_pp']), (-5.2, 6.1))

    def test_snapshot_matches_all_original_workbook_cells(self):
        data = load_losses()
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(), data["source_sha256"])
        ns = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        with ZipFile(SOURCE) as archive:
            shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            strings = ["".join(node.itertext()) for node in shared.findall("x:si", ns)]
            sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        values = {}
        for node in sheet.findall(".//x:sheetData/x:row/x:c", ns):
            value = node.find("x:v", ns)
            if value is not None:
                values[node.attrib["r"]] = strings[int(value.text)] if node.attrib.get("t") == "s" else float(value.text)
        self.assertEqual(values, data["raw_cells"])
        self.assertEqual(len(values), 50)
        from scripts.import_economic_losses import read_sheets
        self.assertEqual(read_sheets(SOURCE), data['raw_sheets'])

    def test_added_sheets_keep_every_report_and_separate_snapshot_dates(self):
        data = load_losses()
        self.assertEqual(len(data['sector_rows']), 24)
        for lang in ('en', 'ar'):
            sectors = html.fromstring(sectors_html(data, lang))
            displacement = html.fromstring(displacement_html(data, lang))
            self.assertEqual(len(sectors.xpath('.//*[@data-sheet="Sectors"]')), 24)
            self.assertEqual(len(displacement.xpath('.//*[@data-sheet="IDPs"]')), 12)
            visible = displacement.text_content()
            for value in ('329,686', '877,203', '324,692', '16,536', 'Sept 29, 2026', 'Sept 15, 2026'):
                self.assertIn(value, visible)
            self.assertIn(tr('displacement_note', lang), visible)
            self.assertIn('No national count found', sectors.text_content())
            self.assertIn('01 Jul 2026', sectors.text_content())
            for row in data['sector_rows'] + data['displacement_indicators'] + data['displacement_locations']:
                for url in row['links'].splitlines():
                    if url.strip():
                        self.assertIn(url.strip(), sectors.xpath('.//a/@href') + displacement.xpath('.//a/@href'))

    def test_arabic_reports_translate_every_line_and_keep_the_workbook_wording(self):
        import re
        from collections import Counter
        from economic_losses import report_text, report_date, report_translations
        data = load_losses()
        translations = report_translations()
        shown = set()
        for row in data['sector_rows'] + data['displacement_indicators'] + data['displacement_locations']:
            shown.update(report_text(row[key]) for key in ('figure', 'source', 'date', 'district')
                         if isinstance(row.get(key), str))
        # No stale entries, and no English sentence left without Arabic.
        self.assertEqual(set(translations) - shown, set())
        self.assertEqual({text for text in shown - set(translations) if re.search('[A-Za-z]', text)}, set())
        for english, arabic in translations.items():
            self.assertRegex(arabic, '[؀-ۿ]')
            source, target = (Counter(re.findall(r'\d[\d,]*\d|\d', text)) for text in (english, arabic))
            # Every figure survives translation; only a spelled-out "one" or "two" may drop its digit.
            self.assertEqual(target - source, Counter(), english)
            self.assertLessEqual(set(source - target), {'1', '2'}, english)
        sectors = html.fromstring(sectors_html(data, 'ar'))
        for row in data['sector_rows']:
            node = sectors.xpath(f'.//*[@data-sheet="Sectors"][@data-row="{row["row"]}"]')[0]
            self.assertEqual(node.xpath('./p[@lang="ar"]/text()')[0], translations[report_text(row['figure'])])
            original = node.xpath('./p[contains(@class,"losses-original")]')[0].text_content()
            for value in (report_text(row['figure']), report_date(row['date']), report_text(row['source'])):
                self.assertIn(value, original)
        self.assertIn('1 تموز 2026', sectors.text_content())
        displacement = html.fromstring(displacement_html(data, 'ar'))
        for row in data['displacement_locations']:
            node = displacement.xpath(f'.//*[@data-sheet="IDPs"][@data-row="{row["row"]}"]')[0]
            self.assertEqual(node.xpath('./h3/text()')[0], translations[row['district']])
            self.assertIn(row['district'], node.text_content())
        # English pages are unchanged: no Arabic lines and no duplicate original line.
        english = sectors_html(data, 'en') + displacement_html(data, 'en')
        self.assertNotIn('lang="ar"', english)
        self.assertNotIn('losses-original', english)

    def test_reworded_workbook_cell_falls_back_to_the_original(self):
        data = load_losses()
        row = dict(data['sector_rows'][0], figure='A newly supplied figure')
        page = html.fromstring(sectors_html({**data, 'sector_rows': [row]}, 'ar'))
        node = page.xpath('.//*[@data-sheet="Sectors"]')[0]
        self.assertEqual(node.xpath('./p[@lang="ar"]'), [])
        self.assertIn('A newly supplied figure', node.text_content())

    def test_units_components_and_ranges_are_not_mixed(self):
        data = load_losses()
        first, second = data["phases"]
        self.assertEqual(first["total"]["usd_m"], [14000])
        self.assertEqual(first["damage"]["usd_m"][0] + first["losses"]["usd_m"][0], first["total"]["usd_m"][0])
        self.assertEqual(second["total"]["usd_m"], [7000, 9000])
        self.assertEqual(second["damage"]["usd_m"], [3000, 4000])
        self.assertEqual(second["losses"]["usd_m"], [4000, 5000])
        self.assertTrue(all(second[key]["estimated"] for key in ("total", "damage", "losses")))
        self.assertEqual(data["channel_totals"][1]["value"], 3571)
        self.assertEqual(sum(row["value"] for row in data["regions"]), 2937)
        self.assertEqual([row["lost_pp"] for row in data["gdp"]], [1, 6.1, 10.4])
        self.assertIsNone(data["gdp"][1]["no_war_pct"])
        for index, expected in enumerate((0.7, -0.4)):
            self.assertAlmostEqual(sum(row["values"][index]["value"] for row in data["channels"]) - data["channel_totals"][index]["value"], expected)
            for row in data["channels"]:
                self.assertEqual(row["values"][index]["value"], data["raw_cells"][row["values"][index]["cell"]])

    def test_bilingual_charts_preserve_values_notes_and_source_links(self):
        data = load_losses()
        for lang in ("en", "ar"):
            content = headline_html(data, lang) + channels_html(data, lang) + regions_html(data, lang) + gdp_html(data, lang)
            tree = html.fromstring(content)
            visible = " ".join(tree.itertext())
            for text in ("$14", "$7–9", "$6.8", "$7.2", "$3–4", "$4–5", "1,263.7", "569.6", "3,571", "2,937", "-6.4%", "10.4"):
                self.assertIn(text, visible)
            self.assertIn(tr("estimate_note", lang), visible)
            for region in data["regions"]:
                self.assertIn(region["label"][lang], visible)
            self.assertEqual(len(tree.xpath('.//*[@data-year]')), 3)
            notes = html.fromstring(source_notes_html(data, lang))
            self.assertEqual(set(notes.xpath(".//a/@href")), {row["url"] for row in data["sources"]})
            self.assertIn("4,200.7 / 4,200", " ".join(notes.itertext()))
            self.assertIn("3,570.6 / 3,571", " ".join(notes.itertext()))
            original = html.fromstring(original_cells_html(data, lang))
            self.assertEqual(len(original.xpath(".//tbody/tr")), sum(len(cells) for cells in data["raw_sheets"].values()))

    def test_new_tab_and_language_switch(self):
        with patch("integrated_tenders.get_monitor"):
            app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
            self.assertFalse(app.exception)
            self.assertEqual([tab.label for tab in app.tabs], TAB_LABELS)
            self.assertEqual(TAB_LABELS[1:3], ["Budget", "Economic losses"])
            app.session_state["reconstruction_section"] = "Economic losses"
            app.run()
            self.assertFalse(app.exception)
            self.assertIn("Economic losses", "".join(node.proto.body for node in app.get("html")))
            app.session_state["reconstruction_section"] = "Economic losses"
            app.button(key="language_toggle").click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state["reconstruction_section"], "الخسائر الاقتصادية")
            rendered = "".join(node.proto.body for node in app.get("html"))
            self.assertIn("خسائر السياحة والأسر", rendered)
            self.assertIn('dir="rtl"', rendered)
            self.assertIn("$7–9", rendered)
            self.assertIn('الأضرار حسب القطاع', rendered)
            self.assertIn('329,686', rendered)


if __name__ == "__main__":
    unittest.main()
