"""Plain-language, bilingual guide to restrictions and missing funding."""
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
    'intro': ('Where was work or access restricted? Which needs were left without funding?', 'أين قُيّدت الأعمال أو حركة الدخول؟ وأي حاجات بقيت دون تمويل؟'),
    'explore': ('What would you like to understand?', 'ما الذي تريد الاطلاع عليه؟'),
    'restrictions': ('Restrictions on work & access', 'قيود الأعمال والدخول'),
    'funding': ('Missing funding', 'التمويل الناقص'),
    'restriction_type': ('Choose a type of restriction', 'اختر نوع القيد'),
    'funding_type': ('Choose the funding evidence', 'اختر نوع أدلة التمويل'),
    'stopped': ('Work stopped', 'وقف الأعمال'),
    'roads': ('Road access', 'استخدام الطرق'),
    'return': ('Return to villages', 'العودة إلى القرى'),
    'conditions': ('Rules before work', 'شروط بدء الأعمال'),
    'stopped_question': ('Where was building or repair work stopped?', 'أين أُوقفت أعمال البناء أو الترميم؟'),
    'stopped_intro': ('Two reports describe work stopped by the Internal Security Forces. Each case has a different permit dispute.', 'يصف تقريران وقف أعمال من قِبل قوى الأمن الداخلي، مع خلاف مختلف حول الترخيص في كل حالة.'),
    'roads_question': ('Which roads could residents not use?', 'أي طرق مُنع الأهالي من استخدامها؟'),
    'roads_intro': ('These cases concern restrictions on using roads for safety reasons. The sources do not establish a ban on repairing roads.', 'تتناول هذه الحالات قيوداً على استخدام الطرق لأسباب تتعلق بالسلامة. ولا تثبت المصادر وجود منع لإصلاح الطرق.'),
    'return_question': ('Where was return delayed or controlled?', 'أين تأخرت العودة أو خضعت لضوابط؟'),
    'return_intro': ('Municipal notices asked residents to wait or use specific routes while the army secured villages.', 'طلبت بيانات بلدية من الأهالي الانتظار أو سلوك طرق محددة أثناء تأمين الجيش للقرى.'),
    'conditions_question': ('What had to happen before work could proceed?', 'ما المطلوب قبل السماح ببدء الأعمال؟'),
    'conditions_intro': ('These are permit, transport or safety requirements. They are different from an order stopping an existing workshop.', 'هذه متطلبات للترخيص أو النقل أو السلامة، وتختلف عن قرار بوقف ورشة قائمة.'),
    'cases': ('cases in this section', 'حالات في هذا القسم'),
    'reported_enforcement': ('Reported work stoppage', 'وقف أعمال بحسب تقرير'),
    'administrative_condition': ('Approval required', 'موافقة مطلوبة'),
    'safety_restriction': ('Safety restriction', 'قيد لأسباب السلامة'),
    'temporary_restriction': ('Temporary entry rules', 'ضوابط دخول مؤقتة'),
    'programme_condition': ('Funding eligibility rule', 'شرط أهلية للتمويل'),
    'responsible': ('Who imposed it?', 'من فرض القيد؟'),
    'blocked': ('What was restricted?', 'ما الذي قُيّد؟'),
    'requirement': ('What was required?', 'ما المطلوب؟'),
    'why': ('Reason & what happened', 'السبب وما حدث'),
    'known_status': ('What we know about its status', 'ما نعرفه عن وضع القيد'),
    'report_date': ('Reported', 'تاريخ التقرير'),
    'notice_date': ('Notice published', 'نُشر الإعلان'),
    'statement_date': ('Statement issued', 'صدر البيان'),
    'document_date': ('Document dated', 'تاريخ الوثيقة'),
    'source': ('Source', 'المصدر'),
    'changes': ('Later changes', 'تطورات لاحقة'),
    'dated_note': ('Read the dates: these records describe what happened then. An old notice is not confirmation that a restriction is still in force.', 'انتبه إلى التاريخ: تصف السجلات ما حدث حينها. الإعلان القديم لا يؤكد استمرار القيد اليوم.'),
    'leap': ('LEAP programme', 'برنامج LEAP'),
    'local': ('Local services & households', 'الخدمات المحلية والأسر'),
    'budget': ('State budget', 'موازنة الدولة'),
    'leap_question': ('Which reconstruction work had no initial financing?', 'أي أعمال إعمار لم تحصل على تمويل أولي؟'),
    'leap_intro': ('The Lebanon Emergency Assistance Project (LEAP) is implemented by the Council for Development and Reconstruction. Its initial financing table shows the following shortfall.', 'ينفّذ مجلس الإنماء والإعمار مشروع المساعدة الطارئة للبنان (LEAP). ويوضح جدول تمويله الأولي النقص التالي.'),
    'initial_date': ('Initial financing table', 'جدول التمويل الأولي'),
    'major_works': ('Major reconstruction works', 'أعمال إعادة الإعمار الكبرى'),
    'needed': ('Planned funding needed', 'التمويل المطلوب في الخطة'),
    'available': ('Available initially', 'متاح أولياً'),
    'gap': ('Still needed', 'التمويل الناقص'),
    'zero_explanation': ('This entire works component was unfunded in the initial plan.', 'كان هذا المكوّن من الأعمال غير مموّل بالكامل في الخطة الأولية.'),
    'zero_limit': ('The $0 applies to this LEAP component. It does not mean Lebanon spent nothing on all reconstruction.', 'يخص مبلغ الصفر هذا المكوّن من LEAP، ولا يعني انعدام الإنفاق على كل الإعمار في لبنان.'),
    'programme_total': ('Across the whole programme', 'على مستوى البرنامج كاملاً'),
    'total': ('Planned total', 'إجمالي الخطة'),
    'money_table': ('Where was the funding missing?', 'أين كان نقص التمويل؟'),
    'money_unit': ('All amounts in US$ millions', 'جميع الأرقام بملايين الدولارات الأميركية'),
    'activity': ('Activity', 'النشاط'),
    'chart_note': ('Solid = available. Striped = missing. Bar lengths share one dollar scale.', 'اللون المصمت = المتاح. المخطط = الناقص. أطوال الأشرطة على مقياس مالي واحد.'),
    'programme_scope': ('The source gives programme totals, without a town-by-town allocation or proof of payments.', 'يعرض المصدر إجماليات البرنامج دون توزيع بحسب البلدة أو إثبات للمدفوعات.'),
    'local_question': ('Which local needs were not fully covered?', 'أي حاجات محلية لم تُغطَّ بالكامل؟'),
    'local_intro': ('Reports identify missing services, school support and household costs. The state allocation for each case is not given, so these amounts remain unknown.', 'تحدد التقارير نقصاً في الخدمات والدعم المدرسي وتكاليف على الأسر. لم يُذكر تخصيص الدولة لكل حالة، لذلك يبقى المبلغ غير معروف.'),
    'uncovered_activity': ('What needed money?', 'ما الذي احتاج إلى تمويل؟'),
    'local_authority': ('Authority involved', 'الجهة المعنية'),
    'local_what': ('What the report found', 'ما الذي رصده التقرير؟'),
    'allocation': ('State funding allocated', 'تمويل الدولة المخصص'),
    'not_quantified': ('Amount not stated', 'المبلغ غير مذكور'),
    'reported_unmet_need': ('Service needing support', 'خدمة تحتاج إلى دعم'),
    'reported_uncovered_cost': ('Cost left to a household', 'كلفة بقيت على أسرة'),
    'fee_relief_missing': ('Fee exemption missing', 'غياب الإعفاء من الرسوم'),
    'household_cost': ('Estimated extra household cost', 'كلفة إضافية تقديرية على الأسرة'),
    'limits': ('What this evidence establishes', 'ما الذي تثبته الأدلة؟'),
    'budget_question': ('Did the state allocate nothing to reconstruction?', 'هل لم تخصص الدولة أي تمويل للإعمار؟'),
    'budget_answer': ('The available records do not establish that.', 'السجلات المتاحة لا تثبت ذلك.'),
    'budget_intro': ('A missing line in a draft budget is only one stage. A later committee announcement added a shelter and repair provision, without stating the amount.', 'غياب بند في مشروع الموازنة يخص مرحلة واحدة فقط. فقد أعلنت اللجنة لاحقاً إضافة بند للإيواء والترميم دون تحديد المبلغ.'),
    'draft_stage': ('Draft budget', 'مشروع الموازنة'),
    'committee_stage': ('Committee change', 'تعديل اللجنة'),
    'payment_stage': ('Amount & payments', 'المبلغ والمدفوعات'),
    'payment_unknown': ('Not established by these sources', 'غير مثبتة في هذه المصادر'),
    'payment_detail': ('These records do not provide the final allocation or evidence that payments reached beneficiaries.', 'لا تقدم هذه السجلات قيمة الاعتماد النهائي أو دليلاً على وصول المدفوعات إلى المستفيدين.'),
    'source_notes': ('Sources & how to read the evidence', 'المصادر وكيفية قراءة الأدلة'),
    'method_title': ('How the cases are labelled', 'كيف صُنّفت الحالات؟'),
    'method': ('“Reported” identifies news coverage, not an enforcement order inspected here. Dates identify a report, statement, notice or document; they are not necessarily the start of a restriction. Past notices are not assumed to remain active. Zero is used only for an explicit numeric allocation; an unreported amount stays unknown. This is a reviewed selection, not a live register.', '«بحسب تقرير» تعني تغطية إعلامية، لا أمراً تنفيذياً اطلعنا عليه. تشير التواريخ إلى تقرير أو بيان أو إعلان أو وثيقة، وليست بالضرورة بداية القيد. لا نفترض استمرار القيود السابقة. يُستخدم الصفر فقط عند وجود تخصيص رقمي صريح؛ والمبلغ غير المذكور يبقى مجهولاً. هذه مجموعة مراجعة وليست سجلاً حياً.'),
    'official': ('Official source', 'مصدر رسمي'),
    'programme': ('Programme document', 'وثيقة برنامج'),
    'report': ('News report', 'تقرير إعلامي'),
    'reported_statement': ('Republished official statement', 'بيان رسمي معاد نشره'),
    'organisation_statement': ('Organisation statement', 'بيان جمعية'),
    'analysis': ('Draft-budget analysis', 'تحليل مشروع الموازنة'),
    'undated': ('Publication date not listed', 'تاريخ النشر غير مذكور'),
    'download': ('Download evidence and sources', 'تنزيل الأدلة والمصادر'),
    'town': ('Town / area', 'البلدة / المنطقة'),
    'authority': ('Responsible authority', 'الجهة المسؤولة'),
    'detail_toggle': ('Context & sources', 'التفاصيل والمصادر'),
    'status_unverified': ('Current status unverified', 'الوضع الحالي غير متحقق منه'),
    'return_reported': ('Later return reported · 17 Mar 2025', 'عودة لاحقة بحسب تقرير · 17 آذار 2025'),
    'rule_scope': ('Requirement at the document date', 'شرط قائم بتاريخ الوثيقة'),
    'funding_shortfall': ('Uncovered need', 'الحاجة غير المغطاة'),
    'amount_unknown': ('Gap not quantified', 'قيمة النقص غير محددة'),
    'initial_gap': ('Initial programme gap', 'فجوة التمويل الأولية للبرنامج'),
    'funding_snapshot': ('LEAP: funding at a glance', 'تمويل LEAP في لمحة'),
    'funding_implementation': ('Implemented by the Council for Development and Reconstruction', 'ينفذه مجلس الإنماء والإعمار'),
    'million_short': ('M', ' مليون'),
    'funding_split': ('Funding split', 'توزيع التمويل'),
    'conditional_blocked': ('Blocked / conditional work', 'أعمال ممنوعة أو مشروطة'),
    'choose_restriction': ('Choose a restriction case', 'اختر حالة قيد'),
    'choose_local_gap': ('Choose a local funding gap', 'اختر فجوة تمويل محلية'),
    'restriction_panel': ('Restrictions', 'القيود'),
    'local_panel': ('Local funding gaps', 'فجوات التمويل المحلية'),
    'all_sources': ('Sources & details', 'المصادر والتفاصيل'),
    'case_evidence': ('Case context & sources', 'سياق الحالة ومصادرها'),
    'local_evidence': ('Funding context & sources', 'سياق التمويل ومصادره'),
    'initial_leap': ('LEAP · initial financing', 'LEAP · التمويل الأولي'),
    'works_short': ('Major works: initially available / needed', 'الأعمال الكبرى: المتاح أولياً / المطلوب'),
    'funded_short': ('Initially funded', 'مموّل أولياً'),
    'gap_short': ('Funding gap', 'فجوة التمويل'),
    'programme_only': ('Programme figures; not total state spending.', 'أرقام البرنامج؛ لا إجمالي إنفاق الدولة.'),
}

