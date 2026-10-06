"""Neutral Phase 1 brief contract; semantic support still requires review."""
from copy import deepcopy
import unittest

from gtm_research.agent import readable_brief
from gtm_research.schema import validate_brief
from helpers import brief, fixture_reader


class NeutralBriefTests(unittest.TestCase):
    def setUp(self):
        self.reader = fixture_reader()
        self.reader.fetch(self.reader.root)

    def test_not_assessed_is_the_only_phase_1_qualification(self):
        self.assertEqual(validate_brief(brief(), self.reader.pages), [])
        for qualification in ({"status": "assessed"}, {"status": "uncertain"},
                              {"status": "not_assessed", "label": "promising"}, {}):
            with self.subTest(qualification=qualification):
                value = brief()
                value["qualification"] = qualification
                self.assertTrue(validate_brief(value, self.reader.pages))

    def test_legacy_fit_and_inference_fields_are_rejected(self):
        value = brief()
        value["fit_label"] = "promising"
        value["sales_inferences"] = [{"text": "Likely needs faster lead handling."}]
        self.assertIn("schema:root:additionalProperties", validate_brief(value, self.reader.pages))

    def test_declared_identity_must_reference_a_sourced_claim(self):
        for reference in (0, 3, True, 1.0, "1"):
            with self.subTest(reference=reference):
                value = brief()
                value["identity_claim_ref"] = reference
                self.assertTrue(validate_brief(value, self.reader.pages))

    def test_zero_questions_and_neutral_rendering(self):
        value = brief()
        value["discovery_questions"] = []
        rendered = readable_brief(value)
        self.assertIn("## Qualification", rendered)
        self.assertIn("**Not assessed.**", rendered)
        self.assertIn("No discovery questions were generated.", rendered)
        self.assertNotIn("fit", rendered.lower().replace("does not assign fit", ""))
        self.assertNotIn("sales inference", rendered.lower())

    def test_attribution_and_period_wording_survives_unchanged(self):
        value = brief()
        value["claims"][1]["claim"] = {
            "subject": "The website",
            "relation": "reports sales since 2021 of",
            "value": "$13B+",
        }
        value["claims"][1]["excerpt"] = "Our team serves Harbor City."
        self.assertEqual(validate_brief(value, self.reader.pages), [])
        rendered = readable_brief(value)
        self.assertIn("The website — reports sales since 2021 of: $13B+", rendered)

    def test_unknowns_and_questions_are_preserved(self):
        value = deepcopy(brief())
        rendered = readable_brief(value)
        self.assertIn(value["unknowns"][0], rendered)
        self.assertIn(value["discovery_questions"][0]["question"], rendered)
