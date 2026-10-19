"""Auditable dashboard enrichment; no network, external AI, or attachment downloads."""
from __future__ import annotations

import re
from datetime import datetime

VERSION = 1
CLASSIFICATION_VERSION = 2
UNKNOWN = "Not specified / غير محدد"
MONTHS = {"كانون الثاني": 1, "شباط": 2, "اذار": 3, "نيسان": 4, "ايار": 5,
          "حزيران": 6, "تموز": 7, "اب": 8, "ايلول": 9, "تشرين الاول": 10,
          "تشرين الثاني": 11, "كانون الاول": 12}
DISTRICTS = ["بيروت", "عكار", "بعلبك", "الهرمل", "زحلة", "راشيا", "البقاع الغربي",
             "بعبدا", "المتن", "الشوف", "عاليه", "كسروان", "جبيل", "طرابلس", "زغرتا",
             "بشري", "البترون", "الكورة", "الضنية", "المنية", "المنية الضنية", "صيدا",
             "صور", "جزين", "النبطية", "بنت جبيل", "مرجعيون", "حاصبيا"]
CONTENT_LABELS = {"موضوع الشراء", "ملخص الشراء", "عنوان المجموعة"}
LEAP_SOURCE = "https://www.worldbank.org/en/news/factsheet/2026/02/17/lebanon-emergency-assistance-project-frequently-asked-questions"


def normalize(text):
    text = str(text or "").lower().translate(str.maketrans("أإآٱى٠١٢٣٤٥٦٧٨٩", "ااااي0123456789"))
    return re.sub(r"\s+", " ", re.sub(r"[\u064b-\u065f\u0670ـ]", "", text)).strip()


