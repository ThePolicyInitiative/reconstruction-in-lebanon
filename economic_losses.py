"""Bilingual visual summary of the supplied economic-loss workbook."""
from html import escape
from datetime import datetime, timedelta
import json
from pathlib import Path

import streamlit as st

from i18n import language

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/Economic_losses_war_AY.xlsx"

UI = {
    "title": ("Economic losses", "الخسائر الاقتصادية"),
    "intro": ("The cost of war across 2023–2024 and 2026", "كلفة الحرب خلال <bdi>2023–2024</bdi> و<bdi>2026</bdi>"),
    "source_button": ("Sources", "المصادر"),
    "cost": ("Total economic cost", "الكلفة الاقتصادية الإجمالية"),
    "damage": ("Physical damage", "الأضرار المادية"),
    "losses": ("Economic losses", "الخسائر الاقتصادية"),
    "billion": ("billion", "مليار دولار"),
    "million": ("US$ million", "مليون دولار أميركي"),
    "estimate": ("Workbook range · basis unverified", "نطاق من الملف · أساسه غير متحقق منه"),
    "assessed": ("Post-conflict estimate", "تقدير لاحق للنزاع"),
    "estimate_note": ("The 2026 all-sector ranges come from the workbook; their derivation has not been verified. They are not a new World Bank damage assessment.", "نطاقات 2026 لكل القطاعات من ملف البيانات؛ لم يُتحقق من طريقة احتسابها. وهي ليست تقييماً جديداً للأضرار من البنك الدولي."),
    "housing": ("Housing damage", "أضرار المساكن"),
    "units": ("More than 100,000 housing units damaged", "تضررت أكثر من 100,000 وحدة سكنية"),
    "subset": ("Housing is included in physical damage.", "أضرار المساكن مشمولة ضمن الأضرار المادية."),
    "channels": ("Tourism & household losses", "خسائر السياحة والأسر"),
    "channels_note": ("2024 estimates and 2026 projections. Household coverage changes from five areas to three; the bars do not measure recovery on a constant geographic basis.", "تقديرات 2024 وتوقعات 2026. تتغير تغطية خسائر الأسر من خمس مناطق إلى ثلاث؛ فلا تقيس الأشرطة التعافي على أساس جغرافي ثابت."),
    "reported_total": ("Total", "الإجمالي"),
    "regions": ("Where household spending fell", "أين تراجع إنفاق الأسر؟"),
    "regional_period": ("2024 household spending losses", "خسائر إنفاق الأسر في 2024"),
    "regional_total": ("Total across the five regions", "الإجمالي في المناطق الخمس"),
    "gdp": ("Impact on economic growth", "الأثر على النمو الاقتصادي"),
    "gdp_intro": ("GDP growth lost against the no-war scenario, in percentage points.", "النقص في نمو الناتج المحلي مقارنة بسيناريو عدم الحرب، بالنقاط المئوية."),
    "pp": ("percentage points lost", "نقطة مئوية مفقودة"),
    "growth": ("GDP growth", "نمو الناتج المحلي"),
    "no_war": ("Without war", "دون الحرب"),
    "no_baseline": ("No-war rate not separately stated", "معدل عدم الحرب غير مذكور منفصلاً"),
    "projected": ("Projection", "توقع"),
    "gdp_note": ("The 2026 figures are projections; percentage-point losses are not dollar amounts.", "أرقام 2026 توقعات، والخسائر بالنقاط المئوية ليست مبالغ مالية."),
    "notes": ("How to read these figures", "كيف تُقرأ هذه الأرقام؟"),
    "period_note": ("The comparison covers 2023–2024 and 2026. The earlier US$4.2 billion tourism-and-consumption figure relates to 2024 alone.", "تشمل المقارنة مرحلة 2023–2024 وعام 2026. تخص خسائر السياحة والاستهلاك السابقة البالغة 4.2 مليارات دولار عام 2024 وحده."),
    "overlap_note": ("Physical damage and economic losses make up total economic cost. Housing, tourism, household and regional figures are breakdowns; do not add them again to the headline totals.", "تتكون الكلفة الاقتصادية من الأضرار المادية والخسائر الاقتصادية. أرقام المساكن والسياحة والأسر والمناطق تفصيلات ضمنها؛ لا تُضاف مجدداً إلى الإجماليات الرئيسية."),
    "rounding": ("Component sums differ slightly from the totals", "تختلف مجاميع المكونات قليلاً عن الإجماليات"),
    "gdp_revision": ("Historical cards keep the Fall 2024 scenarios together. The workbook’s 2024 −5.2% / 6.1-point pair is not a matched scenario in that table and is retained in the original cells; revised growth does not update an older no-war scenario.", "تحافظ البطاقات التاريخية على سيناريوهات خريف 2024 متسقة. لا يطابق زوج أرقام الملف لعام 2024، ‎−5.2% و6.1 نقاط، سيناريو في ذلك الجدول، وحُفظ في الخلايا الأصلية؛ تعديل النمو لا يحدّث تلقائياً سيناريو عدم الحرب الأقدم."),
    "links": ("Source links", "روابط المصادر"),
    "download": ("Download original Excel workbook", "تنزيل ملف إكسل الأصلي"),
    "original": ("Original cells & notes", "الخلايا والملاحظات الأصلية"),
    "original_language": ("Source data in English.", "البيانات المصدرية باللغة الإنجليزية."),
    "cell": ("Cell", "الخلية"),
    "original_value": ("Original value", "القيمة الأصلية"),
    "source_review": ("General economic source mapping reviewed: 23 Oct 2026. Sector and displacement sheets imported: 26 Oct 2026; figures and links are reported as supplied in the workbook.", "مراجعة مصادر البيانات الاقتصادية العامة: 23 تشرين الأول 2026. أُضيفت ورقتا القطاعات والنزوح في 26 تشرين الأول 2026؛ الأرقام والروابط كما وردت في الملف."),
    "headline_source": ("World Bank RDNA · 7 Mar 2025 · Covers 8 Oct 2023–20 Dec 2024; ten sectors nationwide.", "البنك الدولي، تقييم الأضرار · 7 آذار 2025 · يغطي 8 تشرين الأول 2023–20 كانون الأول 2024؛ عشرة قطاعات على المستوى الوطني."),
    "workbook_range": ("Workbook C2–C4 · Source and calculation for these ranges are unresolved.", "الملف، C2–C4 · مصدر هذه النطاقات وطريقة احتسابها غير محسومين."),
    "channels_2024_source": ("2024 · World Bank, Fall 2024 · Table 6, p. 26.", "2024 · البنك الدولي، خريف 2024 · الجدول 6، ص. 26."),
    "channels_2026_source": ("2026 · World Bank, Summer 2026 · Tables 2–3, pp. 20–21.", "2026 · البنك الدولي، صيف 2026 · الجدولان 2–3، ص. 20–21."),
    "regional_source": ("World Bank, Fall 2024 · Table 5, p. 25. Night-light estimates; Baabda proxies for the southern suburbs.", "البنك الدولي، خريف 2024 · الجدول 5، ص. 25. تقديرات الإضاءة الليلية؛ تُستخدم بعبدا كمؤشر للضاحية الجنوبية."),
    "fall2024": ("Fall 2024 scenario · Table 7", "سيناريو خريف 2024 · الجدول 7"),
    "summer2026": ("Summer 2026 projection · Figure 15", "توقع صيف 2026 · الشكل 15"),
    "definitions": ("Damage is the value of destroyed assets; losses are reduced economic flows. Reconstruction needs are a separate measure. These panels use different periods, methods and coverage.", "الأضرار هي قيمة الأصول المدمرة؛ والخسائر هي تراجع التدفقات الاقتصادية. احتياجات الإعمار مقياس منفصل. تختلف الفترات والمنهجيات والتغطية بين هذه اللوحات."),
}

