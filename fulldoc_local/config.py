"""Readme generation configuration params."""

from enum import IntEnum, StrEnum
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING


class LoggerLevels(IntEnum):
    """All levels for logger."""

    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL


class ErrorLevels(StrEnum):
    """All allowed parsing error levels."""

    WARNING = 'WARNING'
    ERROR = 'ERROR'


class DocstringTypes(StrEnum):
    """Possible docstring types."""

    GOOGLE = 'Google'
    RE_STRUCTURED_TEXT = 'reStructuredText'


class ProjectTypes(StrEnum):
    """Possible project types."""

    DJANGO = 'Django'
    FAST_API = 'FastAPI'
    FLASK = 'Flask'
    LIBRARY = 'Library'
    SCRIPT = 'Script'


class LoggerConfig:
    """Logger config params."""

    NAME = 'fulldoc'
    LEVEL = LoggerLevels.INFO
    FORMAT = '%(name)s - %(asctime)s - %(levelname)s - %(message)s'


class Files(StrEnum):
    """Standart filenames."""

    MAIN = 'main.py'
    README = 'README.md'
    GITIGNORE = '.gitignore'
    TOML = 'pyproject.toml'
    READ_THE_DOCS_YML = '.readthedocs.yaml'
    SPHINX_CONFIG = 'conf.py'


class TermColors:
    """Special symbols for different terminal colors."""

    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'


class ArgumentTypes(StrEnum):
    """Allowed argument types."""

    GENERAL = 'general'
    ARGS = 'args'
    KWARGS = 'kwargs'