RESTRICTION_GROUPS = ('stopped', 'roads', 'return', 'conditions')
FUNDING_GROUPS = ('leap', 'local', 'budget')


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


def case_group(record):
    if record['status'] == 'reported_enforcement':
        return 'stopped'
    if record['status'] in ('administrative_condition', 'programme_condition'):
        return 'conditions'
    return record['category']


def case_date(record, lang):
    return f'<span class="barrier-date">{ui(record["date_kind"], lang)} <time datetime="{record["date"]}">{dated(record["date"], lang)}</time></span>'


def links_html(data, keys, lang):
    return f'<div class="barrier-links"><b>{ui("source", lang)}</b>{"".join(source_link(data, key, lang) for key in keys)}</div>'


def field(label, value):
    return f'<div class="barrier-fact"><dt>{label}</dt><dd>{value}</dd></div>'


def place_html(record, lang):
    return f'''<div class="barrier-place"><span class="barrier-field-label">{icon('pin', 16, '#000')}{ui('town', lang)}</span>
      <h3>{escape(record['place'][lang])}</h3>{case_date(record, lang)}</div>'''


def infographic_field(label, value, symbol, extra_class=''):
    return f'''<div class="barrier-visual-field {extra_class}"><span class="barrier-field-label">{icon(symbol, 16, '#000')}{label}</span><p>{value}</p></div>'''


