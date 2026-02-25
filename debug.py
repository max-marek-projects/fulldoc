"""Run current script in debug mode."""

from fulldoc_local import ProjectParser

project_parser = ProjectParser()
project_parser.check()
project_parser.readme.write()
