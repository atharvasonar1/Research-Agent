"""Offline checks for the bounded development-set verifier adapter."""

import json
from pathlib import Path
import tempfile
import unittest

from gtm_research.development import run_development_verifier
from gtm_research.model import ModelError, RetryableModelError
from gtm_research.support import development_predictions, development_verifier_payload


def reference(source="S1", evidence="E1", text="Exact cited evidence."):
    return {
        "snapshot_id": "snapshot-1", "source_id": source, "evidence_id": evidence,
        "url": "https://example.test/", "fetched_at": "2026-01-01T00:00:00Z",
        "start": 0, "end": len(text), "text": text,
    }


def input_data():
    return {
        "schema_version": "support-verifier-development-input-v1",
        "reference_labels": "must not reach verifier",
        "cases": [
            {
                "case_id": "ACME-F001", "kind": "fact",
                "candidate_claim": {"subject": "The site", "relation": "names", "value": "Acme"},
                "evidence_refs": [reference()], "ai_review": {"grade": "supported"},
            },
            {
                "case_id": "ACME-F002", "kind": "fact",
                "candidate_claim": {"subject": "Acme", "relation": "offers", "value": "valuation"},
                "evidence_refs": [reference(evidence="E2", text="Request a valuation.")],
            },
            {
                "case_id": "ACME-Q001", "kind": "question",
                "candidate_question": "How is the valuation request handled?",
                "premise_case_ids": ["ACME-F002"],
                "evidence_refs": [reference(evidence="E2", text="Request a valuation.")],
                "explanation": "must not reach verifier",
            },
        ],
    }


def complete_verdict():
    return {
        "fact_verdicts": [
            {"fact_id": "F1", "grade": "supported", "explanation": "Supported.", "unsupported_clause": ""},
            {"fact_id": "F2", "grade": "partial", "explanation": "Offer is unclear.", "unsupported_clause": "offers"},
        ],
        "question_verdicts": [
            {"question_id": "Q1", "grade": "premise_supported", "explanation": "Premise follows.", "unsupported_clause": ""},
        ],
        "usage": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120},
    }


class FakeVerifier:
    provider = "gemini"
    model = "gemini-test"

    def __init__(self, results):
        self.results = list(results)
        self.inputs = []

    def verify(self, payload, timeout):
        self.inputs.append((payload, timeout))
        value = self.results.pop(0)
        if isinstance(value, Exception):
            raise value
        return json.loads(json.dumps(value))


class DevelopmentInputTests(unittest.TestCase):
    def test_payload_preserves_mappings_and_strips_all_review_fields(self):
        payload, mapping, digest = development_verifier_payload(input_data())
        serialized = json.dumps(payload)
        self.assertEqual(mapping["facts"], {"F1": "ACME-F001", "F2": "ACME-F002"})
        self.assertEqual(mapping["questions"], {"Q1": "ACME-Q001"})
        self.assertEqual(payload["questions"][0]["premise_fact_ids"], ["F2"])
        self.assertEqual(payload["questions"][0]["evidence_refs"][0]["text"], "Request a valuation.")
        self.assertEqual(len(digest), 64)
        for forbidden in ("reference_labels", "ai_review", "explanation", "grade"):
            self.assertNotIn(forbidden, serialized)

    def test_complete_unique_verdicts_map_back_to_stable_case_ids(self):
        _, mapping, _ = development_verifier_payload(input_data())
        value = complete_verdict()
        value.pop("usage")
        predictions, errors = development_predictions(value, mapping)
        self.assertEqual(errors, [])
        self.assertEqual([item["case_id"] for item in predictions],
                         ["ACME-F001", "ACME-F002", "ACME-Q001"])
        for mutate, marker in (
            (lambda verdict: verdict["fact_verdicts"].pop(), "missing_id:F2"),
            (lambda verdict: verdict["question_verdicts"].append(dict(verdict["question_verdicts"][0])),
             "duplicate_id:Q1"),
            (lambda verdict: verdict["fact_verdicts"].append({**dict(verdict["fact_verdicts"][0]), "fact_id": "F99"}),
             "unknown_id:F99"),
        ):
            with self.subTest(marker=marker):
                verdict = complete_verdict()
                verdict.pop("usage")
                mutate(verdict)
                predictions, errors = development_predictions(verdict, mapping)
                self.assertIsNone(predictions)
                self.assertTrue(any(marker in error for error in errors))


class DevelopmentRunnerTests(unittest.TestCase):
    def test_success_records_auditable_files_compatible_with_scoring(self):
        verifier = FakeVerifier([complete_verdict()])
        with tempfile.TemporaryDirectory() as directory:
            result = run_development_verifier(verifier, input_data(), directory, timeout=12)
            destination = Path(result["output_dir"])
            predictions = json.loads((destination / "verifier-predictions.json").read_text())
            runs = json.loads((destination / "verifier-runs.json").read_text())
            manifest = json.loads((destination / "verification.json").read_text())
            saved_input = (destination / "verifier-input.json").read_text()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(predictions), 3)
        self.assertEqual(runs[0]["total_tokens"], 120)
        self.assertEqual(runs[0]["prompt_version"], "factual-support-v1")
        self.assertEqual(runs[0]["input_hash"], manifest["input_hash"])
        self.assertEqual(manifest["case_id_mapping"]["questions"]["Q1"], "ACME-Q001")
        self.assertNotIn("reference_labels", saved_input)
        self.assertNotIn("ai_review", saved_input)

    def test_only_503_gets_one_retry(self):
        verifier = FakeVerifier([RetryableModelError("gemini_http_503"), complete_verdict()])
        delays = []
        with tempfile.TemporaryDirectory() as directory:
            result = run_development_verifier(
                verifier, input_data(), directory, sleep_fn=delays.append,
                jitter_fn=lambda low, high: .75,
            )
            runs = json.loads((Path(result["output_dir"]) / "verifier-runs.json").read_text())
        self.assertEqual(result["status"], "completed")
        self.assertEqual(len(verifier.inputs), 2)
        self.assertEqual(delays, [.75])
        self.assertEqual([item["status"] for item in runs], ["provider_failure", "completed"])

    def test_incomplete_response_is_saved_without_retry(self):
        verifier = FakeVerifier([ModelError("verifier_incomplete_response")])
        with tempfile.TemporaryDirectory() as directory:
            result = run_development_verifier(verifier, input_data(), directory)
            runs = json.loads((Path(result["output_dir"]) / "verifier-runs.json").read_text())
            predictions = json.loads((Path(result["output_dir"]) / "verifier-predictions.json").read_text())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(len(verifier.inputs), 1)
        self.assertTrue(runs[0]["incomplete_response"])
        self.assertEqual(predictions, [])


if __name__ == "__main__":
    unittest.main()
