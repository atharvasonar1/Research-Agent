"""Run a scripted candidate and checker without credentials or network access."""

import argparse
import json

from gtm_research.agent import run_research
from gtm_research.model import Action
from gtm_research.reader import Response, WebsiteReader


ROOT = "https://support-check.example/"
PAGE = b"""<html><body><h1>Northstar Realty</h1>
<p>Northstar Realty serves Bay County.</p>
<p>Visitors may request a home valuation through the website form.</p>
</body></html>"""


class Generator:
    model = "scripted-generator"
    provider = "offline"

    def __init__(self):
        self.calls = 0

    def decide(self, state, timeout):
        self.calls += 1
        if self.calls == 1:
            return Action("fetch_page", {"url": ROOT, "purpose": "Read identity and public services.",
                                         "topic_ids": ["company_identity", "markets", "seller_services", "lead_capture"]})
        return Action("submit_brief", {
            "company_name": "Northstar Realty",
            "claims": [
                {"claim": {"subject": "The website", "relation": "identifies the company as", "value": "Northstar Realty"},
                 "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
                {"claim": {"subject": "Northstar Realty", "relation": "serves", "value": "Bay County"},
                 "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
                {"claim": {"subject": "Northstar Realty", "relation": "responds instantly to", "value": "every valuation request"},
                 "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
            ],
            "identity_claim_ref": 1,
            "unknowns": ["CRM, request volume, response timing, budget, and buying intent are unknown."],
            "qualification": {"status": "not_assessed"},
            "discovery_questions": [
                {"question": "Which CRM, if any, do you use?", "premise_claim_refs": []},
                {"question": "How do you maintain the stated instant response?", "premise_claim_refs": [3]},
            ],
            "coverage": [
                {"topic_id": "company_identity", "status": "covered", "summary": "Identity is stated.", "fact_refs": [1]},
                {"topic_id": "markets", "status": "covered", "summary": "A market is stated.", "fact_refs": [2]},
                {"topic_id": "team", "status": "unresolved", "summary": "Team structure is not stated.", "fact_refs": []},
                {"topic_id": "seller_services", "status": "covered", "summary": "A valuation form is described.", "fact_refs": [3]},
                {"topic_id": "lead_capture", "status": "covered", "summary": "A valuation form is described.", "fact_refs": [3]},
                {"topic_id": "public_follow_up", "status": "covered", "summary": "Response timing is claimed.", "fact_refs": [3]},
            ],
            "relevant_candidates": [],
            "stopping": {"code": "no_relevant_candidates", "summary": "The fixture exposes no additional pages."},
        })


class Checker:
    model = "scripted-verifier"
    provider = "offline"

    def verify(self, candidate, timeout):
        return {
            "fact_verdicts": [
                {"fact_id": "F1", "grade": "supported", "explanation": "The cited excerpt names the company.", "unsupported_clause": ""},
                {"fact_id": "F2", "grade": "supported", "explanation": "The cited excerpt names Bay County.", "unsupported_clause": ""},
                {"fact_id": "F3", "grade": "unsupported", "explanation": "The excerpt shows a form but gives no response-time promise.", "unsupported_clause": "responds instantly to every valuation request"},
            ],
            "question_verdicts": [
                {"question_id": "Q1", "grade": "neutral", "explanation": "The question assumes no company-specific fact.", "unsupported_clause": ""},
                {"question_id": "Q2", "grade": "unsupported", "explanation": "The question assumes the rejected response-time claim.", "unsupported_clause": "stated instant response"},
            ],
            "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="runs/offline-support-checker-example")
    args = parser.parse_args(argv)
    reader = WebsiteReader(ROOT, resolver=lambda *unused: "93.184.216.34",
                           transport=lambda *unused: Response(200, {"content-type": "text/html"}, PAGE))
    result = run_research(Generator(), reader, args.output_dir, verifier=Checker())
    print("SCRIPTED CHECKER EXAMPLE: no model provider or website network calls were made.")
    print(json.dumps(result, indent=2))
    print(f"Accepted brief: {result['run_dir']}/brief.md")
    print(f"Candidate and verdict: {result['run_dir']}/trace.json")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
