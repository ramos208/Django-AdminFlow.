#!/usr/bin/env python3
"""
scripts/bump_version.py
=======================
Auto-bumps the version in pyproject.toml, collects a changelog,
and writes it to both CHANGELOG.md and docs/changelog.rst.

Usage:
    python scripts/bump_version.py patch   # 1.0.0 → 1.0.1
    python scripts/bump_version.py minor   # 1.0.0 → 1.1.0
    python scripts/bump_version.py major   # 1.0.0 → 2.0.0
    python scripts/bump_version.py current # just print current version
"""

import re
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Paths ──────────────────────────────────────────────────────────────────
PYPROJECT   = ROOT / "pyproject.toml"
CHANGELOG   = ROOT / "CHANGELOG.md"
CHANGELOG_RST = ROOT / "docs" / "changelog.rst"


def read_version() -> str:
    text = PYPROJECT.read_text()
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise ValueError("Could not find version in pyproject.toml")
    return m.group(1)


def bump(version: str, part: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump part: {part!r}")


def write_version(new_version: str):
    text = PYPROJECT.read_text()
    updated = re.sub(
        r'^(version\s*=\s*)"[^"]+"',
        f'\\g<1>"{new_version}"',
        text,
        flags=re.MULTILINE,
    )
    PYPROJECT.write_text(updated)


def collect_changelog_items() -> list[str]:
    print()
    print("  Enter what's new (one item per line).")
    print("  Press ENTER on an empty line when done.")
    print()
    items = []
    while True:
        try:
            line = input("  • ").strip()
        except EOFError:
            break
        if not line:
            break
        items.append(line)
    return items


def prepend_changelog_md(version: str, date: str, items: list[str]):
    bullet_lines = "\n".join(f"- {item}" for item in items)
    entry = f"## [{version}] — {date}\n\n{bullet_lines}\n\n"

    if CHANGELOG.exists():
        existing = CHANGELOG.read_text()
        # Insert after the first heading line
        if existing.startswith("# "):
            first_newline = existing.index("\n") + 1
            new_text = existing[:first_newline] + "\n" + entry + existing[first_newline:]
        else:
            new_text = entry + existing
    else:
        new_text = f"# Changelog\n\nAll notable changes are documented here.\n\n" + entry

    CHANGELOG.write_text(new_text)


def prepend_changelog_rst(version: str, date: str, items: list[str]):
    bullet_lines = "\n".join(f"* {item}" for item in items)
    anchor = version.replace(".", "-")
    entry = (
        f"`{version}`_ — {date}\n"
        f"{'-' * (len(version) + len(date) + 7)}\n\n"
        f"Added\n~~~~~\n\n"
        f"{bullet_lines}\n\n"
        f".. _`{version}`: https://github.com/ramos208/Django-AdminFlow./releases/tag/v{version}\n\n"
    )

    if CHANGELOG_RST.exists():
        existing = CHANGELOG_RST.read_text()
        # Insert after the "Changelog\n=========\n\n----\n\n" header block
        marker = "----\n\n"
        idx = existing.find(marker)
        if idx != -1:
            insert_at = idx + len(marker)
            new_text = existing[:insert_at] + entry + existing[insert_at:]
        else:
            new_text = entry + existing
    else:
        header = "Changelog\n=========\n\nAll notable changes to this project are documented here.\n\n----\n\n"
        new_text = header + entry

    CHANGELOG_RST.write_text(new_text)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("patch", "minor", "major", "current"):
        print("Usage: python scripts/bump_version.py [patch|minor|major|current]")
        sys.exit(1)

    part = sys.argv[1]
    current = read_version()

    if part == "current":
        print(current)
        return

    new_version = bump(current, part)
    date = datetime.date.today().strftime("%Y-%m-%d")

    print(f"\n  Current version : {current}")
    print(f"  New version     : {new_version}  ({part} bump)")
    print(f"  Release date    : {date}")

    # Collect what's new
    items = collect_changelog_items()

    if not items:
        print("\n  ⚠  No changelog items entered — aborting.")
        sys.exit(1)

    # Apply changes
    write_version(new_version)
    prepend_changelog_md(new_version, date, items)
    prepend_changelog_rst(new_version, date, items)

    print(f"\n  ✓  pyproject.toml  → version = \"{new_version}\"")
    print(f"  ✓  CHANGELOG.md    → [{new_version}] added")
    print(f"  ✓  docs/changelog.rst → {new_version} added")
    print(f"\n  {new_version}")   # last line = new version (captured by Makefile)


if __name__ == "__main__":
    main()
