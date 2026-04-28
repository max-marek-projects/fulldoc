"""Modules parsing."""

from __future__ import annotations

import ast
import re
from abc import ABC
from collections.abc import Iterator
from importlib.metadata import Distribution
from pathlib import Path
from typing import final

from ..config import ErrorCodes, Regexes
from ..exceptions import WrongValueError
from .basic import EntityParser
from .imports import ImportRow


class ModuleParserBasic(EntityParser[ast.Module], ABC):
    """Parser for python modules."""

    _naming_convention_code = ErrorCodes.INVALID_MODULE_NAME

    def __init__(self, data: Path) -> None:
        """Initialize parser for python module.

        Args:
            data: path to python module.
        """
        self._path = data.absolute()
        self._all_imported_rows: list[ImportRow] = []
        with Path(data).open() as file:
            self._source_code = file.read()
            super().__init__(ast.parse(self._source_code), None)

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Zero as a start line number for module.
        """
        return 0

    @property
    def libraries(
        self,
    ) -> Iterator[str | Distribution]:
        """Libraries used in current module.

        Yields:
            name of builtin module or Distribution object for installed module.
        """
        for import_row in self._all_imported_rows:
            for _, (module, _) in import_row.imported_items.items():
                if isinstance(module, str):
                    yield module
                    continue
                if isinstance(module, tuple):
                    yield from module

    @property
    def imported_modules(self) -> Iterator[ModuleParserBasic]:
        """Modules imported from current module.

        Yields:
            Each imported local module.
        """
        for import_row in self._all_imported_rows:
            for _, (module, _) in import_row.imported_items.items():
                if isinstance(module, ModuleParserBasic):
                    yield module

    @property
    def path(self) -> Path:
        """Get current module path.

        Returns:
            Path of current module.
        """
        return self._path

    def __lt__(self, other: ModuleParserBasic) -> bool:
        """Compare two module parsers.

        Args:
            other: other module parser.

        Returns:
            True / False whether current path is lower that other's parser path.

        Raises:
            WrongValueError: if other element is not module parser.
        """
        if not isinstance(other, ModuleParserBasic):
            raise WrongValueError("Can only compare ModuleParser to ModuleParser object")
        return self._path < other._path

    @property
    def name(self) -> str:
        """Get current module import name.

        Returns:
            Current module name for importlib functions.
        """
        return self.path.stem

    @property
    def full_name(self) -> str:
        """Get current module import name.

        Returns:
            Current module name for importlib functions.
        """
        return ".".join([*self.path.relative_to(Path.cwd()).parent.parts, self.path.stem])

    @property
    def package_name(self) -> str:
        """Get current module import name.

        Returns:
            Current module name for importlib functions.
        """
        return ".".join(self.path.relative_to(Path.cwd()).parent.parts)

    @property
    def source_code(self) -> str:
        """Source code of current python item.

        Returns:
            String with source code for current python item.
        """
        return self._source_code

    @classmethod
    def determine(cls, module_path: Path) -> ModuleParserBasic:
        """Determine module type based on its path.

        Args:
            module_path: python module path.

        Returns:
            Proper module parser for current path.
        """
        if module_path.stem == "__init__":
            if module_path.parent.stem.startswith("_"):
                return ProtectedPackageParser(module_path)
            return PackageParser(module_path)
        if module_path.stem.startswith("_"):
            return ProtectedModuleParser(module_path)
        return ModuleParser(module_path)


@final
class ModuleParser(ModuleParserBasic):
    """Public module parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_MODULE
    _naming_convention_regex = re.compile(f"^{Regexes.SNAKE_CASE}$")


@final
class ProtectedModuleParser(ModuleParserBasic):
    """Protected module parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_MODULE
    _naming_convention_regex = re.compile(f"^_{Regexes.SNAKE_CASE}$")


class PackageParserBasic(ModuleParserBasic):
    """Basic parser for packages."""

    def validate_name(self) -> None:
        """Validate current entity name by naming conventions."""
        if not re.search(self._naming_convention_regex, self.path.parent.stem):
            self.save_error(self._naming_convention_code, params={"name": self.path.parent.stem})

    @property
    def full_name(self) -> str:
        """Get current module import name.

        Returns:
            Current module name for importlib functions.
        """
        return ".".join([*self.path.relative_to(Path.cwd()).parent.parts])


@final
class PackageParser(PackageParserBasic):
    """Public package parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_PACKAGE
    _naming_convention_regex = re.compile(f"^{Regexes.SNAKE_CASE}$")


@final
class ProtectedPackageParser(PackageParserBasic):
    """Protected package parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_PACKAGE
    _naming_convention_regex = re.compile(f"^_{Regexes.SNAKE_CASE}$")
