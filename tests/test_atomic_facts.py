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
        self.sources.items = {'S1': self.data['source']}
        # All exact spans are retained from the saved source; no live fetching.
        self.pages = {self.data['source_url']: {'text': ' '.join(self.data['source']['excerpts'].values())}}
        self.value = submission()
        self.value['company_name'] = 'The Jills Zeder Group'
        self.value['claims'] = [{k:v for k,v in item.items() if k!='case'}
                                for item in self.data['reviewed_atomic_examples']]
        self.value['sales_inferences'] = [{'text': 'A discovery conversation about inquiry handling may be useful.',
            'claim_refs': [4,5], 'limitation': 'Form presence does not establish lead volume, delivery, pain or buying intent.'}]

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
            self.assertEqual(fact['excerpt'], self.data['source']['excerpts'][selected['excerpt_id']])
        self.assertEqual(brief['claims'][1]['claim']['value'], '$13B+ since 2021')
        self.assertNotIn('RealTrends', brief['claims'][2]['claim']['value'])
        self.assertEqual(brief['claims'][-1]['excerpt_id'], 'E9')  # Not the service-menu E10.

    def test_rejects_array_values_or_sales_fields_inside_fact(self):
        for field, value in [('relation',['serves','is affiliated with']),('value',['Miami','Broker']),
                             ('inference','Sophisticated operation'),('relation',' '),('subject','')]:
            with self.subTest(field=field):
                bad=deepcopy(self.value)
                bad['claims'][0]['claim'][field]=value
                self.assertTrue(self.sources.resolve(bad,self.pages)[1])

    def test_inference_must_cite_facts_and_state_limitation(self):
        for field, value in [('claim_refs',[]),('claim_refs',[999]),('limitation',' '),('text','')]:
            with self.subTest(field=field):
                bad=deepcopy(self.value);bad['sales_inferences'][0][field]=value
                self.assertTrue(self.sources.resolve(bad,self.pages)[1])

    def test_legacy_rationale_cannot_hide_interpretations(self):
        bad=deepcopy(self.value)
        bad['fit_rationale']={'text':'A sophisticated operation','claim_refs':[1]}
        self.assertTrue(self.sources.resolve(bad,self.pages)[1])

    def test_inference_has_no_website_evidence_slot(self):
        bad=deepcopy(self.value)
        bad['sales_inferences'][0]['source_id']='S1'
        self.assertTrue(self.sources.resolve(bad,self.pages)[1])

    def test_rendering_visibly_separates_facts_inferences_and_limits(self):
        brief, errors=self.sources.resolve(self.value,self.pages)
        self.assertEqual(errors,[])
        rendered=readable_brief(brief)
        facts, inference_part=rendered.split('## Model sales inferences — not website facts')
        self.assertNotIn('discovery conversation', facts)
        self.assertIn('### I1 — Model inference', inference_part)
        self.assertIn('Based on: [C4](#c4), [C5](#c5)', inference_part)
        self.assertIn('Form presence does not establish', inference_part)
        self.assertIn('Provisional research priority (model judgment)', inference_part)
