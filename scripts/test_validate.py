"""Unit and integration tests for validate.py."""

import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
VALIDATE_PY = SCRIPTS_DIR / "validate.py"


def _import_validate():
    spec = importlib.util.spec_from_file_location("validate", VALIDATE_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    def setUp(self):
        self.v = _import_validate()

    def _write_json(self, tmp, data):
        p = Path(tmp) / "plugin.json"
        p.write_text(json.dumps(data))
        return p

    def test_good_plugin_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, GOOD_PLUGIN_JSON)
            errors = self.v.check_plugin_json(p)
        self.assertEqual(errors, [])

    def test_missing_version_fails(self):
        data = {k: v for k, v in GOOD_PLUGIN_JSON.items() if k != "version"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("version" in e.lower() for e in errors), errors)

    def test_empty_name_fails(self):
        data = {**GOOD_PLUGIN_JSON, "name": ""}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("name" in e.lower() for e in errors), errors)

    def test_bad_semver_fails(self):
        data = {**GOOD_PLUGIN_JSON, "version": "1.0"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("version" in e.lower() for e in errors), errors)

    def test_missing_author_name_fails(self):
        data = {**GOOD_PLUGIN_JSON, "author": {"name": ""}}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("author" in e.lower() for e in errors), errors)

    def test_author_not_object_fails(self):
        data = {**GOOD_PLUGIN_JSON, "author": "Brian"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("author" in e.lower() for e in errors), errors)

    def test_invalid_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "plugin.json"
            p.write_text("{not valid json")
            errors = self.v.check_plugin_json(p)
        self.assertTrue(len(errors) > 0, errors)

    def test_missing_description_fails(self):
        data = {k: v for k, v in GOOD_PLUGIN_JSON.items() if k != "description"}
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_json(tmp, data)
            errors = self.v.check_plugin_json(p)
        self.assertTrue(any("description" in e.lower() for e in errors), errors)


class TestCheckSkillMd(unittest.TestCase):
    def setUp(self):
        self.v = _import_validate()

    def _write_skill(self, parent_dir, skill_name, content):
        skill_dir = Path(parent_dir) / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        p = skill_dir / "SKILL.md"
        p.write_text(content)
        return p

    def test_good_skill_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", GOOD_SKILL_MD)
            errors = self.v.check_skill_md(p)
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
            errors = self.v.check_skill_md(p)
        self.assertTrue(any("description" in e.lower() for e in errors), errors)

    def test_missing_name_fails(self):
        content = textwrap.dedent("""\
            ---
            description: Does the foo thing.
            ---
            # Body
        """)
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = self.v.check_skill_md(p)
        self.assertTrue(any("name" in e.lower() for e in errors), errors)

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
            errors = self.v.check_skill_md(p)
        self.assertTrue(any("myfoo" in e or "wrongname" in e or "match" in e.lower() for e in errors), errors)

    def test_no_frontmatter_fails(self):
        content = "# Just a heading\n\nNo frontmatter here.\n"
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write_skill(tmp, "myfoo", content)
            errors = self.v.check_skill_md(p)
        self.assertTrue(len(errors) > 0, errors)

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
            errors = self.v.check_skill_md(p)
        self.assertTrue(any("description" in e.lower() for e in errors), errors)


class TestRealRepo(unittest.TestCase):
    def test_real_repo_passes(self):
        """The current repo should pass all validation checks."""
        import subprocess
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


if __name__ == "__main__":
    unittest.main()
