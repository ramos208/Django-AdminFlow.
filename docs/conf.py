# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup ---------------------------------------------------------------
# Add the package root so autodoc can import adminflow
sys.path.insert(0, os.path.abspath(".."))

# Minimal Django settings so autodoc can import Django modules
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "docs._sphinx_settings")

import django
try:
    django.setup()
except Exception:
    pass  # autodoc will still work for non-Django modules

# -- Project information ------------------------------------------------------
project   = "django-adminflow"
copyright = "2026, Edgar"
author    = "Edgar"
release   = "1.0.14"
version   = "1.0.14"

# -- General configuration ----------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "myst_parser",
    "sphinx_copybutton",
]

# MyST settings — allow .md and .rst files
source_suffix = {
    ".rst": "restructuredtext",
    ".md":  "markdown",
}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
    "attrs_inline",
]

templates_path   = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- intersphinx --------------------------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", None),
}

# -- Options for HTML output --------------------------------------------------
html_theme = "sphinx_rtd_theme"

html_theme_options = {
    "logo_only":            False,
    "navigation_depth":     4,
    "collapse_navigation":  False,
    "sticky_navigation":    True,
    "includehidden":        True,
    "titles_only":          False,
    "style_external_links": True,
    "prev_next_buttons_location": "both",
}

html_static_path = ["_static"]

html_css_files = ["custom/custom.css"]

html_title = "django-adminflow"

html_context = {
    "display_github":       True,
    "github_user":          "ramos208",
    "github_repo":          "Django-AdminFlow.",
    "github_version":       "master",
    "conf_py_path":         "/docs/",
    "display_version":      True,
}

# -- Napoleon (Google/NumPy docstrings) ---------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring  = False

# -- Copy button --------------------------------------------------------------
copybutton_prompt_text = r"^\$ |^>>> "
copybutton_prompt_is_regexp = True
