"""Any python object parsing."""

import ast
import importlib
import importlib.metadata
import sys
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING, Generic, TypeVar, final

from ..config import ArgumentTypes, ErrorLevels
from ..exceptions import LogicError, WrongValueError
from ..logger import logger
from ..utils import PACKAGES, ArgumentData, AttributeData, ErrorData, Singleton
from .docstrings import DocstringParser

if TYPE_CHECKING:
    from ..project import ProjectParser


EntityData = TypeVar(
    'EntityData',
    bound=ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Module,
)


@dataclass
class EntityParser(Generic[EntityData], ABC, metaclass=Singleton):
    """Parser for any python entity.

    Attributes:
        _data: ast node used to parse current python entity.
        _parent: parent object for current object.
        _project: whole project handler.
    """

    @property
    @abstractmethod
    def TITLE(self) -> str:
        """Title for current entity."""
        ...

    _data: EntityData
    _parent: 'EntityParser | None'
    _project: 'ProjectParser'

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
    def nodes(self) -> list[ast.stmt]:
        """Get list of nodes in current entity.

        Returns:
            ast nodes inside current python entity.
        """
        return self._data.body

    @property
    def node_parsers(self) -> dict[type[ast.AST], Callable[[ast.AST], None]]:
        """Functions for specific nodes parsing.

        Returns:
            Dict with node types as keys and parser-functions as values.
        """
        return {
            ast.AsyncFunctionDef: self._parse_function,
            ast.FunctionDef: self._parse_function,
            ast.ClassDef: self._parse_class,
            ast.Assign: self._parse_assign,
            ast.AnnAssign: self._parse_annassign,
            ast.Import: self._parse_import,
            ast.ImportFrom: self._parse_import_from,
        }

    def _parse_class(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.ClassDef):
            raise WrongValueError('Wrong ast node reveived')
        self._classes.append(
            ClassParser(
                node,
                self,
                self._project,
            ),
        )

    def _parse_function(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise WrongValueError('Wrong ast node reveived')
        self._functions.append(
            FunctionParser(
                node,
                self,
                self._project,
            ),
        )
        return

    def _parse_assign(self, node: ast.AST) -> None:
        """Parse single assign node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Assign):
            raise WrongValueError('Wrong ast node reveived')
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._attributes.append(AttributeData(target.id, None, self.get_source_segment(node.value)))

    def _parse_annassign(self, node: ast.AST) -> None:
        """Parse single ast.Annast.Assign node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.AnnAssign):
            raise WrongValueError('Wrong ast node reveived')
        if isinstance(node.target, ast.Name):
            self._attributes.append(
                AttributeData(
                    node.target.id,
                    node.annotation,
                    self.get_source_segment(node.value),
                ),
            )

    def _parse_import(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Import):
            raise WrongValueError('Wrong ast node reveived')
        for name_node in node.names:
            self.module._parse_imported_module(name_node.name, name_node.lineno)

    def _parse_import_from(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.ImportFrom):
            raise WrongValueError('Wrong ast node reveived')
        self.module._parse_imported_module(
            node.module or '',
            node.lineno,
            level=node.level,
            objects=[alias.name for alias in node.names],
        )

    @property
    def docstring(self) -> DocstringParser | None:
        """Docstring parser for current python entity.

        Returns:
            Docstring parser with text data from current class.
        """
        docstring_node = self.nodes[0]
        if (
            not isinstance(docstring_node, ast.Expr)
            or not isinstance(docstring_node.value, ast.Constant)
            or not isinstance(docstring_node.value.value, str)
        ):
            return None
        return DocstringParser.determine(docstring_node.value.value)

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        """Validate current entity docstring.

        Check it exists and is not empty.

        Args:
            docstring: docstring parsed for current entity object.
        """
        if not docstring:
            self.save_error(f'missing docstring in {self.TITLE}')
            return
        if not docstring.source.strip():
            self.save_error(f'docstring is empty in {self.TITLE}')
            return

    def check_docstrings(self) -> None:
        """Check current docstring and docstrings of each child entity."""
        self.validate_docstring(self.docstring)
        entities: list[EntityParser] = [*self.functions, *self.classes]
        for entity in sorted(entities, key=lambda item: item.start_line_number):
            entity.check_docstrings()

    @property
    def classes(self) -> list['ClassParser']:
        """Get list of classes in current element.

        Returns:
            ClassParser handler for each class placed in current element.
        """
        return self._classes

    @property
    def functions(self) -> list['_FunctionParser']:
        """Get list of functions in current element.

        Returns:
            FunctionParser handler for each function placed in current element.
        """
        return self._functions

    @property
    def attributes(self) -> list[AttributeData]:
        """Get list of attributes in current element.

        Returns:
            All attributes of current entity.
        """
        return self._attributes

    @property
    def module(self) -> 'ModuleParser':
        """Module containing current python item.

        Returns:
            Module parser which contains current entity globally.

        Raises:
            LogicError: if module for current object was not found.
        """
        current_item: EntityParser = self
        while current_item._parent:
            current_item = current_item._parent
        if not isinstance(current_item, ModuleParser):
            raise LogicError('Last parent entity is not module')
        return current_item

    def walk(self) -> Iterator[ast.AST]:
        """Walk through all nodes of current entity except for classdefs and functiondefs.

        Yields:
            Each node from current entity.
        """
        todo: deque[ast.AST] = deque(self.nodes)
        while todo:
            node = todo.popleft()
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                todo.extendleft(list(ast.iter_child_nodes(node))[::-1])
            yield node

    def get_source_segment(self, node: ast.AST | None) -> str:
        """Get source code segment corresponding to current node.

        Args:
            node: current code node.

        Returns:
            Source code for current node or empty string.
        """
        if not node:
            return ''
        return ast.get_source_segment(self.module.source_code, node) or ''

    def __repr__(self) -> str:
        """Get string representation for current entity.

        Returns:
            Entity type with its full name.
        """
        return f'{self.TITLE} "{self.name}"'

    def __hash__(self) -> int:
        """Get hash of current object.

        Returns:
            hash for ast node.
        """
        return hash(self._data)

    # abstract methods

    @property
    @abstractmethod
    def start_line_number(self) -> int:
        """Start code row number."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """ast.Name of current entity."""
        ...

    def save_error(
        self,
        message: str,
        level: ErrorLevels = ErrorLevels.ERROR,
        line_number: int | None = None,
    ) -> None:
        """Print error message with link to code line.

        Args:
            message: error message for terminal.
            level: error level.
            line_number: error line number in source code.
        """
        self._project.errors.append(ErrorData(self.module.path, line_number or self.start_line_number, level, message))


EntityNameData = TypeVar(
    'EntityNameData',
    bound=ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
)


class EntityNameParser(EntityParser[EntityNameData], ABC):
    """Parser for python entities with name."""

    @property
    def name(self) -> str:
        """ast.Name of current entity.

        Returns:
            ast.Name of current entity based on its type.
        """
        return self._data.name

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        return self._data.lineno


class _FunctionParser(EntityNameParser[ast.FunctionDef | ast.AsyncFunctionDef]):
    """Class used to parse single function data."""

    def __post_init__(self) -> None:
        """Initizlize function parser."""
        super().__post_init__()
        self._arguments: list[ArgumentData] = []
        self._return_statements: list[ast.Return] = []
        self._yield_statements: list[ast.Yield | ast.YieldFrom] = []
        self._raise_statements: list[ast.Raise] = []
        self._parse_arguments()

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        """Validate function docstring.

        Args:
            docstring: parsed for current function docstring.
        """
        super().validate_docstring(docstring)
        if not docstring:
            return
        args_data = docstring.args_data.copy()
        for argument in self.filter_required_arguments(self.arguments):
            if not args_data.pop(argument.name, None) and argument.kind not in (
                ArgumentTypes.ARGS,
                ArgumentTypes.KWARGS,
            ):
                self.save_error(f'missing argument `{argument.name}` in {self.TITLE} docstring')
        for left_arg_name in args_data:
            self.save_error(f'extra attribute `{left_arg_name}` description in {self.TITLE} docstring')
        has_return_statement = any(
            return_statement.value
            and not (isinstance(return_statement.value, ast.Constant) and return_statement.value.value is None)
            for return_statement in self._return_statements
        )
        has_yield_statement = any(self._yield_statements)
        if has_return_statement and not docstring.return_value:
            self.save_error(f'missing return value description in {self.TITLE}')
        if has_yield_statement and not docstring.yield_value:
            self.save_error(f'missing yield value description in {self.TITLE}')
        if docstring.has_separate_yield_statement:
            if not has_return_statement and docstring.return_value:
                self.save_error(f'extra return value description in {self.TITLE}')
            if not has_yield_statement and docstring.yield_value:
                self.save_error(f'extra yield value description in {self.TITLE}')
        else:
            if not has_return_statement and not has_yield_statement and docstring.return_value:
                self.save_error(f'extra return value description in {self.TITLE}')
        if self._raise_statements and not docstring.raise_data:
            self.save_error(f'missing raised errors description in {self.TITLE}')
        if not self._raise_statements and docstring.raise_data:
            self.save_error(f'extra raised errors description in {self.TITLE}')

    def filter_required_arguments(self, arguments: list[ArgumentData]) -> list[ArgumentData]:
        """Skip arguments.

        By default no arguments are being skipped.

        Args:
            arguments: all arguments of current function.

        Returns:
            Only arguments that are required to be checked.
        """
        return arguments

    def _parse_arguments(self) -> None:
        """Parse current function arguments."""
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
                    argument.type_comment,
                    self.get_source_segment(default),
                ),
            )
        for optional_argument, argument_type in (
            (args_data.vararg, ArgumentTypes.ARGS),
            (args_data.kwarg, ArgumentTypes.KWARGS),
        ):
            if not optional_argument:
                continue
            self._arguments.append(
                ArgumentData(
                    optional_argument.arg,
                    optional_argument.type_comment,
                    self.get_source_segment(default),
                    kind=argument_type,
                ),
            )

    @property
    def node_parsers(self) -> dict[type[ast.AST], Callable[[ast.AST], None]]:
        """Functions for specific nodes parsing.

        Returns:
            Dict with node types as keys and parser-functions as values.
        """
        return super().node_parsers | {
            ast.Return: self._parse_return,
            ast.Yield: self._parse_yield,
            ast.YieldFrom: self._parse_yield,
            ast.Raise: self._parse_raise,
        }

    def _parse_return(self, node: ast.AST) -> None:
        """Parse return statement.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Return):
            raise WrongValueError('Received other node than ast.Return')
        self._return_statements.append(node)

    def _parse_yield(self, node: ast.AST) -> None:
        """Parse yield statement.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, (ast.Yield, ast.YieldFrom)):
            raise WrongValueError('Received other node than ast.Yield or ast.YieldFrom')
        self._yield_statements.append(node)

    def _parse_raise(self, node: ast.AST) -> None:
        """Parse return statement.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Raise):
            raise WrongValueError('Received wrong ast node')
        self._raise_statements.append(node)

    @property
    def arguments(self) -> list[ArgumentData]:
        """Get function arguments.

        Returns:
            Node for function arguments.
        """
        return self._arguments

    @property
    def return_value(self) -> ast.expr | None:
        """Get current function return value.

        Returns:
            Return value of current function.
        """
        return self._data.returns


