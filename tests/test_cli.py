"""Offline smoke checks for the installed CLI contract."""

import shutil
import subprocess
import unittest
from importlib.metadata import version


class CliSmokeTests(unittest.TestCase):
    def run_cli(self, *args):
        executable = shutil.which("gtm-research")
        self.assertIsNotNone(executable, "Install the project and activate its environment first")
        return subprocess.run(
            [executable, *args], capture_output=True, text=True, timeout=10
        )

    def test_help_discloses_foundation_only(self):
        result = self.run_cli("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("research is not implemented", result.stdout)

    def test_version_matches_installed_package(self):
        result = self.run_cli("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"gtm-research {version('gtm-account-research')}")

    def test_research_argument_is_not_supported(self):
        result = self.run_cli("example.com")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unrecognized arguments", result.stderr)
