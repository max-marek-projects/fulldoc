"""Логирование генерации ридми-файла."""

from logging import Formatter, StreamHandler, getLogger

from .config import LoggerConfig, LoggerLevels

logger = getLogger(LoggerConfig.NAME)
logger.setLevel(LoggerLevels.DEBUG)
formatter = Formatter(LoggerConfig.FORMAT)
handler = StreamHandler()
handler.setLevel(LoggerLevels.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
