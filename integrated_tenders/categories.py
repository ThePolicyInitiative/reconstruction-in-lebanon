"""Website categories derived from saved notice text; no changes to the monitor."""
from __future__ import annotations

import re
import unicodedata
from .tender_analytics import ARABIC_PREFIX, COMPILED_RULES, PREQUALIFICATION, TOPIC_RULES, normalize

CATEGORIES = ('LEAP', 'Reconstruction', 'Damage assessment', 'Roads',
              'Electricity / water', 'Shelter management', 'Debris removal')
SUBJECTS = CATEGORIES[1:]
ANY_SUBJECT = 'Any recovery subject'
NO_SUBJECT = 'No recovery subject match'
ALL_PROGRAMMES = 'All programmes'
NO_LEAP = 'No explicit LEAP reference'
VERSION = 5
DEFINITIONS = {
    'LEAP': 'An explicit LEAP or Lebanon Emergency Assistance Project reference. A programme link can cover consulting, equipment or works.',
    'Reconstruction': 'Explicit rebuilding, or repairs to damaged assets linked to war or LEAP. Measures for property destroyed or damaged by war also count. Routine repairs alone are not reconstruction.',
    'Damage assessment': 'Damage surveys, documentation, or structural assessments of affected buildings and infrastructure.',
    'Roads': 'Road, bridge, paving and asphalt works, including their design, supervision and maintenance.',
    'Electricity / water': 'Power supply, generators, lighting, water networks, irrigation, drainage and wastewater infrastructure.',
    'Shelter management': 'Temporary accommodation, collective shelters and displacement-camp services. Displacement wording alone is not enough.',
    'Debris removal': 'Rubble clearance, hauling, sorting, recycling and disposal of demolition or construction debris. Ordinary household waste is excluded.',
}

def ar(words):
    return ARABIC_PREFIX + '(?:' + words + r')(?!\w)'

