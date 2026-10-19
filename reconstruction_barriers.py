"""Dated evidence on Lebanese authorities' restrictions and funding gaps."""
from datetime import date
from html import escape
import json
from pathlib import Path

import streamlit as st

from i18n import language
from visuals import icon

ROOT = Path(__file__).resolve().parent


def load_barriers():
    return json.loads((ROOT / 'data/reconstruction_barriers.json').read_text(encoding='utf-8'))


UI = {
    'title': ('Restrictions & funding gaps', 'القيود وفجوات التمويل'),
    'scope': ('Lebanese authorities only', 'السلطات اللبنانية فقط'),
    'reviewed': ('Sources reviewed', 'مراجعة المصادر'),
    'intro': ('What restricts rebuilding, road access and return — and where funding is missing.', 'ما يقيّد البناء والوصول والعودة، وأين تنقص الأموال.'),
    'physical': ('Rebuilding & access', 'البناء والوصول'),
    'physical_intro': ('Dated cases and requirements. Safety measures, permit conditions and reported enforcement are identified separately.', 'وقائع وشروط مؤرخة، مع توضيح الفرق بين تدابير السلامة وشروط الترخيص والإجراءات المبلّغ عنها.'),
    'building': ('Rebuilding', 'إعادة البناء'),
    'roads': ('Roads', 'الطرق'),
    'return': ('Returning to land', 'العودة إلى الأرض'),
    'debris': ('Rubble removal', 'إزالة الأنقاض'),
    'funding': ('Funding', 'التمويل'),
    'reported_enforcement': ('Reported work stoppage', 'وقف ورشة مبلّغ عنه'),
    'administrative_condition': ('Administrative condition', 'شرط إداري'),
    'safety_restriction': ('Safety restriction', 'قيد سلامة'),
    'temporary_restriction': ('Temporary entry restriction', 'قيد دخول مؤقت'),
    'programme_condition': ('Programme eligibility', 'أهلية البرنامج'),
    'responsible': ('Authority', 'الجهة'),
    'town': ('Town / area', 'البلدة / المنطقة'),
    'blocked': ('What was blocked or required', 'ما مُنع أو اشترط'),
    'report_date': ('Report date', 'تاريخ التقرير'),
    'notice_date': ('Notice date', 'تاريخ الإعلان'),
    'statement_date': ('Statement date', 'تاريخ البيان'),
    'document_date': ('Document date', 'تاريخ الوثيقة'),
    'case_detail': ('Reason & context', 'السبب والسياق'),
    'local_money_title': ('Local needs still seeking support', 'حاجات محلية ما زالت تطلب الدعم'),
    'local_money_intro': ('These reports identify specific missing support. They do not establish that Parliament allocated zero to these services.', 'تحدد هذه التقارير دعماً ناقصاً بعينه، ولا تثبت أن مجلس النواب خصص صفراً لهذه الخدمات.'),
    'uncovered_activity': ('What needed funding', 'ما احتاج إلى تمويل'),
    'allocation': ('State allocation', 'تخصيص الدولة'),
    'not_quantified': ('Not quantified in the source', 'غير محدد رقمياً في المصدر'),
    'reported_unmet_need': ('Reported unmet need', 'حاجة غير ملباة بحسب التقرير'),
    'reported_uncovered_cost': ('Reported uncovered cost', 'كلفة غير مغطاة بحسب التقرير'),
    'fee_relief_missing': ('No fee exemption reported', 'عدم الإعفاء بحسب التقرير'),
    'household_cost': ('Additional household cost (reported estimate)', 'الكلفة الإضافية للأسرة (تقدير منقول)'),
    'source': ('Read source', 'قراءة المصدر'),
    'changes': ('Later developments to keep in view', 'تطورات لاحقة يجب أخذها في الاعتبار'),
    'money_title': ('What was left without funding?', 'ما الذي بقي دون تمويل؟'),
    'money_scope': ('Initial LEAP programme financing · 17 February 2026 · USD millions', 'التمويل الأولي لبرنامج LEAP · 17 شباط 2026 · مليون دولار'),
    'zero_label': ('Initial financing for major works', 'التمويل الأولي للأعمال الكبرى'),
    'zero_detail': ('The $455M works component had no initial financing.', 'لم يُموّل مكوّن الأعمال البالغ 455 مليون دولار في المرحلة الأولى.'),
    'zero_limit': ('This is a programme allocation, not a claim of zero national reconstruction spending.', 'هذا تخصيص داخل البرنامج، وليس دليلاً على انعدام الإنفاق الوطني على الإعمار.'),
    'available': ('Available initially', 'المتاح أولياً'),
    'gap': ('Unfunded in this plan', 'غير المموّل في الخطة'),
    'chart_note': ('Bar lengths use the same dollar scale. Figures are financing, not completed work or payments.', 'الأشرطة على مقياس مالي واحد. الأرقام تمويل وليست أعمالاً منجزة أو مدفوعات.'),
    'total': ('Total programme', 'إجمالي البرنامج'),
    'national_title': ('And the state budget?', 'وماذا عن موازنة الدولة؟'),
    'national_note': ('An absent draft line, an approved allocation and an actual payment are different things. These records do not establish zero funding across the final national budget.', 'غياب بند في مشروع الموازنة والتخصيص المعتمد والدفع الفعلي أمور مختلفة. لا تثبت هذه السجلات انعدام التمويل في الموازنة الوطنية النهائية.'),
    'source_notes': ('Sources & how to read this page', 'المصادر وكيفية قراءة الصفحة'),
    'method_title': ('What the labels mean', 'ماذا تعني التسميات؟'),
    'method': ('“Reported” identifies news coverage, not an enforcement order inspected here. Old restrictions are not assumed to remain active. “Zero” is used only for an explicit numeric allocation; missing figures remain unknown. This page is a reviewed selection, not a live register of closures or spending.', '«مبلّغ عنه» يعني تغطية إعلامية، لا أمراً تنفيذياً اطلعنا عليه. لا نفترض استمرار القيود القديمة. يُستخدم «صفر» فقط عند وجود تخصيص رقمي صريح؛ وتبقى الأرقام الغائبة غير معروفة. هذه مجموعة منتقاة ومراجعة، وليست سجلاً حياً للإقفالات أو الإنفاق.'),
    'official': ('Official source', 'مصدر رسمي'),
    'programme': ('Programme document', 'وثيقة برنامج'),
    'report': ('News report', 'تقرير إعلامي'),
    'reported_statement': ('Republished official statement', 'بيان رسمي معاد نشره'),
    'organisation_statement': ('Organisation statement', 'بيان جمعية'),
    'analysis': ('Draft-budget analysis', 'تحليل مشروع الموازنة'),
    'undated': ('Publication date not listed', 'تاريخ النشر غير مذكور'),
    'download': ('Download evidence and sources', 'تنزيل الأدلة والمصادر'),
    'case_count': ('dated cases & requirements', 'وقائع وشروط مؤرخة'),
    'local_count': ('local funding gaps', 'فجوات تمويل محلية'),
    'date_label': ('Date', 'التاريخ'),
    'case_heading': ('Town & date', 'البلدة والتاريخ'),
    'short_blocked': ('Blocked / required', 'المنع / الشرط'),
    'historic_note': ('Historical reports and conditions; continued enforcement is not assumed. Open a row for context and sources.', 'تقارير وشروط مؤرخة؛ لا نفترض استمرار تطبيقها. افتح السطر لقراءة السياق والمصادر.'),
    'evidence_details': ('Context, status & sources', 'السياق والحالة والمصادر'),
    'funding_summary': ('LEAP financing gap', 'فجوة تمويل LEAP'),
    'unfunded_share': ('unfunded initially', 'غير مموّل أولياً'),
    'available_short': ('Available', 'متاح'),
    'gap_short': ('Gap', 'فجوة'),
    'programme_scope': ('Initial programme financing', 'التمويل الأولي للبرنامج'),
    'programme_details': ('Programme scope & source', 'نطاق البرنامج ومصدره'),
    'funding_limit_short': ('Programme financing, not national spending.', 'تمويل البرنامج، لا الإنفاق الوطني.'),
    'allocation_unknown': ('State allocation: amount unknown', 'تخصيص الدولة: المبلغ غير معروف'),
    'more_evidence': ('Policy changes & budget history', 'تطورات القرارات والموازنة'),
    'open_case': ('Open case details', 'فتح تفاصيل الحالة'),
    'local_short_note': ('Reported unmet needs and costs. Unknown allocations are not zero.', 'حاجات وكلف غير مغطاة بحسب التقارير. التخصيص غير المعروف لا يعني صفراً.'),
}


