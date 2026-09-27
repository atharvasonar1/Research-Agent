from copy import deepcopy
from pathlib import Path

from gtm_research.model import Action
from gtm_research.evidence import Sources
from gtm_research.schema import normalize_text
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
    return {
        "company_name": "Harbor Example Realty",
        "claims": [
            {"claim": {"subject": "The company", "relation": "is named", "value": "Harbor Example Realty"}, "url": ROOT,
             "excerpt": "Harbor Example Realty"},
            {"claim": {"subject": "The team", "relation": "serves", "value": "Harbor City"}, "url": ROOT,
             "excerpt": "Our team serves Harbor City."},
        ],
        "unknowns": ["CRM size, contact volume, follow-up process, budget, and buying intent are unknown."],
        "fit_label": "uncertain",
        "sales_inferences": [{"text": "Further research may be useful.", "claim_refs": [1, 2], "limitation": "Operating needs are unverified."}],
        "discovery_questions": [{"question": "Which CRM, if any, do you use?", "premise_claim_refs": []}],
    }


def fetch(url=ROOT):
    return Action("fetch_page", {"url": url})


def submission(value=None):
    value = deepcopy(brief() if value is None else value)
    reader = fixture_reader()
    sources = Sources()
    sources.add(reader.fetch(ROOT))
    sources.add(reader.fetch(SELLERS))
    for claim in value.get("claims", []):
        url = claim.pop("url", "")
        excerpt = normalize_text(claim.pop("excerpt", ""))
        source_id = sources.by_url.get(url, "unknown")
        candidates = sources.items.get(source_id, {}).get("excerpts", {})
        excerpt_id = next((key for key, text in candidates.items() if excerpt and excerpt in text), "unknown")
        claim.update(source_id=source_id, excerpt_id=excerpt_id)
    return value


def submit(value=None):
    return Action("submit_brief", submission(value))


def fixture_reader(transport=None, **kwargs):
    pages = {ROOT: "home.html", SELLERS: "sellers.html"}

    def fixture_transport(url, address, timeout, max_bytes):
        return Response(200, {"content-type": "text/html"}, (FIXTURES / pages[url]).read_bytes())

    return WebsiteReader(ROOT, resolver=lambda *args: "93.184.216.34",
                         transport=transport or fixture_transport, **kwargs)
