"""Trusted coverage checkpoint, candidate dispositions, and stopping records."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from gtm_research.agent import run_research
from gtm_research.model import Action
from gtm_research.reader import Response, WebsiteReader
from gtm_research.schema import RESEARCH_TOPICS
from helpers import ROOT, SELLERS, FakeModel, fetch, fixture_reader, submission, submit


PUBLIC_IP = "93.184.216.34"


def candidate(disposition, reason):
    return {
        "url": SELLERS,
        "topic_ids": ["seller_services", "lead_capture"],
        "disposition": disposition,
        "reason": reason,
    }


def mark_covered(value, topic_ids, source_id="S1"):
    for item in value["coverage"]:
        if item["topic_id"] in topic_ids:
            item.update(
                status="covered",
                summary=f"The fetched source addresses {item['topic_id']}.",
                evidence_refs=[{"source_id": source_id, "evidence_id": "E1"}],
            )


class ResearchCoverageTests(unittest.TestCase):
    def run_agent(self, actions, reader=None, max_steps=8):
        model = FakeModel(actions)
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        result = run_research(model, reader or fixture_reader(), directory.name, max_steps=max_steps)
        path = Path(result["run_dir"])
        trace = json.loads((path / "trace.json").read_text())
        brief = json.loads((path / "brief.json").read_text()) if (path / "brief.json").exists() else None
        return result, trace, brief, model, path

    def test_homepage_can_cover_topics_and_submit_early_without_page_minimum(self):
        text = (b"Harbor Example Realty serves Harbor City. The team offers home valuation "
                b"consultations through a website form and states that staff follow up by email.")
        site = WebsiteReader(
            ROOT, resolver=lambda *unused: PUBLIC_IP,
            transport=lambda *unused: Response(200, {"content-type": "text/plain"}, text),
        )
        value = submission()
        mark_covered(value, RESEARCH_TOPICS)
        value["stopping"] = {
            "code": "sufficient_coverage",
            "summary": "The homepage addressed every trusted topic and exposed no relevant follow-up page.",
        }
        result, trace, saved, model, _ = self.run_agent([fetch(), submit(value)], site, 2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["pages"], 1)
        self.assertEqual(result["metadata"]["model_calls"], 2)
        self.assertTrue(all(item["status"] == "covered" for item in saved["coverage"]))
        self.assertEqual(trace["discovered_urls"], [{
            "url": ROOT, "visited": True, "reader_errors": [],
        }])

    def test_unresolved_topic_and_pending_relevant_link_stay_visible(self):
        value = submission()
        value["relevant_candidates"] = [candidate(
            "pending", "The homepage links to seller details that were not fetched within this run.",
        )]
        value["stopping"] = {
            "code": "budget_limited",
            "summary": "The final decision slot was used to preserve the unresolved seller research.",
        }
        result, trace, saved, _, path = self.run_agent([fetch(), submit(value)], max_steps=2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(saved["relevant_candidates"][0]["disposition"], "pending")
        self.assertIn(SELLERS, [item["url"] for item in trace["discovered_urls"]])
        rendered = (path / "brief.md").read_text()
        self.assertIn("Seller Services — Unresolved", rendered)
        self.assertIn("## Remaining relevant candidates", rendered)
        self.assertIn(SELLERS, rendered)
        self.assertIn("budget_limited", rendered)

    def test_follow_up_fetch_updates_coverage_and_candidate_without_extra_call(self):
        value = submission()
        mark_covered(value, {"seller_services", "lead_capture"}, "S2")
        value["relevant_candidates"] = [candidate(
            "visited", "The homepage linked to seller details and the page was fetched.",
        )]
        value["stopping"] = {
            "code": "sufficient_coverage",
            "summary": "The relevant seller page was reviewed and remaining gaps are explicit.",
        }
        result, trace, saved, _, _ = self.run_agent(
            [fetch(), fetch(SELLERS), submit(value)], max_steps=3,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["model_calls"], 3)
        self.assertEqual(result["metadata"]["tool_calls"], 3)
        self.assertEqual(saved["relevant_candidates"][0]["disposition"], "visited")
        self.assertEqual(trace["coverage_checkpoint"]["stopping"]["code"],
                         "sufficient_coverage")
        self.assertEqual(trace["events"][1]["action"]["arguments"]["purpose"],
                         "Read a discovered page for relevant service details.")

    def test_reader_block_is_distinct_from_model_selected_skip(self):
        root = b'<html><body>Harbor Example Realty.<a href="/sellers">Seller details</a></body></html>'

        def transport(url, *unused):
            if url == ROOT:
                return Response(200, {"content-type": "text/html"}, root)
            return Response(200, {"content-type": "text/plain"}, b"x" * 250_001)

        blocked_value = submission()
        blocked_value["relevant_candidates"] = [candidate(
            "blocked", "The reader rejected the discovered page because it exceeded the configured cap.",
        )]
        blocked_value["stopping"] = {
            "code": "reader_limited",
            "summary": "Seller-service research remains unresolved because the reader blocked the page.",
        }
        site = WebsiteReader(ROOT, resolver=lambda *unused: PUBLIC_IP, transport=transport)
        result, _, saved, _, _ = self.run_agent(
            [fetch(), fetch(SELLERS), submit(blocked_value)], site, 3,
        )
        self.assertEqual(result["status"], "completed")
        self.assertEqual(saved["relevant_candidates"][0]["disposition"], "blocked")
        self.assertIn("response_too_large", result["metadata"]["errors"])

        skipped_value = submission()
        skipped_value["relevant_candidates"] = [candidate(
            "skipped", "The model selected the homepage facts and left this page for later review.",
        )]
        skipped_value["stopping"] = {
            "code": "sufficient_coverage",
            "summary": "The skip is explicit and seller-service coverage remains unresolved.",
        }
        result, _, saved, _, _ = self.run_agent([fetch(), submit(skipped_value)], max_steps=2)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(saved["relevant_candidates"][0]["disposition"], "skipped")

    def test_invalid_coverage_reference_and_false_visit_are_rejected(self):
        bad_ref = submission()
        seller = next(item for item in bad_ref["coverage"] if item["topic_id"] == "seller_services")
        seller.update(status="covered", summary="Seller services were covered.",
                      evidence_refs=[{"source_id": "S1", "evidence_id": "E99"}])
        result, _, _, _, _ = self.run_agent([fetch(), submit(bad_ref)], max_steps=2)
        self.assertIn("coverage:3:evidence_ref:0:evidence_not_found", result["metadata"]["errors"])

        false_visit = submission()
        false_visit["relevant_candidates"] = [candidate(
            "visited", "This falsely claims the discovered page was fetched.",
        )]
        result, _, _, _, _ = self.run_agent([fetch(), submit(false_visit)], max_steps=2)
        self.assertIn("candidate:0:not_visited", result["metadata"]["errors"])

    def test_website_text_cannot_change_trusted_topics_or_fetch_permissions(self):
        result, _, _, model, _ = self.run_agent([fetch(), fetch(SELLERS)], max_steps=2)
        self.assertEqual(result["status"], "budget_exhausted")
        state = model.states[1]
        self.assertEqual(
            [item["topic_id"] for item in state["trusted_research_topics"]],
            list(RESEARCH_TOPICS),
        )
        self.assertEqual(state["allowed_urls"], [ROOT, SELLERS])
        self.assertNotIn("http://127.0.0.1/secrets", state["allowed_urls"])

    def test_missing_topic_duplicate_topic_and_false_block_are_rejected(self):
        missing = submission()
        missing["coverage"].pop()
        result, _, _, _, _ = self.run_agent([fetch(), submit(missing)], max_steps=2)
        self.assertTrue(any("coverage" in item for item in result["metadata"]["errors"]))

        duplicate = submission()
        duplicate["coverage"][-1]["topic_id"] = "company_identity"
        result, _, _, _, _ = self.run_agent([fetch(), submit(duplicate)], max_steps=2)
        self.assertIn("coverage:5:duplicate_topic", result["metadata"]["errors"])
        self.assertIn("coverage:missing_topic:public_follow_up", result["metadata"]["errors"])

        false_block = submission()
        false_block["relevant_candidates"] = [candidate(
            "blocked", "This falsely claims a reader-enforced block.",
        )]
        result, _, _, _, _ = self.run_agent([fetch(), submit(false_block)], max_steps=2)
        self.assertIn("candidate:0:not_reader_blocked", result["metadata"]["errors"])

    def test_fetch_purpose_and_topic_targets_are_required_and_bounded(self):
        for arguments in (
            {"url": ROOT, "topic_ids": ["company_identity"]},
            {"url": ROOT, "purpose": "Read identity."},
            {"url": ROOT, "purpose": "x" * 241, "topic_ids": ["company_identity"]},
            {"url": ROOT, "purpose": "Read identity.", "topic_ids": ["website_defined_topic"]},
        ):
            with self.subTest(arguments=arguments):
                result, _, _, _, _ = self.run_agent(
                    [Action("fetch_page", arguments)], max_steps=1,
                )
                self.assertEqual(result["metadata"]["pages"], 0)
                self.assertTrue(any(item.startswith("schema:")
                                    for item in result["metadata"]["errors"]))

    def test_coverage_status_controls_evidence_shape(self):
        covered_without_evidence = submission()
        covered_without_evidence["coverage"][3].update(
            status="covered", summary="Claims coverage without a source.", evidence_refs=[],
        )
        result, _, _, _, _ = self.run_agent(
            [fetch(), submit(covered_without_evidence)], max_steps=2,
        )
        self.assertIn("coverage:3:covered_without_evidence", result["metadata"]["errors"])

        unresolved_with_evidence = submission()
        unresolved_with_evidence["coverage"][3]["evidence_refs"] = [
            {"source_id": "S1", "evidence_id": "E1"},
        ]
        result, _, _, _, _ = self.run_agent(
            [fetch(), submit(unresolved_with_evidence)], max_steps=2,
        )
        self.assertIn("coverage:3:unresolved_with_evidence", result["metadata"]["errors"])


if __name__ == "__main__":
    unittest.main()
