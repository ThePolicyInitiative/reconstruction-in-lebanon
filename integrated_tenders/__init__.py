"""Mona2asat dashboard integrated from the user's local project."""
from __future__ import annotations
import html
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import altair as alt
import pandas as pd
from i18n import st, translate
from .tender_analytics import UNKNOWN, LEAP_SOURCE, district_counts, newest_first, normalize
from .live_data import FeedError
from .automatic import AutomaticTenderFeed, get_process_monitor
from .categories import CATEGORIES, DEFINITIONS, VERSION as CATEGORY_VERSION, classify_recovery as classify
from .categories import (SUBJECTS, ANY_SUBJECT, NO_SUBJECT, ALL_PROGRAMMES, NO_LEAP,
                         matches_subject, matches_programme)

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
REPO = "https://github.com/ThePolicyInitiative/mona2asat"
CDR_START = "https://www.cdr.gov.lb/ar/Procurment.aspx?aliaspath=%2fProcurment"
ANNOUNCEMENT_YEARS = ('2026', '2025', '2024')


def covered_tenders(rows):
    """The website covers announcements dated in 2024, 2025 or 2026."""
    return [row for row in rows if (row.get('announcement_date') or '')[:4] in ANNOUNCEMENT_YEARS]

@st.cache_resource
def get_monitor():
    return get_process_monitor()


@st.cache_resource
def get_feed():
    return AutomaticTenderFeed(monitor=get_monitor())


def preserve_filters():
    """Retain tender choices while another top-level tab is being displayed."""
    keys = ['search', 'districts', 'declared_only', 'years_2024_2026', 'period', 'tender_category',
            'tender_programme', 'buyers', 'cdr_stage']
    keys += [source + suffix for source in ('ppa', 'cdr')
             for suffix in ('_all_tenders_leap', '_topic_tenders_leap', '_detail')]
    for key in keys:
        for candidate in (key, key + '__ar'):
            if candidate in st.session_state:
                st.session_state[candidate] = st.session_state[candidate]

@st.cache_data(show_spinner=False)
def load_json(path, modified_ns):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_data(path):
    return load_json(str(path), path.stat().st_mtime_ns)


@st.cache_data(show_spinner=False)
def classified_tenders(rows, category_version):
    return [classify(row) for row in covered_tenders(rows)]


def ratio_metric(column, label, count, total, help=None):
    column.metric(label, f"{count / total:.2%}" if total else "—", help=help)
    column.caption(f"{count:,} / {total:,} filtered tenders" if total else "No tenders match the current filters.")


def export_frame(rows):
    return pd.DataFrame([{
        "ID": r["id"], "Announced": r.get("announcement_date") or r.get("announced_on", ""),
        "Tender": r["title"], "Buyer": r["procuring_entity"],
        "Districts": " · ".join(r["districts"]), "District basis": r["district_basis"],
        "Deadline": r.get("submission_deadline", ""), "Source status": r.get("status", ""),
        "Categories": " · ".join(r['programmes'] + r['recovery_subjects']) or "Not classified",
        "Related to recovery": "Yes" if r['recovery_subjects'] else "No",
        "Recovery subjects": " · ".join(r['recovery_subjects']) or NO_SUBJECT,
        "Procurement subjects": " · ".join(r['procurement_subjects']),
        "Programme": " · ".join(r['programmes']) or NO_LEAP,
        **{category: category in r['programmes'] + r['recovery_subjects'] for category in CATEGORIES},
        "Source": r["source_url"],
    } for r in rows])


def draw_table(rows, key, source):
    frame = export_frame(rows)
    if frame.empty:
        st.info("No tenders match these filters. Change the category, widen the date range, or clear the search.")
        return rows
    st.dataframe(frame, hide_index=True, width="stretch", height=640,
                 column_order=["Announced", "Related to recovery", "Programme", "Tender", "Buyer", "Districts", "Deadline", "Source"],
                 column_config={"Tender": st.column_config.TextColumn(width="large"),
                                "Buyer": st.column_config.TextColumn(width="medium"),
                                "Categories": st.column_config.TextColumn(width="medium"),
                                "Source": st.column_config.LinkColumn(f"{source.upper()} record", display_text="Open ↗")}, key=key)
    # Neutralize spreadsheet formula prefixes in source text, while preserving Unicode.
    safe = frame.map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@")) else v)
    st.download_button("Download these tenders · CSV", safe.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"{source}_tenders_filtered.csv", mime="text/csv", key=key + "_csv")
    return rows


