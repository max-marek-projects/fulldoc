"""Different classes parsing."""

from ast import ClassDef
from typing import final

from .entities import EntityNameParser


@final
class ClassParser(EntityNameParser[ClassDef]):
    """Parser for class."""

    TITLE = 'Class'
