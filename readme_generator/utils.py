"""Additional functionality."""

from abc import ABCMeta
from typing import Any, Generic, TypeVar

ClassObject = TypeVar('ClassObject')


class Singleton(ABCMeta, Generic[ClassObject]):
    """Metaclass for creating singleton.

    Usage:

    class CustomClass(metaclass=Singleton):
        ...

    Works only with current class, each child class will be separated singleton.
    """

    _instances: dict['Singleton', ClassObject] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> ClassObject:
        """Get singleton instance or create one.

        Args:
            cls: class with singleton functionality.

        Returns:
            Class object previously created or created now.
        """
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]
