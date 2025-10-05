"""Логирование генерации ридми-файла."""

from logging import Formatter, StreamHandler, getLogger

from .config import LoggerConfig, LoggerLevels

logger = getLogger(LoggerConfig.NAME)
logger.setLevel(LoggerLevels.INFO)
formatter = Formatter(LoggerConfig.FORMAT)
handler = StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
