"""Detailed, localized Gazette charts with explicit denominators and date windows."""
from __future__ import annotations
from calendar import month_name
import altair as alt
import pandas as pd
import streamlit as native
from i18n import st, translate as tr
from .analytics import CATEGORIES, subject_breakdown, monthly_breakdown, year_comparison, classification_breakdown
from .labels import TYPE_LABELS, STATUS_LABELS

YEAR_COLORS = ['#a9c9e1', '#e7c997', '#c5b9dc']
TYPE_COLORS = ['#a9c9e1', '#e7c997', '#c5b9dc']


def render(graph, key):
    graph = graph.configure_view(stroke=None).configure_axis(
        labelColor='#000000', titleColor='#000000', gridColor='#e9edf1',
        labelFontSize=12, titleFontSize=12, labelPadding=8,
    ).configure_legend(labelColor='#000000', titleColor='#000000', orient='top',
                       labelFontSize=12, titleFontSize=12).configure_text(color='#000000')
    # All chart labels are localized here, including scale domains and layered
    # tooltips. Do not pass layered specs through the single-chart i18n adapter.
    native.altair_chart(graph, width='stretch', key=key)


def share_label(value):
    return f'{value:.2%}' if 0 < value < .001 else f'{value:.1%}'


def count_labels(rows, label_field='label'):
    return [{**r, label_field: tr(r[label_field]),
             'value_label': f'{r["count"]:,}  ·  {share_label(r["share"])}'} for r in rows]


def count_chart(rows, title, key, color='#a9c9e1'):
    data = count_labels(rows)
    labels = [r['label'] for r in data]
    frame = pd.DataFrame(data)
    limit = max((r['count'] for r in data), default=1) or 1
    base = alt.Chart(frame).encode(
        y=alt.Y('label:N', sort=labels, title=None, axis=alt.Axis(labelLimit=alt.ExprRef(expr='width < 500 ? 145 : 210'))),
        x=alt.X('count:Q', title=tr('Records'), scale=alt.Scale(domain=[0, limit], range=[0, alt.ExprRef(expr='max(width - 110, 20)')]), axis=alt.Axis(tickMinStep=1, tickCount=alt.ExprRef(expr='width < 500 ? 3 : 5'), labelOverlap='greedy', labelSeparation=10)),
        tooltip=[alt.Tooltip('label:N', title=tr(title)), alt.Tooltip('count:Q', title=tr('Records'), format=','),
                 alt.Tooltip('share:Q', title=tr('Share of matching records'), format='.1%'),
                 alt.Tooltip('needs_review:Q', title=tr('Needs source review'), format=',')],
    )
    render((base.mark_bar(color=color, cornerRadiusEnd=3, size=23) +
            base.mark_text(align='right', dx=-2, fontSize=12).encode(x=alt.value(alt.ExprRef(expr='width')), text='value_label:N')).properties(height=max(150, len(data)*42)), key)