def ui(key, lang):
    return UI[key][lang == 'ar']


def dated(value, lang):
    if not value:
        return ui('undated', lang)
    day = date.fromisoformat(value)
    months = ('كانون الثاني', 'شباط', 'آذار', 'نيسان', 'أيار', 'حزيران', 'تموز', 'آب', 'أيلول', 'تشرين الأول', 'تشرين الثاني', 'كانون الأول')
    return f'{day.day} {months[day.month - 1]} {day.year}' if lang == 'ar' else day.strftime('%d %b %Y').lstrip('0')


def source_link(data, key, lang, label=None):
    source = data['sources'][key]
    return f'<a href="{escape(source["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label or source["publisher"][lang])} ↗</a>'


def barrier_card(data, record, lang):
    text = lambda field: escape(record[field][lang])
    return f'''<details class="barrier-case" data-case="{record['id']}">
      <summary class="barrier-case-summary">
        <span class="barrier-location"><strong>{text('place')}</strong>{case_date(record, lang)}</span>
        <span class="barrier-case-actor"><span class="barrier-mobile-label">{ui('responsible', lang)}</span>{text('actor')}</span>
        <span class="barrier-case-impact"><span class="barrier-mobile-label">{ui('short_blocked', lang)}</span>{text('blocked')}
          <span class="barrier-status-label">{ui(record['status'], lang)}</span></span>
        <span class="barrier-expand" aria-hidden="true"></span>
      </summary>
      <div class="barrier-case-detail"><h4>{text('title')}</h4><p>{text('action')}</p>
      <p class="barrier-detail-limit">{text('limit')}</p>
      <div class="barrier-links">{''.join(source_link(data, key, lang) for key in record['sources'])}</div>
      </div></details>'''


