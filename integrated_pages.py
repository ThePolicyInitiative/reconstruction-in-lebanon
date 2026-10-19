"""Local, self-contained pages imported from the user's source projects."""
from pathlib import Path

import streamlit.components.v1 as components
from i18n import language

ROOT = Path(__file__).resolve().parent
_parties = components.declare_component(
    "party_statements", path=str(ROOT / "imported" / "parties")
)
_countries = components.declare_component(
    "country_statements", path=str(ROOT / "imported" / "countries")
)
_evidence = components.declare_component(
    "destruction_evidence", path=str(ROOT / "imported" / "evidence")
)


def _page_key(name):
    """Reload an open component when its saved content or translations change."""
    directory = ROOT / 'imported' / name
    filenames = ['index.html', 'ar.json']
    if name == 'parties':
        filenames += ['positions.json', 'graphs.js', 'graph-model.js', 'graphs.css']
    revision = max((directory / filename).stat().st_mtime_ns for filename in filenames)
    return f'{name}_{language()}_{revision}'


def show_parties():
    _parties(language=language(), key=_page_key('parties'), default=None)


def show_countries():
    _countries(language=language(), key=_page_key('countries'), default=None)


def show_evidence():
    _evidence(language=language(), key=_page_key('evidence'), default=None)
