"""Check docstring of current project."""

import argparse

from ..config import Files
from ..logger import logger
from ..project import ProjectParser


def check_docstrings() -> None:
    """Check docstrings content."""
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
    arguments_parser.add_argument(
        '-a',
        '--all-files',
        help='Parse all files.',
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    args = arguments_parser.parse_args()
    parser = ProjectParser(
        module_name=args.main_module,
        folder=args.folder,
    )
    parser.tree
