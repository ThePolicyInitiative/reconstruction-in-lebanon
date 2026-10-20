"""Reconstruction in Lebanon — government, budget, tenders and evidence."""
import json
from pathlib import Path

from i18n import st, initialize_language, language, toggle_language, translate, TAB_LABELS

from dashboard_data import load_data
from overview import government_overview
from source_notes import sources_explained
from visuals import icon
from integrated_tenders import dashboard as tenders_dashboard, preserve_filters, get_monitor
from integrated_gazette import dashboard as gazette_dashboard, preserve_filters as preserve_gazette_filters
from integrated_pages import show_parties, show_countries, show_evidence
from budget import show_budget
from economic_losses import show_economic_losses
from reconstruction_barriers import show_reconstruction_barriers

ROOT = Path(__file__).parent
DATA = load_data()

initialize_language()
st.set_page_config(page_title=translate('Reconstruction in Lebanon'), page_icon='🇱🇧', layout='wide')
# Start once per server process; collection continues independently of the selected tab.
get_monitor()
st.html(ROOT / 'assets' / 'overview.css')
st.html(ROOT / 'assets' / 'tabs.css')
if language() == 'ar':
    st.html(ROOT / 'assets' / 'arabic.css')
with st.container(key='site-header'):
    brand_column, language_column = st.columns([8, 1.2], vertical_alignment='center')
    with brand_column:
        st.html(f'''<header class="brand"><div class="brand-cedar">{icon('cedar',27,'#ba3037')}</div><div><strong>RECONSTRUCTION</strong><span>IN LEBANON</span></div></header>''')
    with language_column:
        st.button('العربية' if language() == 'en' else 'English', key='language_toggle', on_click=toggle_language, width='stretch')

preserve_filters()
preserve_gazette_filters()
government_tab, budget_tab, losses_tab, barriers_tab, tenders_tab, gazette_tab, parties_tab, countries_tab, evidence_tab = st.tabs(
    TAB_LABELS, key='reconstruction_section', on_change='rerun')


def show_government():
    st.html(government_overview(DATA))
    with st.expander('Sources & notes — explained'):
        st.html(sources_explained(DATA))
        st.download_button('Download all research details (JSON file)', json.dumps(DATA, ensure_ascii=False, indent=2).encode('utf-8'), 'lebanon-government-response-sources.json', 'application/json', use_container_width=True)

if government_tab.open:
    with government_tab:
        show_government()

if budget_tab.open:
    with budget_tab:
        show_budget()

if losses_tab.open:
    with losses_tab:
        show_economic_losses()

if barriers_tab.open:
    with barriers_tab:
        show_reconstruction_barriers()

if tenders_tab.open:
    with tenders_tab:
        with st.container(key='tenders-page'):
            tenders_dashboard()

if gazette_tab.open:
    with gazette_tab:
        with st.container(key='gazette-page'):
            gazette_dashboard()

if parties_tab.open:
    with parties_tab:
        show_parties()

if countries_tab.open:
    with countries_tab:
        show_countries()

if evidence_tab.open:
    with evidence_tab:
        show_evidence()