def subject_charts(rows, years):
    st.subheader('Subjects by publication year')
    if not rows:
        st.info('No Gazette records match these filters. Clear the search or choose another subject or year.')
        return
    segments, totals, matrix = subject_breakdown(rows, years)
    selected_years = sorted({r['year'] for r in segments})
    order = [tr(c) for c in CATEGORIES]
    frame = pd.DataFrame([{**r, 'subject': tr(r['subject'])} for r in segments])
    total_frame = pd.DataFrame(count_labels(totals, 'subject'))
    limit = max(r['count'] for r in totals) or 1
    pick = alt.selection_point(fields=['year'], bind='legend')
    bars = alt.Chart(frame).mark_bar(size=24).encode(
        y=alt.Y('subject:N', sort=order, title=None, axis=alt.Axis(labelLimit=210)),
        x=alt.X('count:Q', stack='zero', title=tr('Records'), scale=alt.Scale(domain=[0, limit*1.5]), axis=alt.Axis(tickMinStep=1)),
        color=alt.Color('year:N', title=tr('Publication year'), scale=alt.Scale(domain=selected_years, range=[YEAR_COLORS[['2024', '2025', '2026'].index(year)] for year in selected_years])),
        order=alt.Order('year:N'), opacity=alt.condition(pick, alt.value(1), alt.value(.25)),
        tooltip=[alt.Tooltip('subject:N', title=tr('Subject')), alt.Tooltip('year:N', title=tr('Publication year')),
                 alt.Tooltip('count:Q', title=tr('Records'), format=','),
                 alt.Tooltip('year_total:Q', title=tr("Matching records in this year"), format=','),
                 alt.Tooltip('year_share:Q', title=tr("Share of this year's records"), format='.1%'),
                 alt.Tooltip('subject_total:Q', title=tr('Subject total'), format=',')],
    ).add_params(pick)
    numbers = alt.Chart(total_frame).mark_text(align='left', dx=7, fontSize=12, color='#000').encode(
        y=alt.Y('subject:N', sort=order), x='count:Q', text='value_label:N')
    render((bars + numbers).properties(height=330), 'gazette_subject_year_chart')

    st.subheader('Which document types cover each subject?')
    heat = pd.DataFrame([{**r, 'subject': tr(r['subject']), 'type': tr(r['type'])} for r in matrix])
    base = alt.Chart(heat).encode(
        y=alt.Y('subject:N', sort=order, title=None, axis=alt.Axis(labelLimit=210)),
        x=alt.X('type:N', sort=[tr(t) for t in TYPE_LABELS.values()], title=None, axis=alt.Axis(orient='top', labelAngle=0)),
        tooltip=[alt.Tooltip('subject:N', title=tr('Subject')), alt.Tooltip('type:N', title=tr('Document type')),
                 alt.Tooltip('count:Q', title=tr('Records'), format=','),
                 alt.Tooltip('subject_total:Q', title=tr('Subject total'), format=','),
                 alt.Tooltip('share:Q', title=tr('Share within subject'), format='.1%')])
    render((base.mark_rect(stroke='#fff', strokeWidth=3).encode(
        color=alt.Color('count:Q', scale=alt.Scale(range=['#f2f6fa', '#9bbfdc']), legend=None)) +
        base.mark_text(color='#000', fontSize=14).encode(text=alt.Text('count:Q', format=','))).properties(height=330), 'gazette_subject_type_chart')
    with st.expander('See the subject figures'):
        table = pd.DataFrame([{'Subject': r['subject'], 'Records': r['count'],
                               'Share of matching records': share_label(r['share']),
                               **{year: next(v['count'] for v in segments if v['subject'] == r['subject'] and v['year'] == year) for year in selected_years},
                               'Needs source review': r['needs_review']} for r in totals])
        st.dataframe(table, hide_index=True, width='stretch')
        st.download_button('Download subject figures · CSV', table.to_csv(index=False).encode('utf-8-sig'),
                           file_name='gazette_subject_figures.csv', mime='text/csv', key='gazette_subject_chart_csv')


