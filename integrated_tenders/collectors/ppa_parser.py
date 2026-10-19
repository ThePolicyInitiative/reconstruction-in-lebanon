"""Pure parsers for the PPA listing and all five detail tabs."""
import datetime as dt
import hashlib
import re
import urllib.parse
from lxml import html

BASE = 'https://www.ppa.gov.lb'
START = BASE + '/ar/tenders'

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def text(node):
    return clean(' '.join(node.itertext()))

def cls(name):
    return f'contains(concat(" ",normalize-space(@class)," ")," {name} ")'

def parse(raw):
    return html.fromstring(raw.decode('utf-8'), parser=html.HTMLParser(huge_tree=True))

def absolute(href, url):
    val = urllib.parse.urljoin(url, href)
    if val.startswith('http://www.ppa.gov.lb/'):
        val = 'https://' + val[len('http://'):]
    return val

def links(node, url):
    result = []
    seen = set()
    for a in node.xpath('.//a[@href]'):
        href = a.get('href', '').strip()
        if not href or href.startswith(('#', 'javascript:')):
            continue
        item = {'text': text(a), 'url': absolute(href, url)}
        key = (item['text'], item['url'])
        if key not in seen:
            result.append(item)
            seen.add(key)
    return result

def listing(raw, page):
    doc = parse(raw)
    tables = doc.xpath('//table[@id="information-table"]')
    if len(tables) != 1:
        raise ValueError(f'Page {page}: expected one listing table, got {len(tables)}')
    headers = [text(n) for n in tables[0].xpath('./thead/tr/th')]
    records = []
    for pos, row in enumerate(tables[0].xpath('./tbody/tr'), 1):
        cells = row.xpath('./td')
        anchors = row.xpath('.//a[contains(@href,"/tenders/details/")]')
        if not anchors:
            continue
        url = absolute(anchors[0].get('href'), START)
        tender_id = url.rstrip('/').rsplit('/', 1)[1]
        if not re.fullmatch(r'\d+',tender_id) or url != BASE+'/ar/tenders/details/'+tender_id:
            raise ValueError('Unexpected tender URL in source listing')
        records.append({
            'id': tender_id, 'source_url': url, 'listing_page': page,
            'listing_position': pos, 'listing_values': dict(zip(headers, map(text, cells))),
            'listing_row_class': row.get('class', ''), 'listing_links': links(row, START),
        })
    pages = [int(n) for n in re.findall(r'[?&]page=(\d+)', raw.decode('utf-8'))]
    totals = re.findall(r'Showing\s*(\d+)\s*to\s*(\d+)\s*of\s*(\d+)\s*results', text(doc))
    if not totals:
        raise ValueError(f'No pagination count found on page {page}')
    first, last, total = map(int, totals[0])
    if len(records) != last - first + 1:
        raise ValueError(f'Page {page}: listed {len(records)}, expected {last-first+1}')
    return {'page': page, 'url': START + f'?page={page}', 'first': first,
            'last': last, 'total': total, 'last_page': max(pages + [page]), 'records': records}

def table_data(table, url):
    rows = []
    for row in table.xpath('.//tr'):
        if row.xpath('ancestor::table[1]')[0] is not table:
            continue
        cells = row.xpath('./th|./td')
        rows.append([{'text': text(c), 'links': links(c, url),
                      **({'colspan': c.get('colspan')} if c.get('colspan') else {})}
                     for c in cells])
    return rows

