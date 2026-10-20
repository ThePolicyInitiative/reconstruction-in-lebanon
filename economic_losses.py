"""Bilingual visual summary of the supplied economic-loss workbook."""
from html import escape
import json
from pathlib import Path

import streamlit as st

from i18n import language

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data/Economic_losses_war_AY.xlsx"

UI = {
    "title": ("Economic losses", "الخسائر الاقتصادية"),
    "intro": ("The cost of war across 2023–2024 and 2026", "كلفة الحرب خلال <bdi>2023–2024</bdi> و<bdi>2026</bdi>"),
    "source_button": ("Sources & workbook", "المصادر وملف البيانات"),
    "cost": ("Total economic cost", "الكلفة الاقتصادية الإجمالية"),
    "damage": ("Physical damage", "الأضرار المادية"),
    "losses": ("Economic losses", "الخسائر الاقتصادية"),
    "billion": ("billion", "مليار دولار"),
    "million": ("US$ million", "مليون دولار أميركي"),
    "estimate": ("Indicative estimate in workbook", "تقدير استرشادي في الملف"),
    "listed": ("Reported in workbook", "كما ورد في الملف"),
    "estimate_note": ("2026 totals are estimates. The workbook marks total cost and physical damage “NA” and provides these indicative ranges.", "إجماليات 2026 تقديرية. يضع الملف «غير متاح» للكلفة الإجمالية والأضرار المادية، ويورد هذه النطاقات الاسترشادية."),
    "housing": ("Housing damage", "أضرار المساكن"),
    "units": ("More than 100,000 housing units damaged", "تضررت أكثر من 100,000 وحدة سكنية"),
    "subset": ("Housing is included in physical damage.", "أضرار المساكن مشمولة ضمن الأضرار المادية."),
    "channels": ("Tourism & household losses", "خسائر السياحة والأسر"),
    "channels_note": ("The earlier column covers 2024 losses; 2026 figures are projections.", "يغطي العمود السابق خسائر 2024؛ وأرقام 2026 توقعات."),
    "reported_total": ("Total as listed", "الإجمالي الوارد"),
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
    "gdp_note": ("GDP values follow the workbook. The 2026 figures are projections; percentage-point losses are not dollar amounts.", "تتبع قيم الناتج المحلي الملف. أرقام 2026 توقعات، والخسائر بالنقاط المئوية ليست مبالغ مالية."),
    "notes": ("How to read these figures", "كيف تُقرأ هذه الأرقام؟"),
    "period_note": ("The workbook compares a 2023–2024 phase with 2026. It specifies that the earlier US$4.2 billion tourism-and-consumption figure relates to 2024 alone.", "يقارن الملف مرحلة 2023–2024 بعام 2026، ويوضح أن خسائر السياحة والاستهلاك السابقة البالغة 4.2 مليارات دولار تخص 2024 وحده."),
    "overlap_note": ("Physical damage and economic losses make up total economic cost. Housing, tourism, household and regional figures are breakdowns; do not add them again to the headline totals.", "تتكون الكلفة الاقتصادية من الأضرار المادية والخسائر الاقتصادية. أرقام المساكن والسياحة والأسر والمناطق تفصيلات ضمنها؛ لا تُضاف مجدداً إلى الإجماليات الرئيسية."),
    "rounding": ("Component sums differ slightly from the listed totals", "تختلف مجاميع المكونات قليلاً عن الإجماليات الواردة"),
    "rounding_kept": ("The website preserves both the component values and the original totals.", "يحافظ الموقع على قيم المكونات والإجماليات الأصلية معاً."),
    "gdp_revision": ("The workbook’s 2023 GDP value is −0.8%. The Summer 2026 World Bank report lists −0.5% for 2023; this page retains the supplied workbook’s −0.8% and its 1.0-point comparison.", "قيمة نمو 2023 في الملف هي ‎−0.8%. يورد تقرير البنك الدولي لصيف 2026 قيمة ‎−0.5% لعام 2023؛ تحتفظ هذه الصفحة بقيمة الملف ‎−0.8% وبفارق النقطة المئوية الواحدة."),
    "links": ("Source links listed in the workbook", "روابط المصادر الواردة في الملف"),
    "download": ("Download original Excel workbook", "تنزيل ملف إكسل الأصلي"),
    "original": ("Original cells & notes", "الخلايا والملاحظات الأصلية"),
    "original_language": ("Original workbook wording is preserved below in English.", "يُحفظ نص الملف الأصلي أدناه باللغة الإنجليزية."),
    "cell": ("Cell", "الخلية"),
    "original_value": ("Original value", "القيمة الأصلية"),
}


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


