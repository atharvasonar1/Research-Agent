"""Integrity checks for the human-review development set and label-free export."""

from copy import deepcopy
import json
from pathlib import Path
import unittest

from scripts.render_support_development_set import (
    render, summary, validate_dataset, verifier_cases,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "evaluation/factual_support_development.json"
REVIEW = ROOT / "evaluation/factual_support_development.md"
GOODHART_CAPTURE = ROOT / "evaluation/evidence/thegoodhartgroup_capture_2026-10-08.json"


class SupportDevelopmentSetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATASET.read_text(encoding="utf-8"))

    def test_dataset_is_valid_and_review_view_is_generated_from_it(self):
        self.assertEqual(validate_dataset(self.data), [])
        self.assertEqual(REVIEW.read_text(encoding="utf-8"), render(self.data))

    def test_fact_balance_and_third_company_are_present_but_human_labels_are_missing(self):
        stats = summary(self.data)
        self.assertEqual(stats["fact_cases"], 30)
        self.assertEqual(stats["question_cases"], 4)
        self.assertEqual(stats["real_companies"], 3)
        self.assertGreaterEqual(stats["supported"], 12)
        self.assertGreaterEqual(stats["partial_or_unsupported"], 12)
        self.assertEqual(stats["human_approved_fact_labels"], 0)
        self.assertTrue(stats["proposed_shape_gate_met"])
        self.assertFalse(stats["ready_for_reference_evaluation"])
        companies = {}
        for case in self.data["cases"]:
            if case["kind"] == "fact":
                companies[case["domain"]] = companies.get(case["domain"], 0) + 1
        self.assertEqual(companies, {
            "kerishull.com": 10,
            "jillszeder.com": 10,
            "www.thegoodhartgroup.com": 10,
        })

    def test_questions_are_separate_and_synthetic_companies_are_excluded(self):
        for case in self.data["cases"]:
            self.assertNotIn(case["domain"], {"team.example", "support-check.example"})
            self.assertEqual(case["counts_toward_fact_requirement"], case["kind"] == "fact")

    def test_required_failure_families_and_controls_are_represented(self):
        required = {
            "KERI-F009",  # wrong/generic excerpt for named guarantees
            "KERI-F013",  # missing reporting period and bundled assertion
            "KERI-F014",  # unsupported qualifier
            "JILLS-F009", # split evidence and form collection assumption
            "JILLS-F014", # form-to-workflow assumption
            "JILLS-F001", # clearly supported control
        }
        self.assertTrue(required.issubset({item["case_id"] for item in self.data["cases"]}))

    def test_cases_are_nonduplicate_and_evidence_has_exact_provenance(self):
        signatures = []
        for case in self.data["cases"]:
            candidate = case.get("candidate_claim", case.get("candidate_question"))
            signatures.append(json.dumps([case["kind"], candidate, [ref["text"] for ref in case["evidence_refs"]]], sort_keys=True))
            for ref in case["evidence_refs"]:
                self.assertEqual(ref["end"] - ref["start"], len(ref["text"]))
                self.assertTrue(ref["url"].startswith("https://"))
                self.assertIn("T", ref["fetched_at"])
        self.assertEqual(len(signatures), len(set(signatures)))

    def test_all_labels_remain_unreviewed_and_ai_proposed(self):
        for case in self.data["cases"] + self.data["retired_cases"]:
            self.assertEqual(case["label_status"], "proposed_unreviewed")
            self.assertEqual(case["reviewer_provenance"]["label_authority"], "ai_proposed")
            self.assertFalse(case["reviewer_provenance"]["human_approval"])

    def test_label_rubric_and_keri_strategy_revision_are_explicit(self):
        rubric = self.data["label_policy"]["rubric"]
        self.assertIn("entire claim", rubric["supported"])
        self.assertIn("substantive part", rubric["partial"])
        self.assertIn("central assertion", rubric["unsupported"])
        self.assertIn("does not necessarily mean contradicted or false", rubric["unsupported"])
        case = next(item for item in self.data["cases"] if item["case_id"] == "KERI-F008")
        self.assertEqual(case["proposed_grade"], "unsupported")
        self.assertEqual(case["label_status"], "proposed_unreviewed")
        self.assertEqual(case["label_history"][0]["proposed_grade"], "partial")
        self.assertEqual(case["label_history"][0]["status"], "superseded_unreviewed_proposal")

    def test_third_company_plan_is_bounded_and_development_only(self):
        plan = " ".join(self.data["bounded_third_company_capture_plan"])
        self.assertIn("development-only", plan)
        self.assertIn("exclude it from the future acceptance sample", plan)
        self.assertIn("at most two", plan)
        self.assertIn("without a generator or verifier", plan)
        self.assertIn("every reader outcome", plan)
        suggestions = self.data["third_company_case_suggestions"]
        self.assertEqual(len(suggestions["supported_controls"]), 4)
        self.assertEqual(len(suggestions["challenging_cases"]), 4)
        candidate = self.data["third_company_candidate"]
        self.assertEqual(candidate["status"], "capture_complete")
        self.assertTrue(candidate["excluded_from_issue_11_acceptance_sample"])

    def test_goodhart_capture_and_case_offsets_are_exact(self):
        capture = json.loads(GOODHART_CAPTURE.read_text(encoding="utf-8"))
        self.assertEqual(capture["generator_calls"], 0)
        self.assertEqual(capture["verifier_calls"], 0)
        self.assertEqual(len(capture["pages"]), 3)
        self.assertEqual(capture["reader_settings"]["max_bytes"], 250000)
        pages = {page["url"]: page["text"] for page in capture["pages"]}
        goodhart = [case for case in self.data["cases"] if case["case_id"].startswith("GOODHART-")]
        self.assertEqual(len(goodhart), 10)
        for case in goodhart:
            for ref in case["evidence_refs"]:
                self.assertEqual(pages[ref["url"]][ref["start"]:ref["end"]], ref["text"])

    def test_verifier_export_contains_no_label_or_review_fields(self):
        payload = verifier_cases(self.data)
        forbidden = {"proposed_grade", "unsupported_clause", "explanation", "label_status", "label_history", "case_history",
                     "reviewer_provenance", "case_origin", "origin_reference"}
        for case in payload["cases"]:
            self.assertTrue(forbidden.isdisjoint(case))
        serialized = json.dumps(payload)
        self.assertNotIn("proposed_unreviewed", serialized)
        self.assertNotIn("ai_proposed", serialized)

    def test_duplicate_id_is_rejected(self):
        changed = deepcopy(self.data)
        changed["cases"][1]["case_id"] = changed["cases"][0]["case_id"]
        self.assertIn("case:1:case_id", validate_dataset(changed))


if __name__ == "__main__":
    unittest.main()
