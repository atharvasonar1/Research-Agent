"""Create a persistent neutral brief from local fixtures without network or credentials."""

import argparse
import json

from gtm_research.agent import run_research
from gtm_research.model import Action
from gtm_research.reader import Response, WebsiteReader


ROOT = "https://team.example/"
PAGE_HTML = b"""<!doctype html>
<html><body>
<h1>Harbor Example Realty</h1>
<p>Our team serves Harbor City.</p>
</body></html>
"""


class OfflineModel:
    model = "offline-fixture"
    provider = "offline"

    def __init__(self):
        self.step = 0

    def decide(self, state, timeout):
        self.step += 1
        if self.step == 1:
            return Action("fetch_page", {"url": ROOT})
        return Action("submit_brief", {
            "company_name": "Harbor Example Realty",
            "claims": [
                {
                    "claim": {
                        "subject": "The website",
                        "relation": "identifies the company as",
                        "value": "Harbor Example Realty",
                    },
                    "source_id": "S1",
                    "excerpt_id": "E1",
                },
                {
                    "claim": {
                        "subject": "The website",
                        "relation": "states that the team serves",
                        "value": "Harbor City",
                    },
                    "source_id": "S1",
                    "excerpt_id": "E1",
                },
            ],
            "identity_claim_ref": 1,
            "unknowns": [
                "CRM, contact volume, follow-up process, budget, and buying intent are not stated on the fixture page."
            ],
            "qualification": {"status": "not_assessed"},
            "discovery_questions": [],
        })


def fixture_transport(url, address, timeout, max_bytes):
    return Response(200, {"content-type": "text/html"}, PAGE_HTML)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="runs/offline-neutral-example")
    args = parser.parse_args(argv)
    reader = WebsiteReader(
        ROOT,
        resolver=lambda *unused: "93.184.216.34",
        transport=fixture_transport,
    )
    result = run_research(OfflineModel(), reader, output_dir=args.output_dir, max_steps=2)
    print(json.dumps(result, indent=2))
    print(f"Brief: {result['run_dir']}/brief.md")
    print(f"Trace: {result['run_dir']}/trace.json")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
