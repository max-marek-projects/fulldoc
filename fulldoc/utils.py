"""Additional functionality."""

from __future__ import annotations

import ast
import importlib.metadata
import re
from abc import ABCMeta
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar, TypeVar

from .config import EMPTY_CODE, ArgumentTypes, ErrorCodes, ErrorLevels, TerminalColors, TerminalFonts

ClassEntity = TypeVar("ClassEntity")


class Singleton[ClassEntity](ABCMeta):
    """Metaclass for creating singleton.

    Usage:

    class CustomClass(metaclass=Singleton):
        ...

    Attributes:
        _instances: created instances for current singleton class for each class-value pair.

    Works only with current class, each child class will be separated singleton.
    """

    _instances: ClassVar[dict[tuple[Singleton[ClassEntity], object], ClassEntity]] = {}

    def __call__(cls, *args: object, **kwargs: object) -> ClassEntity:
        """Get singleton instance or create one.

        Returns:
            Class entity created previously or now.
        """
        if cls not in cls._instances:
            cls._instances[cls, args[0]] = super().__call__(*args, **kwargs)
        return cls._instances[cls, args[0]]


PACKAGES = importlib.metadata.packages_distributions()


@dataclass
class ErrorData:
    """Project validation error data.

    Attributes:
        path: path to file with captured error.
        line_number: line number in file with captured error.
        level: error level.
        code: object containing linting error code and message.
        params: params to fill error message placeholders using format(**params).
    """

    path: Path
    line_number: int
    level: ErrorLevels
    code: ErrorCodes
    params: dict[str, object] = field(default_factory=lambda: {})

    def show(self) -> None:
        """Print current error information to console."""
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
                error_color = TerminalColors.YELLOW
            case ErrorLevels.ERROR:
                error_color = TerminalColors.RED
            case _:
                raise ValueError(f"Wrong error level: {self.level}")
        return (
            f"{FormatTerminal.color(self.level.value, error_color):<16s}"
            f" - {FormatTerminal.color(self.code.code or EMPTY_CODE, TerminalColors.BLUE):<15s}"
            f" - {FormatTerminal.font(self.path.relative_to(Path.cwd()), TerminalFonts.BOLD)}:{self.line_number}"
            f" - {self.code.message.format(**self.params)}"
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


class Validation:
    """All validation functions."""

    @staticmethod
    def check_pascal_camel_case(value: str) -> bool:
        """Check if value is written in PascalCase (class name).

        Args:
            value: value to check case.

        Returns:
            True / False whether value is written in proper upper camel case (pascal camel case).
        """
        return bool(re.search(r"^([A-Z][a-z]*)+$", value)) and not value.isupper()

    @staticmethod
    def check_upper_snake_case(value: str) -> bool:
        """Check if value if written in upper snake case (SOME_CONSTANT).

        Args:
            value: value to check case.

        Returns:
            True / False whether value is written in proper upper snake case.
        """
        return bool(re.search(r"^[A-Z]+(_[A-Z]+)*$", value))


class FormatTerminal:
    """Handler for command line text formatting."""

    END = "\033[0m"

    @classmethod
    def font(cls, value: object, style: TerminalFonts) -> str:
        """Apply selected font style in terminal.

        Args:
            value: object to print with selected font style in terminal.
            style: desired style.

        Returns:
            Object representation with selected font style in terminal.
        """
        return f"{style}{value}{cls.END}"

    @classmethod
    def color(cls, value: object, color: TerminalColors) -> str:
        """Make bold desired color in terminal.

        Args:
            value: object to print with desired color in terminal.
            color: desired color.

        Returns:
            Object representation with desired color in terminal.
        """
        return f"{color}{value}{cls.END}"