CHANNEL_PERIODS = ("2024", "2026")

UI.update({
    "sectors": ("Damage by sector", "الأضرار حسب القطاع"),
    "displacement": ("Displacement & returns · 2026", "النزوح والعودة · 2026"),
    "workbook_reports": ("Figures reported in the supplied workbook. Assessments differ in dates, definitions and coverage; entries are not additive. Source wording is retained in English.", "أرقام واردة في الملف المرفق. تختلف التقييمات في التواريخ والتعريفات والتغطية؛ لا تُجمع الأرقام. تظهر الترجمة العربية أولاً، وتحتها الصياغة الإنجليزية كما وردت في الملف."),
    "displacement_note": ("Snapshots from different dates, as reported in the workbook. Shelter figures are from 15 September; displacement and return totals are from 29 September. Do not combine these snapshots or add returnees to people still displaced.", "لقطات من تواريخ مختلفة كما وردت في الملف. أرقام الإيواء من 15 أيلول، وإجماليات النزوح والعودة من 29 أيلول. لا تُجمع هذه اللقطات ولا يُضاف العائدون إلى من لا يزالون نازحين."),
    "location_note": ("District snapshots are from August 2026 and do not break down the September totals. Origins, destinations and returns describe different populations and dates.", "لقطات المناطق من آب 2026 وليست تفصيلاً لإجماليات أيلول. تصف مناطق المنشأ والاستضافة والعودة مجموعات وتواريخ مختلفة."),
    "report_link": ("Source", "المصدر"),
    "phase_one": ("October 2023–December 2024", "تشرين الأول 2023–كانون الأول 2024"),
    "phase_two": ("March 2026 onward", "منذ آذار 2026"),
})

