"""Тестирование библиотеки."""

from pathlib import Path

from docstrings_parser.project import ProjectParser

project = ProjectParser(folder=Path('docstrings_parser'), parse_all_files=True)
project.check_docstrings()
project.readme.write()
