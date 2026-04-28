"""Basic parser."""

import ast
import re
from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from .. import common  # <= here
from ..config import ErrorCodes, ErrorLevels
from ..exceptions import LogicError, WrongValueError
from ..logger import get_logger
from ..utils import AttributeData, ErrorData, Singleton

if TYPE_CHECKING:
    from .docstrings import DocstringParser
    from .imports import ImportRow
    from .modules import ModuleParserBasic


@dataclass
class BasicParser[NodeType: ast.AST](ABC, metaclass=Singleton):
    """Basic item parser.

    Attributes:
        data: ast node used to parse current python entity.
        parent: parent item for current item.
    """

    data: NodeType
    parent: BasicParser | None

    @property
    def module(self) -> ModuleParserBasic:
        """Module containing current python item.

        Returns:
            Module parser which contains current entity globally.

        Raises:
            LogicError: if module for current item was not found.
        """
        from .modules import ModuleParserBasic

        current_item: BasicParser = self
        while current_item.parent:
            current_item = current_item.parent
        if not isinstance(current_item, ModuleParserBasic):
            raise LogicError("Last parent entity is not an module")
        return current_item

    def get_source_segment(self, node: ast.AST | None) -> str:
        """Get source code segment corresponding to current node.

        Args:
            node: current code node.

        Returns:
            Source code for current node or empty string.
        """
        if not node:
            return ""
        return ast.get_source_segment(self.module.source_code, node) or ""

    def save_error(
        self,
        code: ErrorCodes,
        *,
        level: ErrorLevels = ErrorLevels.ERROR,
        line_number: int | None = None,
        params: dict[str, object] | None = None,
    ) -> None:
        """Print error message with link to code line.

        Args:
            code: error message for terminal.
            level: error level.
            line_number: error line number in source code.
            params: params to fill code message placeholders using format(**params).
        """
        common.errors.append(
            ErrorData(self.module.path, line_number or self.start_line_number, level, code, params=params or {})
        )

    # abstract methods

    @property
    @abstractmethod
    def start_line_number(self) -> int:
        """Start code row number."""
        ...


@dataclass
class EntityParser[EntityData: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef | ast.Module](BasicParser, ABC):
    """Parser for any python entity.

    Attributes:
        data: ast node used to parse current python entity.
        parent: parent entity for current entity.
    """

    @property
    @abstractmethod
    def _missing_docstring_code(self) -> ErrorCodes:
        """Missing docstring error code."""
        ...

    @property
    @abstractmethod
    def _naming_convention_code(self) -> ErrorCodes:
        """Naming convention error code."""
        ...

    @property
    @abstractmethod
    def _naming_convention_regex(self) -> re.Pattern:
        """Pattern used to check naming of current parser."""
        ...

    data: EntityData
    parent: EntityParser | None

    def __post_init__(self) -> None:
        """Initialize python entity parser."""
        self.logger = get_logger()
        self._entities: list[EntityParser] = []
        self._import_rows: list[ImportRow] = []
        self._attributes: list[AttributeData] = []

    def parse(self) -> None:
        """Parse all nodes."""
        self.logger.debug(f"Parsing {self.full_name}")
        node_parsers = self.node_parsers
        for node in self.walk():
            parser = node_parsers.get(type(node))
            if not parser:
                continue
            parser(node)
        for entity in self._entities:
            entity.parse()

    @property
    def nodes(self) -> list[ast.stmt]:
        """Get list of nodes in current entity.

        Returns:
            ast nodes inside current python entity.
        """
        return self.data.body

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
            ast.AnnAssign: self._parse_ann_assign,
            ast.Import: self._parse_import,
            ast.ImportFrom: self._parse_import,
        }

    def _parse_class(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        from .classes import ClassParser, ProtectedClassParser

        if not isinstance(node, ast.ClassDef):
            raise WrongValueError("Wrong ast node received")
        if node.name.startswith("_"):
            self._entities.append(ProtectedClassParser(node, self))
            return
        self._entities.append(ClassParser(node, self))

    def _parse_function(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        from .functions import FunctionParser

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise WrongValueError("Wrong ast node received")
        self._entities.append(FunctionParser(node, self))

    def _parse_assign(self, node: ast.AST) -> None:
        """Parse single assign node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Assign):
            raise WrongValueError("Wrong ast node received")
        for target in node.targets:
            if isinstance(target, ast.Name):
                self._attributes.append(AttributeData(target.id, None, self.get_source_segment(node.value)))

    def _parse_ann_assign(self, node: ast.AST) -> None:
        """Parse single ast.AnnAssign node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.AnnAssign):
            raise WrongValueError("Wrong ast node received")
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
        from .imports import ImportRow

        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            raise WrongValueError("Wrong ast node received")
        import_row = ImportRow(node, self)
        self._import_rows.append(import_row)
        self.module._all_imported_rows.append(import_row)

    @property
    def docstring(self) -> DocstringParser | None:
        """Docstring parser for current python entity.

        Returns:
            Docstring parser with text data from current class.
        """
        from .docstrings import DocstringParser

        return DocstringParser.from_entity(self)

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        """Validate current entity docstring.

        Check it exists and is not empty.

        Args:
            docstring: docstring parsed for current entity object.
        """
        if not docstring:
            self.save_error(self._missing_docstring_code)
            return
        docstring.validate()

    def check(self) -> None:
        """Check current docstring and docstrings of each child entity."""
        self.logger.debug(f"Checking documentation for {self.full_name}")
        self.validate_name()
        self.validate_docstring(self.docstring)
        for entity in self._entities:
            entity.check()

    def validate_name(self) -> None:
        """Validate current entity name by naming conventions."""
        if not re.search(self._naming_convention_regex, self.name):
            self.save_error(self._naming_convention_code, params={"name": self.name})

    @property
    def attributes(self) -> list[AttributeData]:
        """Get list of attributes in current element.

        Returns:
            All attributes of current entity.
        """
        return self._attributes

    def walk(self) -> Iterator[ast.AST]:
        """Walk through all nodes of current entity except for ClassDefs and FunctionDefs.

        Yields:
            Each node from current entity.
        """
        todo: deque[ast.AST] = deque(self.nodes)
        while todo:
            node = todo.popleft()
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                todo.extendleft(list(ast.iter_child_nodes(node))[::-1])
            yield node

    def __repr__(self) -> str:
        """Get string representation for current entity.

        Returns:
            Entity type with its full name.
        """
        return f'{self.__class__.__name__}: "{self.full_name}"'

    @property
    def full_name(self) -> str:
        """Get full name for current entity.

        Returns:
            current entity name with all its parent entity names joined with dots.
        """
        full_name_parts: list[str] = []
        current_item: EntityParser | None = self
        while current_item:
            full_name_parts.append(current_item.name)
            current_item = current_item.parent
        return ".".join(reversed(full_name_parts))

    def __hash__(self) -> int:
        """Get hash of current object.

        Returns:
            hash for ast node.
        """
        return hash(self.data)

    # abstract methods

    @property
    @abstractmethod
    def name(self) -> str:
        """ast.Name of current entity."""
        ...


EntityNameData = TypeVar(
    "EntityNameData",
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
        return self.data.name

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        return self.data.lineno
