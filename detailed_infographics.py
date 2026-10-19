"""Detailed, source-linked diagrams for the curated government response."""
from html import escape

def financing_coverage(data, source_link):
    """Each bar has its own component total as denominator; amounts stay visible."""
    rows = []
    for row in data["allocations"]:
        financed = row["available_m"] / row["total_m"] * 100
        percent = f"{financed:.1f}".removesuffix(".0")
        rows.append(f'''<div class="coverage-row">
        <div class="coverage-label"><span>{escape(row['code'])}</span><strong>{escape(row['label'])}</strong></div>
        <div class="coverage-visual"><div class="coverage-bar" role="img" aria-label="{escape(row['label'])}: {percent}% financed, ${row['available_m']} million available, ${row['gap_m']} million gap, ${row['total_m']} million total"><span style="width:{financed:.4f}%"></span></div><small>{percent}% of this component financed</small></div>
        <div class="coverage-amount available"><small>Available</small>${row['available_m']}M</div>
        <div class="coverage-amount missing"><small>Gap</small>${row['gap_m']}M</div>
        <div class="coverage-amount"><small>Total</small>${row['total_m']}M</div></div>''')
    available = data["funding"]["approved_usd"] / 1e6
    gap = data["funding"]["gap_usd"] / 1e6
    total = data["funding"]["framework_usd"] / 1e6
    return f'''<section class="coverage-board"><div class="detail-heading"><div><span class="kicker">COMPONENT BY COMPONENT</span><h3>The full financing picture</h3></div><div class="coverage-key"><span><i></i>Available financing</span><span><i class="gap-key"></i>Financing gap</span></div></div>
    <div class="coverage-header"><span>Programme component</span><span>Share of its own total · each bar = 100%</span><span>Available</span><span>Gap</span><span>Total</span></div>
    {''.join(rows)}<div class="coverage-total"><span>Total LEAP framework</span><div><span><small>Available</small>${available:,.0f}M</span><span><small>Gap</small>${gap:,.0f}M</span><span><small>Total</small>${total:,.0f}M</span></div></div>
    <div class="under-figure">Bars compare financing coverage, not component size or work completed. Figures are the 17 February 2026 snapshot. {source_link}</div></section>'''


