"""Additional functionality."""

import importlib.metadata
from abc import ABCMeta
from typing import Any, Generic, TypeVar

ClassEntity = TypeVar('ClassEntity')


class Singleton(ABCMeta, Generic[ClassEntity]):
    """Metaclass for creating singleton.

    Usage:

    class CustomClass(metaclass=Singleton):
        ...

    Works only with current class, each child class will be separated singleton.
    """

    _instances: dict[tuple['Singleton', Any], ClassEntity] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> ClassEntity:
        """Get singleton instance or create one.

        Args:
            cls: class with singleton functionality.

        Returns:
            Class entity created previously or now.
        """
        if cls not in cls._instances:
            cls._instances[(cls, args[0])] = super().__call__(*args, **kwargs)
        return cls._instances[(cls, args[0])]


PACKAGES = importlib.metadata.packages_distributions()
