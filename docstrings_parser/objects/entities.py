"""Any python object parsing."""

from abc import ABC, abstractmethod
from ast import ClassDef, Constant, Expr, FunctionDef, Module, stmt
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from ..exceptions import DocstringNotFoundException, UnknownSituationOccured
from ..logger import logger
from ..parsers import DocstringParser
from ..utils import Singleton

if TYPE_CHECKING:
    from .classes import ClassParser
    from .functions import FunctionParser
    from .module import ModuleParser


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
        from .classes import ClassParser
        from .functions import FunctionParser

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
        from .module import ModuleParser

        current_item: EntityParser = self
        while current_item._parent:
            current_item = current_item._parent
        if not isinstance(current_item, ModuleParser):
            raise UnknownSituationOccured('Last parent entity is not module')
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
