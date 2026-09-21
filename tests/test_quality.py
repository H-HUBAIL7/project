import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("flake8"), "flake8 not installed")
class CodeQualityTests(unittest.TestCase):
    def run_flake8(self, target: str) -> str:
        result = subprocess.run(
            ["flake8", "--max-line-length=79", target],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def test_application_is_pep8_compliant(self) -> None:
        self.assertEqual(self.run_flake8("app"), "")

    def test_tests_are_pep8_compliant(self) -> None:
        self.assertEqual(self.run_flake8("tests"), "")
