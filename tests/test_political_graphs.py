"""Checks against omissions and unsupported political positions."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/'imported/parties/positions.json').read_text(encoding='utf-8'))


class PoliticalGraphTests(unittest.TestCase):
    def test_specific_categories_are_reviewed_against_exact_axis_evidence(self):
        coding = json.loads((ROOT/'data/political_specific_categories.json').read_text(encoding='utf-8'))
        self.assertEqual([len(DATA['categories'][a]) for a in ('reconstruction','arms','financing')], [9,8,10])
        for entity in DATA['entities']:
            for axis, position in entity['positions'].items():
                if position is None:
                    continue
                key = ' '.join(sorted(position['sources']))
                self.assertEqual(position['category'], coding['assignments'][axis][key])
                self.assertIn(position['category'], {c['id'] for c in DATA['categories'][axis]})
        for categories in DATA['categories'].values():
            for category in categories:
                for field in ('label','description','examples'):
                    self.assertTrue(category[field]['en'])
                    self.assertRegex(category[field]['ar'], r'[\u0600-\u06ff]')

    def test_every_official_mp_and_minister_is_included(self):
        roster = json.loads((ROOT/'data/political_mp_roster.json').read_text(encoding='utf-8'))
        deputies = [e for e in DATA['entities'] if e['layer'] == 'deputies']
        self.assertEqual(len(deputies), 128)
        self.assertEqual({e['id'] for e in deputies}, {'mp-'+mp['id'] for mp in roster})
        ministers = [e for e in DATA['entities'] if e['layer'] == 'ministers']
        self.assertEqual(len(ministers), 24)
        self.assertIn('minister-salam', {e['id'] for e in ministers})
        # Finance minister is not mistakenly substituted for the elected Jaber.
        self.assertIn('mp-396', {e['id'] for e in deputies})
        self.assertNotIn('minister-jaber', {e['id'] for e in deputies})

    def test_existing_and_non_parliamentary_parties_are_kept(self):
        archive = json.loads((ROOT/'imported/parties/reconstruction-statements.json').read_text(encoding='utf-8'))
        ids = {e['id'] for e in DATA['entities'] if e['layer'] == 'parties'}
        for party in archive['parties']:
            if party['id'] not in ('officials', 'external'):
                self.assertIn('party-'+party['id'], ids)
        self.assertTrue({'party-mmfd','party-nationalbloc','party-ldp','party-hunchak','party-sabaa','party-projectwatan'} <= ids)

    def test_no_inherited_or_unsourced_personal_positions(self):
        sources = DATA['sources']
        for e in DATA['entities']:
            for axis, p in e['positions'].items():
                if p is None:
                    continue
                with self.subTest(entity=e['id'], axis=axis):
                    self.assertIn(p['value'], (1, 2, 3))
                    self.assertTrue(p['sources'])
                    self.assertTrue(p['reason']['ar'])
                    for ref in p['sources']:
                        self.assertIn(sources[ref]['actor'], e['actorIds'])
                        self.assertTrue(sources[ref]['url'].startswith('https://'))
        by_id = {e['id']:e for e in DATA['entities']}
        # Fadlallah is now classified from his own explicit arms statement.
        self.assertEqual(by_id['mp-15']['positions']['arms']['sources'], ['HF-ARMS26'])
        # Nor does cabinet membership imply a personal policy statement.
        self.assertTrue(all(p is None for p in by_id['minister-bayrakdarian']['positions'].values()))
        # Opposition to aid conditionality alone does not establish an arms view.
        self.assertIsNone(by_id['mp-1']['positions']['arms'])
        # A joint party statement is not a personal statement by its MP.
        self.assertTrue(all(p is None for p in by_id['mp-358']['positions'].values()))

    def test_new_evidence_keeps_funding_and_roster_scope(self):
        by_id = {e['id']:e for e in DATA['entities']}
        # Shehadeh's separate budget request concerns older civil-war files.
        self.assertIsNone(by_id['minister-shehadeh']['positions']['financing'])
        self.assertIsNone(by_id['mp-297']['positions']['financing'])
        self.assertEqual(by_id['minister-menassa']['positions']['arms']['sources'], ['MM-ARMS'])
        self.assertEqual(by_id['mp-340']['positions']['financing']['sources'], ['IM-OCT17'])
        # Additional statement research does not imply a new roster verification.
        self.assertEqual(DATA['rosterReviewed'], '2026-10-16')
        self.assertEqual(DATA['statementsReviewed'], '2026-10-19')

    def test_bilingual_names_reasons_and_sources(self):
        for e in DATA['entities']:
            for field in ('name','role'):
                self.assertTrue(e[field]['en'])
                self.assertRegex(e[field]['ar'], r'[\u0600-\u06ff]')
        refs = {ref for e in DATA['entities'] for p in e['positions'].values() if p for ref in p['sources']}
        for ref in refs:
            self.assertRegex(DATA['sources'][ref]['summary']['ar'], r'[\u0600-\u06ff]')
            self.assertLessEqual(DATA['sources'][ref]['date'], DATA['reviewed'])

    def test_recovered_party_statements_keep_attribution_limits(self):
        by_id = {e['id']:e for e in DATA['entities']}
        for id in ('lihaqqi','banner','green','communistaction'):
            self.assertIsNotNone(by_id['party-'+id]['positions']['reconstruction'])
            self.assertIsNone(by_id['party-'+id]['positions']['financing'])
        # Forum participants' proposals are not silently assigned to the host.
        self.assertIsNone(by_id['party-green']['positions']['arms'])
        self.assertEqual(by_id['party-green']['positions']['reconstruction']['value'],1)
        # General support for resistance is not enough to determine arms ownership.
        self.assertIsNone(by_id['party-banner']['positions']['arms'])
        self.assertEqual(by_id['party-lihaqqi']['positions']['arms']['value'],3)
        self.assertEqual(by_id['party-communistaction']['positions']['arms']['value'],3)
        self.assertIn('OCAL', by_id['party-communistaction']['aliases'])
        self.assertEqual(by_id['party-marada']['symbol']['sourceUrl'],'https://elmarada.org/')
        self.assertEqual(by_id['party-communistaction']['symbol']['status'],'unverified')

    def test_portraits_and_symbols_have_real_local_images_and_sources(self):
        for e in DATA['entities']:
            image = e.get('symbol') if e['layer'] == 'parties' else e.get('portrait')
            if e['layer'] == 'parties' and not e['positions']['reconstruction']:
                continue
            with self.subTest(entity=e['id']):
                self.assertIsNotNone(image)
                if image.get('status') == 'unverified':
                    self.assertEqual(e['layer'], 'parties')
                    self.assertTrue(image['label']['ar'])
                    self.assertTrue(image['note']['en'])
                    self.assertNotIn('path', image)
                    continue
                self.assertTrue(image['sourceUrl'].startswith('https://'))
                raw=(ROOT/'imported/parties'/image['path']).read_bytes()
                self.assertGreater(len(raw),1000)
                if image['path'].endswith('.jpg'):
                    self.assertTrue(raw.startswith(b'\xff\xd8'))
                elif image['path'].endswith('.png'):
                    self.assertTrue(raw.startswith(b'\x89PNG'))
        self.assertNotIn('Ahed_2021',next(e for e in DATA['entities'] if e['id']=='minister-haidar')['portrait']['imageUrl'])


if __name__ == '__main__':
    unittest.main()