def show_detail(row, source, revision):
    st.divider()
    st.subheader("Tender details")
    st.markdown(f'<div class="tender-title">{html.escape(row["title"])}</div>', unsafe_allow_html=True)
    st.caption(f'ID {row["id"]} · {row["procuring_entity"]} · Announced {row.get("announcement_date") or "not specified"}')
    subject_label = ' · '.join(translate(c) for c in row['recovery_subjects']) or translate(NO_SUBJECT)
    st.caption(translate("Recovery subjects") + ': ' + subject_label)
    st.caption(translate("Programme") + ': ' + (' · '.join(row['programmes']) or translate(NO_LEAP)))
    st.link_button(f"Open original {source.upper()} record ↗", row["source_url"])
    if row["summary"]:
        st.markdown(f'<div class="arabic-copy">{html.escape(row["summary"])}</div>', unsafe_allow_html=True)
    with st.expander("District and category evidence"):
        st.write("District basis: " + row["district_basis"])
        if row["district_evidence"]:
            st.dataframe(pd.DataFrame(row["district_evidence"]), hide_index=True, width="stretch")
        else:
            st.caption("The saved record does not identify an execution/delivery district or explicitly name a district in its project text.")
        evidence = row['recovery_evidence'] or [e for e in row['category_evidence'] if e['Category'] == 'LEAP']
        if evidence:
            st.dataframe(pd.DataFrame(evidence), hide_index=True, width="stretch")
        else:
            st.caption("No explicit recovery subject or LEAP reference was found in the saved notice text.")
    try:
        record = get_feed().detail(source, row['id'], revision)
    except (FeedError, OSError, ValueError):
        record = None
        st.info('The complete record could not be loaded. You can still open the original source above.')
    if record is not None:
        if source == "cdr":
            with st.expander(f'All lots and source fields · {len(record["lots"])} lots'):
                for lot in record["lots"]:
                    st.markdown(f'**Lot {lot["lot"]}**')
                    if lot["lot_title"]:
                        st.text(lot["lot_title"])
                    st.link_button(f'Open CDR lot {lot["lot"]} ↗', lot["source_url"])
                    st.dataframe(pd.DataFrame(lot["metadata"]), hide_index=True, width="stretch")
                    if lot["events"]:
                        st.dataframe(pd.DataFrame(lot["events"]), hide_index=True, width="stretch")
        with st.expander(f'Documents and complete record · {row["attachment_links"]} attachment entries'):
            links = {}
            for attachment in record.get("attachments", []):
                url = attachment.get("url", attachment.get("href", ""))
                if url.startswith(("https://", "http://")):
                    links.setdefault(url, attachment.get("text") or attachment.get("label") or url.rsplit("/", 1)[-1])
            if links:
                st.dataframe(pd.DataFrame([{"Document": text, "Download": url} for url, text in links.items()]),
                             hide_index=True, width="stretch", column_config={
                                 "Download": st.column_config.LinkColumn(display_text="Open document ↗")})
            else:
                st.caption("No document links in the saved record.")
            st.download_button("Download complete tender · JSON", json.dumps(record, ensure_ascii=False, indent=2),
                               file_name=f'{source}_tender_{row["id"]}.json', mime="application/json", key=source + "_detail_json")
            for section in record.get("sections", []):
                st.text(section.get("title", section.get("label", section.get("id", ""))))
                st.text(section.get("text", ""))


