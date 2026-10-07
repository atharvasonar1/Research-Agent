"""Bounded verifier contract, filtering, scheduling, and experiment metrics."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gtm_research.agent import run_research
from gtm_research.model import ModelError, RetryableModelError
from gtm_research.support import (
    accept_verified_candidate, candidate_for_verification, evaluate_human_labels,
    validate_verdict,
)
from helpers import FakeModel, brief, fetch, fixture_reader, submit


def verdict(value, fact_grades=None, question_grades=None):
    fact_grades = fact_grades or ["supported"] * len(value["claims"])
    question_grades = question_grades or [
        "neutral" if not item["premise_claim_refs"] else "premise_supported"
        for item in value["discovery_questions"]
    ]
    return {
        "fact_verdicts": [
            {"fact_id": f"F{i}", "grade": grade, "explanation": f"Mocked {grade} verdict.",
             "unsupported_clause": "" if grade == "supported" else "unsupported qualifier"}
            for i, grade in enumerate(fact_grades, 1)
        ],
        "question_verdicts": [
            {"question_id": f"Q{i}", "grade": grade, "explanation": f"Mocked {grade} verdict.",
             "unsupported_clause": "" if grade in ("neutral", "premise_supported") else "assumed operational pain"}
            for i, grade in enumerate(question_grades, 1)
        ],
    }


class ScriptedVerifier:
    model = "offline-verifier"
    provider = "offline"

    def __init__(self, replies):
        self.replies = iter(replies)
        self.inputs = []

    def verify(self, candidate, timeout):
        self.inputs.append(deepcopy(candidate))
        item = next(self.replies)
        if isinstance(item, Exception):
            raise item
        return deepcopy(item)


class SupportContractTests(unittest.TestCase):
    def setUp(self):
        self.candidate = brief()

    def test_input_contains_only_final_citations_and_stable_ids(self):
        payload = candidate_for_verification(self.candidate)
        self.assertEqual([item["fact_id"] for item in payload["facts"]], ["F1", "F2"])
        self.assertEqual(payload["facts"][0]["evidence_refs"], self.candidate["claims"][0]["evidence_refs"])
        self.assertNotIn("normalized_text", json.dumps(payload))

    def test_supported_is_verbatim_partial_and_unsupported_are_omitted(self):
        value = deepcopy(self.candidate)
        value["claims"].extend([
            deepcopy(value["claims"][1]), deepcopy(value["claims"][1]),
        ])
        # These represent the historical failure classes: an unsupported qualifier,
        # wrong/generic excerpt, bundled assertion, and missing reporting period.
        checked = verdict(value, ["supported", "partial", "unsupported", "partial"])
        final, outcome = accept_verified_candidate(value, checked)
        self.assertEqual(final["claims"], [value["claims"][0]])
        self.assertEqual(final["claims"][0]["evidence_refs"], value["claims"][0]["evidence_refs"])
        self.assertEqual(outcome["omitted_fact_ids"], ["F2", "F3", "F4"])

    def test_mocked_historical_semantic_failures_are_never_rendered(self):
        cases = {
            "unsupported_qualifier": "is the number-one team in every market",
            "generic_excerpt_for_names": "offers buyer, seller, move-up, and relocation guarantees",
            "bundled_assertion": "has a form and responds instantly",
            "missing_reporting_period": "reports more than $13 billion in sales",
            "operational_assumption": "routes every lead automatically",
        }
        for name, value_text in cases.items():
            with self.subTest(case=name):
                value = deepcopy(self.candidate)
                value["claims"][1]["claim"] = {
                    "subject": "The company", "relation": "claims", "value": value_text,
                }
                final, outcome = accept_verified_candidate(
                    value, verdict(value, ["supported", "partial"]),
                )
                self.assertEqual(len(final["claims"]), 1)
                self.assertEqual(outcome["omitted_fact_ids"], ["F2"])

    def test_question_premise_cleanup_and_reference_remap(self):
        value = deepcopy(self.candidate)
        value["discovery_questions"] = [
            {"question": "Which CRM, if any, do you use?", "premise_claim_refs": []},
            {"question": "How does the stated market affect follow-up?", "premise_claim_refs": [2]},
        ]
        final, outcome = accept_verified_candidate(
            value, verdict(value, ["supported", "unsupported"], ["neutral", "unsupported"]),
        )
        self.assertEqual(final["discovery_questions"], [value["discovery_questions"][0]])
        self.assertEqual(outcome["omitted_question_ids"], ["Q2"])

    def test_coverage_downgrades_without_accepted_fact(self):
        final, outcome = accept_verified_candidate(
            self.candidate, verdict(self.candidate, ["supported", "unsupported"]),
        )
        market = next(item for item in final["coverage"] if item["topic_id"] == "markets")
        self.assertEqual((market["status"], market["fact_refs"]), ("unresolved", []))
        self.assertEqual(outcome["candidate_coverage"], self.candidate["coverage"])

    def test_required_identity_rejection_is_a_semantic_failure(self):
        final, outcome = accept_verified_candidate(
            self.candidate, verdict(self.candidate, ["unsupported", "supported"]),
        )
        self.assertIsNone(final)
        self.assertEqual(outcome["errors"], ["identity_fact_rejected"])

    def test_no_usable_facts_is_reported(self):
        final, outcome = accept_verified_candidate(
            self.candidate, verdict(self.candidate, ["unsupported", "partial"]),
        )
        self.assertIsNone(final)
        self.assertEqual(outcome["errors"], ["identity_fact_rejected", "no_usable_facts"])

    def test_missing_duplicate_unknown_and_malformed_verdicts(self):
        for mutate, marker in (
            (lambda v: v["fact_verdicts"].pop(), "missing_id:F2"),
            (lambda v: v["fact_verdicts"].append(deepcopy(v["fact_verdicts"][0])), "duplicate_id:F1"),
            (lambda v: v["fact_verdicts"].append({**deepcopy(v["fact_verdicts"][0]), "fact_id": "F99"}), "unknown_id:F99"),
            (lambda v: v["fact_verdicts"][0].pop("explanation"), "verifier_schema"),
        ):
            with self.subTest(marker=marker):
                value = verdict(self.candidate)
                mutate(value)
                self.assertTrue(any(marker in error for error in validate_verdict(self.candidate, value)))

    def test_question_neutrality_shape_is_enforced(self):
        value = verdict(self.candidate)
        value["question_verdicts"][0]["grade"] = "premise_supported"
        self.assertIn("verifier:question:unpremised_marked_supported:Q1",
                      validate_verdict(self.candidate, value))


class SupportSchedulingTests(unittest.TestCase):
    def run_case(self, actions, verifier, max_steps=8, max_seconds=120):
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(FakeModel(actions), fixture_reader(), directory,
                                  max_steps=max_steps, max_seconds=max_seconds, verifier=verifier)
            path = Path(result["run_dir"])
            trace = json.loads((path / "trace.json").read_text())
            final = json.loads((path / "brief.json").read_text()) if (path / "brief.json").exists() else None
        return result, trace, final

    def test_verification_starts_immediately_after_early_candidate(self):
        value = brief()
        checker = ScriptedVerifier([{**verdict(value), "usage": {"total_tokens": 17}}])
        result, trace, _ = self.run_case([fetch(), submit()], checker)
        self.assertEqual(result["metadata"]["research_model_calls"], 2)
        self.assertEqual(result["metadata"]["model_calls"], 3)
        self.assertEqual(result["metadata"]["verification_provider_failures"], 0)
        self.assertIn("verification_latency_seconds", result["metadata"])
        self.assertEqual(len(checker.inputs), 1)
        self.assertEqual(trace["verification"]["attempts"][0]["usage"]["total_tokens"], 17)

    def test_research_is_capped_at_six_even_when_total_limit_is_eight(self):
        result, trace, _ = self.run_case([fetch()] * 6, ScriptedVerifier([]), max_steps=8)
        self.assertEqual(result["metadata"]["model_calls"], 6)
        self.assertEqual(trace["verification"]["reason"], "no_valid_candidate")

    def test_one_verifier_503_retry_and_eight_call_ceiling(self):
        value = brief()
        checker = ScriptedVerifier([RetryableModelError("gemini_http_503"), verdict(value)])
        with patch("gtm_research.agent.sleep"), patch("gtm_research.agent.uniform", return_value=.5):
            result, trace, _ = self.run_case([fetch(), submit()], checker)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["verification_calls"], 2)
        self.assertEqual([item["status"] for item in trace["verification"]["attempts"]],
                         ["provider_failure", "accepted"])
        self.assertTrue(trace["verification"]["attempts"][0]["retry"]["scheduled"])
        self.assertLessEqual(result["metadata"]["model_calls"], 8)

    def test_candidate_on_sixth_call_uses_seventh_and_eighth_for_verification(self):
        value = brief()
        checker = ScriptedVerifier([RetryableModelError("gemini_http_503"), verdict(value)])
        with patch("gtm_research.agent.sleep"), patch("gtm_research.agent.uniform", return_value=.5):
            result, _, _ = self.run_case([fetch()] * 5 + [submit()], checker, max_steps=8)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["research_model_calls"], 6)
        self.assertEqual(result["metadata"]["verification_calls"], 2)
        self.assertEqual(result["metadata"]["model_calls"], 8)

    def test_persistent_503_is_provider_failure_not_semantic_rejection(self):
        checker = ScriptedVerifier([RetryableModelError("gemini_http_503")] * 2)
        with patch("gtm_research.agent.sleep"), patch("gtm_research.agent.uniform", return_value=.5):
            result, trace, final = self.run_case([fetch(), submit()], checker)
        self.assertEqual(result["reason"], "verification_provider_unavailable")
        self.assertIsNone(final)
        self.assertNotEqual(result["reason"], "semantic_rejection")
        self.assertIn("candidate_brief", trace)

    def test_semantic_rejection_never_writes_unverified_brief(self):
        value = brief()
        result, trace, final = self.run_case(
            [fetch(), submit()], ScriptedVerifier([verdict(value, ["unsupported", "supported"])]),
        )
        self.assertEqual(result["reason"], "semantic_rejection")
        self.assertIsNone(final)
        self.assertEqual([item["claim"] for item in trace["candidate_brief"]["claims"]],
                         [item["claim"] for item in value["claims"]])

    def test_deadline_prevents_verification(self):
        # A zero/negative budget is rejected before execution; this focused case
        # makes candidate work consume the tiny positive deadline.
        class Slow(FakeModel):
            def decide(self, state, timeout):
                import time
                time.sleep(.02)
                return super().decide(state, timeout)
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(Slow([fetch(), submit()]), fixture_reader(), directory,
                                  max_seconds=.03, model_timeout=.02, verifier=ScriptedVerifier([]))
        self.assertNotEqual(result["status"], "completed")

    def test_model_error_is_distinct_from_rejected_content(self):
        result, _, _ = self.run_case([fetch(), submit()], ScriptedVerifier([ModelError("model_rate_limit")]))
        self.assertEqual(result["reason"], "model_rate_limit")


class EvaluationMetricTests(unittest.TestCase):
    def test_small_human_set_reports_gap_instead_of_passing_gates(self):
        labels = [
            {"case_id": "jills-supported", "company": "Jills Zeder", "kind": "fact", "human_label": "supported"},
            {"case_id": "keri-generic", "company": "Keri Shull", "kind": "fact", "human_label": "unsupported"},
        ]
        predictions = [
            {"case_id": "jills-supported", "grade": "supported"},
            {"case_id": "keri-generic", "grade": "supported"},
        ]
        metrics = evaluate_human_labels(labels, predictions, [
            {"tokens": 120, "latency_seconds": 1.5, "provider_failure": False},
            {"tokens": 0, "latency_seconds": .5, "provider_failure": True},
        ])
        self.assertEqual(metrics["false_acceptance_rate"], 1.0)
        self.assertFalse(metrics["provisional_gates_evaluable"])
        self.assertFalse(metrics["provisional_gates_passed"])
        self.assertEqual(metrics["tokens_total"], 120)
        self.assertEqual(metrics["provider_failures"], 1)


if __name__ == "__main__":
    unittest.main()
