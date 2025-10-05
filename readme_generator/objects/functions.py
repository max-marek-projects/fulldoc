"""Different functions parsing."""

from abc import ABC
from types import FunctionType
from typing import final

from .objects import ObjectParser


class FunctionParserBasic(ObjectParser[FunctionType], ABC):
    """Object used to parse function data."""

    pass


@final
class FunctionParser(FunctionParserBasic):
    """Class used to parse single function data."""

    TITLE = 'Function'


@final
class MethodParser(FunctionParserBasic):
    """Class used to parse method data."""

    TITLE = 'Method'


@final
class StaticMethodParser(FunctionParserBasic):
    """Class used to parse static method data."""

    TITLE = 'Static Method'


@final
class ClassMethodParser(FunctionParserBasic):
    """Class used to parse class method data."""

    TITLE = 'Class Method'


@final
class PropertyParser(FunctionParserBasic):
    """Class used to parse property data."""

    TITLE = 'Property'