RULES = {
    'LEAP': [r'\bleap\b', r'\blebanon\s+emergency\s+assistance\s+project\b',
             r'مشروع\s+(?:الدعم|المساعدة|المساعدات)\s+الطار[ئيءة]+\s+للبنان'],
    'Reconstruction': [r'اعاد[ةه]\s+(?:(?:ال)?اعمار|(?:ال)?بناء)',
                       r'\breconstruction\b', r'\b(?:rebuild(?:ing|s)?|rebuilt)\b'],
    'Damage assessment': [r'(?:تقييم|تقدير|حصر|مسح|توثيق|كشف)\s+(?:(?:علي|عن)\s+)?(?:حجم\s+)?(?:ال)?(?:اضرار|تضرر)',
                          r'\bdamage\s+(?:and\s+needs\s+)?(?:assessment|survey|mapping|evaluation|documentation)s?\b',
                          r'\b(?:assessment|survey|mapping|evaluation|documentation)\s+of\s+(?:(?:the|war|structural)\s+)*damage\b',
                          r'\bevaluation\s+des\s+dommages\b'],
    'Roads': [ar(r'طرقات|طرق|اوتوستراد(?:ات)?|جسور|تزفيت|اسفلت|تعبيد'),
              r'(?:مشروع|مشاريع|وصلة|توسعة|توسيع|تاهيل|صيانة|انشاء|شق|تخطيط)\s+(?:و(?:توسعة|توسيع|تاهيل|صيانة)\s+)?(?:ال)?طريق(?!\w)',
              r'نفق\s+ل(?:ل?طريق)(?!\w)',
              r'(?:اشغال|صيانة|تاهيل|انشاء|ترميم|توسيع|تحسين|تعبيد|تصميم|تنفيذ|شق)\s+(?:واعادة\s+تاهيل\s+)?(?:ال)?(?:طرق|طريق|جسر)(?!\w)',
              r'(?:شبكة|شبكات|مشاريع|مشروع)\s+(?:ال)?طرق(?!\w)',
              r'\b(?:roads?|roadworks?|highways?|bridges?|asphalt|paving|pavements?)\b',
              r'\b(?:routier(?:e|es|s)?|routes?|chaussee|ponts?)\b'],
    'Electricity / water': [ar(r'كهرباء|كهربائية|كهربائي|كهربا[ئي]ية|مولدات|مولد|انارة|كهربا|كهربائيه'),
                            r'(?:امدادات|انظمة|قناة|قسطل|قساطل|انابيب|فلاتر|ابار|بئر|سدود)\s+(?:ال)?مياه(?!\w)',
                            r'مياه\s+(?:الامطار|مبتذلة|المبتذلة)(?!\w)',
                            r'\bwater\s+(?:supplies|mains?|systems?|dams?)\b',
                            r'كابلات\s+\d+\s*ك\.?\s*ف',
                            r'(?:شبك(?:ة|ات)|خطوط|خط|محط(?:ة|ات)|مضخ(?:ة|ات)|ضخ|توزيع|تغذية|تكرير|معالجة|تنقية|خزان(?:ات)?|تخزين|جر|عدادات|توفير|تزويد|توصيل)\s+(?:ل?ل?مياه|ال?مياه)',
                            r'(?:مياه\s+(?:الشفة|الشرب|الصرف)|صرف\s+صحي|الصرف\s+الصحي)',
                            ar(r'اقنية|مجارير|تصريف|فوتوفولطية|كهروضوئية'),
                            # "بري" is a surname and "by land": irrigation needs the bare word or an article.
                            r'(?<!\w)و?(?:ال|لل|بال)?ري(?!\w)',
                            r'(?:الطاقة\s+(?:الشمسية|الكهربائية)|الواح\s+شمسية)',
                            r'\b(?:electricity|electrical|power\s+(?:supply|plant|grid|distribution|generation)|generators?|street\s*lighting|solar\s+(?:panels?|power|energy)|photovoltaic|sewage|sewers?|wastewater|irrigation|drainage)\b',
                            r'\bwater\s+(?:supply|network|distribution|treatment|pumping|pump|reservoir|tank|pipe|infrastructure|well)s?\b',
                            r'\b(?:electricite|eau\s+potable|assainissement)\b'],
    'Shelter management': [ar(r'ايواء|ملاجئ'), r'(?:مراكز|مركز|اماكن|مكان)\s+(?:ال)?(?:نزوح|ايواء)',
                           r'(?:سكن|اسكان|اقامة)\s+(?:ال)?(?:موقت|مؤقت|طارئ|طارئة)',
                           r'(?:مخيمات|خيم|خيام)\s+(?:ال)?(?:نازحين|لاجئين)',
                           r'\b(?:shelters?|temporary\s+(?:housing|accommodation)|(?:displacement|refugee|idp)\s+camps?|camp\s+(?:management|coordination))\b',
                           r'\b(?:hebergement\s+(?:temporaire|d.urgence)|centres?\s+d.accueil)\b'],
    'Debris removal': [ar(r'انقاض|ركام|ردميات'), r'(?:نفايات|مخلفات)\s+(?:ال)?(?:بناء|هدم|انفجار)',
                       r'\b(?:debris|rubble)\b', r'\b(?:construction|demolition)\s+(?:and\s+(?:demolition|construction)\s+)?waste\b',
                       r'\b(?:decombres|gravats)\b'],
}
COMPILED = {key: re.compile('|'.join(rules), re.I) for key, rules in RULES.items()}
DAMAGED = r'متضرر|تضرر|مدمر|مهدم|هدمت|\b(?:damaged|destroyed)\b'
WAR = re.compile(COMPILED_RULES['war'].pattern + '|' + ARABIC_PREFIX
                 + r'اعتداء(?:ات)?\s+(?:ال)?اسرائيلي[ةه]?(?!\w)', re.I)
# "Repair of damaged roads" names recovery work even where the notice omits the war.
REPAIR_OF_DAMAGE = re.compile('(?:' + '|'.join(TOPIC_RULES['rehabilitation'])
                              + r')[^.؛;\n]{0,80}?(?:' + DAMAGED + ')', re.I)
ASSESSMENT = re.compile(r'تقييم|مسح|كشف|\b(?:assessment|survey|inspection)\b')
DAMAGED_ASSET = re.compile(r'(?:مباني|ابنية|جسور|بنية تحتية).{0,100}(?:متضرر|مدمر)|\b(?:damaged|affected)\s+(?:public\s+)?(?:buildings?|infrastructure|bridges?)\b')

