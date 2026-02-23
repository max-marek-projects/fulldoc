"""Additional functionality."""

import ast
import importlib.metadata
from abc import ABCMeta
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

from .config import ArgumentTypes, ErrorLevels, TermColors

ClassEntity = TypeVar('ClassEntity')


class Singleton(ABCMeta, Generic[ClassEntity]):
    """Metaclass for creating singleton.

    Usage:

    class CustomClass(metaclass=Singleton):
        ...

    Attributes:
        _instances: created instances for current singleton class for each class-value pair.

    Works only with current class, each child class will be separated singleton.
    """

    _instances: dict[tuple['Singleton', Any], ClassEntity] = {}

    def __call__(cls, *args: Any, **kwargs: Any) -> ClassEntity:
        """Get singleton instance or create one.

        Returns:
            Class entity created previously or now.
        """
        if cls not in cls._instances:
            cls._instances[(cls, args[0])] = super().__call__(*args, **kwargs)
        return cls._instances[(cls, args[0])]


PACKAGES = importlib.metadata.packages_distributions()


@dataclass
class ErrorData:
    """Project validation error data.

    Attributes:
        path: path to file with captured error.
        line_number: line number in file with captured error.
        level: error level.
        message: error message for console.
    """

    path: Path
    line_number: int
    level: ErrorLevels
    message: str

    def show(self) -> None:
        """Print current error informatino to console."""
        print(self)  # noqa: T201

    def __repr__(self) -> str:
        """Get error data string representation.

        Returns:
            Error data representation with terminal formatting.

        Raises:
            ValueError: if wrong error level is stored in object.
        """
        match self.level:
            case ErrorLevels.WARNING:
                error_color = TermColors.WARNING
            case ErrorLevels.ERROR:
                error_color = TermColors.FAIL
            case _:
                raise ValueError(f'Wrong error level: {self.level}')
        return (
            f'{TermColors.BOLD}{self.path.relative_to(Path.cwd())}{TermColors.ENDC}:{self.line_number}'
            f' - {error_color}{self.level.value}{TermColors.ENDC} - {self.message}'
        )


@dataclass
class AttributeData:
    """Parsed attribute data.

    Attributes:
        name: name of current function argument.
        annotation: argument type annotation parser.
        value: source code for argument default value.
    """

    name: str
    annotation: ast.expr | str | None
    value: str


@dataclass
class ArgumentData(AttributeData):
    """Parsed argument data.

    Attributes:
        kind: attribute kind: general, args, kwargs.
    """

    kind: ArgumentTypes = ArgumentTypes.GENERAL
