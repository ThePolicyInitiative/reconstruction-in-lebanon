"""Sourced institutions, operational responsibilities and planned assurance layers."""
from html import escape as esc

from dashboard_data import display_date
from visuals import icon


def ministry_network(data, link):
    people = {person['initials']: person for person in data['people']}
    cards = []
    for ministry in data['governance']['technical_ministries']:
        person = people[ministry['initials']]
        source_date = display_date(data['sources'][person['source']]['date'])
        cards.append(f'''<article class="ministry-card"><div class="ministry-sector">{icon(ministry['icon'],23,'#137066')}<span>{esc(ministry['sector'])}</span></div>
        <h4>{link(person['source'], person['name'])}</h4><span class="ministry-arabic" lang="ar" dir="rtl">{esc(person['arabic'])}</span><p class="ministry-office">{esc(person['role'])}</p>
        <div class="ministry-focus"><span>SECTOR INPUT</span><strong>{esc(ministry['focus'])}</strong></div><small class="official-evidence">Name source · {source_date}</small></article>''')
    return f'''<section class="ministry-board"><div class="detail-heading"><div><span class="kicker">TECHNICAL MINISTRIES · COMPONENTS 2 & 3</span><h3>Who defines the sector needs?</h3></div><span class="governance-tag">Advisory & technical roles</span></div>
    <div class="ministry-grid">{''.join(cards)}</div><div class="ministry-handoff"><div><span>01</span><strong>Identify urgent needs</strong></div><b aria-hidden="true">→</b><div><span>02</span><strong>Help specify the intervention</strong></div><b aria-hidden="true">→</b><div><span>03</span><strong>CDR manages implementation</strong></div></div>
    <div class="under-figure">These ministries provide strategic and technical advice in prioritised areas. Institutional mandate: {link('wb_faq', 'World Bank FAQ, section 8')}.</div>
    <div class="household-note">{icon('family',25,'#a35c47')}<p><strong>Hanin Sayed also leads the Social Affairs Ministry's response to displaced families.</strong> Temporary shelter and assistance sit within the broader recovery strategy. {link('mosa','Ministry record')} · {link('committee','Committee statement')}</p></div>
    <div class="local-roles"><div><span>CNRS-L</span><p>Provides the damage data used for prioritisation.</p></div><div><span>Lebanese Army</span><p>Clearance of explosive remnants is an eligibility condition.</p></div><div><span>Municipalities & communities</span><p>Contribute local needs and concerns through consultation.</p></div></div>
    <div class="under-figure">Local inputs and eligibility: {link('wb_faq','FAQ, sections 3, 5 & 13')}.</div></section>'''


def implementation_and_assurance(data, link):
    duties = ''.join(f'''<div class="pmu-duty">{icon(item['icon'],25,'#a9d4c3')}<strong>{esc(item['title'])}</strong><p>{esc(item['detail'])}</p></div>''' for item in data['governance']['project_unit'])
    checks = ''.join(f'''<article class="assurance-card"><div class="assurance-top"><span>{item['number']}</span>{icon(item['icon'],27,'#137066')}</div><h4>{esc(item['title'])}</h4><div class="assurance-appointment">{esc(item['engaged_by'])}</div><p>{esc(item['detail'])}</p><div class="assurance-output"><span>EXPECTED OUTPUT</span><strong>{esc(item['output'])}</strong></div></article>''' for item in data['governance']['assurance'])
    return f'''<section class="operations-board"><div class="detail-heading"><div><span class="kicker">INSIDE THE IMPLEMENTING AGENCY</span><h3>Who runs the work day to day?</h3></div><span class="governance-tag">Published management structure</span></div>
    <div class="pmu-reporting"><div><span>CDR PRESIDENT + BOARD</span><strong>{link('pm_cdr','Mohammad Ali Kabbani')} & the Board</strong></div><div class="reports-up"><b aria-hidden="true">↑</b><span>receives reports from the project unit</span></div></div>
    <div class="pmu-panel"><div class="pmu-title"><span class="kicker">CDR · PROJECT MANAGEMENT UNIT</span><h4>One unit coordinates all four components.</h4></div><div class="pmu-duties">{duties}</div></div>
    <div class="under-figure">Mandate and staffing arrangements: {link('wb_faq','FAQ, sections 8, 11 & 12')}. This diagram describes the required structure; it does not confirm that every post has been filled.</div>
    <div class="assurance-heading"><span class="kicker">SUPERVISION, VERIFICATION & ACCOUNTABILITY</span><h3>Who checks the work and the spending?</h3><p>Monitoring arrangements specified in the published framework. Individual appointments are not verified here.</p></div>
    <div class="assurance-grid">{checks}</div><div class="reporting-cadence"><div><strong>Quarterly</strong><span>CDR progress, financial and safeguards reporting</span></div><div><strong>Annually</strong><span>Independent audit of project financial statements</span></div><div><strong>Within 48 hours</strong><span>CDR reports significant incidents to the World Bank</span></div></div>
    <div class="under-figure">Oversight and reporting requirements: {link('wb_faq','World Bank FAQ, sections 9, 11 & 12')} · {link('cdr_faq','CDR published framework')}.</div></section>'''