def parse_date(value):
    text = normalize(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            pass
    for month, number in MONTHS.items():
        match = re.search(r"(?<!\d)(\d{1,2})\s+" + re.escape(month) + r"\s+(\d{4})(?!\d)", text)
        if match:
            try:
                return datetime(int(match[2]), number, int(match[1])).date().isoformat()
            except ValueError:
                return None
    return None


def content_fragments(record):
    seen = set()
    candidates = [("Title", record.get("title", ""))]
    candidates += [(f["label"], value) for f in record.get("fields", [])
                   if f["label"] in CONTENT_LABELS for value in f.get("values", [])]
    for label, text in candidates:
        key = normalize(text)
        if key and key not in seen:
            seen.add(key)
            yield label, text


def location_info(record, fragments):
    locations = list(dict.fromkeys(value.strip() for f in record.get("fields", [])
                                  if f["label"] == "أماكن التنفيذ"
                                  for value in f.get("values", []) if value.strip()))
    districts, evidence = set(), []
    for text in locations:
        for value in re.findall(r"القضاء\s*:\s*(.*?)(?=\s*(?:المحافظة|القضاء|البلدية)\s*:|$)", text):
            if value.strip():
                districts.add(value.strip())
                evidence.append({"district": value.strip(), "source": "Declared execution/delivery location", "text": text})
    basis = "Declared" if districts else "Not specified"
    # A named district in the project text is useful, but stays explicitly marked as inferred.
    if not districts:
        for label, text in fragments:
            normalized = normalize(text)
            for district, snippet in explicit_districts(normalized):
                districts.add(district)
                item = {"district": district, "source": label + " (explicit district mention)", "text": snippet}
                if item not in evidence:
                    evidence.append(item)
        if districts:
            basis = "Text mention"
    return {"districts": sorted(districts) or [UNKNOWN], "district_basis": basis,
            "location_text": "\n".join(locations), "district_evidence": evidence}


def explicit_districts(text):
    """Read only contiguous named districts after an explicit district/caza label."""
    aliases = {normalize(name): name for name in DISTRICTS}
    aliases["عالية"] = "عاليه"
    names = "|".join(re.escape(name) for name in sorted(aliases, key=len, reverse=True))
    # Preserve combined المنية–الضنية rather than counting it twice.
    text = re.sub(r"المنية\s*[-–—]\s*الضنية", "المنية الضنية", text)
    marker = re.compile(r"(?<!\w)(?:و?ال)?(?:اقضية|قضاء(?:ي|ين)?|قضائي)\s+")
    item = re.compile(r"\s*(?:[,،–—-]\s*)?(?:و\s*)?(" + names + r")(?!\w)")
    for prefix in marker.finditer(text):
        position = prefix.end()
        while match := item.match(text, position):
            yield aliases[match[1]], text[max(0, prefix.start()-50):match.end()+100]
            position = match.end()
    english_names = {"akkar": "عكار", "jbeil": "جبيل", "byblos": "جبيل",
                     "bcharré": "بشري", "bcharre": "بشري", "bsharri": "بشري",
                     "tyr": "صور", "tyre": "صور", "sour": "صور"}
    for name, district in english_names.items():
        pattern = r"\b(?:(?:caza|district)\s+(?:of\s+)?" + re.escape(name) + r"|" + re.escape(name) + r"\s+(?:caza|district))\b"
        for match in re.finditer(pattern, text):
            yield district, text[max(0, match.start()-50):match.end()+100]


ARABIC_PREFIX = r"(?<!\w)و?(?:ال|لل|[بلف](?:ال)?)?"
TOPIC_RULES = {
    "war": [ARABIC_PREFIX + r"حرب(?:ية)?(?!\w)", ARABIC_PREFIX + r"عدوان(?!\w)",
            ARABIC_PREFIX + r"قصف(?!\w)", ARABIC_PREFIX + r"نازح(?:ين|ون)(?!\w)",
            r"(?<!\w)و?نزحوا(?!\w)",
            r"مخلفات\s+الحرب", r"\bwar(?:[- ](?:damaged|affected|related|torn))?\b",
            r"\bpost[- ]conflict\b", r"\bconflict[- ](?:affected|damaged|torn)\b",
            r"\b(?:airstrikes?|bombardment|displaced persons)\b"],
    "reconstruction": [r"اعادة\s+(?:ال)?اعمار", r"اعاده\s+(?:ال)?اعمار", r"اعادة\s+بناء",
                       r"\breconstruction\b", r"\brebuild(?:ing|s)?\b"],
    "rehabilitation": [r"(?<!\w)و?(?:ال|لل|[لب](?:ال)?)?تاهيل(?!\w)", r"(?<!\w)و?(?:ال|لل|[لب](?:ال)?)?ترميم(?!\w)",
                       r"(?<!\w)و?(?:ال|لل|[لب](?:ال)?)?اصلاح(?!\w)", r"\brehabilitation\b",
                       r"\brestoration\b", r"\brepair(?:s|ing)?\b"],
}
COMPILED_RULES = {key: re.compile("|".join(patterns), re.I) for key, patterns in TOPIC_RULES.items()}
PREQUALIFICATION = re.compile(ARABIC_PREFIX + r"تاهيل\s+(?:(?:ال)?مسبق|لل(?:متعهدين|مقاولين|عارضين)|لزوم\s+اجراء\s+مناقصة)(?!\w)")
LEAP_RULE = re.compile(r"\bleap\b|مشروع\s+الدعم\s+الطار[ئيء]+\s+للبنان|\blebanon emergency assistance project\b", re.I)


def topic_info(fragments):
    evidence = []
    program_evidence = []
    found = set()
    for label, text in fragments:
        normalized = normalize(text)
        # Harb is also a person's name. This hospital is not evidence of war procurement.
        normalized = re.sub(r"ر(?:اغب|غاب)\s+حرب", lambda m: " " * len(m[0]), normalized)
        normalized = re.sub(r"council\s+for\s+development\s+(?:and|&)\s+reconstruction",
                            lambda m: " " * len(m[0]), normalized)
        normalized = re.sub(r"(?:international|european)\s+bank\s+for\s+reconstruction\s+(?:and|&)\s+development",
                            lambda m: " " * len(m[0]), normalized)
        # Bidder eligibility is not rehabilitation of a building or infrastructure.
        normalized = PREQUALIFICATION.sub(lambda m: " " * len(m[0]), normalized)
        program_match = LEAP_RULE.search(normalized)
        if program_match and not program_evidence:
            program_evidence.append({"program": "LEAP", "source": label, "match": program_match[0],
                                     "text": normalized[max(0, program_match.start()-90):program_match.end()+160],
                                     "reference_url": LEAP_SOURCE})
        for topic, rule in COMPILED_RULES.items():
            match = rule.search(normalized)
            if match and topic not in found:
                found.add(topic)
                evidence.append({"topic": topic, "source": label, "match": match[0],
                                 "text": normalized[max(0, match.start()-90):match.end()+160]})
    # Explicit war wording plus repair/rehabilitation wording is a reconstruction candidate.
    reconstruction = "reconstruction" in found or {"war", "rehabilitation"}.issubset(found)
    return {"war_related": "war" in found, "reconstruction_related": reconstruction,
            "rehabilitation_related": "rehabilitation" in found,
            "reconstruction_or_war": reconstruction or "war" in found,
            "topic_evidence": evidence, "recovery_program_related": bool(program_evidence),
            "program_evidence": program_evidence, "classification_version": CLASSIFICATION_VERSION}


def enrich(index_row, record):
    fragments = list(content_fragments(record))
    row = dict(index_row)
    row.update(location_info(record, fragments))
    row.update(topic_info(fragments))
    row["announcement_date"] = parse_date(row.get("announced_on", ""))
    row["deadline_date"] = parse_date(row.get("submission_deadline", ""))
    row["collected_at"] = record.get("scraped_at_utc", "")
    summaries = [text for label, text in fragments if label == "ملخص الشراء"]
    row["summary"] = "\n\n".join(summaries)[:12000]
    return row


def newest_first(rows):
    return sorted(rows, key=lambda r: (r.get("announcement_date") or "", int(r["id"])), reverse=True)


def district_counts(rows):
    counts = {}
    for row in rows:
        for district in set(row["districts"]):
            counts[district] = counts.get(district, 0) + 1
    return sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))
