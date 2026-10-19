"""Create a compact, deterministic dashboard file from the complete saved records."""
import argparse
import hashlib
import json
from pathlib import Path

from .monitor import read_json, save_json
from .tender_analytics import VERSION, enrich, newest_first


def build(data_dir, source="https://www.ppa.gov.lb/ar/tenders"):
    index = read_json(data_dir / "index.json")
    rows = []
    seen = set()
    for item in index:
        tender_id = item["id"]
        if not str(tender_id).isdigit() or tender_id in seen:
            raise ValueError("Invalid or duplicated tender ID in index")
        seen.add(tender_id)
        record = read_json(data_dir / "tenders" / f"{tender_id}.json")
        if record["id"] != tender_id:
            raise ValueError("Detail record does not match the index")
        rows.append(enrich(item, record))
    rows = newest_first(rows)
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    payload = {"schema_version": VERSION, "fingerprint": fingerprint, "total": len(rows),
               "source": source, "tenders": rows}
    save_json(data_dir / "dashboard.json", payload)
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent / "data")
    args = parser.parse_args()
    result = build(args.data_dir)
    print(json.dumps({"tenders": result["total"], "fingerprint": result["fingerprint"]}))