def category_normalize(text):
    latin = ''.join(unicodedata.normalize('NFKD', c) if '\u00c0' <= c <= '\u024f' else c for c in str(text or ''))
    return normalize(''.join(c for c in latin if not unicodedata.combining(c)))

def clean(text, buyer=''):
    text = category_normalize(text)
    # Named agencies, funding institutions and bidder eligibility are not works.
    for name in str(buyer or '').split('·'):
        name = category_normalize(name)
        if len(name) > 5:
            text = text.replace(name, ' ' * len(name))
    for pattern in [r'council\s+for\s+development\s+(?:and|&)\s+reconstruction',
                    r'(?:international|european)\s+bank\s+for\s+reconstruction\s+(?:and|&)\s+development',
                    r'electricite\s+du\s+liban',r'مؤسسة\s+كهرباء\s+لبنان',
                    r'مؤسسة\s+مياه\s+(?:بيروت\s+وجبل\s+لبنان|لبنان\s+(?:الشمالي|الجنوبي)|البقاع)',
                    r'ر(?:اغب|غاب)\s+حرب',r'(?:electronic|electrical)\s+(?:tendering|procurement)',
                    r'\b(?:bottled|mineral)\s+water\b',r'مياه\s+(?:معدنية|معباة)',
                    r'\b(?:bus|animal)\s+shelters?\b',
                    r'(?:باستثناء|ما عدا|excluding|except\s+for)\s+[^.،؛;\n]{0,180}',
                    r'محطة\s+الكهرباء\s*[-–—]',
                    r'المديريات\s+العامة\s+للموارد\s+المائية\s+والكهربائية',
                    r'عن\s+طريق',r'طرق\s+(?:وكيفية\s+)?(?:الدفع|التقديم|تقديم|الطعن|استيفاء|تادية)',
                    # Directorates, regulators, methods, vehicles and impound fees are not works.
                    r'العامة\s+للطرق\s+والمباني',r'(?:ال|لل)?موارد\s+المائية\s+والكهربائية',
                    r'تنظيم\s+قطاع\s+الكهرباء',
                    r'(?:ال|لل)طرق\s+(?:الكيميائية|الميكانيكية|الثقافية)',
                    r'(?:سيارات|مركبات|اليات|دراجات(?:\s+الالية)?|سلالم|مصاعد|محرك)\s+(?:ال)?كهربائي[ةه]?',
                    r'تعمل\s+على\s+الكهرباء',r'ايواء\s+(?:ال)?(?:سيارات|اليات|مركبات)']:
        text = re.sub(pattern, lambda m:' '*len(m[0]), text)
    return PREQUALIFICATION.sub(lambda m:' '*len(m[0]), text)

def fragments(row):
    candidates = [('Title',row.get('title','')),('Summary',row.get('summary',''))]
    # Preserve useful lot/subject evidence already supplied by the monitor.
    candidates += [(item.get('source','Saved source text'),item.get('text',''))
                   for field in ('topic_evidence','program_evidence') for item in row.get(field,[])]
    seen=set()
    for label,text in candidates:
        key=normalize(text)
        if key and key not in seen:
            seen.add(key)
            yield label,text

def classify(row):
    evidence={}
    texts=[(label,clean(text,row.get('procuring_entity',''))) for label,text in fragments(row)]
    leap=any(COMPILED['LEAP'].search(text) for _,text in texts)
    for label,text in texts:
        for category,rule in COMPILED.items():
            if category in evidence:
                continue
            match=rule.search(text)
            if category=='Damage assessment' and not match and ASSESSMENT.search(text):
                match=DAMAGED_ASSET.search(text)
            if category=='Reconstruction' and not match:
                if WAR.search(text) or leap and re.search(DAMAGED,text):
                    match=COMPILED_RULES['rehabilitation'].search(text)
                match=match or REPAIR_OF_DAMAGE.search(text)
            if match:
                evidence[category]={'Category':category,'Source field':label,'Matched wording':match[0],
                                    'Evidence':text[max(0,match.start()-90):match.end()+180]}
    categories=[category for category in CATEGORIES if category in evidence]
    return {**row,'categories':categories,
            'recovery_subjects':[c for c in categories if c in SUBJECTS],
            'programmes':['LEAP'] if 'LEAP' in categories else [],
            'category_evidence':[evidence[c] for c in categories],
            'category_version':VERSION}