def case_date(record, lang):
    return f'''<span class="barrier-case-date"><span>{ui(record['date_kind'], lang)}</span>
      <time datetime="{record['date']}">{dated(record['date'], lang)}</time></span>'''


def restrictions_html(data, lang):
    groups = []
    for category, symbol in [('building', 'building'), ('roads', 'road'), ('return', 'pin'), ('debris', 'services')]:
        records = [row for row in data['physical'] if row['category'] == category]
        if not records:
            continue
        groups.append(f'''<section class="barrier-group barrier-group-{category}">
          <h3>{icon(symbol, 20, '#000')}{ui(category, lang)}<span class="barrier-group-count">{len(records):02d}</span></h3>
          {''.join(barrier_card(data, row, lang) for row in records)}</section>''')
    return f'''<section class="barrier-register"><div class="barrier-section-heading"><h2>{ui('physical', lang)}</h2>
      <span>{len(data['physical'])} {ui('case_count', lang)}</span></div>
      <p class="barrier-reading-note">{ui('historic_note', lang)}</p>
      <div class="barrier-register-head" aria-hidden="true"><span>{ui('case_heading', lang)}</span><span>{ui('responsible', lang)}</span><span>{ui('short_blocked', lang)}</span><span></span></div>
      {''.join(groups)}</section>'''


