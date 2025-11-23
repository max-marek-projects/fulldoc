"""Different classes parsing."""

from ast import ClassDef
from typing import final

from .objects import ObjectNameParser


@final
class ClassParser(ObjectNameParser[ClassDef]):
    """Object used to parse specific class data."""

    TITLE = 'Class'
