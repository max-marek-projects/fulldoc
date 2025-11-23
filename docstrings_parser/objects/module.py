"""Python modules parsing."""

from ast import Module, parse, stmt, Import, ImportFrom
from os import path
from pathlib import Path
from typing import final

from .entities import EntityParser


@final
class ModuleParser(EntityParser[Module]):
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

    def _parse_node(self, node: stmt) -> None:
        """Parse single node.

        Args:
            node: single node.
        """
        super()._parse_node(node)
        if isinstance(node, Import):
            ...
        if isinstance(node, ImportFrom):
            ...