def local_funding_html(data, lang):
    cards = []
    for record in data['funding_cases']:
        # Unknown amounts must never be displayed as zero.
        allocation = ui('not_quantified', lang) if record['allocation_usd'] is None else f"${record['allocation_usd']:,.0f}"
        household_cost = ''
        if record.get('household_cost_usd') is not None:
            household_cost = f'<span class="barrier-household-cost"><bdi>${record["household_cost_usd"]:,.0f}</bdi> · {ui("household_cost", lang)}</span>'
        cards.append(f'''<details class="barrier-local-case" data-funding-case="{record['id']}">
          <summary><span class="barrier-location"><strong>{escape(record['place'][lang])}</strong>{case_date(record, lang)}</span>
            <span class="barrier-local-impact"><strong>{escape(record['activity'][lang])}</strong>
              <span class="barrier-local-actor"><b>{ui('responsible', lang)}:</b> {escape(record['actor'][lang])}</span>
              <span class="barrier-allocation"><b>{ui('allocation', lang)}:</b> {allocation}</span>{household_cost}</span>
            <span class="barrier-expand" aria-hidden="true"></span></summary>
          <div class="barrier-case-detail"><h4>{escape(record['title'][lang])}</h4><p>{escape(record['action'][lang])}</p>
            <p class="barrier-detail-limit"><b>{ui(record['evidence'], lang)}.</b> {escape(record['limit'][lang])}</p>
            <div class="barrier-links">{''.join(source_link(data, key, lang) for key in record['sources'])}</div></div></details>''')
    return f'''<section class="barrier-local-funding"><div class="barrier-section-heading"><h2>{ui('local_money_title', lang)}</h2><span>{len(cards):02d}</span></div>
      <p class="barrier-reading-note">{ui('local_short_note', lang)}</p><div class="barrier-funding-cases">{''.join(cards)}</div></section>'''


def event_html(data, record, lang):
    return f'''<article class="barrier-event"><time datetime="{record['date']}">{dated(record['date'], lang)}</time>
      <h3>{escape(record['title'][lang])}</h3><p>{escape(record['text'][lang])}</p>
      {source_link(data, record['source'], lang)}</article>'''


def funding_html(data, lang):
    funding = data['funding']
    scale = max(row['available'] + row['gap'] for row in funding['rows'])
    available = sum(row['available'] for row in funding['rows'])
    gap = sum(row['gap'] for row in funding['rows'])
    missing_percent = gap / (available + gap) * 100 if available + gap else 0
    works = next(row for row in funding['rows'] if row['code'] == 'C3b')
    rows = []
    for row in funding['rows']:
        label = row['label'][lang]
        amount = f'{ui("available", lang)}: ${row["available"]}M; {ui("gap", lang)}: ${row["gap"]}M'
        # Numeric labels stay next to their bars; the accessible label states both values.
        rows.append(f'''<div class="barrier-money-row" data-component="{row['code']}">
          <div class="barrier-money-label"><b>{escape(label)}</b><span><bdi>${row['available']}M</bdi></span><span><bdi>${row['gap']}M</bdi></span></div>
          <div class="barrier-track" role="img" aria-label="{escape(label + ': ' + amount, quote=True)}">
            <span class="barrier-funded" style="width:{row['available'] / scale * 100:.4f}%"></span><span class="barrier-gap" style="width:{row['gap'] / scale * 100:.4f}%"></span>
          </div></div>''')
    ring_label = f'{missing_percent:.0f}% {ui("unfunded_share", lang)}; {ui("available", lang)}: ${available}M; {ui("gap", lang)}: ${gap}M'
    return f'''<section id="barrier-funding" class="barrier-programme"><h2>{ui('funding_summary', lang)}</h2>
      <p class="barrier-reading-note">{ui('programme_scope', lang)} · {dated(funding['as_of'], lang)}</p>
      <div class="barrier-finance-hero"><div class="barrier-ring" role="img" aria-label="{escape(ring_label, quote=True)}" style="--gap-share:{missing_percent:.4f}%">
        <span><strong>{missing_percent:.0f}%</strong><small>{ui('unfunded_share', lang)}</small></span></div>
        <div class="barrier-finance-totals"><div><strong><bdi>${gap}M</bdi></strong><span>{ui('gap', lang)}</span></div>
          <p><bdi>${available}M</bdi> {ui('available', lang)}</p><p><bdi>${available + gap}M</bdi> {ui('total', lang)}</p></div></div>
      <div class="barrier-money-chart"><div class="barrier-money-label barrier-money-head"><span></span>
        <span><i class="barrier-funded"></i>{ui('available_short', lang)}</span><span><i class="barrier-gap"></i>{ui('gap_short', lang)}</span></div>
        {''.join(rows)}</div>
      <div class="barrier-zero"><strong><bdi>${works['available']}M</bdi></strong><span><b>{ui('zero_label', lang)}</b><small>{ui('zero_detail', lang)}</small></span></div>
      <p class="barrier-chart-note">{ui('funding_limit_short', lang)}</p>
      <p class="barrier-programme-meta"><b>{ui('responsible', lang)}:</b> {escape(funding['actor'][lang])}</p>
      <p class="barrier-programme-meta"><b>{ui('town', lang)}:</b> {escape(funding['place'][lang])}</p>
      <details class="barrier-supporting"><summary>{ui('programme_details', lang)}</summary><div class="barrier-case-detail">
        <p>{ui('zero_limit', lang)}</p><p>{ui('chart_note', lang)}</p>{source_link(data, funding['source'], lang)}</div></details></section>'''


