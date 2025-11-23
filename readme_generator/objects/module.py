"""Python modules parsing."""

from ast import Module, parse
from os import path
from pathlib import Path
from typing import final

from .objects import ObjectParser


@final
class ModuleParser(ObjectParser[Module]):
    """Parser for python modules."""

    TITLE = 'Module'

    def __init__(self, data: str | Path) -> None:
        """Initizlize parser for python module.

        Args:
            data: path to python module.
        """
        self._path = path.relpath(data)
        with open(data, 'r') as file:
            code = file.read()
            super().__init__(parse(code), code, 0, None)

    @property
    def name(self) -> str:
        """Get module name.

        Returns:
            Module name based on module path.
        """
        return str(self._path.replace('/', '.').replace('\\', '.'))