def evidence_details(data, record, lang):
    return f'''<details class="barrier-details"><summary>{ui('detail_toggle', lang)}</summary>
      <div class="barrier-detail-body"><h4>{escape(record['title'][lang])}</h4><p>{escape(record['action'][lang])}</p>
      <p class="barrier-detail-limit">{escape(record['limit'][lang])}</p>{links_html(data, record['sources'], lang)}</div></details>'''


def barrier_card(data, record, lang):
    text = lambda key: escape(record[key][lang])
    requirement = 'conditional_blocked' if case_group(record) == 'conditions' else 'blocked'
    status = 'return_reported' if record['id'] == 'houla_return' else 'rule_scope' if case_group(record) == 'conditions' else 'status_unverified'
    symbol = {'building': 'building', 'roads': 'road', 'return': 'family', 'debris': 'services'}[record['category']]
    arrow = '<span class="barrier-flow-arrow" aria-hidden="true"></span>'
    return f'''<article class="barrier-card barrier-flow-card" data-case="{record['id']}">
      <div class="barrier-flow">{place_html(record, lang)}{arrow}
        {infographic_field(ui('authority', lang), text('actor'), 'building', 'barrier-actor')}{arrow}
        {infographic_field(ui(requirement, lang), text('blocked'), symbol, 'barrier-impact')}</div>
      <div class="barrier-row-footer"><p class="barrier-status-brief"><span class="barrier-tag">{ui(record['status'], lang)}</span><span>{ui(status, lang)}</span></p>
        {evidence_details(data, record, lang)}</div></article>'''