def headline_html(data, lang):
    cards = []
    for phase in data["phases"]:
        components = "".join(
            f'<div data-cell="{phase[key]["cell"]}"><span>{tr(key, lang)}</span><strong>{billions(phase[key], lang)}</strong></div>'
            for key in ("damage", "losses")
        )
        estimated = phase["total"]["estimated"]
        cards.append(f'''<article class="losses-phase {"losses-estimated" if estimated else ""}" data-period="{phase['period']}">
          <header><h2><bdi>{phase['period']}</bdi></h2><span>{tr("estimate" if estimated else "listed", lang)}</span></header>
          <p>{tr("cost", lang)}</p><strong class="losses-headline" data-cell="{phase['total']['cell']}">{billions(phase['total'], lang)}</strong>
          <div class="losses-components">{components}</div></article>''')
    housing = data["housing"]
    return wrapper(f'''<div class="losses-phases">{''.join(cards)}</div>
      <div class="losses-housing"><strong><bdi>${fmt(housing["damage_usd_m"] / 1000)}</bdi> {tr("billion", lang)}</strong>
        <div><b>{tr("housing", lang)} · <bdi>2023–2024</bdi></b><span>{tr("units", lang)}</span></div>
        <small>{tr("subset", lang)}</small></div>
      <p class="losses-note">{tr("estimate_note", lang)}</p>''', lang)


def bar(value, scale, style="", label=""):
    return f'<div class="losses-track" role="img" aria-label="{escape(label, quote=True)}"><span class="{style}" style="width:{value / scale * 100:.5f}%"></span></div>'


def channels_html(data, lang):
    scale = max(point["value"] for row in data["channels"] for point in row["values"])
    rows = []
    for row in data["channels"]:
        bars = []
        for index, point in enumerate(row["values"]):
            period = data["phases"][index]["period"]
            label = f'{period}: {fmt(point["value"])} {tr("million", lang)}'
            bars.append(f'''<div class="losses-pair" data-cell="{point['cell']}"><span><bdi>{period}</bdi></span>
              {bar(point["value"], scale, "losses-projection" if index else "", label)}
              <strong><bdi>{fmt(point['value'])}</bdi></strong></div>''')
        rows.append(f'<div class="losses-channel"><h3>{escape(row["label"][lang])}</h3>{"".join(bars)}</div>')
    totals = "".join(f'<div><span><bdi>{data["phases"][index]["period"]}</bdi></span><strong><bdi>{fmt(point["value"])}</bdi></strong></div>' for index, point in enumerate(data["channel_totals"]))
    return f'''<section class="losses-panel"><header><h2>{tr("channels", lang)}</h2><span>{tr("million", lang)}</span></header>
      <p class="losses-note">{tr("channels_note", lang)}</p>{''.join(rows)}
      <div class="losses-channel-totals"><b>{tr("reported_total", lang)}</b>{totals}</div></section>'''


