"""Library logging."""

from logging import Formatter, Logger, StreamHandler, getLogger

from .config import LoggerConfig, LoggerLevels


def get_logger() -> Logger:
    """Get logger for current project.

    Returns:
        logger with desired settings.
    """
    logger = getLogger(LoggerConfig.NAME)
    if logger.handlers:
        return logger
    logger.setLevel(LoggerLevels.INFO)
    formatter = Formatter(LoggerConfig.FORMAT)
    handler = StreamHandler()
    handler.setLevel(LoggerLevels.INFO)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