def timeline_charts(rows, coverage, years):
    st.subheader('Monthly publications, by document type')
    if not rows:
        st.info('No Gazette records match these filters. Clear the search or choose another subject or year.')
        return
    months = monthly_breakdown(rows, coverage, years)
    data = [{**r, 'type': tr(kind), 'type_count': r[kind]} for r in months for kind in TYPE_LABELS.values()]
    frame = pd.DataFrame(data)
    order = [r['month'] for r in months]
    domain = [tr(t) for t in TYPE_LABELS.values()]
    pick = alt.selection_point(fields=['type'], bind='legend')
    tips = [alt.Tooltip('month:N', title=tr('Month')),
            *[alt.Tooltip(f'{t}:Q', title=tr(t), format=',') for t in TYPE_LABELS.values()],
            alt.Tooltip('count:Q', title=tr('Monthly total'), format=','),
            alt.Tooltip('source_records:Q', title=tr('Saved records before filters'), format=',')]
    bars = alt.Chart(frame).mark_bar().encode(
        x=alt.X('month:N', sort=order, title=None, axis=alt.Axis(labelAngle=-55, labelFontSize=11, labelOverlap=False,
            labelExpr="width < 600 && length(domain('x')) > 18 && indexof(['01', '04', '07', '10'], slice(datum.label, 5)) < 0 ? '' : datum.label")),
        y=alt.Y('type_count:Q', stack='zero', title=tr('Records'), axis=alt.Axis(tickMinStep=1)),
        color=alt.Color('type:N', title=tr('Document type'), scale=alt.Scale(domain=domain, range=TYPE_COLORS)),
        order=alt.Order('type:N'), opacity=alt.condition(pick, alt.value(1), alt.value(.25)), tooltip=tips,
    ).add_params(pick)
    render(bars.properties(height=360), 'gazette_monthly_type_chart')

    st.subheader('Compare annual activity fairly')
    mode = st.selectbox('Comparison period', ['Same publication window', 'All saved publications'], key='gazette_comparison_window')
    comparison = year_comparison(rows, coverage, years, same_window=mode == 'Same publication window')
    yearly = pd.DataFrame(comparison)
    limit = max((r['count'] or 0 for r in comparison), default=1) or 1
    base = alt.Chart(yearly).encode(
        x=alt.X('year:N', sort='ascending', title=tr('Publication year'), axis=alt.Axis(labelAngle=0)),
        y=alt.Y('count:Q', title=tr('Records'), scale=alt.Scale(domain=[0, limit*1.17]), axis=alt.Axis(tickMinStep=1)),
        tooltip=[alt.Tooltip('year:N', title=tr('Publication year')), alt.Tooltip('count:Q', title=tr('Records in comparison'), format=','),
                 *[alt.Tooltip(f'{t}:Q', title=tr(t), format=',') for t in TYPE_LABELS.values()],
                 alt.Tooltip('through:N', title=tr('Comparison through')),
                 alt.Tooltip('all_records:Q', title=tr('All saved records in year'), format=','),
                 alt.Tooltip('latest_publication:N', title=tr('Latest saved publication'))])
    render((base.mark_bar(color='#a9c9e1', size=72, cornerRadiusTopLeft=4, cornerRadiusTopRight=4) +
            base.mark_text(dy=-10, fontSize=15).encode(text=alt.Text('count:Q', format=','))).properties(height=310), 'gazette_year_comparison_chart')
    with st.expander('See the monthly and yearly figures'):
        st.dataframe(yearly.rename(columns={'year': 'Publication year', 'count': 'Records in comparison',
            'through': 'Comparison through', 'all_records': 'All saved records in year',
            'latest_publication': 'Latest saved publication'}), hide_index=True, width='stretch')
        table = pd.DataFrame(months)[['month', *TYPE_LABELS.values(), 'count', 'source_records']].rename(columns={
            'month': 'Month', 'count': 'Monthly total', 'source_records': 'Saved records before filters'})
        st.dataframe(table, hide_index=True, width='stretch')
        st.download_button('Download monthly figures · CSV', table.to_csv(index=False).encode('utf-8-sig'),
                           file_name='gazette_monthly_figures.csv', mime='text/csv', key='gazette_monthly_chart_csv')


def classification_charts(rows):
    st.subheader('What do these records do?')
    if not rows:
        st.info('No Gazette records match these filters. Clear the search or choose another subject or year.')
        return
    nature = classification_breakdown(rows, 'nature')
    count_chart(nature, 'Nature', 'gazette_nature_chart')
    st.subheader('Policy areas in the Gazette')
    limit = st.selectbox('Policy areas to show', ['Top 10 policy areas', 'All policy areas'], key='gazette_policy_chart_scope')
    areas = classification_breakdown(rows, 'major')
    count_chart(areas[:10] if limit == 'Top 10 policy areas' else areas, 'Main category', 'gazette_policy_chart', color='#c5b9dc')
    st.subheader('How much classification review is complete?')
    review = classification_breakdown(rows, 'status')
    review = [{**r, 'label': STATUS_LABELS.get(r['label'], r['label'])} for r in review]
    count_chart(review, 'Assessment status', 'gazette_assessment_chart', color='#e7c997')
