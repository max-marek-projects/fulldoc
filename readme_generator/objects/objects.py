"""Any python object parsing."""

from abc import ABC, abstractmethod
from ast import ClassDef, Constant, Expr, FunctionDef, Module
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


ObjectData = TypeVar('ObjectData', bound=ClassDef | FunctionDef | Module)


@dataclass
class ObjectParser(Generic[ObjectData], ABC, metaclass=Singleton):
    """Parser for any python-object."""

    @property
    @abstractmethod
    def TITLE(self) -> str:
        """Title for current object type."""
        ...

    _data: ObjectData
    _source_code: str
    _start_line_number: int
    _parent: 'ObjectParser | None'

    def __post_init__(self) -> None:
        """Initialize python-object parser."""
        self._logger = logger
        self._parse_nodes()

    def _parse_nodes(self) -> None:
        """Parse all nodes."""
        from .classes import ClassParser
        from .functions import FunctionParser

        self._classes: list[ClassParser] = []
        self._functions: list[FunctionParser] = []

        for node in self._data.body:
            if isinstance(node, ClassDef):
                self._classes.append(
                    ClassParser(
                        node,
                        self._source_code,
                        node.lineno + self.start_line_number,
                        self,
                    ),
                )
            if isinstance(node, FunctionDef):
                self._functions.append(
                    FunctionParser(
                        node,
                        self._source_code,
                        node.lineno + self.start_line_number,
                        self,
                    ),
                )

    @property
    def docstring(self) -> DocstringParser:
        """Docstring parser for current python object.

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
            Module parser which contains current object globally.
        """
        from .module import ModuleParser

        current_item: ObjectParser = self
        while current_item._parent:
            current_item = current_item._parent
        if not isinstance(current_item, ModuleParser):
            raise UnknownSituationOccured('Last parent object is not module')
        return current_item

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of current object.

        Returns:
            Name of current object based on its type.
        """
        ...

    def __repr__(self) -> str:
        """Get string representation for current object.

        Returns:
            Object type with its full name.
        """
        return f'{self.TITLE} "{self.name}"'


ObjectNameData = TypeVar('ObjectNameData', bound=ClassDef | FunctionDef)


class ObjectNameParser(ObjectParser[ObjectNameData], ABC):
    """Parser for python functions with name."""

    @property
    def name(self) -> str:
        """Name of current object.

        Returns:
            Name of current object based on its type.
        """
        return self._data.name
