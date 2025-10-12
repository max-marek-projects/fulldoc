"""Python modules parsing."""

from types import ModuleType
from typing import final

from .objects import ObjectParser


@final
class ModuleParser(ObjectParser[ModuleType]):
    """Parser for python modules."""

    TITLE = 'Module'

    def __init__(self, data: ModuleType) -> None:
        """Initizlize parser for python module.

        Args:
            data: imported python module.
        """
        super().__init__(data)
