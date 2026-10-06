"""Saved Jills failure cases: contract and rendering, not automatic entailment."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from gtm_research.agent import readable_brief
from gtm_research.evidence import Sources
from helpers import submission


class AtomicFactsTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('fixtures').joinpath('jills_atomic_cases.json').read_text())
        self.sources = Sources()
        # Explicitly adapt the immutable legacy fixture to the current contract;
        # production does not reinterpret old briefs or source catalogues.
        old_source = self.data['source']
        normalized = ' '.join(old_source['excerpts'].values())
        cursor = 0
        evidence = {}
        for evidence_id, text in old_source['excerpts'].items():
            evidence[evidence_id] = {'text': text, 'start': cursor, 'end': cursor + len(text)}
            cursor += len(text) + 1
        self.sources.items = {'S1': {
            'url': old_source['url'], 'fetched_at': old_source['fetched_at'],
            'normalized_text': normalized, 'evidence': evidence,
        }}
        self.sources.by_url = {old_source['url']: 'S1'}
        self.pages = {self.data['source_url']: {
            'text': normalized, 'fetched_at': old_source['fetched_at'],
        }}
        self.value = submission()
        self.value['company_name'] = 'The Jills Zeder Group'
        self.value['claims'] = [
            {'claim': item['claim'], 'evidence_refs': [{
                'source_id': item['source_id'], 'evidence_id': item['excerpt_id'],
            }]}
            for item in self.data['reviewed_atomic_examples']
        ]
        self.value['identity_claim_ref'] = 1

    def test_all_four_saved_bundles_rejected_as_legacy_claims(self):
        for case in self.data['failure_cases']:
            with self.subTest(case=case['case']):
                bad = deepcopy(self.value)
                bad['claims'][0] = {'claim':case['old_claim'],'source_id':'S1','excerpt_id':case['old_excerpt_id']}
                self.assertIn('schema:claims.0.claim:type', self.sources.resolve(bad,self.pages)[1])

    def test_manually_split_saved_examples_preserve_evidence_and_qualifiers(self):
        brief, errors = self.sources.resolve(self.value,self.pages)
        self.assertEqual(errors, [])
        for fact, selected in zip(brief['claims'],self.value['claims']):
            evidence_id = selected['evidence_refs'][0]['evidence_id']
            self.assertEqual(fact['evidence_refs'][0]['text'], self.data['source']['excerpts'][evidence_id])
        self.assertEqual(brief['claims'][1]['claim']['value'], '$13B+ since 2021')
        self.assertNotIn('RealTrends', brief['claims'][2]['claim']['value'])
        self.assertEqual(brief['claims'][-1]['evidence_refs'][0]['evidence_id'], 'E9')  # Not the service-menu E10.

    def test_rejects_array_values_or_sales_fields_inside_fact(self):
        for field, value in [('relation',['serves','is affiliated with']),('value',['Miami','Broker']),
                             ('inference','Sophisticated operation'),('relation',' '),('subject','')]:
            with self.subTest(field=field):
                bad=deepcopy(self.value)
                bad['claims'][0]['claim'][field]=value
                self.assertTrue(self.sources.resolve(bad,self.pages)[1])

    def test_legacy_judgment_fields_are_not_reinterpreted(self):
        for field, value in [('fit_label', 'promising'), ('sales_inferences', []),
                             ('fit_rationale', {'text': 'Sophisticated operation', 'claim_refs': [1]})]:
            with self.subTest(field=field):
                bad = deepcopy(self.value)
                bad[field] = value
                self.assertTrue(self.sources.resolve(bad, self.pages)[1])

    def test_rendering_is_neutral_and_preserves_reported_period(self):
        brief, errors=self.sources.resolve(self.value,self.pages)
        self.assertEqual(errors,[])
        rendered=readable_brief(brief)
        self.assertIn('**Not assessed.**', rendered)
        self.assertIn('### C1 — Declared identity fact', rendered)
        self.assertIn('$13B+ since 2021', rendered)
        self.assertNotIn('Model sales inferences', rendered)
        self.assertNotIn('Provisional research priority', rendered)
