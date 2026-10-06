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


def brief():
    reader = fixture_reader()
    sources = Sources()
    sources.add(reader.fetch(ROOT))
    sources.add(reader.fetch(SELLERS))
    resolved, errors = sources.resolve(_base_submission(), reader.pages)
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
    }


def fetch(url=ROOT):
    return Action("fetch_page", {"url": url})


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