@final
class FunctionParser(_FunctionParser):
    """Class used to parse single classmethod data.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'function'


class _MethodParser(_FunctionParser):
    """Class used to parse single method data.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'method'

    def filter_required_arguments(self, arguments: list[ArgumentData]) -> list[ArgumentData]:
        """Skip arguments from docstring validation.

        Skip first argument from docstring validation.

        Args:
            arguments: current function arguments data.

        Returns:
            Only arguments that are required to be checked.
        """
        return arguments[1:]


@final
class MethodParser(_MethodParser):
    """Class used to parse single method data."""

    ...


@final
class StaticMethodParser(_FunctionParser):
    """Class used to parse single static method data.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'static method'


@final
class ClassMethodParser(_MethodParser):
    """Class used to parse single class method data.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'class method'


@final
class PropertyParser(_MethodParser):
    """Class used to parse single property data.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'property'


@final
class ClassParser(EntityNameParser[ast.ClassDef]):
    """Parser for class.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'class'

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        """Validate class docstring.

        Args:
            docstring: parsed for class docstring.
        """
        super().validate_docstring(docstring)
        if not docstring:
            return
        require_attributes_definitions = any(self.functions) or any(
            isinstance(decorator, ast.Name)
            and decorator.id == 'dataclass'
            or isinstance(decorator, ast.Call)
            and isinstance(decorator.func, ast.Name)
            and decorator.func
            for decorator in self._data.decorator_list
        )
        attrs_data = docstring.attrs_data.copy()
        for attribute in self.attributes:
            if not attrs_data.pop(attribute.name, None) and require_attributes_definitions:
                self.save_error(f'missing attribute `{attribute.name}` in {self.TITLE} docstring')
        for left_attr_name in attrs_data:
            self.save_error(f'extra attribute `{left_attr_name}` description in {self.TITLE} docstring')

    def _parse_function(self, node: ast.AST) -> None:
        """Parse function node in class.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received node is not ast.FunctionDef or ast.AsyncFunctionDef.
        """
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise WrongValueError('Received other node than ast.FunctionDef or ast.AsyncFunctionDef')
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                match decorator.id:
                    case 'property':
                        self._functions.append(PropertyParser(node, self, self._project))
                        return
                    case 'staticmethod':
                        self._functions.append(StaticMethodParser(node, self, self._project))
                        return
                    case 'classmethod':
                        self._functions.append(ClassMethodParser(node, self, self._project))
                        return
        self._functions.append(MethodParser(node, self, self._project))


