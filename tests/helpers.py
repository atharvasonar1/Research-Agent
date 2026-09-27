from copy import deepcopy
from pathlib import Path

from gtm_research.model import Action
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
            {"claim": "The company is Harbor Example Realty.", "url": ROOT,
             "excerpt": "Harbor Example Realty"},
            {"claim": "The team serves Harbor City.", "url": ROOT,
             "excerpt": "Our team serves Harbor City."},
        ],
        "unknowns": ["CRM size, contact volume, follow-up process, budget, and buying intent are unknown."],
        "fit_label": "uncertain",
        "fit_rationale": "The site identifies a real estate team, but qualification evidence is limited.",
        "discovery_questions": ["How do you track and follow up with past seller inquiries?"],
    }


def fetch(url=ROOT):
    return Action("fetch_page", {"url": url})


def submit(value=None):
    return Action("submit_brief", brief() if value is None else value)


def fixture_reader(transport=None, **kwargs):
    pages = {ROOT: "home.html", SELLERS: "sellers.html"}

    def fixture_transport(url, address, timeout, max_bytes):
        return Response(200, {"content-type": "text/html"}, (FIXTURES / pages[url]).read_bytes())

    return WebsiteReader(ROOT, resolver=lambda *args: "93.184.216.34",
                         transport=transport or fixture_transport, **kwargs)
