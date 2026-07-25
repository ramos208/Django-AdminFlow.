# ─────────────────────────────────────────────────────────────────────────────
# django-adminflow — Makefile
#
# Usage:
#   make patch      bump patch version, collect changelog, build, upload
#   make minor      bump minor version, collect changelog, build, upload
#   make major      bump major version, collect changelog, build, upload
#   make build      build dist/ only (no version bump, no upload)
#   make publish    upload existing dist/ to PyPI
#   make check      validate dist/ with twine check
#   make docs       build Sphinx HTML docs locally
#   make clean      remove dist/, build/, docs/_build/
#   make version    print current version
# ─────────────────────────────────────────────────────────────────────────────

PYTHON  := python3
TWINE   := twine
SPHINX  := sphinx-build
DOCSDIR := docs
DISTDIR := dist

.PHONY: help patch minor major build publish check docs clean version

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  django-adminflow publish workflow"
	@echo "  ─────────────────────────────────"
	@echo "  make patch    bump patch version (1.0.0 → 1.0.1), build & upload"
	@echo "  make minor    bump minor version (1.0.0 → 1.1.0), build & upload"
	@echo "  make major    bump major version (1.0.0 → 2.0.0), build & upload"
	@echo "  make build    build dist/ only"
	@echo "  make publish  upload current dist/ to PyPI  (reads token from .env)"
	@echo "  make check    validate dist/ with twine"
	@echo "  make docs     build Sphinx HTML docs"
	@echo "  make clean    remove dist/, build/, docs/_build/"
	@echo "  make version  print current version"
	@echo ""

# ── Version ───────────────────────────────────────────────────────────────────
version:
	@$(PYTHON) scripts/bump_version.py current

# ── Bump + build + publish ────────────────────────────────────────────────────
patch: _bump-patch build check publish
	@echo ""
	@echo "  🚀  Published patch release to PyPI!"

minor: _bump-minor build check publish
	@echo ""
	@echo "  🚀  Published minor release to PyPI!"

major: _bump-major build check publish
	@echo ""
	@echo "  🚀  Published major release to PyPI!"

_bump-patch:
	@$(PYTHON) scripts/bump_version.py patch

_bump-minor:
	@$(PYTHON) scripts/bump_version.py minor

_bump-major:
	@$(PYTHON) scripts/bump_version.py major

# ── Build dist/ ───────────────────────────────────────────────────────────────
build: clean-dist
	@echo ""
	@echo "  Building dist/..."
	@$(PYTHON) -m build
	@echo "  ✓  Build complete:"
	@ls -1 $(DISTDIR)/

# ── Validate ──────────────────────────────────────────────────────────────────
check:
	@echo ""
	@echo "  Validating dist/ with twine..."
	@$(TWINE) check $(DISTDIR)/*

# ── Upload to PyPI ────────────────────────────────────────────────────────────
publish:
	@if [ ! -f .env ]; then \
		echo "  ✗  .env file not found — create one with: token=pypi-xxxx"; \
		exit 1; \
	fi
	$(eval PYPI_TOKEN := $(shell grep '^token=' .env | cut -d'=' -f2-))
	@if [ -z "$(PYPI_TOKEN)" ]; then \
		echo "  ✗  No 'token=' entry found in .env"; \
		exit 1; \
	fi
	@echo ""
	@echo "  Uploading to PyPI using token from .env ..."
	@echo ""
	@TWINE_USERNAME=__token__ TWINE_PASSWORD=$(PYPI_TOKEN) $(TWINE) upload $(DISTDIR)/*

# ── Docs ──────────────────────────────────────────────────────────────────────
docs:
	@echo ""
	@echo "  Building Sphinx docs..."
	@$(SPHINX) -b html $(DOCSDIR) $(DOCSDIR)/_build/html
	@echo "  ✓  Docs ready: $(DOCSDIR)/_build/html/index.html"

docs-open: docs
	@open $(DOCSDIR)/_build/html/index.html

# ── Clean ────────────────────────────────────────────────────────────────────
clean: clean-dist
	@rm -rf build/
	@rm -rf $(DOCSDIR)/_build/
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "  ✓  Cleaned"

clean-dist:
	@rm -rf $(DISTDIR)/
