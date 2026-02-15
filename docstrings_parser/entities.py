"""Any python object parsing."""

import importlib
import importlib.metadata
import sys
from abc import ABC, abstractmethod
from ast import (
    AST,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    ClassDef,
    Constant,
    Expr,
    FunctionDef,
    Import,
    ImportFrom,
    Module,
    Name,
    expr,
    get_source_segment,
    iter_child_nodes,
    parse,
    stmt,
)
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import cached_property
from importlib.util import find_spec
from pathlib import Path
from typing import Generic, TypeVar, final

from .exceptions import LogicError, ModuleNotFoundException, WrongValueError
from .logger import logger
from .parsers import DocstringParser
from .parsers.type_annotation import AnnotationParser
from .utils import PACKAGES, Singleton


@dataclass
class AttributeData:
    """Parsed attribute data."""

    name: str
    annotation: AnnotationParser | None
    value: str


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
    _parent: 'EntityParser | None'

    def __post_init__(self) -> None:
        """Initialize python entity parser."""
        self._logger = logger
        self._classes: list['ClassParser'] = []
        self._functions: list['_FunctionParser'] = []
        self._attributes: list[AttributeData] = []

    def parse(self) -> None:
        """Parse all nodes."""
        node_parsers = self.node_parsers
        for node in self.walk():
            parser = node_parsers.get(type(node))
            if not parser:
                continue
            parser(node)
        for function in self.functions:
            function.parse()
        for class_item in self.classes:
            class_item.parse()

    @property
    def nodes(self) -> list[stmt]:
        """Get list of nodes in current entity."""
        return self._data.body

    @property
    def node_parsers(self) -> dict[type[AST], Callable[[AST], None]]:
        """Functions for specific nodes parsing.

        Returns:
            Dict with node types as keys and parser-functions as values.
        """
        return {
            AsyncFunctionDef: self._parse_function,
            FunctionDef: self._parse_function,
            ClassDef: self._parse_class,
            Assign: self._parse_assign,
            AnnAssign: self._parse_annassign,
        }

    def _parse_class(self, node: AST) -> None:
        """Parse single node.

        Args:
            node: single node of current entity body.
        """
        if not isinstance(node, ClassDef):
            raise WrongValueError('Received other node than ClassDef')
        self._classes.append(
            ClassParser(
                node,
                self._source_code,
                self,
            ),
        )

    def _parse_function(self, node: AST) -> None:
        """Parse single node.

        Args:
            node: single node of current entity body.
        """
        if not isinstance(node, FunctionDef):
            raise WrongValueError('Received other node than ClassDef')
        self._functions.append(
            FunctionParser(
                node,
                self._source_code,
                self,
            ),
        )
        return

    def _parse_assign(self, node: AST) -> None:
        """Parse single assign node."""
        if not isinstance(node, Assign):
            raise WrongValueError('Received other node than ClassDef')
        for target in node.targets:
            if isinstance(target, Name):
                self._attributes.append(AttributeData(target.id, None, self.get_source_segment(node.value)))

    def _parse_annassign(self, node: AST) -> None:
        """Parse single AnnAssign node."""
        if not isinstance(node, AnnAssign):
            raise WrongValueError('Received other node than ClassDef')
        if isinstance(node.target, Name):
            self._attributes.append(
                AttributeData(
                    node.target.id, AnnotationParser(node.annotation, self), self.get_source_segment(node.value),
                ),
            )

    @property
    def docstring(self) -> DocstringParser | None:
        """Docstring parser for current python entity.

        Returns:
            Docstring parser with text data from current class.
        """
        docstring_node = self.nodes[0]
        if (
            not isinstance(docstring_node, Expr)
            or not isinstance(docstring_node.value, Constant)
            or not isinstance(docstring_node.value.value, str)
        ):
            return None
        return DocstringParser.determine(docstring_node.value.value)

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        if not docstring:
            self.print_error('missing docstring')
            return

    def check_docstrings(self) -> None:
        self.validate_docstring(self.docstring)
        entities: list[EntityParser] = [*self.functions, *self.classes]
        for entity in sorted(entities, key=lambda item: item.start_line_number):
            entity.check_docstrings()

    @property
    def classes(self) -> list['ClassParser']:
        """Get list of classes in current element.

        Yields:
            ClassParser handler for each class placed in current element.
        """
        return self._classes

    @property
    def functions(self) -> list['_FunctionParser']:
        """Get list of functions in current element.

        Yields:
            FunctionParser handler for each function placed in current element.
        """
        return self._functions

    @property
    def attributes(self) -> list[AttributeData]:
        """Get list of attributes in current element."""
        return self._attributes

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

    def walk(self) -> Iterator[AST]:
        """Walk through all nodes of current entity except for classdefs and functiondefs.

        Yields:
            Each node from current entity.
        """
        todo: deque[AST] = deque(self.nodes)
        while todo:
            node = todo.popleft()
            if not isinstance(node, (ClassDef, FunctionDef, AsyncFunctionDef)):
                todo.extendleft(list(iter_child_nodes(node))[::-1])
            yield node

    def get_source_segment(self, node: AST | None) -> str:
        """Get source code segment corresponding to current node."""
        if not node:
            return ''
        return get_source_segment(self._source_code, node) or ''

    def __repr__(self) -> str:
        """Get string representation for current entity.

        Returns:
            Entity type with its full name.
        """
        return f'{self.TITLE} "{self.name}"'

    def __hash__(self) -> int:
        """Get hash of current object."""
        return hash(self._data)

    # abstract methods

    @property
    @abstractmethod
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of current entity.

        Returns:
            Name of current entity based on its type.
        """
        ...

    def print_error(self, message: str) -> None:
        """Print error message with link to code line."""
        print(f'{self.module.path}:{self.start_line_number} - {message}')


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

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        return self._data.lineno


@dataclass
class ArgumentData:
    """Function argument data.

    Attributes:
        name: name of current function argument.
        annotation: argument type annotation parser.
        value: source code for argument default value.
    """

    name: str
    annotation: AnnotationParser | None
    value: str


class _FunctionParser(EntityNameParser[FunctionDef]):
    """Class used to parse single function data."""

    TITLE = 'Function'
    OPTIONAL_AGR_NAMES: list[str] = []

    def __post_init__(self) -> None:
        super().__post_init__()
        self._arguments: list[ArgumentData] = []
        self._parse_arguments()

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        super().validate_docstring(docstring)
        if not docstring:
            return
        args_data = docstring.args_data.copy()
        for argument in self.arguments:
            if not args_data.pop(argument.name, None) and argument.name not in self.OPTIONAL_AGR_NAMES:
                self.print_error(f'missing argument `{argument.name}` in function docstring')
        for left_arg_name in args_data:
            if left_arg_name not in self.OPTIONAL_AGR_NAMES:
                self.print_error(f'extra attribute `{left_arg_name}` description in class docstring')

    def _parse_arguments(self) -> None:
        args_data = self._data.args
        all_positional_args = args_data.posonlyargs + args_data.args
        all_positional_defaults = [None] * (len(all_positional_args) - len(args_data.defaults)) + args_data.defaults
        for argument, default in zip(
            all_positional_args + args_data.kwonlyargs,
            all_positional_defaults + args_data.kw_defaults,
        ):
            self._arguments.append(
                ArgumentData(
                    argument.arg,
                    AnnotationParser(argument.type_comment, self) if argument.type_comment else None,
                    self.get_source_segment(default),
                ),
            )
        for optional_argument in (args_data.vararg, args_data.kwarg):
            if not optional_argument:
                continue
            self._arguments.append(
                ArgumentData(
                    optional_argument.arg,
                    AnnotationParser(optional_argument.type_comment, self) if optional_argument.type_comment else None,
                    self.get_source_segment(default),
                ),
            )

    @property
    def arguments(self) -> list[ArgumentData]:
        """Get function arguments.

        Returns:
            Node for function arguments.
        """
        return self._arguments

    @property
    def return_value(self) -> expr | None:
        """Get current function return value.

        Returns:
            Return value of current function.
        """
        return self._data.returns


@final
class FunctionParser(_FunctionParser):
    """Class used to parse single classmethod data."""

    ...


@final
class MethodParser(_FunctionParser):
    """Class used to parse single method data."""

    TITLE = 'Method'
    OPTIONAL_AGR_NAMES = ['self']


@final
class StaticMethodParser(_FunctionParser):
    """Class used to parse single static method data."""

    TITLE = 'Static method'


@final
class ClassMethodParser(_FunctionParser):
    """Class used to parse single class method data."""

    TITLE = 'Class method'
    OPTIONAL_AGR_NAMES = ['cls']


@final
class PropertyParser(_FunctionParser):
    """Class used to parse single property data."""

    TITLE = 'Property'
    OPTIONAL_AGR_NAMES = ['self']


@final
class ClassParser(EntityNameParser[ClassDef]):
    """Parser for class."""

    TITLE = 'Class'

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        super().validate_docstring(docstring)
        if not docstring:
            return
        attrs_data = docstring.attrs_data.copy()
        for attribute in self.attributes:
            if not attrs_data.pop(attribute.name, None):
                self.print_error(f'missing attribute `{attribute.name}` in class docstring')
        for left_attr_name in attrs_data:
            self.print_error(f'extra attribute `{left_attr_name}` description in class docstring')

    def _parse_function(self, node: AST) -> None:
        if not isinstance(node, FunctionDef):
            raise WrongValueError('Received other node than ClassDef')
        for decorator in node.decorator_list:
            if isinstance(decorator, Name):
                match decorator.id:
                    case 'property':
                        self._functions.append(PropertyParser(node, self._source_code, self))
                        return
                    case 'staticmethod':
                        self._functions.append(StaticMethodParser(node, self._source_code, self))
                        return
                    case 'classmethod':
                        self._functions.append(ClassMethodParser(node, self._source_code, self))
                        return
        self._functions.append(MethodParser(node, self._source_code, self))


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
            super().__init__(parse(code), code, None)

    @property
    def name(self) -> str:
        """Get module name.

        Returns:
            Module name based on module path.
        """
        return str(self._path.relative_to(self._folder)).replace('/', '.').replace('\\', '.')

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Zero as a start line number for module.
        """
        return 0

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
        builtin_module_spec = find_spec(main_name)
        if not builtin_module_spec:
            raise ModuleNotFoundError(f'File not found for module "{main_name}"')
        if builtin_module_spec.origin == 'frozen' or sys.base_exec_prefix in (builtin_module_spec.origin or ''):
            self._imported_builtin_modules.add(main_name)
            return
        raise ModuleNotFoundError(
            f'Module named "{module_name}" not found: {self.path}:{line_number}\n'
            f'Module origin: {builtin_module_spec.origin}',
        )

    @property
    def node_parsers(self) -> dict[type[AST], Callable[[AST], None]]:
        """Functions for specific nodes parsing.

        Returns:
            Dict with node types as keys and parser-functions as values.
        """
        return super().node_parsers | {
            Import: self._parse_import,
            ImportFrom: self._parse_import_from,
        }

    def _parse_import(self, node: AST) -> None:
        """Parse single node.

        Args:
            node: single node.
        """
        if not isinstance(node, Import):
            raise WrongValueError('Received other node than Import')
        for name_node in node.names:
            self._parse_imported_module(name_node.name, name_node.lineno)

    def _parse_import_from(self, node: AST) -> None:
        """Parse single node.

        Args:
            node: single node.
        """
        if not isinstance(node, ImportFrom):
            raise WrongValueError('Received other node than ImportFrom')
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
