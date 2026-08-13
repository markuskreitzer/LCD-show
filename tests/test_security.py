import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SecurityPolicyTests(unittest.TestCase):
    def test_github_actions_use_immutable_commit_pins(self):
        workflows = list((ROOT / ".github/workflows").glob("*.yml"))
        self.assertTrue(workflows)
        for workflow in workflows:
            for line in workflow.read_text().splitlines():
                match = re.search(r"\buses:\s*([^\s]+)", line)
                if match:
                    self.assertRegex(match.group(1), r"^[^@]+@[0-9a-f]{40}$")

    def test_modern_runtime_has_no_network_install_commands(self):
        files = [ROOT / "MHS35-safe", *sorted((ROOT / "modern").glob("*"))]
        forbidden = ("curl ", "wget ", "git clone", "pip install", "apt-get", "http://", "https://")
        for path in files:
            if path.is_file():
                text = path.read_text(errors="ignore")
                for pattern in forbidden:
                    self.assertNotIn(pattern, text, f"{pattern!r} found in {path}")

    def test_dependabot_tracks_action_updates(self):
        config = (ROOT / ".github/dependabot.yml").read_text()
        self.assertIn("package-ecosystem: github-actions", config)


if __name__ == "__main__":
    unittest.main()