def section_heading(question, intro, lang, count=None):
    count_html = f'<span class="barrier-count">{count} {ui("cases", lang)}</span>' if count is not None else ''
    return f'<div class="barrier-section-heading"><h2>{ui(question, lang)}</h2>{count_html}<p>{ui(intro, lang)}</p></div>'


def restrictions_html(data, lang, group=None):
    if group is None:
        return ''.join(restrictions_html(data, lang, key) for key in RESTRICTION_GROUPS)
    records = [record for record in data['physical'] if case_group(record) == group]
    updates = [data['updates'][1]] if group == 'roads' else [data['updates'][0]] if group in ('stopped', 'conditions') else []
    later = ''
    if updates:
        later = f'<details class="barrier-later"><summary>{ui("changes", lang)}</summary>{"".join(event_html(data, record, lang) for record in updates)}</details>'
    return f'''<section class="barrier-restrictions" data-group="{group}">
      {section_heading(group + '_question', group + '_intro', lang, len(records))}
      <div class="barrier-case-grid">{''.join(barrier_card(data, record, lang) for record in records)}</div>
      <p class="barrier-reading-note">{icon('calendar', 18, '#000')}{ui('dated_note', lang)}</p>{later}</section>'''


def local_funding_html(data, lang):
    cards = []
    for record in data['funding_cases']:
        text = lambda key: escape(record[key][lang])
        allocation = ui('not_quantified', lang) if record['allocation_usd'] is None else f"${record['allocation_usd']:,.0f}"
        cost = ''
        if record.get('household_cost_usd') is not None:
            cost = f'<strong class="barrier-gap-amount"><bdi>${record["household_cost_usd"]:,.0f}</bdi></strong><span>{ui("household_cost", lang)}</span>'
        else:
            cost = f'<strong class="barrier-gap-unknown">{ui("amount_unknown", lang)}</strong>'
        symbol = 'education' if 'school' in record['id'] else 'services'
        cards.append(f'''<article class="barrier-card barrier-local-card" data-funding-case="{record['id']}">
          <div class="barrier-local-flow">{place_html(record, lang)}
            {infographic_field(ui('local_authority', lang), text('actor'), 'building', 'barrier-actor')}
            {infographic_field(ui('uncovered_activity', lang), text('activity'), symbol, 'barrier-impact')}
            <div class="barrier-local-amount"><span class="barrier-field-label">{icon('fund', 16, '#000')}{ui('funding_shortfall', lang)}</span>{cost}
              <p class="barrier-allocation"><b>{ui('allocation', lang)}:</b> {allocation}</p></div></div>
          <div class="barrier-row-footer"><p class="barrier-status-brief"><span class="barrier-tag">{ui(record['evidence'], lang)}</span></p>{evidence_details(data, record, lang)}</div></article>''')
    return f'<section data-group="local">{section_heading("local_question", "local_intro", lang)}<div class="barrier-case-grid">{"".join(cards)}</div></section>'


