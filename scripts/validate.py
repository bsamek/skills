#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PLUGIN_JSON = REPO_ROOT / "plugins" / "bsamek" / ".claude-plugin" / "plugin.json"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def check_plugin_json(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        text = path.read_text()
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        errors.append(f"plugin.json: invalid JSON — {exc}")
        return errors
    except OSError as exc:
        errors.append(f"plugin.json: cannot read — {exc}")
        return errors

    version = data.get("version", "")
    for field in ("name", "description", "version"):
        val = data.get(field)
        if not isinstance(val, str) or not val.strip():
            errors.append(f"plugin.json: '{field}' must be a non-empty string")

    author = data.get("author")
    if not isinstance(author, dict):
        errors.append("plugin.json: 'author' must be an object")
    else:
        author_name = author.get("name")
        if not isinstance(author_name, str) or not author_name.strip():
            errors.append("plugin.json: 'author.name' must be a non-empty string")

    if isinstance(version, str) and version.strip() and not SEMVER_RE.match(version):
        errors.append(
            f"plugin.json: 'version' must be semver (X.Y.Z), got '{version}'"
        )

    return errors


def _parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return None
    fm_lines = lines[1:end]
    result: dict[str, str] = {}
    for line in fm_lines:
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def check_skill_md(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        text = path.read_text()
    except OSError as exc:
        errors.append(f"{path}: cannot read — {exc}")
        return errors

    fm = _parse_frontmatter(text)
    if fm is None:
        errors.append(f"{path}: missing or malformed YAML frontmatter")
        return errors

    name_val = fm.get("name", "")
    desc_val = fm.get("description", "")

    if not name_val:
        errors.append(f"{path}: frontmatter 'name' is missing or empty")

    if not desc_val:
        errors.append(f"{path}: frontmatter 'description' is missing or empty")

    expected_name = path.parent.name
    if name_val and name_val != expected_name:
        errors.append(
            f"{path}: frontmatter name '{name_val}' does not match "
            f"directory '{expected_name}'"
        )

    return errors


def _report(label: str, errors: list[str]) -> bool:
    print(f"Checking {label} …")
    if errors:
        for e in errors:
            print(f"  FAIL  {e}")
        return False
    print("  OK")
    return True


def main() -> int:
    all_ok = True

    # --- plugin.json ---
    all_ok &= _report(str(PLUGIN_JSON), check_plugin_json(PLUGIN_JSON))

    # --- SKILL.md files ---
    plugins_root = REPO_ROOT / "plugins"
    skill_files = sorted(plugins_root.rglob("SKILL.md"))
    if not skill_files:
        print("WARNING: no SKILL.md files found under plugins/")
    for skill_md in skill_files:
        all_ok &= _report(
            str(skill_md.relative_to(REPO_ROOT)), check_skill_md(skill_md)
        )

    if all_ok:
        print("\nAll checks passed.")
        return 0
    print("\nOne or more checks FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
