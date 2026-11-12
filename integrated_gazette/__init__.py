"""Official Gazette, presented alongside Tenders using Memo automation data."""
from __future__ import annotations
import html
import json
import pandas as pd
from i18n import st, translate
from datetime import datetime
from zoneinfo import ZoneInfo
from .data_feed import YEARS, SITE_URL, FIELDS
from .live_data import CloudGazetteFeed
from .analytics import (ALL, RELATED, CATEGORIES, NO_SUBJECT, tag_records, filter_records, csv_rows,
                        classification_options, field_matches)
from integrated_tenders.categories import ALL_PROGRAMMES, NO_LEAP, VERSION as CATEGORY_VERSION
from .labels import STATUS_LABELS, TYPE_LABELS
from .charts import subject_charts, timeline_charts, classification_charts

FILTER_KEYS = ('gazette_search', 'gazette_years', 'gazette_subject', 'gazette_types', 'gazette_majors', 'gazette_statuses', 'gazette_detail',
               'gazette_subs', 'gazette_natures', 'gazette_functions', 'gazette_programme',
               'gazette_comparison_window', 'gazette_policy_chart_scope')


def preserve_filters():
    for key in FILTER_KEYS:
        for candidate in (key, key + '__ar'):
            if candidate in st.session_state:
                st.session_state[candidate] = st.session_state[candidate]


@st.cache_data(show_spinner=False, max_entries=3)
def saved_data(snapshot, category_version=CATEGORY_VERSION):
    return {**snapshot, 'records': tag_records(snapshot['records'])}


@st.cache_resource
def get_feed():
    return CloudGazetteFeed()


def status_label(value):
    return STATUS_LABELS.get(value, value)


