"""Project for docstrings check and readme generation."""

from .project import ProjectParser
from .scripts import check_docstrings, generate

__all__ = ('ProjectParser', 'check_docstrings', 'generate')