def tender_filters(rows):
    with st.expander("Filter tenders", expanded=True):
        # Keyed so the search box keeps a full row when the other filters pair up on phones.
        with st.container(key='tender-filter-top'):
            search_column, year_column, period_column = st.columns([2, 1, 1])
        with search_column:
            search = st.text_input("Search tenders", placeholder="Arabic, English, buyer or ID", key="search")
        with year_column:
            years = st.multiselect("Announcement year / السنة", ANNOUNCEMENT_YEARS, key="years_2024_2026", placeholder="2024, 2025 and 2026")
        with period_column:
            period = st.selectbox("Announcement period", ["All dates", "Last 7 days", "Last 30 days", "Last 90 days", "This year"], key="period")
        district_column, buyer_column, topic_column, programme_column = st.columns([1.5, 1.5, 1, 1])
        district_options = sorted({d for r in rows for d in r["districts"] if d != UNKNOWN})
        with district_column:
            districts = st.multiselect("District / القضاء", district_options + [UNKNOWN], key="districts")
            declared_only = st.checkbox("Use declared locations only", key="declared_only")
        with buyer_column:
            buyers = st.multiselect("Procuring entity / الجهة الشارية", sorted({r["procuring_entity"] for r in rows if r["procuring_entity"]}), key="buyers")
        with topic_column:
            topic = st.selectbox("Category", ["All tenders", ANY_SUBJECT, NO_SUBJECT, *SUBJECTS], key="tender_category")
        with programme_column:
            programme = st.selectbox("Programme", [ALL_PROGRAMMES, 'LEAP', NO_LEAP], key="tender_programme")
        if st.button("Refresh data"):
            get_feed().refresh(force=True)
            load_json.clear()
            st.rerun()
    return search, districts, declared_only, years, period, topic, buyers, programme


