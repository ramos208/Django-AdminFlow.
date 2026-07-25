# Development Guide

This document is for **contributors and maintainers** of `django-adminflow`.
It covers local setup, the Makefile workflow, version bumping, and publishing to PyPI.

---

## Project Structure

```
AdminFlow Package/
├── adminflow/               ← the Django app (templates, static, views, etc.)
├── docs/                    ← Sphinx documentation (readthedocs.io)
├── scripts/
│   └── bump_version.py      ← auto version bump + changelog generator
├── dist/                    ← built package artifacts (generated, git-ignored)
├── Makefile                 ← all dev commands
├── pyproject.toml           ← package metadata and version
├── CHANGELOG.md             ← auto-updated by bump_version.py
└── DEVELOPMENT.md           ← this file
```

---

## Local Setup

### 1. Clone / open the project

```bash
cd "AdminFlow Package"
```

### 2. Activate the virtual environment

This package uses the venv from the sibling `django test` project for development:

```bash
source "../django test/.venv/bin/activate"
```

### 3. Install the package in editable mode

```bash
pip install -e ".[all]"
```

Changes to `adminflow/` take effect immediately — no reinstall needed.

### 4. Run the test project

```bash
cd "../django test"
python manage.py runserver
# Admin: http://127.0.0.1:8000/admin/
```

---

## Makefile Reference

All commands are run from the `AdminFlow Package/` directory.

```bash
make <target>
```

### Available Targets

| Target | Description |
|---|---|
| `make help` | Show all available targets |
| `make version` | Print the current version |
| `make patch` | Bump **patch** version → build → validate → upload to PyPI |
| `make minor` | Bump **minor** version → build → validate → upload to PyPI |
| `make major` | Bump **major** version → build → validate → upload to PyPI |
| `make build` | Build `dist/` only (no version bump, no upload) |
| `make check` | Validate `dist/` files with `twine check` |
| `make publish` | Upload existing `dist/` to PyPI (no rebuild) |
| `make docs` | Build Sphinx HTML docs locally |
| `make docs-open` | Build Sphinx docs and open in browser |
| `make clean` | Remove `dist/`, `build/`, `docs/_build/`, `__pycache__` |

---

## Publishing a New Release

### Which version type to use?

Follow [Semantic Versioning](https://semver.org/):

| Change type | Command | Example |
|---|---|---|
| Bug fix, small tweak | `make patch` | `1.0.0` → `1.0.1` |
| New feature, backward-compatible | `make minor` | `1.0.0` → `1.1.0` |
| Breaking change | `make major` | `1.0.0` → `2.0.0` |

---

### Step-by-step: publish a patch release

```bash
# 1. Make sure you are in the right directory
cd "/Users/edgar208/Desktop/Github/Django Pypi package/AdminFlow Package"

# 2. Activate the venv
source "../django test/.venv/bin/activate"

# 3. Check current version
make version
# → 1.0.0

# 4. Run the release
make patch
```

The Makefile will then:

1. **Run `bump_version.py patch`** — bumps `pyproject.toml` from `1.0.0` → `1.0.1`

2. **Ask you for changelog entries interactively:**
   ```
     Current version : 1.0.0
     New version     : 1.0.1  (patch bump)
     Release date    : 2026-07-25

     Enter what's new (one item per line).
     Press ENTER on an empty line when done.

     • Fixed JSON export nesting for empty child lists
     • Improved sidebar collapse animation on mobile
     •            ← press ENTER here to finish
   ```

3. **Update files automatically:**
   ```
     ✓  pyproject.toml      → version = "1.0.1"
     ✓  CHANGELOG.md        → [1.0.1] prepended
     ✓  docs/changelog.rst  → 1.0.1 prepended
   ```

4. **Build `dist/`:**
   ```
     Building dist/...
     ✓  Build complete:
        django_adminflow-1.0.1-py3-none-any.whl
        django_adminflow-1.0.1.tar.gz
   ```

5. **Validate with twine:**
   ```
     Validating dist/ with twine...
     Checking dist/django_adminflow-1.0.1.whl: PASSED
     Checking dist/django_adminflow-1.0.1.tar.gz: PASSED
   ```

6. **Upload to PyPI** — prompts for credentials:
   ```
     Uploading to PyPI...
     (Username: __token__  |  Password: your pypi-xxxx token)

     Enter your username: __token__
     Enter your password: pypi-xxxxxxxxxxxxxxxxxxxx
   ```

7. **Done!**
   ```
     🚀  Published patch release to PyPI!
   ```

---

## PyPI Authentication

### Get your API token

1. Log in to [pypi.org](https://pypi.org)
2. **Account Settings** → **API tokens** → **Add API token**
3. Name: `django-adminflow`
4. Scope: **Project: django-adminflow** (or "Entire account" for first upload)
5. Copy the token — it starts with `pypi-`

### Save token so you are never prompted again

Create `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

```bash
chmod 600 ~/.pypirc
```

After this, `twine upload` runs without any prompts.

---

## Build Only (no upload)

If you want to build and inspect the package before publishing:

```bash
make build
```

Then inspect the contents:

```bash
# List files in the wheel
unzip -l dist/django_adminflow-*.whl

# Check package metadata
make check
```

---

## Upload Only (already built)

If `dist/` already has the right artifacts:

```bash
make publish
```

---

## Docs

### Build locally

```bash
make docs
# HTML output: docs/_build/html/index.html

make docs-open   # build + open in browser (macOS)
```

### Dependencies for docs

```bash
pip install sphinx sphinx-rtd-theme myst-parser sphinx-copybutton
```

Or via the docs requirements file:

```bash
pip install -r docs/requirements.txt
```

---

## CHANGELOG.md Format

The `bump_version.py` script auto-prepends new entries at the top of `CHANGELOG.md`.

Each entry follows [Keep a Changelog](https://keepachangelog.com/) format:

```markdown
## [1.0.1] — 2026-07-25

- Fixed JSON export nesting for empty child lists
- Improved sidebar collapse animation on mobile
```

The same content is also written to `docs/changelog.rst` automatically.

---

## Version Numbering

The version is stored in **one place only**: `pyproject.toml`.

```toml
[project]
version = "1.0.0"
```

`bump_version.py` reads and writes this file — never edit the version manually.

---

## Common Errors

### `twine: command not found`
```bash
pip install twine
```

### `build: command not found`
```bash
pip install build
```

### `ERROR: File already exists` on upload
You are trying to upload a version that already exists on PyPI.
You **cannot** overwrite an existing version — bump the version first:
```bash
make patch
```

### `Invalid distribution` on `twine check`
Check your `README.md` for invalid rst-in-markdown or broken image links.
