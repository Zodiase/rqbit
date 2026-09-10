"""Regression checks for immutable Actions and process-free Rust asset validation."""

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def parse_yaml(source):
    # Use the declared, lockfile-pinned YAML parser rather than matching YAML text.
    result = subprocess.run(
        ["node", "-e",
         "let s=''; process.stdin.setEncoding('utf8'); process.stdin.on('data',c=>s+=c); "
         "process.stdin.on('end',()=>process.stdout.write(JSON.stringify(require('js-yaml').load(s))));"],
        input=source, text=True, capture_output=True, check=True, cwd=ROOT, timeout=10)
    return json.loads(result.stdout)


def workflows():
    return [(path, parse_yaml(path.read_text()))
            for path in sorted((ROOT / ".github/workflows").glob("*.yml"))]


def values_for(node, key):
    if isinstance(node, dict):
        for name, value in node.items():
            if name == key:
                yield value
            yield from values_for(value, key)
    elif isinstance(node, list):
        for value in node:
            yield from values_for(value, key)


def valid_reference(ref):
    if not isinstance(ref, str):
        return False
    if ref.startswith("./"):
        return bool(re.fullmatch(r"\./[\w./-]+", ref)) and ".." not in ref.split("/")
    if ref.startswith("docker://"):
        return bool(re.fullmatch(r"docker://[^\s@]+@sha256:[0-9a-f]{64}", ref))
    return bool(re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", ref))


class SecurityTests(unittest.TestCase):
    def test_action_references_are_pinned(self):
        for workflow, document in workflows():
            refs = list(values_for(document, "uses"))
            self.assertTrue(refs, workflow.name)
            for ref in refs:
                self.assertTrue(valid_reference(ref), ref)

    def test_reference_policy(self):
        for ref in ("./actions/local", "owner/repo@" + "a" * 40,
                    "docker://alpine@sha256:" + "b" * 64):
            self.assertTrue(valid_reference(ref), ref)
        for ref in ("owner/repo@main", "docker://alpine:latest", "./../outside", "./"):
            self.assertFalse(valid_reference(ref), ref)

    def test_yaml_comments_and_booleans(self):
        document = parse_yaml("steps:\n- uses: './local' # uses: unsafe@main\n  with:\n    persist-credentials: false\n")
        self.assertEqual(list(values_for(document, "uses")), ["./local"])
        self.assertEqual(list(values_for(document, "persist-credentials")), [False])

    def test_dependency_installation_is_explicit_and_script_free(self):
        for workflow, document in workflows():
            for command in values_for(document, "run"):
                for line in command.splitlines():
                    if line.lstrip().startswith("#"):
                        continue
                    self.assertNotRegex(line, r"\bnpm\s+install\b")
                    if re.search(r"\bnpm\s+ci\b", line):
                        self.assertRegex(line, r"--ignore-scripts(?:\s|$)")
        self.assertNotIn("Command", (ROOT / "crates/librqbit/build.rs").read_text())

    def test_checkout_does_not_persist_credentials(self):
        for workflow, document in workflows():
            for job in document["jobs"].values():
                for step in job.get("steps", []):
                    if step.get("uses", "").startswith("actions/checkout@"):
                        self.assertIs(step.get("with", {}).get("persist-credentials"), False,
                                      workflow.name)

    def test_rust_asset_check(self):
        with tempfile.TemporaryDirectory() as directory:
            cwd = Path(directory)
            binary = cwd / ("check-assets.exe" if os.name == "nt" else "check-assets")
            subprocess.run(["rustc", "--edition=2024", "--cfg", 'feature="webui"',
                            str(ROOT / "crates/librqbit/build.rs"), "-o", str(binary)],
                           check=True, timeout=60)
            missing = subprocess.run([str(binary)], cwd=cwd, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("npm ci --ignore-scripts", missing.stderr)
            for asset in ("index.html", "assets/index.js", "assets/index.css", "assets/logo.svg"):
                path = cwd / "webui/dist" / asset
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test fixture")
            subprocess.run([str(binary)], cwd=cwd, check=True, capture_output=True, timeout=10)


if __name__ == "__main__":
    unittest.main()