def source_dashboard(source, payload, status, filters, revision=None):
    rows = classified_tenders(payload["tenders"], CATEGORY_VERSION)
    search, districts, declared_only, years, period, topic, buyers, programme = filters
    today = datetime.now(ZoneInfo("Asia/Beirut")).date()
    if source == "cdr":
        st.markdown('<div class="eyebrow">COUNCIL FOR DEVELOPMENT AND RECONSTRUCTION / مجلس الإنماء والإعمار</div>', unsafe_allow_html=True)
        stage = st.selectbox("CDR section", ["All sections", "Ongoing", "Archive", "Others"], key="cdr_stage")
        st.link_button("Open CDR procurement list ↗", CDR_START)
    else:
        st.markdown('<div class="eyebrow">PUBLIC PROCUREMENT AUTHORITY / هيئة الشراء العام</div>', unsafe_allow_html=True)

    filtered = rows
    if source == "cdr" and stage != "All sections":
        filtered = [r for r in filtered if stage in r.get("stages", [])]
    if search.strip():
        query = normalize(search)
        filtered = [r for r in filtered if query in normalize(" ".join([r["id"], r["title"], r["procuring_entity"], r["summary"]]))]
    if districts:
        filtered = [r for r in filtered if set(r["districts"]) & set(districts)]
    if declared_only:
        filtered = [r for r in filtered if r["district_basis"] == "Declared"]
    if years:
        filtered = [r for r in filtered if r["announcement_date"][:4] in years]
    if period != "All dates":
        start = today.replace(month=1, day=1) if period == "This year" else today - timedelta(days=int(period.split()[1])-1)
        filtered = [r for r in filtered if r.get("announcement_date") and start.isoformat() <= r["announcement_date"] <= today.isoformat()]
    if topic != 'All tenders':
        filtered = [r for r in filtered if matches_subject(r['recovery_subjects'], topic)]
    filtered = [r for r in filtered if matches_programme(r['categories'], programme)]
    if buyers:
        filtered = [r for r in filtered if r["procuring_entity"] in buyers]
    filtered = newest_first(filtered)

    total, matching, related, mapped = st.columns(4)
    total.metric("Total tenders", f"{len(rows):,}")
    matching.metric("Filtered tenders", f"{len(filtered):,}")
    ratio_metric(related, "Recovery subject matches", sum(bool(r['recovery_subjects']) for r in filtered), len(filtered))
    mapped.metric("Districts represented", len({d for r in filtered for d in r["districts"] if d != UNKNOWN}))

    latest_tab, district_tab, topic_tab = st.tabs(["Newest tenders", "By district", "By category"])
    with latest_tab:
        st.subheader("Latest announcements")
        for column, row in zip(st.columns(3), filtered[:3]):
            with column, st.container(border=True):
                st.caption(f'{row.get("announcement_date") or "Date not specified"}  ·  #{row["id"]}')
                if row['recovery_subjects'] or row['programmes']:
                    st.markdown(' '.join(f'<span class="tag">{html.escape(category)}</span>' for category in row['programmes'] + row['recovery_subjects']), unsafe_allow_html=True)
                st.markdown(f'<div class="tender-title">{html.escape(row["title"])}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="tender-buyer">{html.escape(row["procuring_entity"])}</div>', unsafe_allow_html=True)
                st.link_button(f"View on {source.upper()} ↗", row["source_url"])
        table_rows = draw_table(filtered, source + "_all_tenders", source)
        if table_rows:
            lookup = {r["id"]: r for r in table_rows}
            selected = st.selectbox("Explore a tender", list(lookup), format_func=lambda value: f'#{value} · {lookup[value]["title"]}', key=source + "_detail")
            show_detail(lookup[selected], source, revision)

    with district_tab:
        st.subheader("Where tenders are located")
        declared = sum(r["district_basis"] == "Declared" for r in filtered)
        inferred = sum(r["district_basis"] == "Text mention" for r in filtered)
        unknown = sum(r["district_basis"] == "Not specified" for r in filtered)
        c1, c2, c3 = st.columns(3)
        c1.metric("Declared location", declared)
        c2.metric("Explicit district in text", inferred)
        c3.metric("District not specified", unknown)
        counts = district_counts(filtered)
        named = [(name, count) for name, count in counts if name != UNKNOWN]
        if named:
            frame = pd.DataFrame(named, columns=["District", "Tenders"])
            chart = alt.Chart(frame).mark_bar(color="#0B766D", cornerRadiusEnd=4).encode(
                x=alt.X("Tenders:Q", axis=alt.Axis(tickMinStep=1), title="Number of tenders"),
                y=alt.Y("District:N", sort="-x", title=None, axis=alt.Axis(labelLimit=180)),
                tooltip=["District", "Tenders"]).properties(height=max(260, len(named)*27))
            st.altair_chart(chart.configure_axis(labelColor="#000", titleColor="#000"), width="stretch")
        if counts:
            st.dataframe(pd.DataFrame(counts, columns=["District", "Distinct tenders"]), hide_index=True, width="stretch")
        else:
            st.info("No district data for the current filters.")

    with topic_tab:
        st.subheader("Tenders by category")
        counts = pd.DataFrame([{"Category": category, "Tenders": sum(category in r['recovery_subjects'] for r in filtered)} for category in SUBJECTS])
        chart = alt.Chart(counts).mark_bar(color="#24566B", cornerRadiusEnd=4).encode(
            x=alt.X("Tenders:Q", axis=alt.Axis(tickMinStep=1), title="Number of tenders"),
            y=alt.Y("Category:N", sort=[translate(c) for c in SUBJECTS], title=None, axis=alt.Axis(labelLimit=210)),
            tooltip=["Category", "Tenders"]).properties(height=300)
        st.altair_chart(chart.configure_axis(labelColor="#000", titleColor="#000"), width="stretch")
        st.dataframe(counts, hide_index=True, width="stretch")
        st.caption(f"{sum('LEAP' in r['programmes'] for r in filtered):,} · " + translate("Explicit LEAP references"))
        st.caption(f"{sum(not r['recovery_subjects'] for r in filtered):,} · " + translate(NO_SUBJECT))
        candidates = filtered
        candidates = draw_table(candidates, source + "_topic_tenders", source)
        if candidates:
            with st.expander("Why these tenders matched"):
                evidence = [{"Tender ID": r["id"], **e} for r in candidates for e in r["recovery_evidence"]]
                st.dataframe(pd.DataFrame(evidence), hide_index=True, width="stretch")


@st.fragment(run_every="60s")
def dashboard():
    st.title("A clearer view of public tenders.")
    with st.spinner("Loading tenders…"):
        snapshot = get_feed().refresh()
    sources = snapshot['sources']
    all_rows = covered_tenders([row for data in sources.values() if data for row in data[0]["tenders"]])
    filters = tender_filters(all_rows)
    tabs = st.tabs(["PPA · هيئة الشراء العام", "CDR · مجلس الإنماء والإعمار"])
    for tab, source in zip(tabs, sources):
        with tab:
            if sources[source] is None:
                st.error(f"{source.upper()} dashboard data is unavailable. Automatic collection will retry.")
            else:
                revision = snapshot.get('revisions', {}).get(source, snapshot['revision'])
                source_dashboard(source, *sources[source], filters, revision=revision)
