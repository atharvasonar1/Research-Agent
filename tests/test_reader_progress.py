"""Reader measurement, deterministic failure-cache, and progress regressions."""

import io
import json
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch
import unittest

from gtm_research.agent import run_research
from gtm_research.reader import Response, ToolError, WebsiteReader, request
from helpers import ROOT, SELLERS, FakeModel, fetch, submit


OTHER = ROOT + "other"
PUBLIC_IP = "93.184.216.34"


def reader(transport, **kwargs):
    return WebsiteReader(
        ROOT, resolver=lambda *unused: PUBLIC_IP, transport=transport, **kwargs,
    )


class TransportMeasurementTests(unittest.TestCase):
    def call_request(self, body, headers=(), cap=250_000):
        response = Mock(status=200)
        response.getheaders.return_value = list(headers)
        response.read1.side_effect = io.BytesIO(body).read
        sock = Mock()
        conn = Mock()
        conn.getresponse.return_value = response
        with patch("socket.create_connection", return_value=sock), \
             patch("http.client.HTTPConnection", return_value=conn):
            try:
                return request("http://team.example/", PUBLIC_IP, 1, cap), None
            except ToolError as exc:
                return None, exc

    def test_oversize_with_and_without_content_length(self):
        _, declared = self.call_request(b"", [("Content-Length", "250001")])
        self.assertEqual(declared.code, "response_too_large")
        self.assertEqual(declared.outcome["declared_content_length"], 250001)
        self.assertEqual(declared.outcome["observed_bytes"], 0)
        self.assertEqual(declared.outcome["observed_bytes_kind"], "unavailable")
        self.assertFalse(declared.outcome["read_completed"])

        _, chunked = self.call_request(b"x" * 250_001)
        self.assertEqual(chunked.code, "response_too_large")
        self.assertIsNone(chunked.outcome["declared_content_length"])
        self.assertEqual(chunked.outcome["observed_bytes"], 250_001)
        self.assertEqual(chunked.outcome["observed_bytes_kind"], "lower_bound")
        self.assertFalse(chunked.outcome["read_completed"])

    def test_exact_cap_succeeds_and_one_byte_over_fails(self):
        response, error = self.call_request(b"x" * 250_000)
        self.assertIsNone(error)
        self.assertEqual(len(response.body), 250_000)
        _, error = self.call_request(b"x" * 250_001)
        self.assertEqual(error.code, "response_too_large")

    def test_declared_size_is_distinct_from_observed_bytes(self):
        _, error = self.call_request(b"abc", [("Content-Length", "8")])
        self.assertEqual(error.code, "incomplete_response")
        self.assertEqual(error.outcome["declared_content_length"], 8)
        self.assertEqual(error.outcome["observed_bytes"], 3)
        self.assertEqual(error.outcome["observed_bytes_kind"], "complete")
        self.assertTrue(error.outcome["read_completed"])


