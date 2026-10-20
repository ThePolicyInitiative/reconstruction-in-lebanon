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
)
from i18n import TAB_LABELS

ROOT = Path(__file__).resolve().parents[1]


class EconomicLossTests(unittest.TestCase):
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
        self.assertEqual(len(values), 48)

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
            self.assertEqual(len(original.xpath(".//tbody/tr")), len(data["raw_cells"]))

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


if __name__ == "__main__":
    unittest.main()
