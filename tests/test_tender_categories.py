"""Category overlap and misleading wording in real procurement contexts."""
import unittest
from integrated_tenders.categories import (classify, CATEGORIES, ANY_SUBJECT, NO_SUBJECT,
    ALL_PROGRAMMES, NO_LEAP, matches_subject, matches_programme, classify_recovery)

def categories(title, summary='', buyer=''):
    return classify({'title':title,'summary':summary,'procuring_entity':buyer})['categories']

class TenderCategoryTests(unittest.TestCase):
    def test_recovery_requires_context_and_actual_contract_scope(self):
        for title in ('Road maintenance', 'شراء محروقات لزوم الآليات والمولدات',
                      'LEAP procurement specialist', 'Financial Officer for LEAP water supply project',
                      'LEAP auction sale of electrical generators', 'Office supplies for Council for Development and Reconstruction'):
            with self.subTest(title=title):
                self.assertEqual(classify_recovery({'title': title})['recovery_subjects'], [])
        row = classify_recovery({'title': 'Road maintenance'})
        self.assertEqual(row['procurement_subjects'], ['Roads'])
        row = classify_recovery({'title': 'LEAP rehabilitation of damaged roads and drainage; rubble removal'})
        self.assertEqual(row['recovery_subjects'], ['Reconstruction', 'Roads', 'Electricity / water', 'Debris removal'])
        self.assertTrue(any(e['Category'] == 'Recovery link' for e in row['recovery_evidence']))
        # Repair of explicitly damaged roads is recovery work even where the war is not named.
        row = classify_recovery({'title': 'إعداد الدراسات وملفات التلزيم لأعمال إزالة العوائق وترميم الطرق المتضررة في قضاءي صور وبنت جبيل'})
        self.assertEqual(row['recovery_subjects'], ['Reconstruction', 'Roads'])
        row = classify_recovery({'title': 'أشغال تأهيل وصيانة طريق عاليه', 'summary': 'تعبيد وتزفيت الاجزاء المتضررة'})
        self.assertEqual(row['recovery_subjects'], [])

    def test_names_methods_and_vehicles_are_not_infrastructure(self):
        for title in ('تعيين السيدة فرح نبيه بري سفيرة لبنان', 'تحديد اصول وطرق استيفاء رسم دخول المسافرين',
                      'قطع غيار لزوم المديرية العامة للطرق والمباني', 'اعفاء السيارات الكهربائية الجديدة المستوردة',
                      'تحديد اجرة ايواء السيارات المحجوزة', 'تعيين رئيس واعضاء هيئة تنظيم قطاع الكهرباء'):
            with self.subTest(title=title): self.assertEqual(categories(title), [])
        self.assertIn('Electricity / water', categories('تأهيل قناة ري في البقاع'))
        self.assertIn('Damage assessment', categories('تشكيل لجنة للكشف على الاضرار الزراعية الناتجة عن العدوان'))

    def test_real_notices_keep_primary_scope_and_do_not_inherit_incidental_labels(self):
        import json
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        cases = {'12927': ['Reconstruction'], '12831': [], '12907': [], '12873': [], '9046': [],
                 '12530': ['Reconstruction', 'Roads'], '11833': ['Debris removal']}
        rows = json.loads((root/'integrated_tenders/data/dashboard.json').read_text(encoding='utf-8'))['tenders']
        lookup = {str(row['id']): row for row in rows}
        for identifier, expected in cases.items():
            with self.subTest(identifier=identifier):
                self.assertEqual(classify_recovery(lookup[identifier])['recovery_subjects'], expected)
        cdr = json.loads((root/'integrated_tenders/data/cdr/dashboard.json').read_text(encoding='utf-8'))['tenders']
        satellite = next(row for row in cdr if str(row['id']) == '1219')
        self.assertIn('Damage assessment', classify_recovery(satellite)['recovery_subjects'])
        self.assertNotIn('Debris removal', classify_recovery(satellite)['recovery_subjects'])

    def test_arabic_and_english_categories(self):
        cases={
            'LEAP': ['خدمات استشارية ضمن مشروع المساعدة الطارئة للبنان','LEAP project procurement specialist'],
            'Reconstruction':['تصميم إعادة إعمار المباني العامة','Rebuilding destroyed public buildings'],
            'Damage assessment':['توثيق الأضرار الناجمة عن الأعمال الحربية','Structural assessment of damaged public buildings'],
            'Roads':['أشغال تأهيل وصيانة شبكة الطرق','Road rehabilitation and bridge supervision'],
            'Electricity / water':['صيانة محطات ضخ المياه وشبكة الصرف الصحي','Repair of water distribution network and electrical generators'],
            'Shelter management':['إدارة مراكز إيواء النازحين وتجهيزها','Temporary accommodation and camp management services'],
            'Debris removal':['رفع الأنقاض ونقل نفايات الهدم','Debris sorting, hauling and rubble recycling'],
        }
        self.assertEqual(set(cases),set(CATEGORIES))
        for expected,texts in cases.items():
            for text in texts:
                with self.subTest(text=text): self.assertIn(expected,categories(text))

    def test_categories_overlap_without_duplicates_or_automatic_leap_reconstruction(self):
        row=classify({'title':'LEAP: rehabilitation of damaged roads and drainage; rubble removal',
                      'summary':'LEAP: rehabilitation of damaged roads and drainage; rubble removal'})
        self.assertEqual(row['categories'],['LEAP','Reconstruction','Roads','Electricity / water','Debris removal'])
        self.assertEqual(len(row['category_evidence']),5)
        self.assertEqual(categories('LEAP procurement specialist'),['LEAP'])

    def test_excluded_scope_institutions_and_place_names_are_not_categories(self):
        cases=[
            ('توريد قرطاسية لزوم مؤسسة كهرباء لبنان','','مؤسسة كهرباء لبنان'),
            ('Office furniture for Council for Development and Reconstruction','',''),
            ('شراء مياه معدنية معبأة','',''),
            ('التأهيل المسبق للمتعهدين','',''),
            ('تلزيم تأمين الآليات ضد أضرار جسدية','',''),
            ('Environmental and social impact assessment','',''),
            ('مساعدة أسر المواطنين الذين نزحوا','',''),
            ('Bus shelters for municipal transport','',''),
            ('Household waste collection excluding rubble and demolition waste','',''),
            ('معالجة النفايات المنزلية وغير المنزلية باستثناء الردميات وأغصان الأشجار','',''),
        ]
        for title,summary,buyer in cases:
            with self.subTest(title=title): self.assertEqual(categories(title,summary,buyer),[])
        self.assertEqual(categories('أشغال تأهيل وصيانة شبكة الطرق',
                                    'بيت منذر - محطة الكهرباء - طريق المدافن والماوي في المتين'),['Roads'])

    def test_saved_subject_evidence_and_new_records_use_the_same_rules(self):
        row={'title':'Consulting services','program_evidence':[{'source':'Lot title','text':'Lebanon Emergency Assistance Project'}]}
        self.assertEqual(classify(row)['categories'],['LEAP'])
        self.assertNotIn('categories',row,'classification must not mutate the feed')
        # A legacy flag without supporting text cannot manufacture a category.
        self.assertEqual(classify({'title':'Office supplies','reconstruction_related':True})['categories'],[])

    def test_saved_arabic_project_wording_is_recognized_without_matching_addresses(self):
        for title in ('مشروع تأهيل وتوسعة طريق تنورين التحتا',
                      'مشروع شق وصلة طريق بعبدات – المتين',
                      'دراسة جدوى بهدف إنشاء نفق لطريق بيروت - البقاع'):
            with self.subTest(title=title): self.assertIn('Roads', categories(title))
        for title in ('حفر وتجهيز بئر مياه في بلدة دير نبوح',
                      'تأهيل قسطل المياه الرئيسي العائد لمعمل رشميا',
                      'مشروع زيادة إمدادات المياه الى بيروت الكبرى',
                      'تعديل مسار كابلات 66 ك.ف. غاز - بصاليم'):
            with self.subTest(title=title): self.assertIn('Electricity / water', categories(title))
        self.assertEqual(categories('تأهيل مدرسة الطريق الجديدة الثالثة للبنات'), [])
        self.assertEqual(categories('توريد مياه معدنية معبأة'), [])

    def test_programme_and_subject_filters_are_independent(self):
        consultant = classify({'title':'LEAP procurement specialist'})
        road = classify({'title':'LEAP road rehabilitation'})
        self.assertEqual(consultant['recovery_subjects'], [])
        self.assertEqual(consultant['programmes'], ['LEAP'])
        self.assertTrue(matches_subject(consultant['categories'], NO_SUBJECT))
        self.assertFalse(matches_subject(consultant['categories'], ANY_SUBJECT))
        self.assertTrue(matches_subject(road['categories'], 'Roads'))
        self.assertTrue(matches_programme(road['categories'], 'LEAP'))
        self.assertFalse(matches_programme(road['categories'], NO_LEAP))
        self.assertTrue(matches_programme([], NO_LEAP))
        self.assertTrue(matches_programme([], ALL_PROGRAMMES))

if __name__=='__main__': unittest.main()