@final
class ModuleParser(EntityParser[ast.Module]):
    """Parser for python modules.

    Attributes:
        TITLE: current object name for logs.
    """

    TITLE = 'module'

    def __init__(self, data: Path, project: 'ProjectParser') -> None:
        """Initizlize parser for python module.

        Args:
            data: path to python module.
            project: whole project parser.
        """
        self._path = data.absolute()
        self._imported_local_modules: set['ModuleParser'] = set()
        self._imported_builtin_modules: set[str] = set()
        self._imported_installed_modules: dict[str, list[importlib.metadata.Distribution]] = {}
        with open(data, 'r') as file:
            self._source_code = file.read()
            super().__init__(ast.parse(self._source_code), None, project)

    @property
    def name(self) -> str:
        """Get module name.

        Returns:
            Module name based on module path.
        """
        return str(self.path.relative_to(Path.cwd()))

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Zero as a start line number for module.
        """
        return 0

    def _parse_imported_module(
        self,
        module_name: str,
        line_number: int,
        level: int = 0,
        objects: list[str] | None = None,
    ) -> None:
        """Parse imported module data by it's name.

        Args:
            module_name: imported module name.
            line_number: import node line number in module source code.
            level: import level (amount of dots at the beginning of it's name).
            objects: imported objects (used in case of whole imported module).
        """
        try:
            module_spec = find_spec('.' * level + module_name, package=self.package_name)
        except ModuleNotFoundError:
            self.save_error(
                f'Module named "{module_name}" not found',
                line_number=line_number,
            )
            return
        if not module_spec or not module_spec.origin and not module_spec.submodule_search_locations:
            self.save_error(
                f'Module named "{module_name}" not found',
                line_number=line_number,
            )
            return
        if not module_spec.origin:
            for object in objects or []:
                self._parse_imported_module(f'{module_name}.{object}', line_number, level)
            return
        main_name = module_name.split('.')[0]
        if sys.exec_prefix in module_spec.origin and (distribution_names := PACKAGES.get(main_name)):
            if main_name in self._imported_installed_modules:
                return
            self._imported_installed_modules[main_name] = sorted(
                [importlib.metadata.distribution(distribution_name) for distribution_name in distribution_names],
                key=lambda distribution: distribution.name,
            )
            return
        if module_spec.origin in ('frozen', 'built-in') or sys.base_exec_prefix in module_spec.origin:
            self._imported_builtin_modules.add(main_name)
            return
        if Path(module_spec.origin).is_relative_to(Path.cwd()):
            self._imported_local_modules.add(ModuleParser(Path(module_spec.origin), project=self._project))
            return
        self.save_error(
            f'Module named "{module_name}" not found. Module origin: {module_spec.origin}',
            line_number=line_number,
        )

    @property
    def libraries(
        self,
    ) -> tuple[list[str], dict[str, list[importlib.metadata.Distribution]]]:
        """Libraries used in current module.

        Returns:
            Two values:
            - list of built-in module names
            - dict with imported libraries names and corresponding distributions.
        """
        return sorted(self._imported_builtin_modules), dict(
            sorted(
                self._imported_installed_modules.items(),
            ),
        )

    @property
    def imported_modules(self) -> list['ModuleParser']:
        """Modules imported from current module.

        Returns:
            List of module parser objects.
        """
        return sorted(self._imported_local_modules, key=lambda value: value.name)

    @property
    def path(self) -> Path:
        """Get current module path.

        Returns:
            Path of current module.
        """
        return self._path

    def __lt__(self, other: 'ModuleParser') -> bool:
        """Compare two module parsers.

        Args:
            other: other module parser.

        Returns:
            True / False whether current path is lower that other's parser path.

        Raises:
            WrongValueError: if other element is not module parser.
        """
        if not isinstance(other, ModuleParser):
            raise WrongValueError('Can only compare ModuleParser to ModuleParser object')
        return self._path < other._path

    @property
    def package_name(self) -> str:
        """Get current module import name.

        Returns:
            Current module name for importlib functions.
        """
        return '.'.join(self.path.relative_to(Path.cwd()).parent.parts)

    @property
    def source_code(self) -> str:
        """Source code of current python item.

        Returns:
            String with source code for current python item.
        """
        return self._source_code