def event_html(data, record, lang):
    return f'''<article class="barrier-event"><time datetime="{record['date']}">{dated(record['date'], lang)}</time>
      <h3>{escape(record['title'][lang])}</h3><p>{escape(record['text'][lang])}</p>{source_link(data, record['source'], lang)}</article>'''


def money(value, lang):
    return f'<bdi>${value:,}</bdi> {"مليون" if lang == "ar" else "million"}'


def compact_money(value, lang):
    return f'<bdi>${value:,}</bdi><small>{ui("million_short", lang)}</small>'


def funding_html(data, lang):
    funding = data['funding']
    available = sum(row['available'] for row in funding['rows'])
    gap = sum(row['gap'] for row in funding['rows'])
    scale = max(row['available'] + row['gap'] for row in funding['rows'])
    works = next(row for row in funding['rows'] if row['code'] == 'C3b')
    rows = []
    for row in funding['rows']:
        label = escape(row['label'][lang])
        accessible = f'{row["label"][lang]}; {ui("available", lang)}: ${row["available"]}M; {ui("gap", lang)}: ${row["gap"]}M'
        rows.append(f'''<tr data-component="{row['code']}"><th scope="row">{label}</th><td class="barrier-bar-cell">
          <div class="barrier-track" role="img" aria-label="{escape(accessible, quote=True)}"><span class="barrier-funded" style="width:{row['available'] / scale * 100:.4f}%"></span><span class="barrier-gap" style="width:{row['gap'] / scale * 100:.4f}%"></span></div></td>
          <td><bdi>${row['available']}</bdi></td><td><bdi>${row['gap']}</bdi></td></tr>''')
    return f'''<section data-group="leap"><div class="barrier-section-heading"><h2>{ui('funding_snapshot', lang)}</h2>
      <p>{ui('funding_implementation', lang)} · {ui('initial_date', lang)}: <time datetime="{funding['as_of']}">{dated(funding['as_of'], lang)}</time></p>
      <p><b>{ui('town', lang)}:</b> {escape(funding['place'][lang])}</p></div>
      <div class="barrier-funding-metrics"><div><span>{ui('total', lang)}</span><strong>{compact_money(available + gap, lang)}</strong></div>
        <div><span>{ui('available', lang)}</span><strong>{compact_money(available, lang)}</strong></div>
        <div class="barrier-gap-metric"><span>{ui('initial_gap', lang)}</span><strong>{compact_money(gap, lang)}</strong></div></div>
      <div class="barrier-money-chart"><div class="barrier-chart-heading"><h3>{ui('money_table', lang)}</h3><p>{ui('money_unit', lang)}</p></div>
        <table><thead><tr><th scope="col">{ui('activity', lang)}</th><th scope="col" class="barrier-bar-cell">{ui('funding_split', lang)}</th><th scope="col">{ui('available', lang)}</th><th scope="col">{ui('gap', lang)}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
        <p class="barrier-chart-note">{ui('chart_note', lang)}</p></div>
      <div class="barrier-zero-strip">{icon('building', 24, '#000')}<div><b>{ui('major_works', lang)}: {money(works['available'], lang)} {ui('available', lang).lower()} · {money(works['gap'], lang)} {ui('gap', lang).lower()}</b><p>{ui('zero_limit', lang)}</p></div></div>
      <details class="barrier-later"><summary>{ui('detail_toggle', lang)}</summary><p>{ui('leap_intro', lang)}</p><p>{escape(funding['place'][lang])}</p><p>{ui('programme_scope', lang)}</p>{links_html(data, [funding['source'], 'cdr'], lang)}</details></section>'''


