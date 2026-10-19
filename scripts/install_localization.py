"""Install the shared translation assets in the local Streamlit components."""
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = '<script src="localize.js"></script>'
STYLE = '<link rel="stylesheet" href="arabic.css">'
BRIDGE = '<script src="frame.js"></script>'


def localized_page(text, *, parties=False):
    # The political graphs render both languages themselves, including SVG axes.
    if 'name="native-bilingual" content="political-graphs"' in text:
        return text
    # Upgrade every imported page, including older copies of the resize bridge.
    text = re.sub(r'<script>(?:(?!</script>).)*streamlit:componentReady(?:(?!</script>).)*</script>', BRIDGE, text, flags=re.DOTALL)
    if STYLE not in text:
        text = text.replace('</head>', STYLE + '</head>')
    if SCRIPT not in text:
        # Register the language listener before Streamlit receives componentReady.
        position = text.rfind(BRIDGE)
        text = text[:position] + SCRIPT + text[position:]
    if parties and 'class="party-scroll"' not in text:
        # Preserve source attributes such as data-view on the body element.
        text = re.sub(r'(?:</div>)+(?=' + re.escape(SCRIPT) + ')', '', text)
        text = re.sub(r'<body([^>]*)>', r'<body\1 class="party-page"><div class="party-scroll" tabindex="0" role="region" aria-label="Statement archive">', text, count=1)
        text = text.replace(SCRIPT, '</div>' + SCRIPT, 1)
    return text


def install():
    for name in ('parties', 'countries', 'evidence'):
        directory = ROOT/'imported'/name
        path = directory/'index.html'
        path.write_text(localized_page(path.read_text(encoding='utf-8'), parties=name in ('parties', 'countries')), encoding='utf-8')
        shutil.copyfile(ROOT/'assets/component-i18n.js', directory/'localize.js')
        shutil.copyfile(ROOT/'assets/component-arabic.css', directory/'arabic.css')
        shutil.copyfile(ROOT/'assets/component-frame.js', directory/'frame.js')
        shutil.copyfile(ROOT/'locales/ar.json', directory/'ar.json')


if __name__ == '__main__':
    install()
