import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import httpx2

from gtm_research.agent import run_research
from gtm_research.gemini import GeminiModel
from helpers import brief, fixture_reader
from test_gemini import response


class RetryTests(unittest.TestCase):
    def run_sequence(self, replies, **limits):
        requests = []
        sequence = iter(replies)
        def handler(request):
            requests.append(request)
            code, payload = next(sequence)
            return httpx2.Response(code, json=payload)
        with tempfile.TemporaryDirectory() as directory:
            client = httpx2.Client(transport=httpx2.MockTransport(handler))
            model = GeminiModel('gemini-3.8-flash', 'test-secret', client)
            try:
                with patch('gtm_research.agent.sleep') as sleeper, patch('gtm_research.agent.uniform', side_effect=lambda low, high: high):
                    result = run_research(model, fixture_reader(), directory, **limits)
                trace = json.loads((Path(result['run_dir']) / 'trace.json').read_text())
                exists = (Path(result['run_dir']) / 'brief.json').exists()
            finally:
                model.close()
        return result, trace, requests, sleeper, exists

    def test_503_then_success_uses_existing_loop_and_records_retry(self):
        result, trace, requests, sleeper, exists = self.run_sequence([
            (503, {'error': {'message': 'temporary'}}), (200, response()),
            (200, response('submit_brief', brief()))], max_steps=3)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['metadata']['model_calls'], 3)
        self.assertEqual(result['metadata']['tool_calls'], 2)
        self.assertEqual(len(requests), 3)
        sleeper.assert_called_once_with(1.0)
        self.assertTrue(trace['events'][0]['retry']['scheduled'])
        self.assertEqual(trace['events'][0]['retry']['next_step'], 2)
        self.assertTrue(exists)

    def test_persistent_503_stops_at_retry_limit(self):
        result, trace, requests, sleeper, exists = self.run_sequence([(503, {})] * 4, max_steps=8, max_model_retries=2)
        self.assertEqual(result['reason'], 'gemini_503_retry_limit')
        self.assertEqual(len(requests), 3)
        self.assertEqual([c.args[0] for c in sleeper.call_args_list], [1.0, 2.0])
        self.assertFalse(trace['events'][-1]['retry']['scheduled'])
        self.assertFalse(exists)

    def test_call_budget_includes_retries(self):
        result, trace, requests, sleeper, exists = self.run_sequence([(503, {})] * 3, max_steps=2)
        self.assertEqual(result['reason'], 'model_call_budget_exhausted_after_503')
        self.assertEqual(len(requests), 2)
        self.assertEqual(sleeper.call_count, 1)

    def test_insufficient_time_does_not_sleep_or_retry(self):
        result, trace, requests, sleeper, exists = self.run_sequence([(503, {})], max_seconds=0.5)
        self.assertEqual(result['reason'], 'time_limit_before_retry')
        self.assertEqual(len(requests), 1)
        sleeper.assert_not_called()

    def test_auth_and_quota_errors_are_never_retried(self):
        for code, reason in ((403, 'model_auth_error'), (429, 'model_rate_limit'), (400, 'model_bad_request'), (404, 'model_unavailable')):
            with self.subTest(code=code):
                result, trace, requests, sleeper, exists = self.run_sequence([(code, {})])
                self.assertEqual(result['reason'], reason)
                self.assertEqual(len(requests), 1)
                sleeper.assert_not_called()

    def test_retry_allowance_is_run_wide_not_reset_after_success(self):
        result, trace, requests, sleeper, exists = self.run_sequence([
            (503, {}), (200, response()), (503, {})], max_model_retries=1)
        self.assertEqual(result['reason'], 'gemini_503_retry_limit')
        self.assertEqual(len(requests), 3)
        sleeper.assert_called_once()

    def test_backoff_oversleep_does_not_start_another_call(self):
        from gtm_research.model import RetryableModelError
        from helpers import FakeModel
        clock = [0.0]
        def oversleep(delay):
            clock[0] += 3
        model = FakeModel([RetryableModelError('gemini_http_503')])
        with tempfile.TemporaryDirectory() as directory, \
             patch('gtm_research.agent.monotonic', side_effect=lambda: clock[0]), \
             patch('gtm_research.agent.uniform', return_value=1.0), \
             patch('gtm_research.agent.sleep', side_effect=oversleep):
            result = run_research(model, fixture_reader(), directory, max_seconds=2)
        self.assertEqual(result['reason'], 'time_limit')
        self.assertEqual(result['metadata']['model_calls'], 1)
        self.assertEqual(len(model.states), 1)

    def test_exponential_delay_has_a_hard_cap(self):
        result, trace, requests, sleeper, exists = self.run_sequence(
            [(503, {})] * 6, max_model_retries=5, max_steps=8)
        self.assertEqual(result['reason'], 'gemini_503_retry_limit')
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [1, 2, 4, 8, 8])
