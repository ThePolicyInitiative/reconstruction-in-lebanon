"""Collect new reconstruction headlines from public feeds.

Only the headline, link, publisher and date are saved. Nothing collected here
is reviewed or coded: it is shown separately from the research on each tab and
never changes a figure, position or source record.
"""
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import html
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from . import stamp

INTERVAL = 20 * 60
RETRY_INTERVAL = 5 * 60
KEEP = 400
MAX_BYTES = 4 * 1024 * 1024
OUTPUT = 'data/auto_collected.json'
TOPICS = ('government', 'budget', 'losses', 'barriers', 'parties', 'countries', 'evidence')

# (publisher, url, Lebanese outlet?) – each outlet's own public feed.
FEEDS = [
    ('National News Agency', 'https://www.nna-leb.gov.lb/en/rss', True),
    ('الوكالة الوطنية للإعلام', 'https://www.nna-leb.gov.lb/ar/rss', True),
    ('Naharnet', 'https://www.naharnet.com/tags/lebanon/en/feed.atom', True),
    ('LBCI', 'https://www.lbcgroup.tv/Rss/latest-news/en', True),
    ('النهار', 'https://www.annahar.com/rss', True),
    ('المنار', 'https://www.almanar.com.lb/rss', True),
    ('ReliefWeb', 'https://reliefweb.int/updates/rss.xml?advanced-search=%28PC137%29', True),
    ('UN News', 'https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml', False),
]
WORLD_BANK = ('https://search.worldbank.org/api/v3/wds?format=json&countrycode_exact=LB&rows=40'
              '&srt=docdt&order=desc&fl=docdt,display_title,url,docty')

LEBANON = ('lebanon', 'lebanese', 'beirut', 'لبنان', 'بيروت', 'الجنوب', 'الضاحية')
ELSEWHERE = ('gaza', 'syria', 'ukraine', 'sudan', 'yemen', 'غزة', 'غزه', 'سوريا', 'سورية', 'أوكرانيا', 'السودان', 'اليمن', 'درعا', 'ليبيا', 'العراق', 'الأردن', 'iraq', 'libya', 'jordan')
RECOVERY = ('reconstruction', 'rebuild', 'rebuilt', 'rubble', 'debris', 'war damage', 'war-damaged', 'compensation for',
            'leap ', 'إعادة الإعمار', 'اعادة الاعمار', 'إعادة إعمار', 'اعادة اعمار', 'الإعمار', 'الاعمار', 'ترميم',
            'رفع الأنقاض', 'رفع الانقاض', 'الردم', 'الركام', 'مسح الأضرار', 'مسح الاضرار', 'التعويضات', 'تعويضات',
            'مجلس الجنوب', 'المتضررين', 'الوحدات السكنية المتضررة')
RULES = {
    'government': ('cabinet', 'council of ministers', 'prime minister', 'minister', 'ministry', 'government', 'cdr',
                   'council for development', 'مجلس الوزراء', 'رئيس الحكومة', 'رئيس مجلس الوزراء', 'وزير', 'وزيرة',
                   'وزارة', 'الحكومة', 'مجلس الإنماء والإعمار', 'مجلس الانماء والاعمار'),
    'budget': ('budget', 'موازنة', 'الموازنة'),
    'losses': ('economic loss', 'economic cost', 'gdp', 'economic monitor', 'damage and needs', 'billion',
               'الخسائر الاقتصادية', 'خسائر', 'الناتج المحلي', 'مليار', 'البنك الدولي'),
    'barriers': ('prevent', 'ban ', 'bans ', 'banned', 'halt', 'stopped', 'blocked', 'forbid', 'prohibit', 'permit',
                 'municipality', 'funding gap', 'منع', 'حظر', 'وقف العمل', 'وقف الأعمال', 'أوقف', 'توقيف', 'ممنوع', 'ترخيص', 'رخص', 'بلدية',
                 'نقص التمويل', 'غياب التمويل'),
    'parties': ('mp ', 'mps ', 'bloc', 'party', 'hezbollah', ' amal ', 'lebanese forces', 'kataeb', 'النائب', 'النواب',
                'كتلة', 'حزب', 'تيار', 'حركة أمل', 'القوات اللبنانية', 'الكتائب', 'التقدمي'),
    'countries': ('ambassador', 'embassy', 'donor', 'envoy', 'grant from', 'pledge', 'سفير', 'السفير', 'السفارة',
                  'المانحة', 'المانحين', 'الموفد', 'هبة', 'منحة', 'قرض'),
    'evidence': ('destroyed', 'destruction', 'demolish', 'demolition', 'satellite', 'damage assessment', 'razed',
                 'levelled', 'leveled', 'دمار', 'تدمير', 'هدم', 'نسف', 'تفجير منازل', 'تجريف', 'أقمار صناعية'),
}
# World Bank documents: only substantive analysis and reconstruction-project records.
WORLD_BANK_TOPICS = {
    'losses': ('economic monitor', 'damage and needs', 'rdna', 'economic update', 'macro poverty'),
    'government': ('leap', 'emergency assistance project', 'reconstruction'),
}


def normalize(text):
    text = re.sub(r'[ً-ْـ]', '', text or '')  # Arabic vowel marks and tatweel.
    return ' ' + re.sub(r'\s+', ' ', text).strip().casefold() + ' '


def clean(text):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', text or ''))).strip()


def contains(text, words):
    return [word for word in words if word in text]


