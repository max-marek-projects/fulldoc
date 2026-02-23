"""Check docstring of current project."""

import argparse
import importlib
import sys
from pathlib import Path

from ..config import Files
from ..logger import logger
from ..project import ProjectParser


def check_docstrings() -> None:
    """Check docstrings content."""
    if 'docstrings_parser' in sys.modules:
        del sys.modules['docstrings_parser']
    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module('docstrings_parser')

    logger.info('Read command')
    arguments_parser = argparse.ArgumentParser(prog='check-docstrings')
    arguments_parser.add_argument(
        '-m',
        '--main-module',
        help=(f'Main module name. Default: "{Files.MAIN}"'),
        default=Files.MAIN,
        type=str,
    )
    arguments_parser.add_argument(
        '-f',
        '--folder',
        help='Project folder name.',
        default='',
        type=str,
    )
    args = arguments_parser.parse_args()
    parser = ProjectParser(
        folder=Path(args.folder),
    )
    parser.check()
