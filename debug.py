"""Run current script in debug mode."""

from pathlib import Path

from fulldoc import ProjectParser

project_parser = ProjectParser(
    folder=Path('docstrings_parser'),
)
project_parser.check()
project_parser.readme.write()
