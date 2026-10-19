"""Parse CDR's public procurement listings and detail pages without fetching documents."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, quote, unquote, urljoin, urlsplit, urlunsplit

from lxml import html

from .ppa_parser import now
from .tender_analytics import parse_date

BASE = "https://www.cdr.gov.lb"
START = BASE + "/ar/Procurment.aspx?aliaspath=%2fProcurment"
STAGES = ("Ongoing", "Archive", "Others")
BUYER = "مجلس الإنماء والإعمار · Council for Development and Reconstruction"
CONTENT = 'contains(concat(" ", normalize-space(@class), " "), " content ")'
EMPTY = "لا يوجد حاليا اي مناقصة"


def text(node):
    return " ".join(" ".join(node.itertext()).split())


def document(raw):
    return html.fromstring(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw)


def detail_url(ident, lot):
    if not str(ident).isdigit() or not str(lot).isdigit():
        raise ValueError("Invalid CDR project or lot ID")
    return BASE + f"/ar/Procurment/ProcurementDetail.aspx?id={ident}&lot={lot}&aliaspath=%2fProcurment%2fProcurementDetail"


def listing(raw, stage, fragment=False):
    if stage not in STAGES:
        raise ValueError("Unknown CDR stage")
    raw = raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw
    if fragment and not raw.strip():
        return []
    doc = html.fragment_fromstring(raw, create_parent="table") if fragment else document(raw)
    rows = doc.xpath(f'.//tr[{CONTENT}]')
    if not rows:
        main = doc.xpath('//main') if not fragment else []
        if main and EMPTY in text(main[0]):
            return []
        raise ValueError(f"Unrecognized CDR {stage} listing; refusing an empty/error page")
    result = []
    for row in rows:
        cells = row.xpath('./td')
        if len(cells) not in (9, 10):
            raise ValueError("CDR listing columns changed")
        links = cells[0].xpath('.//a[@href]')
        if not links:
            raise ValueError("CDR row has no detail link")
        url = urlsplit(urljoin(BASE, links[0].get('href')))
        query = parse_qs(url.query)
        ident, lot = query.get('id', [''])[0], query.get('lot', [''])[0]
        if url.hostname != 'www.cdr.gov.lb' or not url.path.endswith('/Procurment/ProcurementDetail.aspx'):
            raise ValueError("Unexpected CDR detail URL")
        source_url = detail_url(ident, lot)
        titles = cells[3].xpath('./a')
        if not titles:
            raise ValueError("Missing CDR title link")
        lot_title = ' '.join(text(span) for span in cells[3].xpath('./span')).strip()
        ppa = cells[2].xpath('./a')
        deadline = text(cells[9 if len(cells) == 10 else 7])
        result.append({
            'id': ident, 'lot': lot, 'key': f'{ident}-{lot}', 'source_url': source_url,
            'title': text(titles[0]), 'lot_title': lot_title,
            'announced_on': parse_date(text(cells[1])) or text(cells[1]),
            'ppa_id': text(ppa[0]) if ppa else '', 'ppa_announcement': text(cells[2]),
            'category': text(cells[4]), 'procurement_method': text(cells[5]),
            'funding': text(cells[6]), 'cost': text(cells[7]) if len(cells) == 10 else '',
            'language': text(cells[8]) if len(cells) == 10 else '',
            'submission_deadline': parse_date(deadline) or deadline,
            'status': text(cells[8]) if len(cells) == 9 else stage,
            'stages': [stage], 'cancelled': bool(row.xpath('.//*[contains(@class,"cancelled")]')),
            'raw_cells': [text(cell) for cell in cells],
        })
    return result


def attachment_url(value):
    """CDR pads filenames with spaces; discard padding and bare directory links."""
    url = urlsplit(urljoin(BASE, value.strip()))
    if url.scheme not in ('http', 'https'):
        return None
    path = unquote(url.path).rstrip()
    if path.endswith('/'):
        return None
    return urlunsplit((url.scheme, url.netloc, quote(path, safe='/'), url.query, url.fragment))


def parse_detail(row, raw):
    doc = document(raw)
    roots = doc.xpath('//*[contains(concat(" ",normalize-space(@class)," ")," ProcurementDetail ")]')
    if len(roots) != 1:
        raise ValueError('Missing CDR procurement detail')
    root = roots[0]
    headings = root.xpath('.//h1')
    if not headings:
        raise ValueError('Missing CDR detail heading')
    metadata = []
    for tr in root.xpath('.//table[@id="procurementTable"]//tr'):
        th, td = tr.xpath('./th'), tr.xpath('./td')
        if th and td:
            metadata.append({'label': text(th[0]), 'value': text(td[0])})
    project = next((f['value'] for f in metadata if f['label'] in ('رقم المشروع', 'CDR Procurement #')), '')
    if not re.match(r'^' + re.escape(row['id']) + r'(?!\d)', project):
        raise ValueError('CDR detail ID does not match listing')
    attachments = []
    for anchor in root.xpath('.//a[@href]'):
        href = anchor.get('href')
        if '/MediaFolder/' not in href and '/getattachment/' not in href:
            continue
        url = attachment_url(href)
        if url:
            names = anchor.getparent().xpath('./span')
            attachments.append({'url': url, 'text': text(names[0]) if names else text(anchor),
                                'lot': row['lot'], 'source_url': row['source_url']})
    events = []
    for td in root.xpath('.//table[contains(@class,"RoadMapTable")]//tr/td'):
        divs = td.xpath('./div')
        events.append({'label': text(divs[0]) if divs else '',
                       'date': text(divs[1]) if len(divs) > 1 else '', 'text': text(td)})
    lot_names = root.xpath('.//*[contains(@class,"procurementLot")]')
    return {'id': row['id'], 'lot': row['lot'], 'title': text(headings[0]),
            'lot_title': text(lot_names[0]) if lot_names else row['lot_title'],
            'source_url': row['source_url'], 'listing': row,
            'metadata': metadata, 'events': events, 'attachments': attachments,
            'full_text': text(root), 'scraped_at_utc': now()}


def combine_project(lots):
    """One project is the counting unit; retain every source row and lot detail."""
    lots = sorted(lots, key=lambda item: int(item['lot']))
    first = lots[0]
    if len({lot['id'] for lot in lots}) != 1:
        raise ValueError('Cannot combine different CDR projects')
    rows = [lot['listing'] for lot in lots]
    dates = [r['announced_on'] for r in rows if parse_date(r['announced_on'])]
    deadlines = [r['submission_deadline'] for r in rows if parse_date(r['submission_deadline'])]
    stages = sorted({s for r in rows for s in r['stages']})
    fields = []
    sections = []
    for lot in lots:
        for label, value in [('موضوع الشراء', lot['title']), ('عنوان المجموعة', lot['lot_title'])]:
            fields.append({'section_id': 'tenderInfo', 'context': 'Lot '+lot['lot'], 'label': label, 'values': [value]})
        for field in lot['metadata']:
            fields.append({'section_id': 'cdrMetadata', 'context': 'Lot '+lot['lot'],
                           'label': field['label'], 'values': [field['value']]})
        sections.append({'id': 'lot-'+lot['lot'], 'title': 'Lot '+lot['lot'], 'text': lot['full_text']})
    attachments = [a for lot in lots for a in lot['attachments']]
    record = {'id': first['id'], 'source': 'cdr', 'title': first['title'], 'source_url': first['source_url'],
              'header': {'الجهة الشارية': BUYER, 'أُعلنت في': max(dates, default=''),
                         'الحالة': ' · '.join(dict.fromkeys(r['status'] for r in rows))},
              'listing_values': {}, 'fields': fields, 'sections': sections,
              'attachments': attachments, 'lots': lots, 'stages': stages,
              'scraped_at_utc': max(lot['scraped_at_utc'] for lot in lots)}
    index = {'id': first['id'], 'title': first['title'], 'procuring_entity': BUYER,
             'procurement_code': first['id'], 'procurement_method': rows[0]['procurement_method'],
             'status': record['header']['الحالة'], 'announced_on': max(dates, default=''),
             'submission_deadline': max(deadlines, default=''), 'opening_at': '',
             'source_url': first['source_url'], 'attachment_links': len({a['url'] for a in attachments}),
             'detail_file': f"tenders/{first['id']}.json", 'lot_count': len(lots), 'stages': stages,
             'ppa_ids': sorted({r['ppa_id'] for r in rows if r['ppa_id']})}
    return record, index
