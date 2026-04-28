"""Sphinx configuration for fulldoc."""

import pathlib
import sys

from sphinx_pyproject import SphinxConfig

sys.path.insert(0, str(pathlib.Path("..").resolve()))

config = SphinxConfig("../pyproject.toml", globalns=globals())

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autoclass_content = "both"

napoleon_google_docstring = True
napoleon_numpy_docstring = False

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "fulldoc"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
