import json
from pathlib import Path
import tempfile
import time
import unittest

from gtm_research.agent import run_research
from gtm_research.model import Action, ModelError
from gtm_research.reader import ToolError
from helpers import ROOT, SELLERS, FakeModel, brief, fetch, fixture_reader, submit


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def run_agent(self, actions, reader=None, **kwargs):
        self.model = FakeModel(actions)
        result = run_research(self.model, reader or fixture_reader(), self.temp.name, **kwargs)
        path = Path(result["run_dir"])
        self.trace = json.loads((path / "trace.json").read_text())
        self.path = path
        return result

    def test_success_discovers_link_and_writes_brief_and_trace(self):
        value = brief()
        value["claims"].append({"claim": {"subject": "The team", "relation": "offers", "value": "home valuation consultations"},
                                 "url": SELLERS, "excerpt": "We offer home valuation consultations."})
        result = self.run_agent([fetch(), fetch(SELLERS), submit(value)])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["pages"], 2)
        self.assertEqual(result["metadata"]["tool_calls"], 3)
        self.assertIn(SELLERS, self.model.states[1]["allowed_urls"])
        self.assertEqual(len(self.trace["events"]), 3)
        saved = json.loads((self.path / "brief.json").read_text())["claims"]
        self.assertEqual([c["claim"] for c in saved], [c["claim"] for c in value["claims"]])
        self.assertEqual(saved[-1]["url"], SELLERS)
        self.assertIn(value["claims"][-1]["excerpt"], saved[-1]["excerpt"])
        self.assertIn("Harbor City", (self.path / "brief.md").read_text())
        self.assertTrue(self.trace["pages"][0]["fetched_at"])
        self.assertIsNone(result["metadata"]["cost_usd"])

    def test_unsupported_citation_is_rejected_then_corrected(self):
        bad = brief()
        bad["claims"][0]["excerpt"] = "We have one million CRM contacts."
        result = self.run_agent([fetch(), submit(bad), submit()])
        self.assertEqual(result["status"], "completed")
        rejection = self.trace["events"][1]["result"]
        self.assertFalse(rejection["ok"])
        self.assertIn("claim:0:excerpt_not_found", rejection["errors"])
        self.assertEqual(self.model.states[2]["events"][1]["result"], rejection)

    def test_blocked_external_and_undiscovered_urls(self):
        result = self.run_agent([fetch("https://evil.example/"), fetch(SELLERS)], max_steps=2)
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["metadata"]["errors"], ["blocked_host", "undiscovered_url"])
        self.assertFalse((self.path / "brief.json").exists())

    def test_page_instructions_do_not_grant_permissions(self):
        result = self.run_agent([fetch(), fetch("http://127.0.0.1/secrets"), submit()])
        self.assertEqual(result["status"], "completed")
        self.assertIn("blocked_host", result["metadata"]["errors"])
        self.assertNotIn("http://127.0.0.1/secrets", self.model.states[1]["allowed_urls"])

    def test_tool_error_is_recorded_and_can_recover(self):
        reader = fixture_reader()
        real_fetch = reader.fetch
        calls = []

        def flaky(*args, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                raise ToolError("timeout")
            return real_fetch(*args, **kwargs)

        reader.fetch = flaky
        result = self.run_agent([fetch(), fetch(), submit()], reader)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["errors"], ["timeout"])

    def test_exhausted_budget_saves_failure_without_brief(self):
        result = self.run_agent([fetch(), fetch()], max_steps=2)
        self.assertEqual(result["reason"], "step_limit")
        self.assertEqual(result["metadata"]["model_calls"], 2)
        self.assertFalse((self.path / "brief.md").exists())
        self.assertEqual(json.loads((self.path / "result.json").read_text())["status"], "budget_exhausted")

    def test_unfetched_and_wrong_page_citations(self):
        bad = brief()
        bad["claims"][0]["url"] = SELLERS
        result = self.run_agent([fetch(), submit(bad), fetch(SELLERS), submit(bad)], max_steps=4)
        self.assertIn("claim:0:source_not_fetched", result["metadata"]["errors"])
        self.assertIn("claim:0:excerpt_not_found", result["metadata"]["errors"])
        self.assertFalse((self.path / "brief.json").exists())

    def test_invalid_schema_and_unknown_tool_consume_steps(self):
        result = self.run_agent([Action("other", {}), submit({}), Action("fetch_page", {"url": ROOT, "extra": True})], max_steps=3)
        self.assertEqual(result["metadata"]["tool_calls"], 3)
        self.assertIn("unknown_tool", result["metadata"]["errors"])
        self.assertEqual(result["metadata"]["pages"], 0)

    def test_empty_excerpt_cannot_pass(self):
        bad = brief()
        bad["claims"][0]["excerpt"] = "   "
        result = self.run_agent([fetch(), submit(bad)], max_steps=2)
        self.assertIn("claim:0:excerpt_not_found", result["metadata"]["errors"])

    def test_model_error_does_not_invent_brief(self):
        result = self.run_agent([ModelError("model_auth_error")])
        self.assertEqual(result["reason"], "model_auth_error")
        self.assertEqual(result["metadata"]["tool_calls"], 0)
        self.assertFalse((self.path / "brief.json").exists())

    def test_model_timeout_bounds_caller_wait(self):
        class SlowModel:
            def decide(self, state, timeout):
                time.sleep(0.15)
                return fetch()
        start = time.monotonic()
        result = run_research(SlowModel(), fixture_reader(), self.temp.name, model_timeout=0.01)
        self.assertEqual(result["reason"], "model_timeout")
        self.assertEqual(result["metadata"]["tool_calls"], 0)
        self.assertLess(time.monotonic() - start, 0.14)

    def test_time_budget_stops_loop(self):
        result = self.run_agent([fetch()], max_seconds=1e-9)
        self.assertEqual(result["reason"], "time_limit")
        self.assertEqual(result["metadata"]["model_calls"], 0)

    def test_unique_run_directories_prevent_stale_success(self):
        success = self.run_agent([fetch(), submit()])
        failure = self.run_agent([fetch()], max_steps=1)
        self.assertNotEqual(success["run_dir"], failure["run_dir"])
        self.assertFalse((self.path / "brief.json").exists())

    def test_known_secrets_redacted_from_all_artifacts(self):
        secret = "sk-test-secret-not-real"
        value = brief()
        value["unknowns"] = [secret]
        self.run_agent([fetch(), submit(value)], secrets=(secret,))
        for path in self.path.iterdir():
            self.assertNotIn(secret, path.read_text())
        self.assertIn("[REDACTED]", (self.path / "brief.json").read_text())

    def test_unexpected_errors_do_not_log_exception_secrets(self):
        self.run_agent([RuntimeError("secret-value")])
        self.assertNotIn("secret-value", (self.path / "trace.json").read_text())

    def test_whitespace_normalized_excerpt(self):
        value = brief()
        value["claims"][1]["excerpt"] = "Our team\n serves  Harbor City."
        self.assertEqual(self.run_agent([fetch(), submit(value)])["status"], "completed")

    def test_overall_deadline_during_model_call_is_budget_exhaustion(self):
        class SlowModel:
            def decide(self, state, timeout):
                time.sleep(0.15)
                return fetch()
        result = run_research(SlowModel(), fixture_reader(), self.temp.name, max_seconds=0.01)
        self.assertEqual(result["status"], "budget_exhausted")
        self.assertEqual(result["reason"], "time_limit")

    def test_invalid_brief_fields_rejected(self):
        for field, value in (("company_name", "   "), ("claims", []), ("fit_label", "certain-buyer"),
                             ("unknowns", [" "]), ("discovery_questions", [])):
            with self.subTest(field=field):
                invalid = brief()
                invalid[field] = value
                result = self.run_agent([fetch(), submit(invalid)], max_steps=2)
                self.assertEqual(result["status"], "budget_exhausted")
                self.assertFalse((self.path / "brief.json").exists())
