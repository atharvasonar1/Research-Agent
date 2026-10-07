"""Offline checks of the installed CLI and configuration errors."""

from importlib.metadata import version
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from gtm_research.cli import main


class CliSmokeTests(unittest.TestCase):
    def run_cli(self, *args):
        executable = shutil.which("gtm-research")
        self.assertIsNotNone(executable, "Install the project and activate its environment first")
        env = {key: value for key, value in os.environ.items() if key not in ("OPENAI_API_KEY", "OPENAI_MODEL", "GEMINI_API_KEY", "GEMINI_MODEL", "RESEARCH_PROVIDER")}
        return subprocess.run([executable, *args], capture_output=True, text=True, timeout=10, env=env)

    def test_help_lists_research(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("research", result.stdout)
        self.assertIn("verify-saved", result.stdout)
        self.assertIn("evaluate-support", result.stdout)

    def test_version_matches_installed_package(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"gtm-research {version('gtm-account-research')}")

    def test_missing_credentials_clear_error(self):
        result = self.run_cli("research", "team.example", "--model", "test-model")
        self.assertEqual(result.returncode, 2)
        self.assertIn("set OPENAI_API_KEY", result.stderr)

    def test_model_must_be_selected(self):
        result = self.run_cli("research", "team.example")
        self.assertEqual(result.returncode, 2)
        self.assertIn("provide --model", result.stderr)

    def test_invalid_budgets(self):
        for option, value in (("--max-steps", "0"), ("--max-steps", "9"), ("--max-seconds", "nan"), ("--page-timeout", "-1")):
            result = self.run_cli("research", "team.example", option, value)
            self.assertEqual(result.returncode, 2)

    def test_cli_success_and_failure_exit_codes(self):
        from helpers import FakeModel, fetch, fixture_reader, submit
        with tempfile.TemporaryDirectory() as directory:
            for actions, expected in (([fetch(), submit()], 0), ([fetch(), fetch()], 1)):
                model = FakeModel(actions)
                model.close = lambda: None
                with patch.dict(os.environ, {"OPENAI_API_KEY": "test-secret"}), \
                     patch("gtm_research.model.OpenAIModel", return_value=model), \
                     patch("gtm_research.model.OpenAISupportVerifier", return_value=model), \
                     patch("gtm_research.reader.WebsiteReader", return_value=fixture_reader()), \
                     patch("builtins.print"):
                    result = main(["research", "team.example", "--model", "test-model", "--max-steps", "3", "--output-dir", directory])
                self.assertEqual(result, expected)

    def test_gemini_key_error_names_correct_provider(self):
        result = self.run_cli("research", "team.example", "--provider", "gemini", "--model", "gemini-2.5-flash")
        self.assertEqual(result.returncode, 2)
        self.assertIn("set GEMINI_API_KEY", result.stderr)

    def test_gemini_selected_from_explicit_env_file(self):
        from pathlib import Path
        from helpers import FakeModel, fetch, fixture_reader, submit
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env.local'
            path.write_text('GEMINI_API_KEY=hidden-key\nGEMINI_MODEL=gemini-2.5-flash\nRESEARCH_PROVIDER=gemini\n')
            model = FakeModel([fetch(), submit()])
            model.close = lambda: None
            with patch.dict(os.environ, {}, clear=True), \
                 patch("gtm_research.gemini.GeminiModel", return_value=model) as factory, \
                 patch("gtm_research.gemini.GeminiSupportVerifier", return_value=model), \
                 patch("gtm_research.model.OpenAIModel") as openai, \
                 patch("gtm_research.reader.WebsiteReader", return_value=fixture_reader()), \
                 patch("builtins.print"):
                result = main(["research", "team.example", "--env-file", str(path), "--output-dir", directory])
            self.assertEqual(result, 0)
            factory.assert_called_once_with('gemini-2.5-flash', 'hidden-key')
            openai.assert_not_called()

    def test_verify_saved_uses_candidate_trace_without_reader(self):
        from pathlib import Path
        from helpers import FakeModel, ROOT, brief, fixture_reader
        with tempfile.TemporaryDirectory() as directory:
            trace = Path(directory) / "trace.json"
            candidate = brief()
            ref = candidate["claims"][0]["evidence_refs"][0]
            reader = fixture_reader()
            page = reader.fetch(ROOT)
            trace.write_text(__import__("json").dumps({
                "candidate_brief": candidate, "pages": [page],
                "sources": {"S1": {"url": ref["url"], "fetched_at": ref["fetched_at"],
                                    "evidence": {"E1": {"start": ref["start"], "end": ref["end"], "text": ref["text"]}}}},
            }))
            checker = FakeModel([])
            checker.close = lambda: None
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test-secret"}), \
                 patch("gtm_research.model.OpenAISupportVerifier", return_value=checker), \
                 patch("builtins.print"):
                result = main(["verify-saved", str(trace), "--model", "test-model",
                               "--output-dir", directory])
            self.assertEqual(result, 0)
            outputs = list(Path(directory).glob("*/verified-brief.json"))
            self.assertEqual(len(outputs), 1)
