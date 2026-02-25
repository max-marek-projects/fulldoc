"""Sphinx configuration file."""

from sphinx_pyproject import SphinxConfig

# The extension will find pyproject.toml in the root directory relative to conf.py
config = SphinxConfig('../pyproject.toml', globalns=globals())
