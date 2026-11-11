"""Import the supplied workbook snapshot without changing reviewed headline data."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_sheets(path):
    with ZipFile(path) as archive:
        shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings = ["".join(node.itertext()) for node in shared.findall("x:si", NS)]
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target") for rel in rels}
        result = {}
        for sheet in workbook.find("x:sheets", NS):
            target = targets[sheet.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")]
            sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
            cells = {}
            for node in ET.fromstring(archive.read(sheet_path)).findall(".//x:sheetData/x:row/x:c", NS):
                value = node.find("x:v", NS)
                if value is not None:
                    cells[node.get("r")] = strings[int(value.text)] if node.get("t") == "s" else float(value.text)
            result[sheet.get("name")] = cells
        return result


def main(source):
    sheets = read_sheets(source)
    target = ROOT / "data/Economic_losses_war_AY.xlsx"
    data_path = ROOT / "data/economic_losses.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    general = sheets["General (US$)"]
    # Never silently retain reviewed charts when an incoming source changes their inputs.
    changed = [cell for cell, value in data["raw_cells"].items() if general.get(cell) != value]
    if changed:
        raise ValueError(f"Review changed general cells before importing: {changed}")
    data.update(source_file=source.name, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                sheet="General (US$)", raw_cells=general, raw_sheets=sheets)
    sector_rows = []
    for phase, rows in [("2023–2024", range(3, 17)), ("2026", range(22, 32))]:
        category = None
        for row in rows:
            category = sheets["Sectors"].get(f"A{row}", category)
            sector_rows.append({"phase": phase, "category": category, "row": row,
                                **{key: sheets["Sectors"].get(f"{col}{row}", "")
                                   for key, col in [("figure", "B"), ("source", "C"), ("date", "D"), ("links", "E")]}})
    data["sector_rows"] = sector_rows
    data["displacement_indicators"] = [
        {"row": row, **{key: sheets["IDPs"].get(f"{col}{row}", "")
                        for key, col in [("label", "A"), ("figure", "B"), ("date", "C"), ("links", "D")]}}
        for row in range(3, 7)]
    group = None
    destinations = []
    for row in range(11, 19):
        group = sheets["IDPs"].get(f"A{row}", group)
        destinations.append({"group": group, "row": row,
                             **{key: sheets["IDPs"].get(f"{col}{row}", "")
                                for key, col in [("district", "B"), ("figure", "C"), ("date", "D"), ("links", "E")]}})
    data["displacement_locations"] = destinations
    shutil.copyfile(source, target)
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
