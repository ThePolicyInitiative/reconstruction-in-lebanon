"""Budget extract: preserve unavailable values and count parent totals once."""
import csv
from html import escape
import io
from pathlib import Path

from i18n import st

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'data' / 'war_achraf_budget.csv'
PERIODS = ('2026 Law USD', '2027 First Draft USD', '2027 Second Draft USD')
LABELS = ('2026 law', '2027 first draft', '2027 second draft')
GROUPS = {
    'Mixed assistance, shelter, structural support and assessment': 'Mixed assistance, shelter & assessments',
    'Shelter compensation, structural repairs and reconstruction': 'Housing compensation & reconstruction',
    'War-related capital works / reconstruction': 'Capital works & reconstruction',
    'Repairs to damaged buildings in Beirut southern suburbs': 'Building repairs in southern suburbs',
    'Recurring income support to families of victims': 'Family & victim support',
    'Education assistance to children of victims': 'Family & victim support',
    'Support to injured victims': 'Family & victim support',
    'Medical assistance / hospitalization gap': 'Family & victim support',
    'Support to families, injured persons and permanent disability': 'Family & victim support',
    'Support to former detainees / liberated persons': 'Family & victim support',
    'Contribution to Martyr Foundation': 'Contribution to Martyr Foundation',
    'Response to Israeli attacks': 'Response to Israeli attacks',
}


def parse_amount(value):
    return None if value.strip() in ('n.a.', '') else int(value.replace(',', ''))


def load_budget(path=SOURCE):
    raw = Path(path).read_bytes()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1252')
    records = []
    for row in csv.DictReader(io.StringIO(text)):
        records.append({
            'code': row['Code'], 'level': int(row['Level']), 'parent': row['Parent code'],
            'activity': row['Support / activity type'],
            'beneficiary': row['Ultimate beneficiary / disclosure'],
            'institution': row['Ministry / institution'], 'arabic': row['Arabic category'],
            'economic_code': row['Economic code'],
            'amounts': {period: parse_amount(row[period]) for period in PERIODS},
        })
    return records


def primary_lines(records):
    return [row for row in records if row['level'] == 5]


def reported_sum(values):
    available = [value for value in values if value is not None]
    return sum(available) if available else None


def totals(records):
    return {period: reported_sum(row['amounts'][period] for row in primary_lines(records))
            for period in PERIODS}


def allocation_groups(records, period):
    groups = {}
    for row in primary_lines(records):
        group = GROUPS.get(row['activity'], row['activity'])
        groups.setdefault(group, []).append(row['amounts'][period])
    return sorted(((name, reported_sum(values)) for name, values in groups.items()),
                  key=lambda item: (item[1] is None, -(item[1] or 0)))


def money(value):
    return 'n.a.' if value is None else f'${value:,.0f}'


def short_money(value):
    if value is None:
        return 'n.a.'
    return f'${value / 1_000_000:,.2f}m' if value >= 1_000_000 else f'${value / 1_000:,.1f}k'


def headline_html(records):
    amounts = totals(records)
    cards = []
    for period, label in zip(PERIODS, LABELS):
        amount = amounts[period]
        cards.append(f'''<article class="budget-total"><h2>{label}</h2>
          <strong>{short_money(amount)}</strong><p>{money(amount)}</p></article>''')
    difference = amounts[PERIODS[2]] - amounts[PERIODS[0]]
    percent = difference / amounts[PERIODS[0]] * 100
    return f'''<section class="budget-page" aria-labelledby="budget-title">
      <div class="budget-heading"><div><p class="budget-kicker">2026 / 2027</p>
      <h1 id="budget-title">War-related budget allocations</h1>
      <p>The 2026 law and two 2027 drafts, as listed in the supplied budget extract.</p></div>
      <div class="budget-unit"><span>All amounts in USD</span><span>{len(primary_lines(records))} budget lines</span></div></div>
      <div class="budget-totals">{''.join(cards)}</div>
      <div class="budget-difference"><strong>+{short_money(difference)} <span>(+{percent:.1f}%)</span></strong>
      <p>Difference between the 2026 law and 2027 second draft across the listed allocations.</p></div>
      <p class="budget-scope">Totals cover the lines in this extract, not the entire national budget. These figures describe allocations and draft proposals; expenditure is not provided.</p>
      </section>'''


def draft_change_html(records):
    by_code = {row['code']: row for row in records}
    mixed = by_code['1.3.211.1091.14.1.2|D001']
    repairs = by_code['1.3.211.1091.14.1.2|D002']
    first, second = PERIODS[1:]
    change = mixed['amounts'][first] - mixed['amounts'][second]
    return f'''<aside class="budget-draft-change"><p class="budget-kicker">First draft → second draft</p>
      <h2>Same total. Two lines change.</h2>
      <p>The second draft reduces one mixed-assistance line by {money(change)} and lists the same amount for building repairs.</p>
      <div class="budget-flow-start"><small>First draft · mixed assistance</small>
        <strong>{money(mixed['amounts'][first])}</strong></div>
      <div class="budget-flow-arrow" aria-hidden="true">↓</div>
      <div class="budget-flow-split">
        <div><small>Second draft · mixed assistance</small><strong>{money(mixed['amounts'][second])}</strong>
        <span>Assistance, shelter, structural support and assessment</span></div>
        <div><small>Second draft · building repairs</small><strong>{money(repairs['amounts'][second])}</strong>
        <span>Damaged buildings in Beirut’s southern suburbs</span></div>
      </div>
      <p class="budget-flow-note">The repairs line is marked “n.a.” in the first draft. The two second-draft amounts add to {money(mixed['amounts'][first])}.</p>
      <details class="budget-code-note"><summary>Budget codes</summary><p>Mixed assistance: {escape(mixed['code'])}<br>Building repairs: {escape(repairs['code'])}</p></details>
      </aside>'''


