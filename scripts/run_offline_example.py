"""Create a persistent neutral brief from local fixtures without network or credentials."""

import argparse
import json

from gtm_research.agent import run_research
from gtm_research.model import Action
from gtm_research.reader import Response, WebsiteReader


ROOT = "https://team.example/"
REPORTING = ROOT + "reporting"
PAGES = {
ROOT: b"""<!doctype html>
<html><body>
<h1>Harbor Example Realty.</h1>
<p>The website reports more than $13 billion in sales.</p>
<a href="/reporting">Seller services and reporting details</a>
</body></html>
""",
REPORTING: b"""<!doctype html>
<html><body>
<p>The website states that the reporting period for that sales figure is since 2021.</p>
<p>The team offers home valuation consultations. Visitors can request one using the website form.</p>
</body></html>
""",
}


class OfflineModel:
    model = "offline-fixture"
    provider = "offline"

    def __init__(self):
        self.step = 0

    def decide(self, state, timeout):
        self.step += 1
        if self.step == 1:
            return Action("fetch_page", {
                "url": ROOT,
                "purpose": "Establish company identity and inspect relevant navigation.",
                "topic_ids": ["company_identity", "markets", "team"],
            })
        if self.step == 2:
            return Action("fetch_page", {
                "url": REPORTING,
                "purpose": "Review the discovered seller-service and form details.",
                "topic_ids": ["seller_services", "lead_capture"],
            })
        return Action("submit_brief", {
            "company_name": "Harbor Example Realty",
            "claims": [
                {
                    "claim": {
                        "subject": "The website",
                        "relation": "identifies the company as",
                        "value": "Harbor Example Realty",
                    },
                    "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}],
                },
                {
                    "claim": {
                        "subject": "The website",
                        "relation": "reports sales since 2021 exceeding",
                        "value": "$13 billion",
                    },
                    "evidence_refs": [
                        {"source_id": "S1", "evidence_id": "E1"},
                        {"source_id": "S2", "evidence_id": "E1"},
                    ],
                },
            ],
            "identity_claim_ref": 1,
            "unknowns": [
                "CRM, contact volume, follow-up process, budget, and buying intent are not stated on the fetched fixture pages."
            ],
            "qualification": {"status": "not_assessed"},
            "discovery_questions": [],
            "coverage": [
                {"topic_id": "company_identity", "status": "covered",
                 "summary": "The homepage identifies Harbor Example Realty.",
                 "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
                {"topic_id": "markets", "status": "unresolved",
                 "summary": "The fetched fixture pages do not name a served market.",
                 "evidence_refs": []},
                {"topic_id": "team", "status": "unresolved",
                 "summary": "The fetched fixture pages do not describe team composition.",
                 "evidence_refs": []},
                {"topic_id": "seller_services", "status": "covered",
                 "summary": "The follow-up page describes home valuation consultations.",
                 "evidence_refs": [{"source_id": "S2", "evidence_id": "E1"}]},
                {"topic_id": "lead_capture", "status": "covered",
                 "summary": "The follow-up page describes a website request form.",
                 "evidence_refs": [{"source_id": "S2", "evidence_id": "E1"}]},
                {"topic_id": "public_follow_up", "status": "unresolved",
                 "summary": "The fetched fixture pages do not state follow-up timing or process.",
                 "evidence_refs": []},
            ],
            "relevant_candidates": [{
                "url": REPORTING,
                "topic_ids": ["seller_services", "lead_capture"],
                "disposition": "visited",
                "reason": "The homepage linked to seller-service details and the page was fetched.",
            }],
            "stopping": {
                "code": "sufficient_coverage",
                "summary": "The relevant discovered page was reviewed; remaining topics are explicit unknowns.",
            },
        })


def fixture_transport(url, address, timeout, max_bytes):
    return Response(200, {"content-type": "text/html"}, PAGES[url])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="runs/offline-coverage-example")
    args = parser.parse_args(argv)
    reader = WebsiteReader(
        ROOT,
        resolver=lambda *unused: "93.184.216.34",
        transport=fixture_transport,
    )
    result = run_research(OfflineModel(), reader, output_dir=args.output_dir, max_steps=3)
    print("SCRIPTED OFFLINE EXAMPLE: no model provider or website network calls were made.")
    print(json.dumps(result, indent=2))
    print(f"Brief: {result['run_dir']}/brief.md")
    print(f"Trace: {result['run_dir']}/trace.json")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