CATEGORY_AR = {
    "Agricultural land": "الأراضي الزراعية", "Hospitals": "المستشفيات",
    "Schools": "المدارس", "Houses": "المساكن", "Businesses": "المؤسسات التجارية",
    "Factories": "المصانع", "Total IDPs still displaced": "إجمالي من لا يزالون نازحين",
    "People who have returned": "الأشخاص الذين عادوا", "In collective shelters": "في مراكز الإيواء الجماعية",
    "Outside shelters (rented homes, relatives, host families)": "خارج مراكز الإيواء (مساكن مستأجرة وأقارب وأسر مضيفة)",
    "Fled from": "مناطق النزوح", "Went to": "مناطق الاستضافة", "Returned to": "مناطق العودة",
}


def report_text(value):
    """Format Excel dates/numbers without changing the raw workbook snapshot."""
    if isinstance(value, (float, int)):
        return f"{value:,.0f}"
    return str(value).replace("�", "–").strip()


def report_date(value):
    if isinstance(value, (float, int)):
        return (datetime(1899, 12, 30) + timedelta(days=value)).strftime("%d %b %Y")
    return report_text(value)


AR_MONTHS = ["كانون الثاني", "شباط", "آذار", "نيسان", "أيار", "حزيران", "تموز", "آب", "أيلول", "تشرين الأول", "تشرين الثاني", "كانون الأول"]


def report_translations():
    """Arabic wording for workbook report text, keyed by the exact English shown on screen."""
    return json.loads((ROOT / "locales/economic_losses_ar.json").read_text(encoding="utf-8"))


def report_ar(value, translations):
    """Arabic for one workbook value; None when its current wording has no translation."""
    if isinstance(value, (float, int)):
        return None
    return translations.get(report_text(value))


def report_date_ar(value, translations):
    if isinstance(value, (float, int)):
        day = datetime(1899, 12, 30) + timedelta(days=value)
        return f"{day.day} {AR_MONTHS[day.month - 1]} {day.year}"
    return report_ar(value, translations)


def original_line(*parts):
    """The workbook wording, kept under its Arabic translation."""
    return f'<p class="losses-note losses-original" lang="en" dir="ltr">{escape(" · ".join(parts))}</p>'