def barriers_html(data, lang='en'):
    direction = 'rtl' if lang == 'ar' else 'ltr'
    return f'''<article class="barriers-page" lang="{lang}" dir="{direction}">
      <header class="barriers-heading"><div class="barriers-meta"><b>{ui('scope', lang)}</b><span>{ui('reviewed', lang)} {dated(data['reviewed_on'], lang)}</span></div>
        <h1>{ui('title', lang)}</h1><p>{ui('intro', lang)}</p></header>
      <div class="barrier-dashboard">{restrictions_html(data, lang)}
        <div class="barrier-finance-column">{funding_html(data, lang)}{local_funding_html(data, lang)}</div></div>
      <details class="barrier-history barrier-supporting"><summary>{icon('calendar', 18, '#000')}{ui('more_evidence', lang)}<span>{len(data['updates']) + len(data['budget_history']):02d}</span></summary>
        <div class="barrier-history-body"><section><h3>{ui('changes', lang)}</h3><div class="barrier-events">{''.join(event_html(data, record, lang) for record in data['updates'])}</div></section>
          <section><h3>{ui('national_title', lang)}</h3><div class="barrier-events">{''.join(event_html(data, record, lang) for record in data['budget_history'])}</div><p class="barrier-context">{ui('national_note', lang)}</p></section></div></details></article>'''


def sources_html(data, lang='en'):
    records = []
    for key, source in data['sources'].items():
        records.append(f'''<article class="barrier-source"><b>{source_link(data, key, lang, source['title'][lang])}</b>
          <p>{escape(source['publisher'][lang])} · {ui(source['kind'], lang)} · {dated(source['date'], lang)}</p>
          <p>{escape(source['access'][lang])}</p></article>''')
    return f'''<div class="barriers-page" lang="{lang}" dir="{'rtl' if lang == 'ar' else 'ltr'}"><h3>{ui('method_title', lang)}</h3>
      <p>{ui('method', lang)}</p><div class="barrier-source-grid">{''.join(records)}</div></div>'''


def show_reconstruction_barriers():
    data = load_barriers()
    lang = language()
    st.html(ROOT / 'assets/reconstruction-barriers.css')
    st.html(barriers_html(data, lang))
    with st.expander(ui('source_notes', lang)):
        st.html(sources_html(data, lang))
        st.download_button(ui('download', lang), json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'),
                           file_name='lebanon-restrictions-and-funding-gaps.json', mime='application/json', key='barriers_evidence')
