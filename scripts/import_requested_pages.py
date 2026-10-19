"""Copy the requested local pages into this app; never modify the originals."""
from pathlib import Path
import ast
import hashlib
from html.parser import HTMLParser
import json
import re
import shutil
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TENDERS = Path(r'C:\Users\Achra\Documents\ChatGPT\mona2asat')
PARTIES = Path(r'C:\Users\Achra\Documents\ChatGPT\what parties are saying about reconstruction\website')
EVIDENCE = Path(r'C:\Users\Achra\Documents\Codex\2026-10-07\fi\outputs\lebanon-gallery')

BRIDGE = '<script src="frame.js"></script>'

STYLE = '''<style>
:root{--ink:#000;--muted:#000;--blue:#000;--paper:#fff;--nav:#f1f5f2}
body{margin:0;background:#fff!important}
body,body *{color:#000!important}
header,th,button,select,input,nav a[aria-current="page"]{background:#f1f5f2!important}
header{border-bottom:1px solid #dce4e0}
main{padding-left:12px;padding-right:12px;padding-top:24px}
footer{display:none!important}
dialog{background:#fff!important}
</style>'''

GALLERY_STYLE = '''<style>
html,body{height:100%;overflow:hidden;scroll-behavior:auto}
.archive-scroll{height:100vh;height:100dvh;overflow-y:scroll;overflow-x:hidden;
  scrollbar-gutter:stable;scroll-padding-top:20px;scroll-behavior:auto;
  -webkit-overflow-scrolling:touch;overscroll-behavior-y:contain}
.archive-scroll:focus-visible{outline:2px solid #000;outline-offset:-2px}
.archive-scroll header{padding:14px 18px;gap:16px}
.archive-scroll main{padding-bottom:32px}
dialog[open]{display:flex;flex-direction:column;overflow:hidden}
.viewer-head,.viewer-caption{flex-shrink:0}
.viewer-body{flex:1;min-height:0;height:auto}
@media(max-width:560px){
  .archive-scroll header{padding:12px;gap:8px}
  .archive-scroll nav{gap:8px 16px}
  .archive-scroll .intro{gap:12px;margin-bottom:20px;padding-bottom:18px}
  .archive-scroll .inventory{display:flex;flex-wrap:wrap;gap:0 12px}
  .archive-scroll .inventory strong{width:100%}
}
@media(prefers-reduced-motion:reduce){.archive-scroll{scroll-behavior:auto}}
</style>'''


class LocalReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = set()

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('src', 'href') or not value:
                continue
            url = urlsplit(value)
            if not url.scheme and not url.netloc and url.path:
                self.paths.add(unquote(url.path))


def simplify_gallery(text):
    """Keep requested gallery removals when refreshing the imported page."""
    text = text.replace('<br>46 total · 92 satellite views<br>4 research & image reports<br>Compiled 7 October 2026', '')
    text = re.sub(r'<div class="gallery-controls">.*?</div>\s*', '', text, count=1, flags=re.DOTALL)
    text = re.sub(r'(<section id="additional-towns">)<div class="section-title">.*?</div></div>(?=<div class="gallery">)', r'\1', text, count=1, flags=re.DOTALL)
    text = text.replace("const annotationToggle=document.getElementById('show-annotated');", "let showAnnotated=false;")
    text = text.replace('annotationToggle.checked', 'showAnnotated')
    text = text.replace("annotationToggle.addEventListener('change',updateAnnotations);", '')
    text = text.replace('Images with embedded analysis markings remain available through “Show annotated originals.”', 'Images with embedded analysis markings remain available through “Show original comparisons” in the 2006 section.')
    return text


def embed_page(text, *, gallery=False):
    if gallery:
        text = simplify_gallery(text)
        # Streamlit components disable iframe viewport scrolling. Provide an
        # explicit scroll container; keep the modal outside it in the viewport.
        text = text.replace('<body>', '<body><div class="archive-scroll" tabindex="0" role="region" aria-label="Evidence of destruction gallery">', 1)
        text = text.replace('<dialog id="viewer"', '</div><dialog id="viewer"', 1)
        text = text.replace("document.body.style.overflow='hidden';", "document.querySelector('.archive-scroll').style.overflowY='hidden';")
        text = text.replace("document.body.style.overflow='';", "document.querySelector('.archive-scroll').style.overflowY='';")
    style = STYLE + (GALLERY_STYLE if gallery else '')
    return text.replace('</head>', style + '</head>').replace('</body>', BRIDGE + '</body>')


