"""Build the bilingual, evidence-coded political graph dataset.

Null is unknown, never neutral. No MP or minister inherits a party position.
The party layer explicitly identifies the speakers whose statements it uses.
Re-run after reviewing new statements or updating the saved official rosters.
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTIES = ROOT / 'imported' / 'parties'
ROSTER_REVIEWED = '2026-10-16'
PARTY_LIST = 'https://en.wikipedia.org/w/index.php?title=List_of_political_parties_in_Lebanon&oldid=1375638110'
MP_LIST = 'https://lp.gov.lb/Members'
CABINET = 'https://pcm.gov.lb/arabic/subpg.aspx?pageid=13587'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(filename):
    return [line.split('|') for line in (ROOT / 'data' / filename).read_text(encoding='utf-8').splitlines() if line.strip()]


def bilingual(en, ar):
    return {'en': en, 'ar': ar}


def position(value, refs, en, ar):
    return {'value': value, 'sources': refs.split(), 'reason': bilingual(en, ar)}


def build():
    archive = read_json(PARTIES / 'reconstruction-statements.json')
    catalog = read_json(ROOT / 'locales' / 'ar.json')
    actors = {a['id']: a for a in archive['actors']}
    sources = {}
    for s in archive['statements']:
        actor = actors[s['actor']]
        sources[s['id']] = {
            'id': s['id'], 'actor': s['actor'], 'date': s['date'], 'url': s['url'],
            'speaker': bilingual(actor['name'], catalog.get(actor['name'], actor['name'])),
            'publisher': bilingual(s['source'], catalog.get(s['source'], s['source'])),
            'summary': bilingual(s['summary'], catalog.get(s['summary'], s['summary'])),
        }

    def source(id, actor, name, name_ar, date, url, publisher, publisher_ar, en, ar):
        sources[id] = dict(id=id, actor=actor, speaker=bilingual(name, name_ar), date=date,
                           url=url, publisher=bilingual(publisher, publisher_ar), summary=bilingual(en, ar))

    source('HQ-ARMS', 'hezbollah', 'Naim Qassem', 'نعيم قاسم', '2025-04-18', sources['HQ-02']['url'],
           'The National', 'ذا ناشيونال',
           'Qassem opposed disarming Hezbollah and said defence-strategy talks would require Israeli withdrawal. This arms position is separately documented from his rejection of an arms-for-reconstruction trade.',
           'رفض قاسم نزع سلاح حزب الله وربط مناقشة الاستراتيجية الدفاعية بالانسحاب الإسرائيلي. هذا موقف موثق من السلاح، منفصل عن رفضه مقايضة الإعمار بنزع السلاح.')
    source('TM-01', 'mitri', 'Tarek Mitri', 'طارق متري', '2025-10-13', 'https://www.alanba.com.kw/1327968/',
           'Al-Anbaa — direct interview', 'الأنباء — مقابلة مباشرة',
           'Mitri supported state control of arms through a phased army plan without armed confrontation. He described a reconstruction fund supported by Arab and international contributions, and a World Bank loan awaiting approval at the time.',
           'أيد متري حصر السلاح بيد الدولة عبر خطة مرحلية للجيش من دون صدام مسلح. ووصف صندوق إعمار يقوم على الدعم العربي والدولي وقرضاً من البنك الدولي كان ينتظر الإقرار آنذاك.')
    source('YJ-01', 'jaber', 'Yassine Jaber', 'ياسين جابر', '2025-11-07',
           'https://www.pcm.gov.lb/arabic/subpg.aspx?pageid=26512', 'Presidency of the Council of Ministers', 'رئاسة مجلس الوزراء',
           'Jaber urged Parliament to approve the reconstruction loan as a basis for a larger infrastructure fund. The statement supports international public financing; it does not establish his personal arms position.',
           'دعا جابر مجلس النواب إلى إقرار قرض إعادة الإعمار كأساس لصندوق أوسع للبنى التحتية. يوثق التصريح تأييد التمويل العام الدولي ولا يحدد موقفه الشخصي من السلاح.')
    source('MH-01', 'helou', 'Michel Helou', 'ميشال حلو', '2025-11-15',
           'https://www.nationalbloc.org/national_bloc_political_program_discussions', 'National Bloc — party conference', 'الكتلة الوطنية — مؤتمر الحزب',
           'Helou called for state control of arms and described reconstruction, Israeli withdrawal and the return of southern residents as state responsibilities. No reconstruction financing source was specified in that passage.',
           'دعا حلو إلى حصر السلاح بيد الدولة وعدّ الإعمار والانسحاب الإسرائيلي وإعادة أهل الجنوب مسؤوليات للدولة. لم يحدد المقطع مصدراً لتمويل الإعمار.')

    # Categorical editorial coding; each axis has its own direct evidence.
    codes = {}
    def code(actor, reconstruction=None, arms=None, financing=None):
        codes[actor] = dict(reconstruction=reconstruction, arms=arms, financing=financing)
    p = position
    code('hezbollah', p(3,'HQ-03','Announces a housing contribution and calls for state compensation.','يعلن مساهمة سكنية ويطالب بتعويضات من الدولة.'),
         p(1,'HQ-ARMS','Defends retaining Hezbollah’s weapons; negotiations are conditional.','يدافع عن الاحتفاظ بسلاح حزب الله ويضع شروطاً للحوار.'),
         p(2,'HQ-01 HQ-03','Combines party assistance, donations and calls for state responsibility.','يجمع بين مساعدات الحزب والتبرعات ومطالبة الدولة بمسؤولياتها.'))
    code('fadlallah', p(3,'HF-02 HF-04','Specifies structural repairs, infrastructure and shelter support.','يحدد ترميم الأبنية والبنية التحتية ودعم الإيواء.'), None,
         p(2,'HF-03 HF-04','Seeks public budget support alongside a party shelter programme.','يطلب دعماً من الموازنة العامة إلى جانب برنامج إيواء حزبي.'))
    code('fayyad', p(3,'AF-02','Names surveys, rubble clearance and restoration of basic services.','يسمي المسوحات ورفع الأنقاض واستعادة الخدمات الأساسية.'), None,
         p(1,'AF-02','Proposes using available treasury resources before foreign aid arrives.','يقترح استخدام موارد الخزينة المتاحة قبل وصول المساعدات الخارجية.'))
    code('amal', p(2,'NB-02','Calls for urgent state follow-up and resources for rebuilding.','يطالب بمتابعة عاجلة من الدولة وتأمين موارد للإعمار.'))
    code('khalil', p(2,'AK-02','Calls for rebuilding without delay or political prices.','يدعو إلى الإعمار من دون تأخير أو أثمان سياسية.'))
    code('inaya', p(3,'IE-01 IE-02','Calls for an education emergency plan and rapid school repairs.','تدعو إلى خطة طوارئ تربوية والإسراع في ترميم المدارس.'))
    code('lf', p(1,'SG-03','Supports reconstruction while stating state-authority prerequisites.','يؤيد الإعمار مع وضع شروط تتعلق بسلطة الدولة.'),
         p(3,'SG-01 SG-03','Calls for exclusive legitimate arms control and one army.','يدعو إلى حصرية السلاح الشرعي وجيش واحد.'))
    code('hasbani', p(1,'GH-02','Supports rebuilding through restored investment and external support.','يؤيد الإعمار عبر استعادة الاستثمار والدعم الخارجي.'),
         p(3,'GH-01 GH-02','Treats resolving non-state weapons as necessary for recovery.','يعد معالجة السلاح خارج الدولة شرطاً للتعافي.'),
         p(3,'GH-01 GH-02','Seeks foreign investment and support, including an Iranian contribution.','يطلب استثمارات ودعماً خارجياً، بما في ذلك مساهمة إيرانية.'))
    code('bouassi', p(1,'PB-01','Supports recovery through state authority.','يؤيد التعافي عبر سلطة الدولة.'), None,
         p(3,'PB-01','Calls for international rebuilding aid through official state channels.','يدعو إلى مرور المساعدات الدولية للإعمار عبر قنوات الدولة الرسمية.'))
    code('fpm', p(2,'GB-02','Calls for reconstruction to proceed regardless of political disputes.','يدعو إلى استمرار الإعمار بمعزل عن الخلافات السياسية.'),
         p(2,'GB-01','Supports state arms control with reciprocal national gains.','يؤيد حصر السلاح بالدولة مع مكاسب وطنية متبادلة.'))
    code('atallah', p(3,'GA-01','Demands a specific reconstruction budget allocation.','يطالب باعتماد محدد للإعمار في الموازنة.'), None,
         p(1,'GA-01','Explicitly calls for a reconstruction line in the state budget.','يطالب صراحة ببند للإعمار في موازنة الدولة.'))
    code('kataeb', p(1,'SM-02','Supports reconstruction within a sovereignty-first argument.','يؤيد الإعمار ضمن طرح يعطي الأولوية للسيادة.'),
         p(3,'SM-01 SM-02','Calls for ending independent militia weapons.','يدعو إلى إنهاء السلاح المستقل للميليشيات.'),
         p(3,'SM-01','Seeks international support conferences and assistance.','يدعو إلى مؤتمرات دعم ومساعدات دولية.'))
    code('sayegh', p(1,'SS-01','Supports recovery through restoring external confidence.','يؤيد التعافي عبر استعادة الثقة الخارجية.'),
         p(3,'SS-01','Calls for armed structures to become civilian political institutions.','يدعو إلى تحويل البنى المسلحة إلى مؤسسات سياسية مدنية.'),
         p(3,'SS-01','Discusses foreign support and the progress partners expect.','يناقش الدعم الخارجي والتقدم الذي ينتظره الشركاء.'))
    code('hankach', p(3,'EH-01','Proposes a transparent fund and clear grant-management mechanism.','يقترح صندوقاً شفافاً وآلية واضحة لإدارة المنح.'),
         p(3,'EH-02','Places state sovereignty and arms control before reconstruction.','يضع سيادة الدولة وحصر السلاح قبل الإعمار.'),
         p(3,'EH-01','Proposes transparent administration of grants.','يقترح إدارة شفافة للمنح.'))
    code('timour', p(2,'TJ-02','Names return and reconstruction among national priorities.','يضع العودة والإعمار ضمن الأولويات الوطنية.'),
         p(3,'TJ-02','Explicitly supports exclusive state arms control.','يؤيد صراحة حصر السلاح بيد الدولة.'),
         p(3,'TJ-01','Welcomes international reconstruction support and a donor conference.','يرحب بالدعم الدولي للإعمار وبمؤتمر للمانحين.'))
    code('tony', p(2,'TF-01','Calls for return and the start of rebuilding as priorities.','يدعو إلى اعتبار العودة وبدء الإعمار من الأولويات.'))
    code('hariri', p(1,'SH-01','Describes rebuilding and livelihoods as a collective responsibility.','يصف الإعمار واستعادة سبل العيش بالمسؤولية الجماعية.'))
    code('gharib', p(2,'HG-01','Demands rapid rebuilding and adequate compensation.','يطالب بإعمار سريع وتعويضات كافية.'))
    code('hardan', p(2,'AH-02','Calls on government to begin reconstruction.','يدعو الحكومة إلى بدء الإعمار.'))
    code('chamoun', p(1,'CC-01','Supports rebuilding under rule of law.','يؤيد الإعمار في ظل سيادة القانون.'),
         p(3,'CC-01 CC-02','Advocates disarmament and army-led weapons collection.','يدعو إلى نزع السلاح وجمعه بقيادة الجيش.'),
         p(3,'CC-01','Discusses promised investment for reconstruction.','يناقش الاستثمارات الموعودة للإعمار.'))
    code('hout', p(1,'IH-01','Supports rebuilding within a wider recovery agenda.','يؤيد الإعمار ضمن برنامج أوسع للنهوض.'), None,
         p(3,'IH-01','Expects Arab and Gulf assistance; this is an expectation, not a pledge.','يتوقع مساعدات عربية وخليجية؛ وهو توقع وليس تعهداً تمويلياً.'))
    code('terzian', p(2,'HT-02','Prioritises rebuilding the South and residents’ return.','يعطي الأولوية لإعمار الجنوب وعودة الأهالي.'), None,
         p(3,'HT-02','Calls for a central international role in rebuilding.','يدعو إلى دور دولي أساسي في الإعمار.'))
    code('daou', p(2,'MD-02','Calls for reconstruction efforts to continue alongside reform.','يدعو إلى مواصلة جهود الإعمار بالتوازي مع الإصلاح.'), None,
         p(3,'MD-01','Calls for Arab and international support for government recovery tasks.','يدعو إلى دعم عربي ودولي لمهام الحكومة في النهوض.'))
    code('karami', p(2,'FK-01 FK-02','Calls for rebuilding the South and fair regional development.','يدعو إلى إعمار الجنوب والإنماء المتوازن بين المناطق.'),
         p(3,'FK-02','Explicitly calls for weapons held solely by the state.','يدعو صراحة إلى حصر السلاح بالدولة.'))
    code('mrad', p(2,'HM-02','Demands an immediate start outside political bargaining.','يطالب بالبدء الفوري خارج المساومات السياسية.'))
    code('saad', p(3,'OS-02','Demands reconstruction and return commitments in the budget.','يطالب بالتزامات للإعمار والعودة في الموازنة.'), None,
         p(1,'OS-02','Seeks domestic budget commitments and questions the political cost of foreign aid.','يطلب التزامات من الموازنة ويحذر من الكلفة السياسية للمساعدات الخارجية.'))
    code('makhzoumi', p(3,'FM-01','Specifies state implementation, transparency and independent oversight.','يحدد التنفيذ عبر الدولة والشفافية والرقابة المستقلة.'),
         p(2,'FM-01','Links arms control to coordinated withdrawal and return.','يربط حصر السلاح بتنسيق الانسحاب والعودة.'))
    code('najaat', p(3,'NA-01','Proposes opening cement imports and lowering customs costs.','تقترح فتح استيراد الإسمنت وخفض الرسوم الجمركية.'))
    code('salam', p(3,'NS-04','Announces rehabilitation tenders and named recovery measures.','يعلن مناقصات للتأهيل وخطوات محددة للتعافي.'),
         p(2,'NS-02 NS-05','Supports a state arms monopoly with reciprocal, parallel implementation.','يؤيد حصرية السلاح بالدولة مع تنفيذ متبادل ومتوازٍ.'),
         p(2,'NS-04 NS-05','Uses available state resources while seeking external reconstruction support.','يستخدم الموارد العامة المتاحة ويسعى إلى دعم خارجي للإعمار.'))
    code('raggi', p(1,'YR-01','Supports recovery while describing external political requirements.','يؤيد التعافي ويعرض متطلبات سياسية خارجية.'),
         p(3,'YR-01','Endorses exclusive state weapons control north and south of the Litani.','يؤيد حصرية السلاح بيد الدولة شمال الليطاني وجنوبه.'),
         p(3,'YR-01','Discusses conditions reported for international reconstruction assistance.','يناقش شروطاً منقولة للمساعدات الدولية للإعمار.'))
    code('mitri', p(3,'TM-01','Describes an independent reconstruction fund and infrastructure financing.','يصف صندوقاً مستقلاً للإعمار وتمويل البنية التحتية.'),
         p(2,'TM-01','Supports a phased army plan and avoids armed confrontation.','يؤيد خطة مرحلية للجيش وتجنب الصدام المسلح.'),
         p(3,'TM-01','Seeks Arab and international contributions and World Bank financing.','يسعى إلى مساهمات عربية ودولية وتمويل من البنك الدولي.'))
    code('jaber', p(3,'YJ-01','Advocates a specific infrastructure loan and larger reconstruction fund.','يدعو إلى قرض محدد للبنى التحتية وصندوق أوسع للإعمار.'), None,
         p(3,'YJ-01','Supports World Bank financing for damaged infrastructure.','يؤيد تمويل البنك الدولي للبنية التحتية المتضررة.'))
    code('helou', p(2,'MH-01','Places rebuilding and residents’ return among state responsibilities.','يضع الإعمار وعودة الأهالي ضمن مسؤوليات الدولة.'),
         p(3,'MH-01','Calls for the state to recover control over weapons.','يدعو الدولة إلى استعادة السيطرة على السلاح.'))

    mp_actors = {'15':'fadlallah','115':'fayyad','1':'amal','108':'khalil','280':'inaya','372':'hasbani',
                 '330':'bouassi','302':'fpm','376':'atallah','113':'kataeb','367':'sayegh','327':'hankach',
                 '326':'timour','296':'tony','394':'chamoun','82':'hout','307':'terzian','393':'daou',
                 '289':'karami','357':'mrad','344':'saad','313':'makhzoumi','390':'najaat'}
    representatives = {'hezbollah':'hezbollah','amal':'amal','lf':'lf','fpm':'fpm','kataeb':'kataeb',
                       'psp':'timour','marada':'tony','future':'hariri','lcp':'gharib','ssnp':'hardan',
                       'nlp':'chamoun','jamaa':'hout','tashnag':'terzian','taqaddom':'daou','karama':'karami',
                       'union':'mrad','pno':'saad','dialogue':'makhzoumi','nationalbloc':'helou'}
    # Reviewed additions are merged axis by axis. An absent axis stays unknown;
    # a personal statement is never inferred from another speaker's position.
    additions = read_json(ROOT / 'data' / 'political_positions_additions.json')
    for ref, statement in additions['sources'].items():
        assert ref not in sources, ref
        sources[ref] = statement
    for actor, positions in additions['codes'].items():
        codes.setdefault(actor, dict(reconstruction=None, arms=None, financing=None)).update(positions)
    mp_actors.update(additions['mpActors'])
    representatives.update(additions['representatives'])
    empty = dict(reconstruction=None, arms=None, financing=None)
    entities = []
    def entity(id, layer, name, name_ar, role, role_ar, url, actor=None):
        entry = dict(id=id, layer=layer, name=bilingual(name, name_ar), role=bilingual(role, role_ar),
                     rosterUrl=url, actorIds=[actor] if actor else [], positions=copy.deepcopy(codes.get(actor, empty)))
        entities.append(entry)
        return entry

    for id, name, ar in lines('political_party_register.tsv'):
        actor = representatives.get(id)
        row = entity('party-'+id, 'parties', name, ar, 'Party / political movement', 'حزب / حركة سياسية', PARTY_LIST, actor)
        row.update(copy.deepcopy(additions.get('partyDetails', {}).get(id, {})))
        if id == 'projectwatan': row['rosterUrl'] = 'https://projectwatan.com/ar/من-نحن'
        # Do not pretend one speaker describes every party member or faction.
        if actor:
            speaker = next(s['speaker'] for s in sources.values() if s['actor'] == actor)
            row['scope'] = bilingual('Based on statements by '+speaker['en']+'.', 'بناءً على تصريحات '+speaker['ar']+'.')
            if id in additions.get('partyScopes', {}):
                row['scope'] = additions['partyScopes'][id]
        if id == 'lf':
            row['positions']['financing'] = copy.deepcopy(codes['hasbani']['financing'])
            row['actorIds'].append('hasbani')
            row['scope'] = bilingual('Based on Samir Geagea and Ghassan Hasbani; individual MPs are assessed separately.', 'بناءً على تصريحات سمير جعجع وغسان حاصباني؛ يُقيّم كل نائب بشكل منفصل.')
        if id == 'amal':
            row['positions']['financing'] = copy.deepcopy(codes['khalil']['financing'])
            row['actorIds'].append('khalil')
            row['scope'] = bilingual('Reconstruction: Nabih Berri. Public funding: Ali Hassan Khalil. Individual MPs are assessed separately.', 'الإعمار: نبيه بري. التمويل العام: علي حسن خليل. يُقيّم كل نائب بشكل منفصل.')
        if id == 'fpm':
            row['positions']['financing'] = copy.deepcopy(codes['atallah']['financing'])
            row['actorIds'].append('atallah')
            row['scope'] = bilingual('Arms and reconstruction: Gebran Bassil. Budget allocation: Ghassan Atallah.', 'السلاح والإعمار: جبران باسيل. اعتماد الموازنة: غسان عطالله.')
        if id == 'ssnp':
            row['scope'] = bilingual('Asaad Hardan’s statements only; other SSNP currents are not represented by this placement.', 'تصريحات أسعد حردان فقط؛ لا يمثل هذا التصنيف سائر تيارات الحزب.')

    names = dict(lines('political_mp_names.tsv'))
    roster = read_json(ROOT / 'data' / 'political_mp_roster.json')
    assert len(roster) == 128 and len({r['id'] for r in roster}) == 128
    assert set(names) == {r['id'] for r in roster}
    regions = {'بيروت':'Beirut','جبل لبنان':'Mount Lebanon','الشمال':'North','البقاع':'Bekaa','الجنوب':'South'}
    for mp in roster:
        entity('mp-'+mp['id'], 'deputies', names[mp['id']], mp['name_ar'],
               'MP · '+regions[mp['region_ar']], 'نائب · '+mp['region_ar'], mp['url'], mp_actors.get(mp['id']))
    ministers = lines('political_ministers.tsv')
    assert len(ministers) == 24
    for id, name, ar, role, role_ar in ministers:
        entity('minister-'+id, 'ministers', name, ar, role, role_ar, CABINET, id)

    category_coding = read_json(ROOT / 'data' / 'political_specific_categories.json')
    category_ids = {axis: {c['id'] for c in definitions} for axis, definitions in category_coding['axes'].items()}
    used_bundles = {axis: set() for axis in category_ids}
    symbols = read_json(ROOT / 'data' / 'political_party_symbols.json')
    portraits = read_json(ROOT / 'data' / 'political_person_photos.json')
    for row in entities:
        if row['id'] in symbols:
            row['symbol'] = symbols[row['id']]
            if row['symbol'].get('path'):
                assert (PARTIES / row['symbol']['path']).is_file(), row['id']
            else:
                assert row['symbol'].get('status') == 'unverified' and row['symbol'].get('label'), row['id']
        if row['id'] in portraits:
            row['portrait'] = portraits[row['id']]
            assert (PARTIES / row['portrait']['path']).is_file(), row['id']
        row['statementIds'] = [s['id'] for s in sources.values() if s['actor'] in row['actorIds']]
        for axis, pos in row['positions'].items():
            if pos:
                assert pos['value'] in (1,2,3) and pos['sources']
                # A new evidence bundle needs explicit review; never infer a finer
                # category from party membership, a keyword or the legacy score.
                bundle = ' '.join(sorted(pos['sources']))
                assert bundle in category_coding['assignments'][axis], (row['id'], axis, 'Category review needed', bundle)
                pos['category'] = category_coding['assignments'][axis][bundle]
                assert pos['category'] in category_ids[axis]
                used_bundles[axis].add(bundle)
                for ref in pos['sources']:
                    assert ref in sources, (row['id'], axis, ref)
                    assert sources[ref]['actor'] in row['actorIds'], (row['id'], ref)
    for axis, bundles in used_bundles.items():
        assert bundles == set(category_coding['assignments'][axis]), (axis, 'Unused category coding')
    # Topic claims are non-exclusive and tied to named actors, never membership.
    review = read_json(ROOT / 'data' / 'political_topic_review.json')
    for ref, statement in review['sources'].items():
        assert ref not in sources, ref
        sources[ref] = statement
    by_id = {row['id']: row for row in entities}
    for identifier, actors_to_add in review['actorBindings'].items():
        assert identifier in by_id, identifier
        by_id[identifier]['actorIds'] += [a for a in actors_to_add if a not in by_id[identifier]['actorIds']]
    for row in entities:
        row['stances'] = {axis: [copy.deepcopy(pos)] if pos else [] for axis, pos in row['positions'].items()}
    for claim in review['claims']:
        axis = claim['axis']
        assert claim['category'] in category_ids[axis]
        assert claim['sources'] and all(claim['reason'].values())
        for identifier in claim['entities']:
            row = by_id[identifier]
            for ref in claim['sources']:
                assert ref in sources and sources[ref]['actor'] in row['actorIds'], (identifier, ref)
            if not any(p['category'] == claim['category'] and p['sources'] == claim['sources'] for p in row['stances'][axis]):
                row['stances'][axis].append({k: copy.deepcopy(claim[k]) for k in ('category', 'sources', 'reason')})
    for row in entities:
        row['statementIds'] = list(dict.fromkeys(row['statementIds'] + [ref for ps in row['stances'].values() for p in ps for ref in p['sources']]))
    output = dict(reviewed=max(additions['reviewed'], review['reviewed']), rosterReviewed=ROSTER_REVIEWED,
                  topicReview=review['reviewed'], topicReviewNote=review['note'],
                  categories=category_coding['axes'], categoryMethod=category_coding['method'], categoriesReviewed=category_coding['reviewed'],
                  statementsReviewed=additions['reviewed'], archiveReviewed=archive['checked'], entities=entities, sources=sources,
                  rosterSources={'deputies':MP_LIST,'ministers':CABINET,'parties':PARTY_LIST},
                  rosterMethod='MPs: 128 region-populated entries in the official directory, cross-checked against the saved names. Cabinet: 24 members on the official government roster. Party directory: all non-defunct entries in the cited list, existing archive and Project Watan. No completeness claim for Lebanon’s legal register; activity of minor movements is not individually reverified.')
    (PARTIES / 'positions.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print({layer:sum(e['layer']==layer for e in entities) for layer in ('parties','deputies','ministers')})
    return output


if __name__ == '__main__':
    build()
