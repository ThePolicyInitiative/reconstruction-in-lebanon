import unittest
from pathlib import Path

from dashboard_data import filter_events, filter_projects, load_data
from streamlit.testing.v1 import AppTest
from tests.support import offline_tender_feed

ROOT = Path(__file__).resolve().parents[1]


class EvidenceTests(unittest.TestCase):
    def test_financing_is_internally_consistent_and_dated(self):
        data = load_data()
        funding = data["funding"]
        self.assertEqual(funding["approved_usd"] + funding["gap_usd"], funding["framework_usd"])
        self.assertEqual(funding["as_of"], data["sources"][funding["source"]]["date"])
        allocations = data["allocations"]
        self.assertEqual(sum(row["available_m"] for row in allocations) * 1e6, funding["approved_usd"])
        self.assertEqual(sum(row["gap_m"] for row in allocations) * 1e6, funding["gap_usd"])
        for row in allocations:
            self.assertEqual(row["available_m"] + row["gap_m"], row["total_m"])

    def test_every_displayed_record_has_an_identifiable_source(self):
        data = load_data()
        for group in ["stages", "people", "events", "projects", "allocations"]:
            for record in data[group]:
                for key in ["source", "context_source", "scope_source"]:
                    if key in record:
                        source = data["sources"][record[key]]
                        self.assertTrue(source["url"].startswith("https://"))
                        self.assertTrue(source["publisher"])
        people = {person["initials"] for person in data["people"]}
        self.assertIn(data["governance"]["source"], data["sources"])
        for initials, role in data["governance"]["roles"].items():
            self.assertIn(initials, people)
            for source in role["sources"]:
                self.assertIn(source, data["sources"])
        for ministry in data["governance"]["technical_ministries"]:
            self.assertIn(ministry["initials"], people)

    def test_filters_combine_and_search_ignores_case(self):
        data = load_data()
        matches = filter_events(data, "Public infrastructure", "Government", " SALAM ")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["date"], "2025-12-31")
        self.assertEqual(filter_events(data, query="no_such_milestone"), [])

    def test_project_filters_use_coverage_and_intersect(self):
        data = load_data()
        for area in ["Beirut & Mount Lebanon", "Beqaa", "South Lebanon"]:
            matches = filter_projects(data, area, "Public buildings")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["step"], 2)
        self.assertEqual(len(filter_projects(data, "Nabatieh", "Roads")), 1)
        self.assertEqual(filter_projects(data, "Nabatieh", "Environment"), [])

    def test_streamlit_renders_remaining_sections(self):
        self.enterContext(offline_tender_feed())
        app = AppTest.from_file(str(ROOT / "streamlit_app.py"), default_timeout=30).run()
        self.assertEqual(len(app.exception), 0, str(app.exception))
        main_labels = ['Government response', 'Budget', 'Economic losses', 'Restrictions & funding gaps', 'Tenders', 'Gazette', 'What parties are saying', 'What countries are saying', 'Evidence of destruction']
        self.assertEqual([tab.label for tab in app.tabs if tab.label in main_labels], main_labels)
        html = "".join(element.proto.body for element in app.get("html"))
        self.assertNotIn('id="delivery"', html)
        self.assertNotIn('id="timeline"', html)
        self.assertIn('id="stages"', html)
        self.assertIn('id="sources"', html)
        self.assertEqual(len(app.tabs[0].selectbox), 0)
        self.assertEqual(len(app.tabs[0].text_input), 0)


if __name__ == "__main__":
    unittest.main()