def budget_html(data, lang):
    events = ''.join(f'<div class="barrier-budget-step"><span class="barrier-step-label">{ui(key, lang)}</span>{event_html(data, record, lang)}</div>' for key, record in zip(('draft_stage', 'committee_stage'), data['budget_history']))
    return f'''<section data-group="budget">{section_heading('budget_question', 'budget_intro', lang)}
      <div class="barrier-budget-answer">{ui('budget_answer', lang)}</div><div class="barrier-budget-timeline">{events}
      <div class="barrier-budget-step"><span class="barrier-step-label">{ui('payment_stage', lang)}</span><article class="barrier-event"><h3>{ui('payment_unknown', lang)}</h3><p>{ui('payment_detail', lang)}</p></article></div></div></section>'''


def page_wrapper(content, lang, view='all'):
    return f'<div class="barriers-page" lang="{lang}" dir="{"rtl" if lang == "ar" else "ltr"}" data-view="{view}">{content}</div>'


def heading_html(data, lang):
    return page_wrapper(f'''<header class="barriers-heading"><div class="barriers-meta"><b>{ui('scope', lang)}</b><span>{ui('reviewed', lang)} {dated(data['reviewed_on'], lang)}</span></div>
      <h1>{ui('title', lang)}</h1><p>{ui('intro', lang)}</p></header>''', lang)


