"""Generate readme for current project."""

import argparse

from ..config import Files
from ..logger import logger


def generate_readme() -> None:
    """Generate README file."""
    logger.info('Read command')
    parser = argparse.ArgumentParser(prog='generate-readme')
    parser.add_argument(
        '-m',
        '--main-module',
        help=(f'Main module name. Default: "{Files.MAIN}"'),
        default=Files.MAIN,
        type=str,
    )
    parser.add_argument(
        '-r',
        '--readme-name',
        help=f'Readme file name. Default: "{Files.README}"',
        default=Files.README,
        type=str,
    )
    parser.add_argument(
        '-f',
        '--folder',
        help='Project folder name.',
        default='',
        type=str,
    )
    parser.add_argument(
        '-t',
        '--diagram-theme',
        help='Theme for diagram. Possible oprions: default, neutral, dark, forest, base. Default: base',
        default='base',
        type=str,
    )
