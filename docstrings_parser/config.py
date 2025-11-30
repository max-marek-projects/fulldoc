"""Readme generation configuration params."""

from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING


class LoggerLevels:
    """All levels for logger."""

    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL


class LoggerConfig:
    """Logger config params."""

    NAME = 'README-Generator'
    LEVEL = INFO
    FORMAT = '%(name)s %(asctime)s %(levelname)s %(message)s'


class Files:
    """Standart filenames."""

    MAIN = 'main.py'
    README = 'README.md'
    GITIGNORE = '.gitignore'
    TOML = 'pyproject.toml'