def barriers_html(data, lang='en', view='all', group=None):
    """Render one focused section, or all evidence for export and validation."""
    if view == 'restrictions':
        content = restrictions_html(data, lang, group)
    elif view == 'funding':
        render = {'leap': funding_html, 'local': local_funding_html, 'budget': budget_html}
        content = render[group or 'leap'](data, lang)
    else:
        content = restrictions_html(data, lang) + funding_html(data, lang) + local_funding_html(data, lang) + budget_html(data, lang)
    return page_wrapper(content, lang, view)


def sources_html(data, lang='en'):
    records = []
    for key, source in data['sources'].items():
        records.append(f'''<article class="barrier-source"><b>{source_link(data, key, lang, source['title'][lang])}</b>
          <p>{escape(source['publisher'][lang])} · {ui(source['kind'], lang)} · {dated(source['date'], lang)}</p><p>{escape(source['access'][lang])}</p></article>''')
    return page_wrapper(f'<h3>{ui("method_title", lang)}</h3><p>{ui("method", lang)}</p><div class="barrier-source-grid">{"".join(records)}</div>', lang)


def board_header(data, lang):
    return page_wrapper(f'''<header class="barriers-board-heading"><h1>{ui('title', lang)}</h1>
      <p>{ui('scope', lang)} · {ui('reviewed', lang)} {dated(data['reviewed_on'], lang)}</p></header>''', lang)


def funding_strip(data, lang):
    funding = data['funding']
    available = sum(row['available'] for row in funding['rows'])
    gap = sum(row['gap'] for row in funding['rows'])
    works = next(row for row in funding['rows'] if row['code'] == 'C3b')
    return page_wrapper(f'''<section class="barriers-board-funding" aria-label="{ui('initial_leap', lang)}">
      <div class="board-funding-scope"><b>{ui('initial_leap', lang)}</b><time datetime="{funding['as_of']}">{dated(funding['as_of'], lang)}</time><small>{ui('programme_only', lang)}</small></div>
      <div class="board-total"><strong>{compact_money(available, lang)}</strong><span>{ui('funded_short', lang)}</span></div>
      <div class="board-total board-main-gap"><strong>{compact_money(gap, lang)}</strong><span>{ui('gap_short', lang)}</span></div>
      <div class="board-total board-works"><strong>{compact_money(works['available'], lang)} <span>/</span> {compact_money(works['available'] + works['gap'], lang)}</strong><span>{ui('works_short', lang)}</span></div>
      </section>''', lang, 'overview')


def board_case_html(record, lang, funding=False):
    text = lambda key: escape(record[key][lang])
    label = ui('uncovered_activity', lang) if funding else ui('conditional_blocked' if case_group(record) == 'conditions' else 'blocked', lang)
    amount_html = ''
    if funding:
        allocation = ui('not_quantified', lang) if record['allocation_usd'] is None else f"${record['allocation_usd']:,.0f}"
        if record.get('household_cost_usd') is not None:
            amount = f'<strong><bdi>${record["household_cost_usd"]:,.0f}</bdi></strong><span>{ui("household_cost", lang)}</span>'
        else:
            amount = f'<strong class="board-unknown">{ui("amount_unknown", lang)}</strong>'
        amount_html = f'<div class="board-money">{amount}<p><b>{ui("allocation", lang)}:</b> {allocation}</p></div>'
        status_html = ''
    else:
        status = 'return_reported' if record['id'] == 'houla_return' else 'rule_scope' if case_group(record) == 'conditions' else 'status_unverified'
        status_html = f'<p class="board-status"><b>{ui(record["status"], lang)}</b> · {ui(status, lang)}</p>'
    attribute = 'data-funding-case' if funding else 'data-case'
    return page_wrapper(f'''<article class="board-case {'board-local' if funding else 'board-restriction'}" {attribute}="{record['id']}">
      <header aria-label="{ui('town', lang)}"><div class="board-location-title">{icon('pin', 16, '#000')}<h3>{text('place')}</h3></div>{case_date(record, lang)}</header>
      {infographic_field(ui('local_authority' if funding else 'authority', lang), text('actor'), 'building', 'board-authority')}
      {infographic_field(label, text('activity' if funding else 'blocked'), 'fund' if funding else 'shield', 'board-impact')}
      {amount_html}{status_html}</article>''', lang, 'selected-funding' if funding else 'selected-restriction')


