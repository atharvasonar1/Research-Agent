"""Complete-evidence provenance checks; these do not test semantic entailment."""

from copy import deepcopy
import unittest

from gtm_research.agent import readable_brief
from gtm_research.evidence import Sources, excerpts
from gtm_research.model import INSTRUCTIONS
from gtm_research.schema import (
    MAX_COMBINED_EVIDENCE_CHARS,
    MAX_EVIDENCE_REFS_PER_CLAIM,
    MAX_EVIDENCE_SPAN_CHARS,
    normalize_text,
)


ROOT = "https://evidence.example/"
SECOND = ROOT + "services"


def page(url, text, fetched_at="2026-10-06T00:00:00+00:00"):
    return {"url": url, "text": text, "fetched_at": fetched_at}


def candidate(refs, value="Evidence Example"):
    return {
        "company_name": "Evidence Example",
        "claims": [{
            "claim": {"subject": "The website", "relation": "reports", "value": value},
            "evidence_refs": refs,
        }],
        "identity_claim_ref": 1,
        "unknowns": ["Operational details are unknown."],
        "qualification": {"status": "not_assessed"},
        "discovery_questions": [],
    }


class EvidenceBoundaryTests(unittest.TestCase):
    def test_sentence_boundaries_ignore_abbreviations_and_decimals(self):
        text = "Dr. Rivera reported $5.2 million in the U.S. market. Café® clients agreed. Next item."
        spans = list(excerpts(text, limit=60).values())
        self.assertEqual(spans[0]["text"], "Dr. Rivera reported $5.2 million in the U.S. market.")
        self.assertEqual(spans[1]["text"], "Café® clients agreed. Next item.")

    def test_unicode_offsets_and_normalized_text_are_exact(self):
        raw = "  Café®\nclients   agreed.  第二 sentence is here. "
        normalized = normalize_text(raw)
        spans = excerpts(raw, limit=30)
        self.assertEqual(" ".join(item["text"] for item in spans.values()), normalized)
        for item in spans.values():
            self.assertEqual(normalized[item["start"]:item["end"]], item["text"])

    def test_long_sentence_falls_back_within_limit_without_text_loss(self):
        text = "word " * 310 + "finished."
        normalized = normalize_text(text)
        spans = excerpts(text)
        self.assertGreater(len(spans), 2)
        self.assertTrue(all(len(item["text"]) <= MAX_EVIDENCE_SPAN_CHARS
                            for item in spans.values()))
        self.assertEqual(" ".join(item["text"] for item in spans.values()), normalized)

    def test_keri_consent_sentence_is_not_split_when_it_fits(self):
        consent = ("Consent: I agree to be contacted by Keri Shull Team and Guild Mortgage "
                   "Company via call, email, and text for real estate services.")
        text = ("Navigation labels " * 32) + "End navigation! " + consent + " Submit."
        span_texts = [item["text"] for item in excerpts(text).values()]
        self.assertTrue(any(consent in item for item in span_texts), span_texts)


class EvidenceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.first = page(ROOT, "Evidence Example identifies the company. First supporting sentence.")
        self.second = page(SECOND, "Second supporting sentence. More service detail.")
        self.sources = Sources()
        self.sources.add(self.first)
        self.sources.add(self.second)
        self.pages = {ROOT: self.first, SECOND: self.second}

    def test_valid_multi_source_refs_resolve_in_canonical_order(self):
        value = candidate([
            {"source_id": "S1", "evidence_id": "E1"},
            {"source_id": "S2", "evidence_id": "E1"},
        ])
        resolved, errors = self.sources.resolve(value, self.pages)
        self.assertEqual(errors, [])
        refs = resolved["claims"][0]["evidence_refs"]
        self.assertEqual([(item["source_id"], item["evidence_id"]) for item in refs],
                         [("S1", "E1"), ("S2", "E1")])
        self.assertEqual(refs[0]["text"], self.first["text"])
        self.assertEqual(refs[1]["url"], SECOND)
        rendered = readable_brief(resolved)
        self.assertIn("Evidence 1 [S1/E1]", rendered)
        self.assertIn("Evidence 2 [S2/E1]", rendered)
        self.assertIn("Normalized offsets: [0,", rendered)

    def test_invalid_reference_combinations_are_rejected(self):
        cases = {
            "missing": [],
            "duplicate": [{"source_id": "S1", "evidence_id": "E1"}] * 2,
            "unfetched": [{"source_id": "S9", "evidence_id": "E1"}],
            "nonexistent": [{"source_id": "S1", "evidence_id": "E99"}],
            "wrong_source": [{"source_id": "S1", "evidence_id": "E2"}],
            "reordered": [
                {"source_id": "S2", "evidence_id": "E1"},
                {"source_id": "S1", "evidence_id": "E1"},
            ],
        }
        for name, refs in cases.items():
            with self.subTest(name=name):
                resolved, errors = self.sources.resolve(candidate(refs), self.pages)
                self.assertIsNone(resolved)
                self.assertTrue(errors)

    def test_forged_selector_fields_and_legacy_contract_are_rejected(self):
        forged = candidate([{"source_id": "S1", "evidence_id": "E1", "text": "forged"}])
        legacy = candidate([{"source_id": "S1", "evidence_id": "E1"}])
        legacy["claims"][0].pop("evidence_refs")
        legacy["claims"][0].update(source_id="S1", excerpt_id="E1")
        for value in (forged, legacy):
            self.assertTrue(self.sources.resolve(value, self.pages)[1])

    def test_reference_count_and_combined_text_are_bounded(self):
        self.assertEqual(MAX_EVIDENCE_REFS_PER_CLAIM, 4)
        too_many = candidate([{"source_id": "S1", "evidence_id": "E1"}] * 5)
        self.assertTrue(self.sources.resolve(too_many, self.pages)[1])

        large_text = " ".join((character * 490) + "." for character in "ABCD")
        large_page = page(ROOT, large_text)
        sources = Sources()
        sources.add(large_page)
        refs = [{"source_id": "S1", "evidence_id": f"E{index}"} for index in range(1, 5)]
        self.assertGreater(sum(len(item["text"]) for item in sources.items["S1"]["evidence"].values()),
                           MAX_COMBINED_EVIDENCE_CHARS)
        resolved, errors = sources.resolve(candidate(refs), {ROOT: large_page})
        self.assertIsNone(resolved)
        self.assertIn("claim:0:combined_evidence_too_large", errors)

    def test_jills_style_amount_and_adjacent_period_can_both_be_retained(self):
        selected_text = selected_spans = None
        for count in range(60, 100):
            text = (("context " * count) + "$13B+ in sales " + ("detail " * 20) +
                    "since 2021 according to the website.")
            spans = excerpts(text)
            amount = next((key for key, item in spans.items() if "$13B+" in item["text"]), None)
            period = next((key for key, item in spans.items() if "since 2021" in item["text"]), None)
            if amount and period and amount != period:
                selected_text, selected_spans = text, (amount, period)
                break
        self.assertIsNotNone(selected_text)
        amount_page = page(ROOT, selected_text)
        sources = Sources()
        sources.add(amount_page)
        refs = [{"source_id": "S1", "evidence_id": item} for item in selected_spans]
        resolved, errors = sources.resolve(candidate(refs, "$13B+ in sales since 2021"), {ROOT: amount_page})
        self.assertEqual(errors, [])
        self.assertEqual(len(resolved["claims"][0]["evidence_refs"]), 2)

    def test_keri_generic_guarantee_text_is_only_provenance(self):
        guarantee_page = page(ROOT, "Keri offers several guarantee programs.")
        sources = Sources()
        sources.add(guarantee_page)
        value = candidate([{"source_id": "S1", "evidence_id": "E1"}],
                          "buyer, seller, move-up, and relocation guarantees")
        resolved, errors = sources.resolve(value, {ROOT: guarantee_page})
        self.assertEqual(errors, [])  # Exact provenance, not semantic support.
        self.assertIn("semantic support still needs human review", readable_brief(resolved))
        self.assertIn("do not prove", INSTRUCTIONS)


if __name__ == "__main__":
    unittest.main()
