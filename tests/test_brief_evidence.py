"""Evidence-link regression tests; these do not measure semantic entailment."""
import json
from pathlib import Path
import tempfile
import unittest

from gtm_research.agent import run_research, readable_brief
from gtm_research.schema import validate_brief
from helpers import brief, fixture_reader, fetch, submit, FakeModel


class BriefEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.reader = fixture_reader()
        self.reader.fetch(self.reader.root)

    def test_legacy_uncited_rationale_and_questions_are_rejected(self):
        value = brief()
        value['sales_inferences'] = 'High sales imply complex operations and buying intent.'
        value['discovery_questions'] = ['What causes your routing bottlenecks?']
        errors = validate_brief(value, self.reader.pages)
        self.assertIn('schema:sales_inferences:type', errors)
        self.assertIn('schema:discovery_questions.0:type', errors)

    def test_missing_empty_and_invalid_rationale_refs_rejected(self):
        for refs in ([], [0], [-1], [999], [1, 1], [True], [1.0], ['1']):
            with self.subTest(refs=refs):
                value = brief()
                value['sales_inferences'][0]['claim_refs'] = refs
                self.assertTrue(validate_brief(value, self.reader.pages))

    def test_question_requires_explicit_premise_declaration(self):
        value = brief()
        del value['discovery_questions'][0]['premise_claim_refs']
        self.assertTrue(validate_brief(value, self.reader.pages))

    def test_dangling_question_premise_rejected_then_corrected_in_loop(self):
        bad = brief()
        bad['discovery_questions'] = [{'question': 'Given your Harbor City focus, which CRM, if any, do you use?',
                                       'premise_claim_refs': [3]}]
        good = brief()
        good['discovery_questions'] = [{'question': 'Given your Harbor City focus, which CRM, if any, do you use?',
                                        'premise_claim_refs': [2]}]
        model = FakeModel([fetch(), submit(bad), submit(good)])
        with tempfile.TemporaryDirectory() as folder:
            result = run_research(model, fixture_reader(), folder)
            self.assertEqual(result['status'], 'completed')
            self.assertIn('discovery_question:0:claim_ref_not_found', result['metadata']['errors'])
            trace = json.loads(Path(result['run_dir'], 'trace.json').read_text())
            self.assertFalse(trace['events'][1]['result']['ok'])
            self.assertEqual(model.states[2]['events'][1]['result'], trace['events'][1]['result'])

    def test_referenced_claim_still_requires_actual_page_evidence(self):
        value = brief()
        value['claims'][1]['excerpt'] = 'Our sophisticated CRM handles a million leads.'
        value['sales_inferences'][0]['claim_refs'] = [2]
        self.assertIn('claim:1:excerpt_not_found', validate_brief(value, self.reader.pages))

    def test_neutral_question_and_unobserved_optional_features_allowed(self):
        # Identity/market-only evidence must not require invented forms or services.
        value = brief()
        self.assertEqual(validate_brief(value, self.reader.pages), [])
        rendered = readable_brief(value)
        self.assertIn('[C2](#c2)', rendered)
        self.assertIn('### C2', rendered)
        self.assertIn('Which CRM, if any, do you use?', rendered)
        self.assertIn('review neutrality', rendered)

    def test_blank_structured_text_rejected(self):
        for field, key in [('sales_inferences', 'text'), ('discovery_questions', 'question')]:
            value = brief()
            block = value[field][0]
            block[key] = ' '
            self.assertTrue(validate_brief(value, self.reader.pages))