def selected_evidence(data, record, lang):
    return page_wrapper(f'''<div class="board-evidence"><h3>{escape(record['title'][lang])}</h3><p>{escape(record['action'][lang])}</p>
      <p>{escape(record['limit'][lang])}</p>{links_html(data, record['sources'], lang)}</div>''', lang)


def _remember_board_choice(canonical_key, widget_key):
    st.session_state[canonical_key] = st.session_state[widget_key]


def board_selector(key, label, options, formatter, lang):
    # A fresh widget per language also refreshes BaseWeb's selected label.
    # Keep the actual case ID separately so switching language retains the case.
    widget_key = f'{key}__{lang}'
    selected = st.session_state.get(key, options[0])
    st.session_state[widget_key] = selected if selected in options else options[0]
    return st.selectbox(label, options, key=widget_key, format_func=formatter, label_visibility='collapsed',
                        on_change=_remember_board_choice, args=(key, widget_key))


def show_reconstruction_barriers():
    data = load_barriers()
    lang = language()
    st.html(ROOT / 'assets/reconstruction-barriers.css')
    with st.container(key='barriers-onepage'):
        heading_column, source_column = st.columns([3, 1], gap='small', vertical_alignment='center')
        with heading_column:
            st.html(board_header(data, lang))
        with source_column:
            with st.popover(ui('all_sources', lang), width='stretch'):
                st.html(page_wrapper(funding_html(data, lang) + budget_html(data, lang), lang))
                st.html(sources_html(data, lang))
                st.download_button(ui('download', lang), json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'),
                                   file_name='lebanon-restrictions-and-funding-gaps.json', mime='application/json', key='barriers_evidence')
        st.html(funding_strip(data, lang))
        restrictions_column, funding_column = st.columns(2, gap='medium')
        with restrictions_column:
            st.html(page_wrapper(f'<h2 class="board-panel-title">{ui("restriction_panel", lang)}<span>{len(data["physical"])} {ui("cases", lang)}</span></h2>', lang))
            physical = {row['id']: row for row in data['physical']}
            selected = board_selector('barriers_selected_case', ui('choose_restriction', lang), list(physical),
                                      lambda key: f'{physical[key]["place"][lang]} · {ui(case_group(physical[key]), lang)}', lang)
            record = physical[selected]
            st.html(board_case_html(record, lang))
            with st.popover(ui('case_evidence', lang), width='stretch'):
                st.html(selected_evidence(data, record, lang))
                st.html(page_wrapper(f'<p>{ui("dated_note", lang)}</p>' + ''.join(event_html(data, row, lang) for row in data['updates']), lang))
        with funding_column:
            st.html(page_wrapper(f'<h2 class="board-panel-title">{ui("local_panel", lang)}<span>{len(data["funding_cases"])} {ui("cases", lang)}</span></h2>', lang))
            local = {row['id']: row for row in data['funding_cases']}
            selected_local = board_selector('barriers_selected_local', ui('choose_local_gap', lang), list(local),
                                            lambda key: f'{local[key]["place"][lang]} · {local[key]["title"][lang]}', lang)
            st.html(board_case_html(local[selected_local], lang, funding=True))
            with st.popover(ui('local_evidence', lang), width='stretch'):
                st.html(selected_evidence(data, local[selected_local], lang))
                st.html(page_wrapper(f'<p>{ui("local_intro", lang)}</p>', lang))