def parse_detail(record, raw, fetched_at=None):
    ident, url = record['id'], record['source_url']
    doc = parse(raw)
    title = doc.xpath(f'//div[{cls("article-title")}]')
    # The source contains mismatched closing divs. DOM-based descendants can
    # swallow the footer/search form, or place later tabs outside myTabContent.
    # Slice the five observed tab boundaries in source order, then parse each
    # independently so none of the purchase lifecycle sections are dropped.
    source = raw.decode('utf-8')
    tab_matches = list(re.finditer(r'<div\b[^>]*\bid="(planInfo|tenderInfo|tenderdeadline|offerGuarentee|tenderFiles)"[^>]*>', source))
    if not title or len(tab_matches) != 5:
        raise ValueError(f'{ident}: missing tender title or detail tabs')
    tabs = []
    for index, match in enumerate(tab_matches):
        if index + 1 < len(tab_matches):
            end = tab_matches[index + 1].start()
        else:
            sidebar_start = re.search(r'<div\b[^>]*class="col-sm-4"', source[match.end():])
            if not sidebar_start:
                raise ValueError(f'{ident}: cannot locate end of tender content')
            end = match.end() + sidebar_start.start()
        fragment = source[match.end():end]
        tab = html.fromstring('<div>' + fragment + '</div>', parser=html.HTMLParser(huge_tree=True))
        tab.set('id', match.group(1))
        for noise in tab.xpath('.//script|.//style'):
            noise.drop_tree()
        tabs.append(tab)
    header = {}
    for label in doc.xpath(f'//span[{cls("article-date-title")}]'):
        siblings = label.getparent().xpath(f'./span[{cls("article-date-text")} or {cls("article-badge")}]')
        header[text(label)] = ' | '.join(text(s) for s in siblings)
    sections, fields, attachments, related = [], [], [], []
    for tab in tabs:
        sid = tab.get('id')
        labels = doc.xpath(f'//*[@id="{sid}-tab"]')
        label = text(labels[0]) if labels else sid
        tables = []
        for idx, table in enumerate(tab.xpath('.//table'), 1):
            context = []
            for ancestor in table.iterancestors():
                if ancestor is tab:
                    break
                if ancestor.tag == 'fieldset':
                    legends = ancestor.xpath('./legend')
                    context[:0] = [text(x) for x in legends]
                if 'accordion-item' in ancestor.get('class', '').split():
                    context[:0] = [text(x) for x in ancestor.xpath('./h2|./h3|./h4')]
            rows = table_data(table, url)
            tables.append({'table_number': idx, 'context': context, 'rows': rows})
            group = ''
            for row_idx, cells in enumerate(rows, 1):
                if len(cells) == 1:
                    group = cells[0]['text']
                if len(cells) >= 2:
                    fields.append({'section': label, 'section_id': sid,
                                   'context': ' > '.join(context), 'group': group,
                                   'table_number': idx, 'row_number': row_idx,
                                   'label': cells[0]['text'].rstrip(' :'),
                                   'values': [c['text'] for c in cells[1:]],
                                   'links': [l for c in cells for l in c['links']]})
        slinks = links(tab, url)
        for link in slinks:
            if '/storage/' in link['url'] or re.search(r'\.(pdf|docx?|xlsx?|zip|rar|jpe?g|png)(?:[?#]|$)', link['url'], re.I):
                attachments.append({'section': label, 'section_id': sid, **link})
            if re.search(r'/(?:lot|tenders)/details/', link['url']):
                related.append(link)
        media = [{'tag': n.tag, 'url': absolute(n.get('src') or n.get('data'), url)}
                 for n in tab.xpath('.//iframe[@src]|.//embed[@src]|.//object[@data]|.//img[@src]')
                 if not (n.get('src') or n.get('data')).startswith('data:')]
        sections.append({'id': sid, 'label': label, 'text': text(tab),
                         'tables': tables, 'links': slinks, 'media': media})
    sidebar = doc.xpath(f'//div[{cls("tender-left-side-cont")}]')
    options = doc.xpath('//select[@id="getLotData"]/option[@value]')
    for opt in options:
        if opt.get('value'):
            related.append({'text': text(opt), 'url': BASE + '/ar/lot/details/' + opt.get('value')})
    header_images = [absolute(n.get('src'),url) for n in doc.xpath(f'//div[{cls("article-header")}]//img[@src]')
                     if not n.get('src').startswith('data:')]
    result = {**record, 'parser_version': 2, 'title': text(title[0]), 'header': header, 'header_images': header_images,
              'sections': sections, 'fields': fields, 'attachments': attachments,
              'related_detail_links': related, 'sidebar_text': [text(n) for n in sidebar],
              'scraped_at_utc': fetched_at or now(),
              'parsed_at_utc': now(), 'source_html_sha256': hashlib.sha256(raw).hexdigest()}
    return result