def breakdown_html(records, period):
    total = totals(records)[period]
    bars, unavailable = [], []
    for name, amount in allocation_groups(records, period):
        if amount is None:
            unavailable.append(escape(name))
            continue
        share = amount / total * 100
        bars.append(f'''<li><div class="budget-bar-label"><span>{escape(name)}</span>
          <strong title="{money(amount)}">{short_money(amount)}</strong></div>
          <div class="budget-bar-track" aria-hidden="true"><span style="width:{share:.5f}%"></span></div>
          <div class="budget-bar-detail"><span>{share:.2f}% of reported total</span><span>{money(amount)}</span></div></li>''')
    absent = f'<p class="budget-missing">n.a. in this version: {"; ".join(unavailable)}.</p>' if unavailable else ''
    return f'''<section class="budget-page budget-breakdown">
      <div class="budget-allocations"><p class="budget-kicker">{LABELS[PERIODS.index(period)]}</p>
      <h2>Where the allocations go</h2><p class="budget-chart-note">Grouped by activity. Bar lengths show shares of the reported total.</p>
      <ul class="budget-bars">{''.join(bars)}</ul>{absent}</div>
      {draft_change_html(records)}</section>'''


def line_table(records, *, components=False):
    rows = [row for row in records if (row['level'] == 6 if components else row['level'] == 5)]
    body = []
    for row in rows:
        cells = ''.join(f'<td class="budget-number">{money(row["amounts"][period])}</td>' for period in PERIODS)
        institution = row['institution'] if '?' not in row['institution'] else 'Name unavailable in the CSV'
        body.append(f'''<tr><th scope="row">{escape(row['activity'])}
          <small>{escape(row['code'])}</small><details><summary>Beneficiary and classification</summary>
          <p>{escape(row['beneficiary'])}</p><p>Institution: {escape(institution)}<br>Economic code: {escape(row['economic_code'])}</p>
          </details></th>{cells}</tr>''')
    footer = ''
    if not components:
        amounts = totals(records)
        footer = '<tfoot><tr><th>Reported total</th>' + ''.join(f'<td class="budget-number">{money(amounts[period])}</td>' for period in PERIODS) + '</tr></tfoot>'
    caption = 'Family income support components (already included in the parent total)' if components else 'All budget lines in the extract'
    return f'''<div class="budget-page budget-table-wrap" tabindex="0" role="region" aria-label="{caption}">
      <table class="budget-table"><caption>{caption} · USD</caption><thead><tr><th>Support / activity</th>
      {''.join(f'<th>{label}</th>' for label in LABELS)}</tr></thead><tbody>{''.join(body)}</tbody>{footer}</table></div>'''


def show_budget():
    records = load_budget()
    st.html(ROOT / 'assets' / 'budget.css')
    with st.container(key='budget-page'):
        st.html(headline_html(records))
        version = st.selectbox('Show allocations for', PERIODS, index=2,
                               format_func=lambda value: LABELS[PERIODS.index(value)], key='budget_version')
        st.html(breakdown_html(records, version))
        with st.expander('All budget lines and beneficiaries'):
            st.caption('n.a. is preserved from the source. It does not mean zero. Expand a line to see its beneficiary and classification.')
            st.html(line_table(records))
        with st.expander('Family income support: component amounts'):
            st.write('The $5,119,519 family income-support total is counted once in each version. The three 2026 components and single 2027 component below are included in that total.')
            st.html(line_table(records, components=True))
        with st.expander('Source and calculation notes'):
            st.markdown('''Source: **war_achraf(Sheet1).csv**, supplied for this website.

- Totals sum the reported amounts of the 15 level-5 lines. The four level-6 family-support component rows are excluded from totals to avoid counting them twice.
- “n.a.” remains unavailable. A line without a reported amount is omitted from the sum; this does not establish zero funding.
- “Family & victim support” groups the six English activities covering recurring income, education, injured victims, medical assistance, family/disability support and former detainees. Other groups follow the file’s activity descriptions.
- Arabic categories and institution names contain question marks in the supplied file and cannot be recovered from it. The page uses its English activity and beneficiary descriptions. Full budget codes remain available above.
- Dollar amounts are used as supplied. The file does not specify a conversion rate, expenditure figures or the dates of the two drafts.''')
            st.download_button('Download original budget CSV', SOURCE.read_bytes(),
                               file_name='war_achraf(Sheet1).csv', mime='text/csv', key='budget_csv')
