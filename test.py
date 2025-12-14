"""Тестирование библиотеки."""

from pathlib import Path

from docstrings_parser.project import ProjectParser

ProjectParser(folder=Path('docstrings_parser'), parse_all_files=True).readme.write()