def matches_subject(categories, subject):
    """Programme membership alone does not establish a recovery work subject."""
    subjects = set(categories) & set(SUBJECTS)
    if subject == ANY_SUBJECT:
        return bool(subjects)
    if subject == NO_SUBJECT:
        return not subjects
    return subject in categories


def matches_programme(categories, programme):
    return (programme == ALL_PROGRAMMES or
            programme == 'LEAP' and 'LEAP' in categories or
            programme == NO_LEAP and 'LEAP' not in categories)


ADMINISTRATIVE = re.compile(r'\b(?:financial\s+officer|procurement\s+specialist|accounting\s+software|financial\s+audit|forensic\s+audit|third\s+party\s+monitoring|compliance\s+monitoring)\b|برنامج\s+محاسب|مدقق\s+حسابات|تدقيق\s+(?:جنائي|مالي)|خبير\s+(?:مالي|في\s+المشتريات)|ادار[ةي]\s+مالية|مراجعة\s+وتدقيق\s+واعداد\s+التقارير')
DISPOSAL_OR_FUEL = re.compile(r'\b(?:auction|sale\s+of|fuel|diesel|gasoline)\b|(?:لبيع|بيع)\s+(?:خردة|مولد|اليات)|محروقات|مازوت|بنزين')
BUILDING_SCOPE = re.compile(r'مدارس|مدرسة|منشات\s+تربوية|قسم\s+(?:القسطرة|العناية)|\b(?:schools?|hospital\s+ward|medical\s+equipment)\b')
SATELLITE_SCOPE = re.compile(r'صور\s+اقمار\s+صناعية|\bsatellite\s+(?:imagery|images?)\b')
TELECOM_SCOPE = re.compile(r'\b(?:cell\s+on\s+wheels|cows|lte[- ]a[- ]cpes)\b|اجهزة\s+انتهائية\s+لاسلكية')


def classify_recovery(row):
    """Separate a procurement sector from evidence that it serves recovery.

    General sector detection remains available in exports. Tender and Gazette
    recovery labels require context and follow the stated scope.
    """
    result = classify(row)
    texts = [(label, clean(text, row.get('procuring_entity', ''))) for label, text in fragments(row)]
    title = clean(row.get('title', ''), row.get('procuring_entity', ''))
    primary = classify({'title': row.get('title', ''), 'procuring_entity': row.get('procuring_entity', ''),
                        'topic_evidence': [item for item in row.get('topic_evidence', [])
                                           if 'lot' in item.get('source', '').lower()]})
    subjects = list(primary['recovery_subjects'])
    # A named building contract must not acquire utility labels from ancillary repairs.
    if not subjects and not BUILDING_SCOPE.search(title):
        subjects = list(result['recovery_subjects'])
    if 'Reconstruction' in result['recovery_subjects'] and 'Reconstruction' not in subjects:
        subjects.insert(0, 'Reconstruction')
    if SATELLITE_SCOPE.search(title) and 'Damage assessment' in subjects:
        subjects = ['Damage assessment']
    if TELECOM_SCOPE.search(title):
        subjects = []
    contexts = []
    for label, text in texts:
        match = (COMPILED['LEAP'].search(text) or WAR.search(text) or COMPILED['Reconstruction'].search(text)
                 or REPAIR_OF_DAMAGE.search(text))
        if match:
            contexts.append({'Category': 'Recovery link', 'Source field': label,
                             'Matched wording': match[0],
                             'Evidence': text[max(0, match.start()-90):match.end()+180]})
    # Buying fuel, selling assets and project administration do not perform these works.
    if not contexts or ADMINISTRATIVE.search(title) or DISPOSAL_OR_FUEL.search(title):
        subjects = []
    result['procurement_subjects'] = result['recovery_subjects']
    result['recovery_subjects'] = [subject for subject in SUBJECTS if subject in subjects]
    result['recovery_evidence'] = ([e for e in result['category_evidence'] if e['Category'] in subjects]
                                   + contexts) if subjects else []
    return result