def copy_tenders():
    target = ROOT / 'integrated_tenders'
    if (target / 'live_data.py').exists():
        # Preserve the maintained live adapter and its offline fallback records.
        return {source: json.loads((target / 'data' / relative / 'dashboard.json').read_text(encoding='utf-8'))['total']
                for source, relative in [('ppa', Path('.')), ('cdr', Path('cdr'))]}
    target.mkdir(exist_ok=True)
    original = (TENDERS / 'streamlit_app.py').read_text(encoding='utf-8')
    tree = ast.parse(original)
    functions = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            functions.append('\n'.join(original.splitlines()[start - 1:node.end_lineno]))
    prefix = '''"""Mona2asat dashboard integrated from the user's local project."""
from __future__ import annotations
import html
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import altair as alt
import pandas as pd
import streamlit as st
from .tender_analytics import UNKNOWN, LEAP_SOURCE, district_counts, newest_first, normalize

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO = "https://github.com/ThePolicyInitiative/mona2asat"
CDR_START = "https://www.cdr.gov.lb/ar/Procurment.aspx?aliaspath=%2fProcurment"

'''
    text = prefix + '\n\n\n'.join(functions) + '\n'
    text = text.replace('def sidebar_filters(rows):', 'def tender_filters(rows):')
    text = text.replace('with st.sidebar:', 'with st.expander("Filter tenders", expanded=False):')
    text = text.replace('        st.markdown("### 🇱🇧 Mona2asat")\n', '')
    text = text.replace('        st.caption("Lebanon procurement observatory")\n', '')
    text = text.replace('        st.link_button("Email alert issues ↗", REPO + "/issues", width="stretch")\n', '')
    text = text.replace('sidebar filters', 'tender filters').replace('in the sidebar', 'in Filter tenders')
    text = text.replace('@st.fragment(run_every="60s")', '@st.fragment')
    text = text.replace('    filters = sidebar_filters(all_rows)\n', '')
    text = text.replace('    tabs = st.tabs(["PPA', '    filters = tender_filters(all_rows)\n    tabs = st.tabs(["PPA')
    text = text.replace('Reads GitHub-synced data every 60 seconds while open. The monitor is scheduled every 5 minutes.', 'Imported Mona2asat snapshot. This website does not run the tender monitor.')
    text = text.replace('The last saved monitor check is over 36 hours old. Open GitHub Actions to verify that monitoring is running.', 'This imported snapshot is over 36 hours old. Use the original source links for later updates.')
    text = text.replace('**Refresh:** GitHub Actions collects new tender IDs and builds the dashboard data. Streamlit Community Cloud updates its checkout from the repository. This page re-reads those files every 60 seconds while open. Scheduling and deployment delays can occur.', '**Snapshot:** this tab includes the saved data imported from Mona2asat. Refresh data reloads the bundled files; it does not fetch new notices. The source project has its own monitor, independent of this website.')
    text = text.replace('st.altair_chart(chart, width="stretch")', 'st.altair_chart(chart.configure_axis(labelColor="#000", titleColor="#000"), width="stretch")')
    (target / '__init__.py').write_text(text, encoding='utf-8')
    shutil.copy2(TENDERS / 'tender_analytics.py', target / 'tender_analytics.py')
    counts = {}
    for source, relative in [('ppa', Path('.')), ('cdr', Path('cdr'))]:
        src = TENDERS / 'data' / relative
        dest = target / 'data' / relative
        dest.mkdir(parents=True, exist_ok=True)
        for filename in ['dashboard.json', 'status.json']:
            shutil.copy2(src / filename, dest / filename)
        (dest / 'tenders').mkdir(exist_ok=True)
        for record in (src / 'tenders').glob('*.json'):
            shutil.copy2(record, dest / 'tenders' / record.name)
        counts[source] = len(json.loads((src / 'dashboard.json').read_text(encoding='utf-8'))['tenders'])
    return counts


def main():
    parties = ROOT / 'imported' / 'parties'
    evidence = ROOT / 'imported' / 'evidence'
    parties.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    party_source = PARTIES / 'Lebanon reconstruction.html'
    party_text = party_source.read_text(encoding='utf-8')
    (parties / 'index.html').write_text(embed_page(party_text), encoding='utf-8')
    shutil.copy2(PARTIES.parent / 'reconstruction-statements.json', parties / 'reconstruction-statements.json')
    gallery_source = EVIDENCE / 'index.html'
    gallery_text = gallery_source.read_text(encoding='utf-8')
    refs = LocalReferences()
    refs.feed(gallery_text)
    for relative in sorted(refs.paths):
        source = (EVIDENCE / relative).resolve()
        if not source.is_relative_to(EVIDENCE.resolve()) or not source.is_file():
            raise ValueError(f'Invalid or missing gallery asset: {relative}')
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for filename in ['catalog.json', 'additional-towns.json', 'READ-ME.txt']:
        shutil.copy2(EVIDENCE / filename, evidence / filename)
    (evidence / 'index.html').write_text(embed_page(gallery_text, gallery=True), encoding='utf-8')
    if __package__:
        from .install_localization import install
    else:
        from install_localization import install
    install()
    counts = copy_tenders()
    manifest = {
        'imported_on': '2026-10-09',
        'tenders': {'source': str(TENDERS), 'counts': counts, 'mode': 'bundled snapshot'},
        'parties': {'source': str(party_source), 'source_sha256': hashlib.sha256(party_source.read_bytes()).hexdigest()},
        'evidence': {'source': str(gallery_source), 'source_sha256': hashlib.sha256(gallery_source.read_bytes()).hexdigest(), 'asset_count': len(refs.paths)},
    }
    (ROOT / 'imported' / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps({'tenders': counts, 'gallery_assets': len(refs.paths), 'pages': ['Tenders', 'What parties are saying', 'Evidence of destruction']}))


if __name__ == '__main__':
    main()
