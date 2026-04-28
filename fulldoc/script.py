"""Check docstrings for current project."""

import argparse
import importlib
import sys
from pathlib import Path
from typing import get_args

from .logger import get_logger
from .parsers.docstrings import DocstringTypes
from .project import ProjectParser


def fulldoc() -> None:
    """Check project docstrings."""
    if "fulldoc" in sys.modules:
        del sys.modules["fulldoc"]
    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module("fulldoc")

    logger = get_logger()
    logger.debug("Read command")
    arguments_parser = argparse.ArgumentParser(prog="fulldoc")
    arguments_parser.add_argument(
        "-a",
        "--all",
        help="Check all entities (even private)",
        default=False,
        type=bool,
    )
    arguments_parser.add_argument(
        "-d",
        "--docstring",
        help="Docstring type",
        choices=get_args(DocstringTypes),
        default="google",
    )
    args = arguments_parser.parse_args()
    parser = ProjectParser()
    parser.check(args.all)