class ReaderProgressTests(unittest.TestCase):
    def test_historical_size_fixtures_are_explicitly_simulated(self):
        body = b"x" * 480_787
        site = reader(
            lambda *unused: Response(200, {
                "content-type": "text/plain", "content-length": "480787",
            }, body),
            max_bytes=1_000_000,
            diagnostic_label="simulated_historical_size_fixture",
        )
        page = site.fetch(ROOT)
        self.assertEqual(page["bytes"], 480_787)
        self.assertEqual(page["declared_content_length"], 480_787)
        self.assertTrue(page["read_completed"])
        self.assertEqual(site.outcomes[0]["measurement_context"],
                         "simulated_historical_size_fixture")

    def test_repeated_oversize_fetch_uses_one_network_attempt(self):
        transport = Mock(return_value=Response(
            200, {"content-type": "text/plain"}, b"x" * 250_001,
        ))
        site = reader(transport)
        for _ in range(2):
            with self.assertRaisesRegex(ToolError, "response_too_large"):
                site.fetch(ROOT)
        self.assertEqual(transport.call_count, 1)
        self.assertFalse(site.outcomes[0]["cached"])
        self.assertTrue(site.outcomes[0]["network_attempted"])
        self.assertEqual(site.outcomes[0]["observed_bytes"], 250_001)
        self.assertEqual(site.outcomes[0]["observed_bytes_kind"], "lower_bound")
        self.assertTrue(site.outcomes[1]["cached"])
        self.assertFalse(site.outcomes[1]["network_attempted"])
        self.assertNotIn("body", site.outcomes[0])

    def test_undiscovered_url_is_rejected_without_network(self):
        transport = Mock()
        site = reader(transport)
        with self.assertRaisesRegex(ToolError, "undiscovered_url"):
            site.fetch(SELLERS)
        transport.assert_not_called()
        self.assertFalse(site.outcomes[0]["network_attempted"])
        self.assertFalse(site.outcomes[0]["cached"])

    def test_transient_failure_can_recover_and_is_not_cached(self):
        transport = Mock(side_effect=[
            ToolError("network_error"),
            Response(200, {"content-type": "text/plain"}, b"Recovered team"),
        ])
        site = reader(transport)
        with self.assertRaisesRegex(ToolError, "network_error"):
            site.fetch(ROOT)
        page = site.fetch(ROOT)
        self.assertEqual(page["text"], "Recovered team")
        self.assertEqual(transport.call_count, 2)
        self.assertFalse(site.outcomes[0]["cached"])
        self.assertEqual(site.untried_allowed_urls(), [])

    def test_transient_http_failure_can_recover_and_is_not_cached(self):
        transport = Mock(side_effect=[
            Response(503, {"content-type": "text/plain"}, b"Unavailable"),
            Response(200, {"content-type": "text/plain"}, b"Recovered team"),
        ])
        site = reader(transport)
        with self.assertRaisesRegex(ToolError, "http_503"):
            site.fetch(ROOT)
        page = site.fetch(ROOT)
        self.assertEqual(page["text"], "Recovered team")
        self.assertEqual(transport.call_count, 2)
        self.assertFalse(site.outcomes[0]["cached"])

    def test_failed_redirect_chain_retains_history_and_final_url(self):
        transport = Mock(side_effect=[
            Response(301, {"location": "/large", "content-length": "0"}, b""),
            Response(200, {"content-type": "text/plain"}, b"x" * 250_001),
        ])
        site = reader(transport)
        with self.assertRaisesRegex(ToolError, "response_too_large"):
            site.fetch(ROOT)
        outcome = site.outcomes[0]
        self.assertEqual(outcome["final_url"], ROOT + "large")
        self.assertEqual(outcome["redirects"], [{
            "status": 301, "from": ROOT, "to": ROOT + "large",
        }])
        self.assertEqual(outcome["observed_bytes"], 250_001)
        self.assertIsNone(outcome["declared_content_length"])

    def test_root_oversize_stops_after_visible_cached_repeat(self):
        transport = Mock(return_value=Response(
            200, {"content-type": "text/plain"}, b"x" * 250_001,
        ))
        site = reader(transport, diagnostic_label="simulated_250001_byte_cutoff")
        model = FakeModel([fetch(), fetch(), fetch()])
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(model, site, directory, max_steps=8)
            trace = json.loads(Path(result["run_dir"], "trace.json").read_text())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "no_researchable_sources")
        self.assertEqual(result["metadata"]["model_calls"], 2)
        self.assertEqual(result["metadata"]["tool_calls"], 2)
        self.assertEqual(transport.call_count, 1)
        self.assertEqual([item["cached"] for item in trace["reader_outcomes"]], [False, True])
        self.assertEqual(trace["events"][-1]["result"]["stop_reason"], "no_researchable_sources")

    def test_no_progress_does_not_block_discovered_alternative(self):
        root = b'<html><body>Evidence Example.<a href="/sellers">Sellers</a><a href="/other">Other</a></body></html>'

        def response_for(url, *unused):
            if url == ROOT:
                return Response(200, {"content-type": "text/html"}, root)
            if url == SELLERS:
                return Response(200, {"content-type": "text/plain"}, b"x" * 250_001)
            return Response(200, {"content-type": "text/plain"}, b"Alternative evidence.")

        transport = Mock(side_effect=response_for)
        site = reader(transport)
        model = FakeModel([fetch(), fetch(SELLERS), fetch(SELLERS), fetch(OTHER), submit()])
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(model, site, directory, max_steps=6)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metadata"]["pages"], 2)
        self.assertIn("response_too_large", result["metadata"]["errors"])
        self.assertEqual(transport.call_count, 3)

    def test_partial_success_trace_retains_page_and_failure_diagnostics(self):
        root = b'<html><body>Evidence Example.<a href="/sellers">Sellers</a></body></html>'
        transport = Mock(side_effect=[
            Response(200, {"content-type": "text/html", "content-length": str(len(root))}, root),
            Response(200, {"content-type": "text/plain"}, b"x" * 250_001),
        ])
        site = reader(transport)
        model = FakeModel([fetch(), fetch(SELLERS), fetch(SELLERS)])
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(model, site, directory, max_steps=8)
            trace = json.loads(Path(result["run_dir"], "trace.json").read_text())
        self.assertEqual(result["reason"], "no_research_progress")
        self.assertEqual(len(trace["pages"]), 1)
        self.assertEqual(trace["pages"][0]["bytes"], len(root))
        self.assertEqual(trace["reader_outcomes"][1]["observed_bytes"], 250_001)
        self.assertTrue(trace["reader_outcomes"][2]["cached"])
        self.assertEqual(transport.call_count, 2)

    def test_reader_outcomes_still_redact_known_secrets(self):
        secret = "reader-secret-not-real"
        secret_url = ROOT + "?token=" + secret
        site = reader(Mock())
        model = FakeModel([fetch(secret_url)])
        with tempfile.TemporaryDirectory() as directory:
            result = run_research(model, site, directory, max_steps=1, secrets=(secret,))
            trace_text = Path(result["run_dir"], "trace.json").read_text()
        self.assertNotIn(secret, trace_text)
        self.assertIn("[REDACTED]", trace_text)


if __name__ == "__main__":
    unittest.main()