def regions_html(data, lang):
    scale = max(row["value"] for row in data["regions"])
    rows = []
    for row in sorted(data["regions"], key=lambda value: -value["value"]):
        label = row["label"][lang]
        rows.append(f'''<div class="losses-region" data-cell="{row['cell']}"><div><span>{escape(label)}</span><strong><bdi>{fmt(row['value'])}</bdi></strong></div>
          {bar(row['value'], scale, label=f'{label}: {fmt(row["value"])} {tr("million", lang)}')}</div>''')
    return f'''<section class="losses-panel"><header><h2>{tr("regions", lang)}</h2><span>{tr("million", lang)}</span></header>
      <p class="losses-note">{tr("regional_period", lang)}</p>{''.join(rows)}
      <div class="losses-regional-total"><span>{tr("regional_total", lang)}</span><strong><bdi>{fmt(data["regional_total"]["value"])}</bdi></strong></div></section>'''


def gdp_html(data, lang):
    cards = []
    scale = max(row["lost_pp"] for row in data["gdp"])
    for row in data["gdp"]:
        baseline = f'<bdi>{row["no_war_pct"]:+.1f}%</bdi> {tr("no_war", lang)}' if row["no_war_pct"] is not None else tr("no_baseline", lang)
        projected = f'<span>{tr("projected", lang)}</span>' if row["projected"] else ""
        cards.append(f'''<article class="losses-gdp-card" data-year="{row['year']}"><header><h3>{row['year']}</h3>{projected}</header>
          <strong><bdi>{row['lost_pp']:.1f}</bdi><small>{tr("pp", lang)}</small></strong>
          {bar(row["lost_pp"], scale, "losses-projection" if row["projected"] else "", f'{row["year"]}: {row["lost_pp"]} {tr("pp", lang)}')}
          <p><bdi>{row['growth_pct']:+.1f}%</bdi> {tr("growth", lang)}</p><p class="losses-note">{baseline}</p></article>''')
    return wrapper(f'''<section class="losses-gdp"><header><h2>{tr("gdp", lang)}</h2><p>{tr("gdp_intro", lang)}</p></header>
      <div class="losses-gdp-grid">{''.join(cards)}</div><p class="losses-note">{tr("gdp_note", lang)}</p></section>''', lang)


def source_notes_html(data, lang):
    differences = []
    for index, total in enumerate(data["channel_totals"]):
        component_sum = sum(row["values"][index]["value"] for row in data["channels"])
        differences.append(f'<bdi>{data["phases"][index]["period"]}: {fmt(component_sum)} / {fmt(total["value"])}</bdi>')
    sources = "".join(f'<li><a href="{escape(row["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(row["label"][lang])} ↗</a></li>' for row in data["sources"])
    return wrapper(f'''<section class="losses-sources"><h2>{tr("notes", lang)}</h2>
      <p><b>{escape(data['source_file'])}</b> · {data['sheet']}</p>
      <ul><li>{tr("period_note", lang)}</li><li>{tr("overlap_note", lang)}</li><li>{tr("estimate_note", lang)}</li>
      <li>{tr("rounding", lang)} ({tr("million", lang)}): {'; '.join(differences)}. {tr("rounding_kept", lang)}</li>
      <li>{tr("gdp_revision", lang)}</li></ul>
      <h3>{tr("links", lang)}</h3><ul>{sources}</ul></section>''', lang)


def original_cells_html(data, lang):
    rows = []
    for cell, value in data["raw_cells"].items():
        rows.append(f'<tr><th scope="row">{escape(cell)}</th><td dir="ltr">{escape(str(value)).replace(chr(10), "<br>")}</td></tr>')
    return wrapper(f'''<p>{tr("original_language", lang)}</p><table class="losses-original"><thead><tr><th>{tr("cell", lang)}</th>
      <th>{tr("original_value", lang)}</th></tr></thead><tbody>{''.join(rows)}</tbody></table>''', lang)


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
                st.download_button(tr("download", lang), SOURCE.read_bytes(), file_name=SOURCE.name,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key="economic_losses_xlsx")
        st.html(headline_html(data, lang))
        st.html(wrapper(f'<div class="losses-charts">{channels_html(data, lang)}{regions_html(data, lang)}</div>', lang))
        st.html(gdp_html(data, lang))
        with st.expander(tr("original", lang)):
            st.html(original_cells_html(data, lang))
