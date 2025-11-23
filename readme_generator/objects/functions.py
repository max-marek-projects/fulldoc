"""Different functions parsing."""

from ast import FunctionDef
from typing import final

from .objects import ObjectNameParser


@final
class FunctionParser(ObjectNameParser[FunctionDef]):
    """Class used to parse single function data."""

    TITLE = 'Function'
