"""Regression checks for immutable Actions and process-free Rust asset validation."""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SecurityTests(unittest.TestCase):
    def test_action_references_are_pinned(self):
        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            refs = re.findall(r"uses:\s*(\S+)", workflow.read_text())
            self.assertTrue(refs, workflow.name)
            for ref in refs:
                self.assertRegex(ref, r"^[\w.-]+/[\w./-]+@[0-9a-f]{40}$")

    def test_dependency_installation_is_explicit_and_script_free(self):
        for workflow in (ROOT / ".github/workflows").glob("*.yml"):
            self.assertNotIn("npm install", workflow.read_text())
            for line in workflow.read_text().splitlines():
                if "npm ci" in line:
                    self.assertIn("--ignore-scripts", line)
        self.assertNotIn("Command", (ROOT / "crates/librqbit/build.rs").read_text())

    def test_rust_asset_check(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            binary = cwd / "check-assets"
            subprocess.run(["rustc", "--edition=2024", "--cfg", 'feature="webui"',
                            str(ROOT / "crates/librqbit/build.rs"), "-o", str(binary)],
                           check=True)
            missing = subprocess.run([str(binary)], cwd=cwd, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("npm ci --ignore-scripts", missing.stderr)
            for asset in ("index.html", "assets/index.js", "assets/index.css", "assets/logo.svg"):
                path = cwd / "webui/dist" / asset
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test fixture")
            subprocess.run([str(binary)], cwd=cwd, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()
