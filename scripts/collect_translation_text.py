"""Inventory visible copy without changing data, IDs, links, or source images."""
import ast
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def clean(text):
    return re.sub(r'\s+', ' ', text).strip()


class Texts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip = 0
        self.items = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'svg'):
            self.skip += 1
        if not self.skip:
            self.items += [value for key, value in attrs if key in ('title', 'aria-label', 'placeholder', 'alt') and value]
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'svg') and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.items.append(data)


def visible(markup):
    parser = Texts()
    parser.feed(markup)
    return parser.items


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in ('id', 'actor', 'partyId', 'url', 'affiliationUrl', 'corroboration', 'language', 'date', 'published', 'checked', 'periodStart'):
                yield from strings(item)


def keep(text):
    return bool(re.search(r'[A-Za-z]{3}', text)) and not re.match(r'^(https?://|[\d.]+\|)', text)


def main():
    from overview import government_overview
    from dashboard_data import load_data
    from budget import load_budget, headline_html, breakdown_html, line_table, PERIODS
    from streamlit.testing.v1 import AppTest
    core = visible(government_overview(load_data()))
    budget = load_budget()
    core += visible(headline_html(budget)) + visible(line_table(budget)) + visible(line_table(budget, components=True))
    for period in PERIODS:
        core += visible(breakdown_html(budget, period))
    app = AppTest.from_file(str(ROOT/'streamlit_app.py')).run()
    for element in app.get('html'):
        core += visible(element.proto.body)
    # Keep source titles and UI copy that is only shown in expanded panels.
    for filename in ['budget.py', 'integrated_tenders/__init__.py', 'integrated_tenders/live_data.py']:
        tree = ast.parse((ROOT/filename).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value
                if '\n' in text:
                    core.extend(text.splitlines())
                elif '<' not in text and (' ' in text or text[:1].isupper()):
                    core.append(text)
    groups = {'core':core}
    groups['parties'] = visible((ROOT/'imported/parties/index.html').read_text(encoding='utf-8'))
    groups['parties'] += list(strings(json.loads((ROOT/'imported/parties/reconstruction-statements.json').read_text(encoding='utf-8'))))
    groups['evidence'] = visible((ROOT/'imported/evidence/index.html').read_text(encoding='utf-8'))
    seen = set()
    for group, items in groups.items():
        unique = []
        for text in items:
            text = clean(text)
            if keep(text) and text not in seen:
                unique.append(text)
                seen.add(text)
        path = ROOT/'.artifacts'/f'translation-{group}.json'
        path.write_text(json.dumps(unique, ensure_ascii=False, indent=2), encoding='utf-8')
        print(group, len(unique), sum(len(item) for item in unique))


if __name__ == '__main__':
    main()
