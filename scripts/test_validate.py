"""Unit and integration tests for validate.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
VALIDATE_PY = SCRIPTS_DIR / "validate.py"


def _import_validate():
    spec = importlib.util.spec_from_file_location("validate", VALIDATE_PY)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _assert_has_error(errors: list[str], *keywords: str) -> None:
    assert any(kw in e.lower() for e in errors for kw in keywords), (
        f"Expected error mentioning {keywords!r}, got: {errors}"
    )


_V = _import_validate()

GOOD_PLUGIN_JSON = {
    "name": "bsamek",
    "description": "A fine plugin.",
    "version": "0.2.0",
    "author": {"name": "Brian Samek"},
}

GOOD_SKILL_MD = textwrap.dedent("""\
    ---
    name: myfoo
    description: Does the foo thing.
    ---
    # Body
""")


class TestCheckPluginJson(unittest.TestCase):
    def _write_json(self, tmp, data):
        p = Path(tmp) / "plugin.json"
        p.write_text(json.dumps(data))
        return p

    def test_good_plugin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, GOOD_PLUGIN_JSON)
            errors = _V.check_plugin_json(p)
        self.assertEqual(errors, [])

    def test_missing_version_fails(self):
        data = {k: v for k, v in GOOD_PLUGIN_JSON.items() if k != "version"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "version")

    def test_empty_name_fails(self):
        data = {**GOOD_PLUGIN_JSON, "name": ""}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "name")

    def test_bad_semver_fails(self):
        data = {**GOOD_PLUGIN_JSON, "version": "1.0"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "version")

    def test_missing_author_name_fails(self):
        data = {**GOOD_PLUGIN_JSON, "author": {"name": ""}}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "author")

    def test_author_not_object_fails(self):
        data = {**GOOD_PLUGIN_JSON, "author": "Brian"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "author")

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plugin.json"
            p.write_text("{not valid json")
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "invalid", "json", "parse")

    def test_missing_description_fails(self):
        data = {k: v for k, v in GOOD_PLUGIN_JSON.items() if k != "description"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = _V.check_plugin_json(p)
        _assert_has_error(errors, "description")


class TestCheckSkillMd(unittest.TestCase):
    def _write_skill(self, parent_dir, skill_name, content):
        skill_dir = Path(parent_dir) / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        p = skill_dir / "SKILL.md"
        p.write_text(content)
        return p

    def test_good_skill_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", GOOD_SKILL_MD)
            errors = _V.check_skill_md(p)
        self.assertEqual(errors, [])

    def test_missing_description_fails(self):
        content = textwrap.dedent("""\
            ---
            name: myfoo
            ---
            # Body
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = _V.check_skill_md(p)
        _assert_has_error(errors, "description")

    def test_missing_name_fails(self):
        content = textwrap.dedent("""\
            ---
            description: Does the foo thing.
            ---
            # Body
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = _V.check_skill_md(p)
        _assert_has_error(errors, "name")

    def test_name_mismatch_fails(self):
        content = textwrap.dedent("""\
            ---
            name: wrongname
            description: Does the foo thing.
            ---
            # Body
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = _V.check_skill_md(p)
        _assert_has_error(errors, "myfoo", "wrongname", "match")

    def test_no_frontmatter_fails(self):
        content = "# Just a heading\n\nNo frontmatter here.\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = _V.check_skill_md(p)
        _assert_has_error(errors, "frontmatter")

    def test_empty_description_fails(self):
        content = textwrap.dedent("""\
            ---
            name: myfoo
            description: ""
            ---
            # Body
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = _V.check_skill_md(p)
        _assert_has_error(errors, "description")


class TestRealRepo(unittest.TestCase):
    def test_real_repo_passes(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATE_PY)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "validate.yml"


class TestWorkflowFile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import yaml
        with WORKFLOW_PATH.open() as fh:
            cls._workflow = yaml.safe_load(fh)

    def test_triggers_push_and_pull_request(self):
        on = self._workflow.get("on", {})
        self.assertIn("push", on, "Workflow must trigger on push")
        self.assertIn("pull_request", on, "Workflow must trigger on pull_request")

    def test_runner_is_ubuntu_latest(self):
        jobs = self._workflow.get("jobs", {})
        self.assertTrue(len(jobs) > 0, "Workflow must have at least one job")
        for job_name, job in jobs.items():
            self.assertEqual(
                job.get("runs-on"),
                "ubuntu-latest",
                f"Job '{job_name}' must use ubuntu-latest runner",
            )

    def test_validate_command_present(self):
        jobs = self._workflow.get("jobs", {})
        found = any(
            "python3 scripts/validate.py" in step.get("run", "")
            for job in jobs.values()
            for step in job.get("steps", [])
        )
        self.assertTrue(found, "No step found running 'python3 scripts/validate.py'")

    def test_checkout_step_present(self):
        jobs = self._workflow.get("jobs", {})
        found = any(
            step.get("uses", "").startswith("actions/checkout")
            for job in jobs.values()
            for step in job.get("steps", [])
        )
        self.assertTrue(found, "No checkout step found in workflow")


if __name__ == "__main__":
    unittest.main()
