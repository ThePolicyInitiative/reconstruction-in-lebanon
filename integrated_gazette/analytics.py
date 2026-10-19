"""Display-only subject tags; Memo's four classification fields stay exact."""
from __future__ import annotations
import re
from collections import Counter
from integrated_tenders.categories import CATEGORIES, classify, category_normalize
from .data_feed import YEARS
from .labels import TYPE_LABELS

ALL = 'All Gazette records'
RELATED = 'Any of the seven subjects'


def tag_records(rows):
    result = []
    for row in rows:
        title = category_normalize(row['title'])
        # An institution's name does not establish reconstruction works.
        for pattern in (
            r'المجلس?\s+الانماء\s+والاعمار', r'مجلس\s+الانماء\s+والاعمار',
            r'البنك\s+(?:الاوروبي|الدولي)\s+(?:ل?اعادة|لاعاده)\s+الاعمار\s+والتنمية',
            r'بنك\s+اعادة\s+الاعمار\s+الالماني',
        ):
            title = re.sub(pattern, lambda m: ' ' * len(m[0]), title)
        matched = classify({'title': title})
        # The original title and original classification are always retained.
        result.append({**row, 'subjects': matched['categories'], 'subject_evidence': matched['category_evidence']})
    return result


def filter_records(rows, query='', years=(), subject=ALL, types=(), majors=(), statuses=()):
    query = category_normalize(query).strip()
    return [r for r in rows
            if r['date'][:4] in (years or YEARS)
            and (not query or query in category_normalize(' '.join(str(r.get(k) or '') for k in ('id', 'number', 'title', 'major', 'sub', 'admin_function'))))
            and (subject == ALL or subject == RELATED and r['subjects'] or subject in r['subjects'])
            and (not types or r['type'] in types)
            and (not majors or r['major'] in majors)
            and (not statuses or r['status'] in statuses)]


def csv_rows(rows):
    return [{'ID': r['id'], 'Published': r['date'], 'Document type': r['type'],
             'Document number': r['number'], 'Gazette title': r['title'],
             'Website subjects': ' · '.join(r['subjects']), 'Nature': r['nature'],
             'Administrative function': r['admin_function'], 'Main category': r['major'],
             'Subcategory': r['sub'], 'Assessment status': r['status'],
             'Assessment method': r['method'], 'Review notes': r['review_reasons'],
             'Document date': r['doc_date'] or '', 'Source': r['url']} for r in rows]


def subject_breakdown(rows, years=()):
    """One record per subject; multiple subjects can overlap, unlike document types."""
    years = sorted(years or YEARS)
    year_totals = Counter(r['date'][:4] for r in rows)
    segments, totals, matrix = [], [], []
    for subject in CATEGORIES:
        matches = [r for r in rows if subject in r['subjects']]
        total = len(matches)
        totals.append({'subject': subject, 'count': total, 'share': total / len(rows) if rows else 0,
                       'needs_review': sum(r['status'] == 'needs-source-review' for r in matches)})
        for year in years:
            count = sum(r['date'][:4] == year for r in matches)
            segments.append({'subject': subject, 'year': year, 'count': count,
                             'year_total': year_totals[year],
                             'year_share': count / year_totals[year] if year_totals[year] else 0,
                             'subject_total': total})
        for key, label in TYPE_LABELS.items():
            count = sum(r['type'] == key for r in matches)
            matrix.append({'subject': subject, 'type': label, 'count': count,
                           'subject_total': total, 'share': count / total if total else 0})
    return segments, totals, matrix


def monthly_breakdown(rows, coverage, years=()):
    """A filtered zero is distinct from a month absent from the retained archive."""
    years = sorted(years or YEARS)
    available = Counter(r['date'][:7] for r in coverage)
    cutoff = max((r['date'][:7] for r in coverage), default='')
    counts = Counter((r['date'][:7], r['type']) for r in rows)
    result = []
    for year in years:
        for month in range(1, 13):
            key = f'{year}-{month:02}'
            if key > cutoff:
                continue
            source_count = available[key]
            values = {label: counts[(key, dtype)] if source_count else None for dtype, label in TYPE_LABELS.items()}
            total = sum(value or 0 for value in values.values()) if source_count else None
            result.append({'month': key, **values, 'count': total, 'source_records': source_count,
                           'available': bool(source_count)})
    return result


def year_comparison(rows, coverage, years=(), same_window=True):
    years = sorted(years or YEARS)
    last = {year: max((r['date'] for r in coverage if r['date'][:4] == year), default=None) for year in years}
    cutoff = min((value[5:] for value in last.values() if value), default=None)
    result = []
    for year in years:
        matches = [r for r in rows if r['date'][:4] == year]
        comparable = [r for r in matches if not same_window or r['date'][5:] <= cutoff] if cutoff else []
        result.append({'year': year, 'count': len(comparable) if last[year] else None,
                       'all_records': len(matches) if last[year] else None,
                       'through': f'{year}-{cutoff}' if same_window and cutoff else last[year],
                       'latest_publication': last[year],
                       **{label: sum(r['type'] == key for r in comparable) if last[year] else None for key, label in TYPE_LABELS.items()}})
    return result


def classification_breakdown(rows, field):
    """Group case/space variants for charts only; retain all original labels in exports."""
    groups = {}
    for row in rows:
        label = row.get(field, '').strip() or 'Not specified'
        group = groups.setdefault(label.casefold(), {'variants': Counter(), 'records': []})
        group['variants'][label] += 1
        group['records'].append(row)
    result = []
    for group in groups.values():
        matches = group['records']
        label = sorted(group['variants'], key=lambda value: (-group['variants'][value], value))[0]
        result.append({'label': label, 'count': len(matches), 'share': len(matches) / len(rows),
                       'variants': ' · '.join(sorted(group['variants'])),
                       'needs_review': sum(r['status'] == 'needs-source-review' for r in matches),
                       **{name: sum(r['type'] == key for r in matches) for key, name in TYPE_LABELS.items()}})
    return sorted(result, key=lambda r: (-r['count'], r['label']))
