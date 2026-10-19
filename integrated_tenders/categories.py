"""Website categories derived from saved notice text; no changes to the monitor."""
from __future__ import annotations

import re
import unicodedata
from .tender_analytics import ARABIC_PREFIX, COMPILED_RULES, PREQUALIFICATION, normalize

CATEGORIES = ('LEAP', 'Reconstruction', 'Damage assessment', 'Roads',
              'Electricity / water', 'Shelter management', 'Debris removal')
VERSION = 2
DEFINITIONS = {
    'LEAP': 'An explicit LEAP or Lebanon Emergency Assistance Project reference. A programme link can cover consulting, equipment or works.',
    'Reconstruction': 'Explicit rebuilding, or repairs to damaged assets linked to war or LEAP. Routine repairs alone are not reconstruction.',
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
    'Damage assessment': [r'(?:تقييم|تقدير|حصر|مسح|توثيق|كشف)\s+(?:حجم\s+)?(?:ال)?(?:اضرار|تضرر)',
                          r'\bdamage\s+(?:and\s+needs\s+)?(?:assessment|survey|mapping|evaluation|documentation)s?\b',
                          r'\b(?:assessment|survey|mapping|evaluation|documentation)\s+of\s+(?:(?:the|war|structural)\s+)*damage\b',
                          r'\bevaluation\s+des\s+dommages\b'],
    'Roads': [ar(r'طرقات|طرق|اوتوستراد(?:ات)?|جسور|تزفيت|اسفلت|تعبيد'),
              r'(?:اشغال|صيانة|تاهيل|انشاء|ترميم|توسيع|تحسين|تعبيد|تصميم|تنفيذ|شق)\s+(?:واعادة\s+تاهيل\s+)?(?:ال)?(?:طرق|طريق|جسر)(?!\w)',
              r'(?:شبكة|شبكات|مشاريع|مشروع)\s+(?:ال)?طرق(?!\w)',
              r'\b(?:roads?|roadworks?|highways?|bridges?|asphalt|paving|pavements?)\b',
              r'\b(?:routier(?:e|es|s)?|routes?|chaussee|ponts?)\b'],
    'Electricity / water': [ar(r'كهرباء|كهربائية|كهربائي|كهربا[ئي]ية|مولدات|مولد|انارة|كهربا|كهربائيه'),
                            r'(?:شبك(?:ة|ات)|خطوط|خط|محط(?:ة|ات)|مضخ(?:ة|ات)|ضخ|توزيع|تغذية|تكرير|معالجة|تنقية|خزان(?:ات)?|تخزين|جر|عدادات|توفير|تزويد|توصيل)\s+(?:ل?ل?مياه|ال?مياه)',
                            r'(?:مياه\s+(?:الشفة|الشرب|الصرف)|صرف\s+صحي|الصرف\s+الصحي)',
                            ar(r'اقنية|مجارير|ري|تصريف|فوتوفولطية|كهروضوئية'),
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
                    r'عن\s+طريق',r'طرق\s+(?:الدفع|التقديم|تقديم|الطعن)']:
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
            if category=='Reconstruction' and not match and (COMPILED_RULES['war'].search(text) or
                    leap and re.search(r'متضرر|تضرر|مدمر|\b(?:damaged|destroyed)\b',text)):
                match=COMPILED_RULES['rehabilitation'].search(text)
            if match:
                evidence[category]={'Category':category,'Source field':label,'Matched wording':match[0],
                                    'Evidence':text[max(0,match.start()-90):match.end()+180]}
    categories=[category for category in CATEGORIES if category in evidence]
    return {**row,'categories':categories,'category_evidence':[evidence[c] for c in categories],
            'category_version':VERSION}