def report_links(row, lang):
    urls = [url.strip() for url in row.get("links", "").splitlines() if url.strip().startswith(("https://", "http://"))]
    return " · ".join(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{tr("report_link", lang)} {index + 1} ↗</a>' for index, url in enumerate(urls))


def sectors_html(data, lang):
    translations = report_translations() if lang == "ar" else {}
    phases = []
    for phase, title in [("2023–2024", "phase_one"), ("2026", "phase_two")]:
        categories = []
        for category in dict.fromkeys(row["category"] for row in data["sector_rows"] if row["phase"] == phase):
            reports = []
            for row in data["sector_rows"]:
                if row["phase"] != phase or row["category"] != category:
                    continue
                figure, date, source = report_text(row['figure']), report_date(row['date']), report_text(row['source'])
                arabic = [report_ar(row['figure'], translations), report_date_ar(row['date'], translations), report_ar(row['source'], translations)]
                if lang == "ar" and all(arabic):
                    # A reworded workbook cell has no match and falls back to the original alone.
                    text = f'''<p lang="ar" dir="rtl">{escape(arabic[0])}</p>
                  <p class="losses-note" lang="ar" dir="rtl">{escape(arabic[1])} · {escape(arabic[2])}</p>{original_line(figure, date, source)}'''
                else:
                    text = f'''<p lang="en" dir="ltr">{escape(figure)}</p>
                  <p class="losses-note" lang="en" dir="ltr">{escape(date)} · {escape(source)}</p>'''
                reports.append(f'''<div class="losses-report" data-sheet="Sectors" data-row="{row['row']}">
                  {text}
                  <p class="losses-note">{report_links(row, lang)}</p></div>''')
            label = CATEGORY_AR[category] if lang == "ar" else category
            categories.append(f'<article class="losses-panel"><h3>{escape(label)}</h3>{"".join(reports)}</article>')
        phases.append(f'<h3 class="losses-section-title">{tr(title, lang)}</h3><div class="losses-sector-grid">{"".join(categories)}</div>')
    return wrapper(f'<section><h2>{tr("sectors", lang)}</h2><p class="losses-note">{tr("workbook_reports", lang)}</p>{"".join(phases)}</section>', lang)


def displacement_html(data, lang):
    translations = report_translations() if lang == "ar" else {}

    def localized(value, tag, css=""):
        """Arabic when this wording is translated; otherwise the workbook value as supplied."""
        arabic = report_date_ar(value, translations) if tag == "date" else report_ar(value, translations)
        element = "p" if tag == "date" else tag
        css = f' class="{css}"' if css else ""
        if lang == "ar" and arabic:
            return f'<{element}{css} lang="ar" dir="rtl">{escape(arabic)}</{element}>'
        text = report_date(value) if tag == "date" else report_text(value)
        return f'<{element}{css} lang="en" dir="ltr">{escape(text)}</{element}>'

    def original(*values):
        """Workbook wording under the Arabic, listing only the parts that were translated."""
        parts = [report_text(value) for value in values if report_ar(value, translations)]
        return original_line(*parts) if lang == "ar" and parts else ""

    cards = []
    for row in data["displacement_indicators"]:
        label = CATEGORY_AR[row["label"]] if lang == "ar" else row["label"]
        cards.append(f'''<article class="losses-panel" data-sheet="IDPs" data-row="{row['row']}"><h3>{escape(label)}</h3>
          {localized(row['figure'], "strong", "losses-idp-value")}
          {localized(row['date'], "date", "losses-note")}{original(row['figure'], row['date'])}<p class="losses-note">{report_links(row, lang)}</p></article>''')
    groups = []
    for group in ("Fled from", "Went to", "Returned to"):
        rows = []
        for row in data["displacement_locations"]:
            if row["group"] == group:
                rows.append(f'''<div class="losses-report" data-sheet="IDPs" data-row="{row['row']}">
                  {localized(row['district'], "h3")}{localized(row['figure'], "p")}
                  {localized(row['date'], "date", "losses-note")}{original(row['district'], row['figure'], row['date'])}<p class="losses-note">{report_links(row, lang)}</p></div>''')
        label = CATEGORY_AR[group] if lang == "ar" else group
        groups.append(f'<article class="losses-panel"><h3>{escape(label)}</h3>{"".join(rows)}</article>')
    return wrapper(f'''<section><h2>{tr("displacement", lang)}</h2><p class="losses-caution">{tr("displacement_note", lang)}</p>
      <div class="losses-idp-grid">{''.join(cards)}</div><p class="losses-note">{tr("location_note", lang)}</p>
      <div class="losses-location-grid">{''.join(groups)}</div></section>''', lang)


def tr(key, lang):
    return UI[key][lang == "ar"]


def load_losses():
    return json.loads((ROOT / "data/economic_losses.json").read_text(encoding="utf-8"))


def wrapper(content, lang):
    return f'<div class="losses-page" lang="{lang}" dir="{"rtl" if lang == "ar" else "ltr"}">{content}</div>'


def fmt(value, decimals=1):
    return f"{value:,.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{value:,.0f}"


def billions(metric, lang):
    values = "–".join(fmt(value / 1000) for value in metric["usd_m"])
    return f'<bdi>${values}</bdi><small>{tr("billion", lang)}</small>'


def provenance(data, key, lang, source_cell=None, page=None):
    text = escape(tr(key, lang))
    if source_cell:
        source = next(row for row in data['sources'] if row.get('cell', row.get('id')) == source_cell)
        url = source['url'] + (f'#page={page}' if page else '')
        text = f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{text} ↗</a>'
    return f'<p class="losses-provenance" data-provenance="{key}">{text}</p>'


def headline_html(data, lang):
    cards = []
    for phase in data["phases"]:
        components = "".join(
            f'<div data-cell="{phase[key]["cell"]}"><span>{tr(key, lang)}</span><strong>{billions(phase[key], lang)}</strong></div>'
            for key in ("damage", "losses")
        )
        estimated = phase["total"]["estimated"]
        badge = f'<span>{tr("estimate" if estimated else "assessed", lang)}</span>'
        source = provenance(data, 'workbook_range', lang) if estimated else provenance(data, 'headline_source', lang, 'A32')
        cards.append(f'''<article class="losses-phase {"losses-estimated" if estimated else ""}" data-period="{phase['period']}">
          <header><h2><bdi>{phase['period']}</bdi></h2>{badge}</header>
          <p>{tr("cost", lang)}</p><strong class="losses-headline" data-cell="{phase['total']['cell']}">{billions(phase['total'], lang)}</strong>
          <div class="losses-components">{components}</div>{source}</article>''')
    housing = data["housing"]
    return wrapper(f'''<div class="losses-phases">{''.join(cards)}</div>
      <div class="losses-housing"><strong><bdi>${fmt(housing["damage_usd_m"] / 1000)}</bdi> {tr("billion", lang)}</strong>
        <div><b>{tr("housing", lang)} · <bdi>2023–2024</bdi></b><span>{tr("units", lang)}</span></div>
        <small>{tr("subset", lang)}</small></div>
      <p class="losses-caution">{tr("estimate_note", lang)}</p>
      <p class="losses-note">{tr("definitions", lang)}</p>''', lang)


def bar(value, scale, style="", label=""):
    return f'<div class="losses-track" role="img" aria-label="{escape(label, quote=True)}"><span class="{style}" style="width:{value / scale * 100:.5f}%"></span></div>'


def channels_html(data, lang):
    scale = max(point["value"] for row in data["channels"] for point in row["values"])
    rows = []
    for row in data["channels"]:
        bars = []
        for index, point in enumerate(row["values"]):
            period = CHANNEL_PERIODS[index]
            label = f'{period}: {fmt(point["value"])} {tr("million", lang)}'
            bars.append(f'''<div class="losses-pair" data-cell="{point['cell']}"><span><bdi>{period}</bdi></span>
              {bar(point["value"], scale, "losses-projection" if index else "", label)}
              <strong><bdi>{fmt(point['value'])}</bdi></strong></div>''')
        rows.append(f'<div class="losses-channel"><h3>{escape(row["label"][lang])}</h3>{"".join(bars)}</div>')
    totals = "".join(f'<div><span><bdi>{CHANNEL_PERIODS[index]}</bdi></span><strong><bdi>{fmt(point["value"])}</bdi></strong></div>' for index, point in enumerate(data["channel_totals"]))
    return f'''<section class="losses-panel"><header><h2>{tr("channels", lang)}</h2><span>{tr("million", lang)}</span></header>
      <p class="losses-note">{tr("channels_note", lang)}</p>{''.join(rows)}
      <div class="losses-channel-totals"><b>{tr("reported_total", lang)}</b>{totals}</div>
      {provenance(data, 'channels_2024_source', lang, 'WB-FALL24', 42)}{provenance(data, 'channels_2026_source', lang, 'A26', 33)}</section>'''


def regions_html(data, lang):
    scale = max(row["value"] for row in data["regions"])
    rows = []
    for row in sorted(data["regions"], key=lambda value: -value["value"]):
        label = row["label"][lang]
        rows.append(f'''<div class="losses-region" data-cell="{row['cell']}"><div><span>{escape(label)}</span><strong><bdi>{fmt(row['value'])}</bdi></strong></div>
          {bar(row['value'], scale, label=f'{label}: {fmt(row["value"])} {tr("million", lang)}')}</div>''')
    return f'''<section class="losses-panel"><header><h2>{tr("regions", lang)}</h2><span>{tr("million", lang)}</span></header>
      <p class="losses-note">{tr("regional_period", lang)}</p>{''.join(rows)}
      <div class="losses-regional-total"><span>{tr("regional_total", lang)}</span><strong><bdi>{fmt(data["regional_total"]["value"])}</bdi></strong></div>
      {provenance(data, 'regional_source', lang, 'WB-FALL24', 41)}</section>'''


def gdp_html(data, lang):
    cards = []
    scale = max(row["lost_pp"] for row in data["gdp_comparisons"])
    for row in data["gdp_comparisons"]:
        baseline = f'<bdi>{row["no_war_pct"]:+.1f}%</bdi> {tr("no_war", lang)}' if row["no_war_pct"] is not None else tr("no_baseline", lang)
        projected = f'<span>{tr("projected", lang)}</span>' if row["projected"] else ""
        cards.append(f'''<article class="losses-gdp-card" data-year="{row['year']}"><header><h3>{row['year']}</h3>{projected}</header>
          <strong><bdi>{row['lost_pp']:.1f}</bdi><small>{tr("pp", lang)}</small></strong>
          {bar(row["lost_pp"], scale, "losses-projection" if row["projected"] else "", f'{row["year"]}: {row["lost_pp"]} {tr("pp", lang)}')}
          <p><bdi>{row['growth_pct']:+.1f}%</bdi> {tr("growth", lang)}</p><p class="losses-note">{baseline}</p>
          {provenance(data, row['vintage'], lang, row['source'], row['source_page'])}</article>''')
    return wrapper(f'''<section class="losses-gdp"><header><h2>{tr("gdp", lang)}</h2><p>{tr("gdp_intro", lang)}</p></header>
      <div class="losses-gdp-grid">{''.join(cards)}</div><p class="losses-note">{tr("gdp_note", lang)}</p>
      <p class="losses-caution">{tr("gdp_revision", lang)}</p></section>''', lang)


def source_notes_html(data, lang):
    differences = []
    for index, total in enumerate(data["channel_totals"]):
        component_sum = sum(row["values"][index]["value"] for row in data["channels"])
        differences.append(f'<bdi>{CHANNEL_PERIODS[index]}: {fmt(component_sum)} / {fmt(total["value"])}</bdi>')
    sources = "".join(f'<li><a href="{escape(row["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(row["label"][lang])} ↗</a></li>' for row in data["sources"])
    return wrapper(f'''<section class="losses-sources"><h2>{tr("notes", lang)}</h2>
      <p><b>{escape(data['source_file'])}</b> · {data['sheet']}</p><p>{tr('source_review', lang)}</p>
      <ul><li>{tr("period_note", lang)}</li><li>{tr("overlap_note", lang)}</li><li>{tr("estimate_note", lang)}</li>
      <li>{tr("rounding", lang)} ({tr("million", lang)}): {'; '.join(differences)}.</li>
      <li>{tr("gdp_revision", lang)}</li></ul>
      <h3>{tr("links", lang)}</h3><ul>{sources}</ul></section>''', lang)


def original_cells_html(data, lang):
    tables = []
    for sheet, cells in data.get("raw_sheets", {data["sheet"]: data["raw_cells"]}).items():
        rows = []
        for cell, value in cells.items():
            rows.append(f'<tr><th scope="row">{escape(cell)}</th><td dir="ltr">{escape(str(value)).replace(chr(10), "<br>")}</td></tr>')
        tables.append(f'<h3>{escape(sheet)}</h3><table class="losses-original"><thead><tr><th>{tr("cell", lang)}</th><th>{tr("original_value", lang)}</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')
    return wrapper(f'<p>{tr("original_language", lang)}</p>{"".join(tables)}', lang)


def show_economic_losses():
    data, lang = load_losses(), language()
    st.html(ROOT / "assets/economic-losses.css")
    with st.container(key="economic-losses"):
        title, sources = st.columns([3, 1], gap="small", vertical_alignment="center")
        with title:
            st.html(wrapper(f'<header class="losses-heading"><h1>{tr("title", lang)}</h1><p>{tr("intro", lang)}</p></header>', lang))
        with sources:
            with st.popover(tr("source_button", lang), width="stretch"):
                st.html(source_notes_html(data, lang))
                st.download_button(tr("download", lang), SOURCE.read_bytes(), file_name=data['source_file'],
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="economic_losses_xlsx")
        st.html(headline_html(data, lang))
        st.html(wrapper(f'<div class="losses-charts">{channels_html(data, lang)}{regions_html(data, lang)}</div>', lang))
        st.html(gdp_html(data, lang))
        st.html(sectors_html(data, lang))
        st.html(displacement_html(data, lang))
        with st.expander(tr("original", lang)):
            st.html(original_cells_html(data, lang))
