from copy import deepcopy
from pathlib import Path

from gtm_research.model import Action
from gtm_research.evidence import Sources
from gtm_research.reader import Response, WebsiteReader

ROOT = "https://team.example/"
SELLERS = ROOT + "sellers"
FIXTURES = Path(__file__).parent / "fixtures"


class FakeModel:
    model = "offline-fake"

    def __init__(self, actions):
        self.actions = iter(actions)
        self.states = []

    def decide(self, state, timeout):
        self.states.append(deepcopy(state))
        action = next(self.actions)
        if isinstance(action, Exception):
            raise action
        return action

    def verify(self, candidate, timeout):
        return {
            "fact_verdicts": [
                {"fact_id": f"F{i}", "grade": "supported", "explanation": "Fixture evidence supports the fact.", "unsupported_clause": ""}
                for i, _ in enumerate(candidate["facts"], 1)
            ],
            "question_verdicts": [
                {"question_id": f"Q{i}", "grade": "neutral" if not q["premise_fact_ids"] else "premise_supported", "explanation": "Fixture question is neutral or has supported premises.", "unsupported_clause": ""}
                for i, q in enumerate(candidate["questions"], 1)
            ],
            "usage": {},
        }


def brief():
    reader = fixture_reader()
    sources = Sources()
    sources.add(reader.fetch(ROOT))
    sources.add(reader.fetch(SELLERS))
    resolved, errors = sources.resolve(_base_submission(), reader.pages, reader)
    assert not errors, errors
    return resolved


def _base_submission():
    return {
        "company_name": "Harbor Example Realty",
        "claims": [
            {"claim": {"subject": "The company", "relation": "is named", "value": "Harbor Example Realty"},
             "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
            {"claim": {"subject": "The team", "relation": "serves", "value": "Harbor City"},
             "evidence_refs": [{"source_id": "S1", "evidence_id": "E1"}]},
        ],
        "identity_claim_ref": 1,
        "unknowns": ["CRM size, contact volume, follow-up process, budget, and buying intent are unknown."],
        "qualification": {"status": "not_assessed"},
        "discovery_questions": [{"question": "Which CRM, if any, do you use?", "premise_claim_refs": []}],
        "coverage": [
            {"topic_id": "company_identity", "status": "covered",
             "summary": "The fetched homepage identifies the company.",
             "fact_refs": [1]},
            {"topic_id": "markets", "status": "covered",
             "summary": "The fetched homepage names a served market.",
             "fact_refs": [2]},
            {"topic_id": "team", "status": "covered",
             "summary": "The fetched homepage describes the team.",
             "fact_refs": [1]},
            {"topic_id": "seller_services", "status": "unresolved",
             "summary": "Seller-service details are unresolved in this reusable fixture brief.",
             "fact_refs": []},
            {"topic_id": "lead_capture", "status": "unresolved",
             "summary": "Lead-capture details are unresolved in this reusable fixture brief.",
             "fact_refs": []},
            {"topic_id": "public_follow_up", "status": "unresolved",
             "summary": "Public follow-up timing and process were not stated on the fetched pages.",
             "fact_refs": []},
        ],
        "relevant_candidates": [],
        "stopping": {
            "code": "no_relevant_candidates",
            "summary": "This reusable fixture leaves optional topics explicitly unresolved.",
        },
    }


def fetch(url=ROOT, purpose=None, topic_ids=None):
    return Action("fetch_page", {
        "url": url,
        "purpose": purpose or ("Read the starting page for company context." if url == ROOT
                               else "Read a discovered page for relevant service details."),
        "topic_ids": topic_ids or (["company_identity", "markets", "team"] if url == ROOT
                                   else ["seller_services", "lead_capture"]),
    })


def submission(value=None):
    value = deepcopy(_base_submission() if value is None else value)
    for claim in value.get("claims", []):
        claim["evidence_refs"] = [
            {"source_id": ref["source_id"], "evidence_id": ref["evidence_id"]}
            for ref in claim.get("evidence_refs", [])
        ]
    return value


def submit(value=None):
    return Action("submit_brief", submission(value))


def fixture_reader(transport=None, **kwargs):
    pages = {ROOT: "home.html", SELLERS: "sellers.html"}

    def fixture_transport(url, address, timeout, max_bytes):
        return Response(200, {"content-type": "text/html"}, (FIXTURES / pages[url]).read_bytes())

    return WebsiteReader(ROOT, resolver=lambda *args: "93.184.216.34",
                         transport=transport or fixture_transport, **kwargs)