def detail(row):
    st.subheader('Gazette record details')
    st.markdown(f'<div class="gazette-title">{html.escape(row["title"])}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric('Document type', translate(TYPE_LABELS[row['type']]))
    c2.metric('Document number', row['number'] or '—')
    c3.metric('Published', row['date'])
    st.link_button('Open original Gazette record ↗', row['url'])
    st.write('Assessment status: ' + status_label(row['status']))
    st.caption(translate('Programme') + ': ' + (' · '.join(row['programmes']) or translate(NO_LEAP)))
    fields = [('Nature', row['nature']), ('Administrative function', row['admin_function']),
              ('Main category', row['major']), ('Subcategory', row['sub'])]
    st.dataframe(pd.DataFrame([{'Field': name, 'Saved classification': value or 'Not specified'} for name, value in fields]),
                 hide_index=True, width='stretch')
    with st.expander('Subject matches and source notes'):
        if row['subject_evidence']:
            st.dataframe(pd.DataFrame([{'Subject': e['Category'], 'Matched wording': e['Matched wording']} for e in row['subject_evidence']]), hide_index=True, width='stretch')
        else:
            st.caption('No explicit recovery subject or LEAP reference was found in the saved title.')
        st.download_button('Download original Gazette record · JSON',
                           json.dumps({k: row[k] for k in FIELDS}, ensure_ascii=False, indent=2),
                           file_name=f'gazette_{row["id"]}.json', mime='application/json', key='gazette_record_json')


@st.fragment(run_every='60s')
def dashboard():
    st.title('Official Gazette')
    try:
        connection = get_feed().refresh()
        snapshot = saved_data(connection['snapshot'])
    except (ValueError, OSError):
        st.error('The Gazette export could not be loaded. Open Memo automation to view the source records.')
        st.link_button('Open live Memo automation dashboard ↗', SITE_URL)
        return
    rows = snapshot['records']
    with st.expander('Filter Gazette records', expanded=True):
        search = st.text_input('Search Gazette records', placeholder='Arabic title, document number, subject or ID', key='gazette_search')
        a, b, c = st.columns(3)
        years = a.multiselect('Publication year', YEARS, key='gazette_years', placeholder='2024, 2025 and 2026')
        subject = b.selectbox('Website subject', [ALL, RELATED, NO_SUBJECT, *CATEGORIES], key='gazette_subject')
        types = c.multiselect('Document type', list(TYPE_LABELS), format_func=lambda v: TYPE_LABELS[v], key='gazette_types')
        a, b = st.columns(2)
        majors = a.multiselect('Memo main category', classification_options(rows, 'major'), key='gazette_majors')
        sub_options = classification_options([r for r in rows if field_matches(r, 'major', majors)], 'sub')
        # A new main category can invalidate a previously selected subcategory.
        for key in ('gazette_subs', 'gazette_subs__ar'):
            if key in st.session_state:
                st.session_state[key] = [v for v in st.session_state[key] if v in sub_options]
        saved = st.session_state.get('_localized_choices', {}).get('gazette_subs')
        if saved:
            saved['value'] = [v for v in saved['value'] if v in sub_options]
        subs = b.multiselect('Memo subcategory', sub_options, key='gazette_subs')
        a, b = st.columns(2)
        natures = a.multiselect('Nature', classification_options(rows, 'nature'), key='gazette_natures')
        functions = b.multiselect('Administrative function', classification_options(rows, 'admin_function'), key='gazette_functions')
        a, b = st.columns(2)
        statuses = a.multiselect('Assessment status', sorted({r['status'] for r in rows}), format_func=status_label, key='gazette_statuses')
        programme = b.selectbox('Programme', [ALL_PROGRAMMES, 'LEAP', NO_LEAP], key='gazette_programme')
        if st.button('Refresh Gazette data', key='gazette_reload'):
            get_feed().refresh(force=True)
            saved_data.clear()
            st.rerun()
    filtered = filter_records(rows, search, years, subject, types, majors, statuses,
                              subs, natures, functions, programme)
    a, b, c, d = st.columns(4)
    a.metric('Gazette records', f'{len(rows):,}')
    b.metric('Matching records', f'{len(filtered):,}')
    c.metric('Records matching a subject', f'{sum(bool(r["subjects"]) for r in filtered):,}')
    d.metric('Latest saved publication', snapshot['latest_publication'] or '—')
    latest, subjects, timeline, classifications = st.tabs(['Latest Gazette records', 'By subject', 'By month', 'Classifications'])
    with latest:
        if not filtered:
            st.info('No Gazette records match these filters. Clear the search or choose another subject or year.')
        else:
            st.subheader('Latest laws, decrees and decisions')
            for column, row in zip(st.columns(3), filtered[:3]):
                with column, st.container(border=True):
                    st.caption(f'{row["date"]} · {translate(TYPE_LABELS[row["type"]])} {row["number"]}')
                    st.markdown(f'<div class="gazette-title">{html.escape(row["title"])}</div>', unsafe_allow_html=True)
                    if row['subjects']:
                        st.markdown(' '.join(f'<span class="gazette-tag">{html.escape(translate(c))}</span>' for c in row['subjects']), unsafe_allow_html=True)
                    if row['programmes']:
                        st.caption(translate('Programme') + ': ' + ' · '.join(row['programmes']))
                    st.link_button('Open Gazette record ↗', row['url'])
            frame = pd.DataFrame(csv_rows(filtered))
            st.dataframe(frame, hide_index=True, width='stretch', height=640, column_order=['Published', 'Related to recovery', 'Website subjects', 'Document type', 'Document number', 'Gazette title', 'Programme', 'Main category', 'Subcategory', 'Source'],
                         column_config={'Gazette title': st.column_config.TextColumn(width='large'),
                                        'Source': st.column_config.LinkColumn(display_text='Open ↗')}, key='gazette_records_table')
            safe = frame.map(lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(('=', '+', '-', '@')) else value)
            st.download_button('Download Gazette records · CSV', safe.to_csv(index=False).encode('utf-8-sig'),
                               file_name='gazette_2024_2026_filtered.csv', mime='text/csv', key='gazette_csv')
            lookup = {r['id']: r for r in filtered}
            selected = st.selectbox('Explore a Gazette record', list(lookup), format_func=lambda rid: f'{lookup[rid]["date"]} · {lookup[rid]["type"]} {lookup[rid]["number"]} · {lookup[rid]["title"]}', key='gazette_detail')
            detail(lookup[selected])
    with subjects:
        st.caption(f"{sum('LEAP' in r['programmes'] for r in filtered):,} · " + translate('Explicit LEAP references'))
        st.caption(f"{sum(not r['subjects'] for r in filtered):,} · " + translate(NO_SUBJECT))
        subject_charts(filtered, years)
    with timeline:
        timeline_charts(filtered, rows, years)
    with classifications:
        classification_charts(filtered)
