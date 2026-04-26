"""Sphinx configuration file."""

from sphinx_pyproject import SphinxConfig

# The extension will find pyproject.toml in the root directory relative to conf.py
config = SphinxConfig("../pyproject.toml", globalns=globals())

extensions = [
    "sphinx.ext.autodoc",  # auto-generate documentation from docstrings
    "sphinx.ext.napoleon",  # support for Google/NumPy docstring formats
    "sphinx.ext.viewcode",  # add links to highlighted source code
]
