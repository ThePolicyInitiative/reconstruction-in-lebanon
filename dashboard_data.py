"""Curated public evidence. Display dates describe sources, not live updates."""
import json
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "government_response.json"


def load_data():
    with DATA_FILE.open(encoding="utf-8") as file:
        data = json.load(file)
    with DATA_FILE.with_name("governance_details.json").open(encoding="utf-8") as file:
        data["governance"] = json.load(file)
    return data


def display_date(value):
    if not value:
        return "Undated page"
    if len(value) == 7:
        return datetime.strptime(value, "%Y-%m").strftime("%b %Y")
    return datetime.strptime(value, "%Y-%m-%d").strftime("%d %b %Y")


def filter_events(data, sector="All sectors", source_type="All sources", query=""):
    query = query.strip().casefold()
    return sorted(
        [event for event in data["events"]
         if (sector == "All sectors" or event["sector"] == sector)
         and (source_type == "All sources" or data["sources"][event["source"]]["kind"] == source_type)
         and (not query or query in " ".join(str(value) for value in event.values()).casefold())],
        key=lambda event: event["date"], reverse=True,
    )


def filter_projects(data, area="All areas", sector="All sectors"):
    return [project for project in data["projects"]
            if (area == "All areas" or area in project["areas"])
            and (sector == "All sectors" or sector == project["sector"])]
