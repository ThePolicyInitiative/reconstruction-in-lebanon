"""Category overlap and misleading wording in real procurement contexts."""
import unittest
from integrated_tenders.categories import classify, CATEGORIES

def categories(title, summary='', buyer=''):
    return classify({'title':title,'summary':summary,'procuring_entity':buyer})['categories']

class TenderCategoryTests(unittest.TestCase):
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

if __name__=='__main__': unittest.main()
