"""Imports parsing."""

import ast
import sys
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
from importlib.metadata import Distribution, distribution
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, final

from ..config import ErrorCodes
from ..exceptions import MutuallyExclusiveArgumentsError, WrongValueError
from ..utils import PACKAGES
from .basic import BasicParser

if TYPE_CHECKING:
    from .modules import ModuleParserBasic


type ImportedModuleType = str | tuple[Distribution, ...] | ModuleParserBasic


@final
@dataclass
class ImportRow(BasicParser[ast.Import | ast.ImportFrom]):
    """Import row parser."""

    def __post_init__(self) -> None:
        """Initialize import row parser.

        Raises:
            WrongValueError: when something other than ast.Import or ast.ImportFrom received.
        """
        self.imported_items: dict[str, tuple[ImportedModuleType, str | None]] = {}
        if isinstance(self.data, ast.Import):
            for name_node in self.data.names:
                self._parse_imported_module(name_node.name, name_node.lineno, as_name=name_node.asname)
        elif isinstance(self.data, ast.ImportFrom):
            self._parse_imported_module(
                self.data.module or "",
                self.data.lineno,
                level=self.data.level,
                imported_names=[(alias.name, alias.asname) for alias in self.data.names],
            )
        else:
            raise WrongValueError("Can only parse imports from Import or ImportFrom node")

    def _parse_imported_module(
        self,
        module_name: str,
        line_number: int,
        level: int = 0,
        imported_names: list[tuple[str, str | None]] | None = None,
        as_name: str | None = None,
    ) -> None:
        """Parse imported module data by it's name.

        Args:
            module_name: imported module name.
            line_number: import node line number in module source code.
            level: import level (amount of dots at the beginning of it's name).
            imported_names: imported objects from `from ... import ...` statement.
            as_name: replacement name for `import ... as ...` statement.

        Raises:
            MutuallyExclusiveArgumentsError: if both `as_name` parameter (for import statement)
                and `imported_names` parameter (for from-import statement) used.
        """
        from .modules import ModuleParserBasic

        if as_name and imported_names:
            raise MutuallyExclusiveArgumentsError(
                "Argument `imported_names` is for `from ... import ...` statement "
                "and `as_name` parameter - only for `import ...` statement"
            )
        if not (module_spec := self._is_module(module_name, level)):
            self.save_error(ErrorCodes.NO_MODULE_NAMED, line_number=line_number, params={"module_name": module_name})
            return
        if isinstance(imported_names, list):
            for object_name, local_name in imported_names:
                submodule_name = f"{module_name}.{object_name}" if module_name else object_name
                if self._is_module(submodule_name, level):
                    self._parse_imported_module(submodule_name, line_number, level, as_name=local_name)
        if not module_spec.origin:
            return
        main_name = module_name.split(".")[0]
        if sys.exec_prefix in module_spec.origin and (distribution_names := PACKAGES.get(main_name)):
            distributions = tuple(
                sorted(
                    [distribution(distribution_name) for distribution_name in distribution_names],
                    key=lambda distribution: distribution.name,
                )
            )
            if imported_names:
                for object_name, local_name in imported_names:
                    self.imported_items[local_name or object_name] = (distributions, object_name)
                return
            self.imported_items[as_name or main_name] = (distributions, None)
            return
        if module_spec.origin in ("frozen", "built-in") or sys.base_exec_prefix in module_spec.origin:
            if imported_names:
                for object_name, local_name in imported_names:
                    self.imported_items[local_name or object_name] = (main_name, object_name)
                return
            self.imported_items[as_name or main_name] = (main_name, None)
            return
        if (module_path := Path(module_spec.origin)).is_relative_to(Path.cwd()):
            module_parser = ModuleParserBasic.determine(module_path)
            if imported_names:
                for object_name, local_name in imported_names:
                    self.imported_items[local_name or object_name] = (module_parser, object_name)
                return
            self.imported_items[as_name or main_name] = (module_parser, None)
            return
        self.save_error(ErrorCodes.NO_MODULE_NAMED, line_number=line_number, params={"module_name": module_name})

    def _is_module(self, module_name: str, level: int = 0) -> ModuleSpec | None:
        """Check if imported item is module.

        Args:
            module_name: imported module name.
            level: relative module level (amount of dots at the beginning of import).

        Returns:
            Module spec if module successfully found.
        """
        try:
            module_spec = find_spec("." * level + module_name, package=self.module.package_name)
        except ModuleNotFoundError:
            return None
        except Exception:
            raise
        if not module_spec or (not module_spec.origin and not module_spec.submodule_search_locations):
            return None
        return module_spec

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Import row line number.
        """
        return self.data.lineno