def roster_names(root):
    """Names already on the site, used only to label which headline mentions whom."""
    root, names = Path(root), {'parties': set(), 'countries': set()}
    try:
        catalog = json.loads((root / 'locales/ar.json').read_text(encoding='utf-8'))
        for entity in json.loads((root / 'imported/parties/positions.json').read_text(encoding='utf-8'))['entities']:
            name = entity.get('name')
            names['parties'].update(name.values() if isinstance(name, dict) else [name])
        for country in json.loads((root / 'imported/countries/country-statements.json').read_text(encoding='utf-8'))['parties']:
            names['countries'].update([country['name'], catalog.get(country['name'], country['name'])])
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    # Lebanon and Israel are the subject of nearly every headline, not a third country's statement.
    names['countries'] -= {'Lebanon', 'Israel', 'لبنان', 'إسرائيل'}
    return {topic: sorted(n for n in values if isinstance(n, str) and len(n) >= 5) for topic, values in names.items()}


def classify(title, summary='', lebanese=True, names=None):
    """Return (topics, matched names) for a headline, or ([], []) when it is off-topic."""
    # The headline itself must be about recovery; article text only confirms the country.
    head, text = normalize(title), normalize(title + ' ' + summary)
    if not contains(head, RECOVERY):
        return [], []
    if contains(head, ELSEWHERE) and not contains(head, LEBANON):
        return [], []
    if not lebanese and not contains(text, LEBANON):
        return [], []
    topics, matched = [], []
    for topic in TOPICS:
        found = [name for name in (names or {}).get(topic, []) if normalize(name).strip() in head]
        if found or contains(head, RULES[topic]):
            topics.append(topic)
            matched += found
    return topics or ['government'], sorted(set(matched))


def parse_date(value):
    value = (value or '').strip()
    if not value:
        return None
    try:
        date = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            date = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)
    return date.astimezone(timezone.utc).isoformat(timespec='seconds')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def parse_feed(raw):
    """Read RSS or Atom entries as (title, link, summary, date)."""
    entries = []
    for node in ET.fromstring(raw).iter():
        if local(node.tag) not in ('item', 'entry'):
            continue
        fields = {}
        for child in node:
            name = local(child.tag)
            if name == 'link' and child.get('href') and child.get('rel', 'alternate') == 'alternate':
                fields.setdefault('link', child.get('href'))
            elif name in ('title', 'link', 'description', 'summary', 'pubDate', 'published', 'updated', 'date'):
                fields.setdefault(name, ''.join(child.itertext()))
        entries.append((clean(fields.get('title')), (fields.get('link') or '').strip(),
                        clean(fields.get('description') or fields.get('summary')),
                        parse_date(fields.get('pubDate') or fields.get('published') or fields.get('date') or fields.get('updated'))))
    return entries


def fetch(url):
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; feed reader)', 'Accept': '*/*'})
    with urlopen(request, timeout=25) as response:
        return response.read(MAX_BYTES)


def record(title, url, publisher, published, topics, matched, now):
    if not title or urlsplit(url).scheme not in ('http', 'https'):
        return None
    return {'id': hashlib.sha256(url.encode()).hexdigest()[:16], 'title': title[:300], 'url': url,
            'publisher': publisher, 'published': published, 'topics': topics, 'mentions': matched,
            'first_seen': stamp(now)}


def gather(root, now, fetcher=fetch):
    names, found, failures = roster_names(root), [], []
    for publisher, url, lebanese in FEEDS:
        try:
            for title, link, summary, published in parse_feed(fetcher(url)):
                topics, matched = classify(title, summary, lebanese, names)
                item = topics and record(title, link, publisher, published, topics, matched, now)
                if item:
                    found.append(item)
        except Exception:
            failures.append(publisher)
    try:
        for document in json.loads(fetcher(WORLD_BANK))['documents'].values():
            title = clean(document.get('display_title'))
            head = normalize(title)
            topics = [topic for topic, words in WORLD_BANK_TOPICS.items() if contains(head, words)]
            item = topics and record(title, (document.get('url') or '').replace('http://', 'https://'),
                                     'World Bank documents', parse_date(document.get('docdt')), topics, [], now)
            if item:
                found.append(item)
    except Exception:
        failures.append('World Bank documents')
    return found, failures


def load(root):
    try:
        return json.loads((Path(root) / OUTPUT).read_text(encoding='utf-8'))['items']
    except (OSError, ValueError, KeyError):
        return []


def run(root, state, now, fetcher=fetch):
    if now < state.get('next_check', 0):
        return
    found, failures = gather(root, now, fetcher)
    saved = load(root)
    known = {item['id'] for item in saved} | {normalize(item['title']) for item in saved}
    added = []
    for item in found:
        if item['id'] not in known and normalize(item['title']) not in known:
            known.update([item['id'], normalize(item['title'])])
            added.append(item)
    if added:
        items = sorted(saved + added, key=lambda item: item['published'] or item['first_seen'], reverse=True)[:KEEP]
        path = Path(root) / OUTPUT
        payload = {'note': 'Headlines collected automatically from public feeds. Not reviewed; '
                           'not part of the coded evidence on this website.', 'items': items}
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
        temporary.replace(path)
    all_failed = len(failures) == len(FEEDS) + 1
    state.update(checked_at=stamp(now), added=len(added), failures=failures,
                 next_check=now + (RETRY_INTERVAL if all_failed else INTERVAL))
    if added:
        state['last_added_at'] = stamp(now)
    state.pop('error', None)
