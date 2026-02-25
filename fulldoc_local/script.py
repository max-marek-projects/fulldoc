"""Generate readme for current project."""

import argparse
import importlib
import sys
from pathlib import Path

from .config import Files
from .logger import get_logger
from .project import ProjectParser


def fulldoc() -> None:
    """Check project and generate README file."""
    if 'fulldoc' in sys.modules:
        del sys.modules['fulldoc']
    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module('fulldoc')

    logger = get_logger()
    logger.info('Read command')
    arguments_parser = argparse.ArgumentParser(prog='fulldoc')
    arguments_parser.add_argument(
        '-r',
        '--readme-name',
        help=f'Readme file name. Default: "{Files.README}"',
        default=Files.README,
        type=str,
    )
    arguments_parser.add_argument(
        '-c',
        '--check',
        help='Check project only',
        default=False,
        type=bool,
    )
    args = arguments_parser.parse_args()
    parser = ProjectParser()
    parser.check()
    if args.check:
        return
    parser.readme.write(args.readme_name)
