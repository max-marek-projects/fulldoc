"""Different classes parsing."""

from typing import final

from .objects import ObjectParser


@final
class ClassParser(ObjectParser[type]):
    """Object used to parse specific class data."""

    TITLE = 'Class'
