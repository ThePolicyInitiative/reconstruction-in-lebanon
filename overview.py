"""A compact, source-linked infographic of Lebanon's government response."""
from html import escape

from dashboard_data import display_date
from visuals import icon


def government_overview(data):
    people = {person['initials']: person for person in data['people']}
    funding = data['funding']
    covered = funding['approved_usd'] / funding['framework_usd'] * 100
    allocations = {row['code']: row for row in data['allocations']}

    def source(key, label):
        record = data['sources'][key]
        return f'<a href="{escape(record["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(label)}<span aria-hidden="true"> ↗</span></a>'

    def name(initials):
        person = people[initials]
        return source(person['source'], person['name'])

    allocation_rows = ''.join(
        f'<div class="allocation-line"><span><i style="background:{allocations[code]["color"]}"></i><span><b>{label}</b><small>{escape(allocations[code]["detail"])}</small></span></span><strong>${allocations[code]["available_m"]}M</strong></div>'
        for code, label in [('C2', 'Public services'), ('C1', 'Immediate response'), ('C3a', 'Reconstruction designs'), ('C4', 'Management')]
    )
    ministry_rows = ''.join(
        f'<div class="sector-person">{icon(ministry["icon"],19,"#176c61")}<div><strong>{name(ministry["initials"])}</strong><span>{escape(ministry["sector"])}</span><small>{escape(ministry["focus"])}</small></div></div>'
        for ministry in data['governance']['technical_ministries']
    )
    unit_tasks = ''.join(f'<span>{icon(symbol,15,"#176c61")}{label}</span>' for symbol, label in [
        ('people', 'Daily coordination'), ('oversight', 'Contracts & procurement'),
        ('fund', 'Budgets & expenditure'), ('shield', 'Environmental & social risks'),
    ])
    checks = ''.join(f'<div><strong>{title}</strong><p>{detail}</p></div>' for title, detail in [
        ('Engineering supervision', 'Checks work quality, timing, costs and safeguards.'),
        ('Independent monitoring', 'Cross-checks activities and spending through visits, imagery and records.'),
        ('World Bank checks', 'Reviews procurement, eligible transactions and reported results.'),
    ])
    stages = [
        ('01', 'Make areas safe', ['Clear rubble and address unsafe buildings.', 'Reopen roads and restore emergency access.', 'Help schools used as shelters return to teaching.'], 'CDR implements · Environment oversees rubble', 'shield', '#af5d37'),
        ('02', 'Restore services', ['Repair water, energy and transport networks.', 'Restore health facilities and education services.', 'Recover essential municipal services.'], 'CDR + sector ministries', 'services', '#137066'),
        ('03', 'Rebuild', ['Prepare engineering studies and detailed designs.', 'Rebuild severely damaged public infrastructure.', 'Apply resilient standards to reduce future risks.'], 'Major works depend on further financing', 'building', '#ba3037'),
    ]
    stage_cards = ''.join(f'''<article class="stage" style="--stage-color:{color}"><div class="stage-top"><span>{number}</span>{icon(symbol,25,color)}</div><h3>{title}</h3><ul>{''.join(f'<li>{task}</li>' for task in tasks)}</ul><small>{owner}</small></article>''' for number, title, tasks, owner, symbol, color in stages)
    updates = ''.join(f'''<article><span class="update-date">{escape(item['status'])}</span><strong>{escape(item['value'])}</strong><h3>{escape(item['title'])}</h3><p>{escape(item['detail'])}</p><div class="delivery-result"><span>Documented outcome</span><p>{escape(item['delivery_evidence'])}</p></div>{source(item['source'], item['link_label'])}</article>''' for item in data.get('updates', []))
    accountability = [
        ('PRIME MINISTER', 'NS', 'Provides overall strategic guidance.', 'Reported tenders issued and further tenders planned.', 'Project-level starts and completed works are not established by the speech.', 'nabatieh_oct'),
        ('PUBLIC WORKS & TRANSPORT', 'FR', 'Ministry leads oversight of LEAP execution.', 'Implementation plans discussed in the reviewed reporting.', 'Work on site and completed services need separate verification.', 'mtv'),
        ('CDR PRESIDENT', 'MK', 'Heads the agency implementing all four programme components.', 'Road works and consultancy procurement are documented; one road contract is reported awarded.', 'Verified start, contractor and completion evidence remain outstanding in the reviewed road record.', 'roads'),
        ('ENVIRONMENT', 'TE', 'Oversees rubble work and environmental & social safeguards across LEAP.', 'Environmental and social studies were put to tender.', 'Award and delivery of the consultancy are not established in the reviewed record.', 'esia'),
        ('FINANCE MINISTER', 'YJ', 'Consulted on the programme’s direction.', 'The programme assigns a consultation role.', 'This role does not establish disbursements or actual expenditure.', 'cdr_faq'),
    ]
    accountability_rows = ''.join(f'''<article class="accountability-row"><div class="accountability-owner"><span>{role}</span><h3>{name(initials)}</h3><p>{duty}</p></div><div><span class="accountability-label">Documented commitment / action</span><p>{action}</p>{source(key, 'Supporting record')}</div><div class="accountability-gap"><span class="accountability-label">Evidence still needed</span><p>{gap}</p></div></article>''' for role, initials, duty, action, gap, key in accountability)

    return f'''<article class="overview" aria-label="Government response infographic">
    <div class="overview-title"><h1>What has the government actually rebuilt?</h1><p>Lebanon Emergency Assistance Project <strong>LEAP</strong></p></div>
    <section class="recent-progress" aria-label="Announcements versus delivery"><div class="recent-heading"><h2>Announcements versus delivery</h2></div><p class="evidence-intro">Announcements, financing and procurement do not establish completed reconstruction. These outcomes reflect the reviewed records, not a complete inventory of works.</p><div class="progress-grid">{updates}</div></section>
    <div class="overview-main"><section class="funding-panel" id="funding"><div class="panel-title"><span>01</span><h2>The funding</h2></div>
    <div class="funding-context">${funding['framework_usd']/1e9:g} billion programme framework</div>
    <div class="funding-numbers"><div><strong>${funding['approved_usd']/1e6:,.0f}<em>M</em></strong><span>initial financing</span></div><div class="funding-gap"><strong>${funding['gap_usd']/1e6:,.0f}<em>M</em></strong><span>financing gap</span></div></div>
    <div class="coverage-bar" role="img" aria-label="{covered:.0f}% financed, {100-covered:.0f}% financing gap"><span style="width:{covered}%"></span></div><div class="coverage-labels"><span>{covered:.0f}% financed</span><span>{100-covered:.0f}% gap</span></div>
    <div class="allocation-heading">WHERE THE INITIAL FINANCING GOES</div><div class="allocation-list">{allocation_rows}</div>
    <div class="works-gap"><strong>${allocations['C3b']['available_m']}M</strong><p>initial allocation for major rebuilding works</p></div>
    <div class="works-needed"><strong>${allocations['C3b']['gap_m']}M needed</strong> for these works — part of the ${funding['gap_usd']/1e6:,.0f}M gap above.</div>
    <div class="funding-source">Initial World Bank financing approved in June 2025.<br>{source('wb_faq',display_date(funding['as_of']) + ' · funding snapshot')}<br>Allocations do not measure spending or completed work.</div></section>
    <section class="responsibility-panel" id="responsibility"><div class="panel-title"><span>02</span><h2>Who is accountable?</h2></div>
    <p class="evidence-intro">Responsibilities identify who must answer for delivery. Missing verification is not proof that no work occurred.</p>
    <div class="accountability-list">{accountability_rows}</div>
    <details class="accountability-requirements"><summary>Programme requirements & sector responsibilities</summary>
    <p>These are assigned duties and required checks; their completion is not established here.</p>
    <div class="project-unit"><div class="unit-heading"><strong>CDR project unit</strong><span>Reports to the CDR president and Board</span></div><div class="unit-tasks">{unit_tasks}</div></div>
    <div class="sector-label">SECTOR MINISTRIES · NEEDS & TECHNICAL INPUT</div><div class="sector-grid">{ministry_rows}</div>
    <p class="sector-duty">Help identify urgent needs and set technical specifications for services and rebuilding.</p>
    <div class="oversight-note"><div class="check-heading"><strong>REQUIRED CHECKS</strong>{source('cdr_faq','Roles & oversight')}</div><div class="checks-grid">{checks}</div><p class="reporting"><strong>Every quarter:</strong> progress, financial & safeguard reports. <strong>Every year:</strong> independent audit.</p></div></details>
    <div class="cdr-definition">CDR = Council for Development and Reconstruction.</div></section></div>
    <section class="stages-panel" id="stages"><div class="panel-title"><span>03</span><h2>The reconstruction path</h2><small>Stages can overlap</small></div><div class="stage-path">{stage_cards}</div>
    <div class="stage-source">{source('cdr_leap','Official programme stages')}<span>Public infrastructure is one part of the wider government recovery response.</span></div></section></article>'''
