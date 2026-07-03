"""Sphinx configuration for django-for-agents docs."""

project = "django-for-agents"
author = "Eneko Illarramendi"
copyright = "2026, Eneko Illarramendi"

release = "0.0.1"
version = "0.0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

autodoc_typehints = "description"
