"""Any python object parsing."""

import importlib
import importlib.metadata
import sys
from abc import ABC, abstractmethod
from ast import ClassDef, Constant, Expr, FunctionDef, Import, ImportFrom, Module, arguments, expr, parse, stmt
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Generic, TypeVar, final

from .exceptions import DocstringNotFoundException, LogicError, ModuleNotFoundException, WrongValueError
from .logger import logger
from .parsers import DocstringParser
from .utils import PACKAGES, Singleton

EntityData = TypeVar('EntityData', bound=ClassDef | FunctionDef | Module)


@dataclass
class EntityParser(Generic[EntityData], ABC, metaclass=Singleton):
    """Parser for any python entity."""

    @property
    @abstractmethod
    def TITLE(self) -> str:
        """Title for current entity."""
        ...

    _data: EntityData
    _source_code: str
    _start_line_number: int
    _parent: 'EntityParser | None'

    def __post_init__(self) -> None:
        """Initialize python entity parser."""
        self._logger = logger
        self._parse_nodes()

    def _parse_nodes(self) -> None:
        """Parse all nodes."""
        self._classes: list['ClassParser'] = []
        self._functions: list['FunctionParser'] = []

        for node in self._data.body:
            self._parse_node(node)

    def _parse_node(self, node: stmt) -> None:
        """Parse single node.

        Args:
            node: single node of current entity body.
        """
        if isinstance(node, ClassDef):
            self._classes.append(
                ClassParser(
                    node,
                    self._source_code,
                    node.lineno + self.start_line_number,
                    self,
                ),
            )
            return
        if isinstance(node, FunctionDef):
            self._functions.append(
                FunctionParser(
                    node,
                    self._source_code,
                    node.lineno + self.start_line_number,
                    self,
                ),
            )
            return

    @property
    def docstring(self) -> DocstringParser:
        """Docstring parser for current python entity.

        Returns:
            Docstring parser with text data from current class.
        """
        docstring_node = self._data.body[0]
        if (
            not isinstance(docstring_node, Expr)
            or not isinstance(docstring_node.value, Constant)
            or not isinstance(docstring_node.value.value, str)
        ):
            raise DocstringNotFoundException('Docstring not found')
        return DocstringParser.determine(docstring_node.value.value)

    @property
    def classes(self) -> list['ClassParser']:
        """Get list of classes in current element.

        Yields:
            ClassParser handler for each class placed in current element.
        """
        return self._classes

    @property
    def functions(self) -> list['FunctionParser']:
        """Get list of functions in current element.

        Yields:
            FunctionParser handler for each function placed in current element.
        """
        return self._functions

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        return self._start_line_number

    @property
    def source_code(self) -> str:
        """Source code of current python item.

        Returns:
            String with source code for current python item.
        """
        return self._source_code

    @property
    def module(self) -> 'ModuleParser':
        """Module containing current python item.

        Returns:
            Module parser which contains current entity globally.
        """
        current_item: EntityParser = self
        while current_item._parent:
            current_item = current_item._parent
        if not isinstance(current_item, ModuleParser):
            raise LogicError('Last parent entity is not module')
        return current_item

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of current entity.

        Returns:
            Name of current entity based on its type.
        """
        ...

    def __repr__(self) -> str:
        """Get string representation for current entity.

        Returns:
            Entity type with its full name.
        """
        return f'{self.TITLE} "{self.name}"'

    def __hash__(self) -> int:
        """Get hash of current object."""
        return hash(self._data)


EntityNameData = TypeVar('EntityNameData', bound=ClassDef | FunctionDef)


class EntityNameParser(EntityParser[EntityNameData], ABC):
    """Parser for python entities with name."""

    @property
    def name(self) -> str:
        """Name of current entity.

        Returns:
            Name of current entity based on its type.
        """
        return self._data.name


@final
class ClassParser(EntityNameParser[ClassDef]):
    """Parser for class."""

    TITLE = 'Class'


@final
class FunctionParser(EntityNameParser[FunctionDef]):
    """Class used to parse single function data."""

    TITLE = 'Function'

    @property
    def args(self) -> arguments:
        """Get function arguments.

        Returns:
            Node for function arguments.
        """
        return self._data.args

    @property
    def return_value(self) -> expr | None:
        """Get current function return value.

        Returns:
            Return value of current function.
        """
        return self._data.returns


@final
class ModuleParser(EntityParser[Module]):
    """Parser for python modules."""

    TITLE = 'Module'

    def __init__(self, data: Path, folder: Path) -> None:
        """Initizlize parser for python module.

        Args:
            data: path to python module.
            folder: project folder.
        """
        self._path = data
        self._folder = folder
        self._imported_local_modules: set['ModuleParser'] = set()
        self._imported_builtin_modules: set[str] = set()
        self._imported_installed_modules: dict[str, list[importlib.metadata.Distribution]] = {}
        with open(data, 'r') as file:
            code = file.read()
            super().__init__(parse(code), code, 0, None)

    @property
    def name(self) -> str:
        """Get module name.

        Returns:
            Module name based on module path.
        """
        return str(self._path.relative_to(self._folder)).replace('/', '.').replace('\\', '.')

    def _parse_imported_module(self, module_name: str, line_number: int, level: int = 0) -> None:
        """Parse imported module data by it's name."""
        module_path = module_name.replace('.', '/')
        if level:
            folder = self.path.parent
            for _ in range(level - 1):
                folder = folder.parent
        else:
            folder = self._folder
        for path in ((folder / module_path).with_suffix('.py'), (folder / module_path / '__init__.py')):
            if path.exists():
                self._imported_local_modules.add(ModuleParser(path, folder=self._folder))
                return
        if module_path.startswith('.'):
            raise ModuleNotFoundException(f'Module not found: {self.path}:{line_number}')
        main_name = module_name.split('.')[0]
        if distribution_names := PACKAGES.get(main_name):
            if main_name in self._imported_installed_modules:
                return
            self._imported_installed_modules[main_name] = sorted(
                [importlib.metadata.distribution(distribution_name) for distribution_name in distribution_names],
                key=lambda distribution: distribution.name,
            )
            return
        if main_name in sys.builtin_module_names:
            self._imported_builtin_modules.add(main_name)
            return
        builtin_module = importlib.import_module(main_name)
        if not builtin_module.__file__:
            raise ModuleNotFoundError(f'File not found for module "{main_name}"')
        if sys.base_exec_prefix in builtin_module.__file__:
            self._imported_builtin_modules.add(main_name)
            return
        raise ModuleNotFoundError(f'Module named "{module_name}" not found: {self.path}:{line_number}')

    def _parse_node(self, node: stmt) -> None:
        """Parse single node.

        Args:
            node: single node.
        """
        super()._parse_node(node)
        if isinstance(node, Import):
            for name_node in node.names:
                self._parse_imported_module(name_node.name, name_node.lineno)
        if isinstance(node, ImportFrom):
            if not node.module:
                raise LogicError(
                    f'Module data not found in `from ... import ...` syntax: {self.path}:{node.lineno}',
                )
            self._parse_imported_module(node.module, node.lineno, level=node.level)

    @cached_property
    def libraries(self) -> tuple[list[str], dict[str, list[importlib.metadata.Distribution]]]:
        """Libraries used in current module."""
        return sorted(self._imported_builtin_modules), dict(
            sorted(
                self._imported_installed_modules.items(),
            ),
        )

    @cached_property
    def imported_modules(self) -> list['ModuleParser']:
        """Modules imported from current module."""
        return sorted(self._imported_local_modules, key=lambda value: value.name)

    @property
    def path(self) -> Path:
        """Get current module path."""
        return self._path

    def __lt__(self, other: object) -> bool:
        """Compare two module parsers."""
        if not isinstance(other, ModuleParser):
            raise WrongValueError('Can only compare ModuleParser to ModuleParser object')
        return self._path < other._path
