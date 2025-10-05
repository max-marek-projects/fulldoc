"""Any python object parsing."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from ..exceptions import DocstringNotFoundException
from ..parsers import DocstringParser
from ..utils import Singleton

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

    @property
    def docstring(self) -> DocstringParser | None:
        """Docstring parser for current python object.

        Returns:
            Docstring parser with text data from current class.
        """
        if not self._data.__doc__:
            raise DocstringNotFoundException('Docstring not found')
        return DocstringParser.determine(self._data.__doc__)
