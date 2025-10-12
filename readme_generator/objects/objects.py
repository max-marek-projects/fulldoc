"""Any python object parsing."""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from inspect import isfunction
from typing import TYPE_CHECKING, Generic, TypeVar

from ..exceptions import DocstringNotFoundException, NameNotFoundException
from ..logger import logger
from ..parsers import DocstringParser
from ..utils import Singleton

if TYPE_CHECKING:
    from .classes import ClassParser
    from .functions import FunctionParserBasic

ObjectData = TypeVar('ObjectData')


class ObjectParser(Generic[ObjectData], ABC, metaclass=Singleton):
    """Parser for any python-object."""

    @property
    @abstractmethod
    def TITLE(self) -> str:
        """Title for current object type."""
        ...

    def __init__(self, data: ObjectData) -> None:
        """Initialize python-object parser.

        Args:
            data: object-data (original pbject).
        """
        self._data = data
        self._logger = logger

    @property
    def docstring(self) -> DocstringParser | None:
        """Docstring parser for current python object.

        Returns:
            Docstring parser with text data from current class.
        """
        if not self._data.__doc__:
            raise DocstringNotFoundException('Docstring not found')
        return DocstringParser.determine(self._data.__doc__)

    @property
    def classes(self) -> Iterator['ClassParser']:
        """Get list of classes in current element.

        Yields:
            ClassParser handler for each class placed in current element.
        """
        from .classes import ClassParser

        for item_name, value in self._data.__dict__.items():
            if isinstance(value, type):
                self._logger.debug(f'Found class named "{item_name}"')
                yield ClassParser(value)

    @property
    def functions(self) -> Iterator['FunctionParserBasic']:
        """Get list of functions in current element.

        Yields:
            FunctionParser handler for each class placed in current element.
        """
        from .functions import ClassMethodParser, FunctionParser, PropertyParser, StaticMethodParser

        for item_name, value in self._data.__dict__.items():
            if isfunction(value):
                self._logger.debug(f'Found function named "{item_name}"')
                yield FunctionParser(value)
            if isinstance(value, staticmethod):
                self._logger.debug(f'Found staticmethod named "{item_name}"')
                yield StaticMethodParser(value.__func__)
            if isinstance(value, classmethod):
                self._logger.debug(f'Found classmethod named "{item_name}"')
                yield ClassMethodParser(value.__func__)
            if isinstance(value, property):
                self._logger.debug(f'Found property named "{item_name}"')
                yield PropertyParser(value.fget)

    @property
    def name(self) -> str:
        """Name of current object.

        Returns:
            Name of current object based on its type.
        """
        name = getattr(self._data, '__name__')
        if not name:
            raise NameNotFoundException('Name not found')
        return name

    def __repr__(self) -> str:
        """Get string representation for current object.

        Returns:
            Object type with its full name.
        """
        return f'{self.TITLE} "{self.name}"'
