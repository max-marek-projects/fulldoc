"""Python modules parsing."""

from types import ModuleType
from typing import final

from .objects import ObjectParser


@final
class ModuleParser(ObjectParser[ModuleType]):
    """Parser for python modules."""

    TITLE = 'Module'
