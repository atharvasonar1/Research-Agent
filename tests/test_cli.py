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
        env = {key: value for key, value in os.environ.items() if key not in ("OPENAI_API_KEY", "OPENAI_MODEL")}
        return subprocess.run([executable, *args], capture_output=True, text=True, timeout=10, env=env)

    def test_help_lists_research(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("research", result.stdout)

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
        for option, value in (("--max-steps", "0"), ("--max-seconds", "nan"), ("--page-timeout", "-1")):
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
                     patch("gtm_research.reader.WebsiteReader", return_value=fixture_reader()), \
                     patch("builtins.print"):
                    result = main(["research", "team.example", "--model", "test-model", "--max-steps", "2", "--output-dir", directory])
                self.assertEqual(result, expected)
