"""A plain-language guide to the existing government research sources."""
from html import escape

from dashboard_data import display_date


GUIDE = {
    'wb_faq': ('Funding: what is available and what is still needed',
               'Explains the programme’s financing and funding gap.', 'Full page read.'),
    'cdr_faq': ('Responsibilities: who manages and checks the work',
                'Budgets are on page 2. Responsibilities are on page 4.', 'Official PDF read. No publication date is listed.'),
    'cdr_leap': ('Reconstruction plan: what the programme covers',
                 'Describes rubble removal, public services, designs and larger rebuilding works.', 'Full page read.'),
    'pm_leap': ('Nawaf Salam and the LEAP leadership',
                'Records a meeting with the officials responsible for the programme.', 'Only a search-engine excerpt of the official page could be read.'),
    'pm_cdr': ('Mohammad Ali Kabbani — CDR president',
               'Used to identify the president of the Council for Development and Reconstruction.', 'Only a search-engine excerpt of the official page could be read.'),
    'finance_minister': ('Yassine Jaber — Minister of Finance',
                         'Official biography identifying the minister.', 'Official biography read on 8 October 2026.'),
    'environment_minister': ('Tamara Elzein — Minister of Environment',
                             'Official account of discussions about LEAP’s environmental safeguards.', 'Official article read.'),
    'energy_minister': ('Joe Saddi — Minister of Energy and Water',
                        'Official report used to identify the minister.', 'Official article read.'),
    'education_minister': ('Rima Karami — Minister of Education',
                           'Official biography identifying the minister.', 'Only a search-engine excerpt of the official biography could be read.'),
    'health_minister': ('Rakan Nassereddine — Minister of Public Health',
                        'Official report used to identify the minister.', 'Official article and search-engine excerpt read.'),
    'mosa': ('Hanin Sayed and support for displaced families',
             'Official account of a visit to displaced families.', 'Only a search-engine excerpt of the official page could be read.'),
    'wb_rdna': ('National recovery needs: $11 billion',
                'Estimate for the 2023–2024 conflict. Later damage is not included.', 'Full page read.'),
    'committee': ('The government’s three recovery tracks',
                  'Family assistance; infrastructure and livelihoods; regional development.', 'Newspaper report of a ministerial committee statement.'),
    'un_update': ('Recovery priorities for late 2026',
                  'UN update covering return, shelter repairs and basic services.', 'Full page read.'),
    'mtv': ('Ministers discuss reconstruction work',
            'News coverage of plans for rubble removal, roads, services and studies.', 'News report read. Reported plans do not confirm that work has started.'),
    'roads': ('Nabatieh: clearing and repairing roads',
              'A notice inviting bids for road works.', 'Notice and deadline read. Evaluation status was not confirmed on the page.'),
    'esia': ('Environmental and social studies',
             'A notice inviting bids for studies, plans and audits under LEAP.', 'Notice read. A contract award or later progress was not confirmed.'),
    'procurement': ('Damaged public buildings: assessments and designs',
                    'A consultancy tender for assessments, rebuilding designs and supervision.', 'The page said “Under Evaluation” when reviewed. An award or completed work was not verified.'),
    'ppa': ('Public-building consultancy: locations and services',
            'Explains the areas and services covered by the public-building tender.', 'Full page read.'),
}


def sources_explained(data):
    sources = data['sources']

    def row(key):
        source = sources[key]
        title, purpose, checked = GUIDE.get(key, (source['title'], source.get('purpose', ''), source['access']))
        checked = source.get('review_note', checked)
        kind = {'Government':'Government source', 'Media':'News report'}.get(source['kind'], source['kind'])
        date = ('Source date: ' + display_date(source['date'])) if source['date'] else 'Publication date not listed'
        return f'''<article class="explained-source" data-source="{key}">
        <a href="{escape(source['url'], quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)} ↗</a>
        <p>{escape(purpose)}</p><div class="source-meta"><span>{escape(kind)}</span><span>{escape(source['publisher'])}</span><span>{escape(date)}</span></div>
        <p class="source-check">{escape(checked)}</p></article>'''

    groups = [
        ('Recent developments',
         'Dates distinguish announced plans, reported procurement and local recovery needs.',
         tuple(dict.fromkeys(item['source'] for item in data.get('updates', [])))),
        ('Names and official roles',
         'These records identify the people named above. Their LEAP responsibilities come from the programme documents in “Start here”.',
         ('pm_leap','pm_cdr','finance_minister','environment_minister','energy_minister','education_minister','health_minister','mosa')),
        ('The wider recovery plan',
         'Reconstruction also involves displaced families, jobs and local economies. These sources explain that wider context.',
         ('wb_rdna','committee','un_update','mtv')),
        ('Tender notices and preparatory work',
         'These notices show that services or works were put out to tender. A tender notice alone does not show that a contract was awarded or that rebuilding is finished.',
         ('roads','esia','procurement','ppa')),
    ]
    sections = ''.join(f'''<details class="source-group"><summary>{escape(title)}</summary><p class="source-group-intro">{escape(intro)}</p>{''.join(row(key) for key in keys)}</details>''' for title, intro, keys in groups)
    return f'''<section class="source-notes source-guide" id="sources">
    <p class="source-guide-intro">These links let you check the money, responsibilities and reconstruction plans shown above.</p>
    <div class="source-reading-guide">
      <div><h3>What do the amounts mean?</h3><p>They show financing approved or still needed. They do not tell us how much money has been spent or how much rebuilding is finished.</p></div>
      <div><h3>What do the roles mean?</h3><p>They describe who is meant to lead, manage or check the programme. The documents do not confirm that every project-team or monitoring post has been filled.</p></div>
      <div><h3>What period does this cover?</h3><p>The funding figures are dated {display_date(data['funding']['as_of'])}. The $11 billion national estimate covers the 2023–2024 conflict, excluding later damage.</p></div>
    </div>
    <p class="source-scope">This is a selected set of records about LEAP (Lebanon Emergency Assistance Project) and the wider government response. It is not a live progress report or a list of every reconstruction project.</p>
    <h3 class="source-start-title">Start here</h3><p>These three sources explain most of the infographic.</p>
    <div class="source-main-links">{''.join(row(key) for key in ('wb_faq','cdr_faq','cdr_leap'))}</div>
    <h3 class="source-more-title">Check a specific topic</h3>{sections}
    </section>'''
