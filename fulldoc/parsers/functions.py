"""Parsing functions."""

import ast
import re
from abc import ABC
from collections.abc import Callable
from dataclasses import dataclass
from typing import final

from ..config import MAGIC_METHODS, ArgumentTypes, ErrorCodes, Regexes
from ..exceptions import WrongValueError
from ..utils import ArgumentData, Validation
from .basic import EntityNameParser
from .docstrings import DocstringParser


class FunctionParserBasic(EntityNameParser[ast.FunctionDef | ast.AsyncFunctionDef], ABC):
    """Class used to parse single function data."""

    _naming_convention_code = ErrorCodes.INVALID_FUNCTION_NAME
    _RESOLVE_ORDER_MATTERS = True

    def __post_init__(self) -> None:
        """Initialize function parser."""
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
                self.save_error(ErrorCodes.UNDOCUMENTED_PARAM, params={"definition": self.name, "name": argument.name})
        for left_arg_name in args_data:
            self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_PARAMETER, params={"id": left_arg_name})
        has_return_statement = any(
            return_statement.value
            and not (isinstance(return_statement.value, ast.Constant) and return_statement.value.value is None)
            for return_statement in self._return_statements
        )
        has_yield_statement = any(self._yield_statements)
        if has_return_statement and not docstring.return_value:
            self.save_error(ErrorCodes.DOCSTRING_MISSING_RETURNS)
        if has_yield_statement and not docstring.yield_value:
            self.save_error(ErrorCodes.DOCSTRING_MISSING_YIELDS)
        if docstring.has_separate_yield_statement:
            if not has_return_statement and docstring.return_value:
                self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_RETURNS)
            if not has_yield_statement and docstring.yield_value:
                self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_YIELDS)
        else:
            if not has_return_statement and not has_yield_statement and docstring.return_value:
                self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_RETURNS)
        if self._raise_statements and not docstring.raise_data:
            for raise_statement in self._raise_statements:
                if exc_name := self._parse_raise_statement(raise_statement):
                    self.save_error(ErrorCodes.DOCSTRING_MISSING_EXCEPTION, params={"id": exc_name})
        if not self._raise_statements and docstring.raise_data:
            for raise_data in docstring.raise_data:
                self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_EXCEPTION, params={"id": raise_data.type})

    def _parse_raise_statement(self, raise_statement: ast.Raise) -> str | None:
        """Parse raise statement.

        Args:
            raise_statement: Raise ast node.

        Returns:
            Name of exception class that needs to be documented.
        """
        exc = raise_statement.exc
        if not exc:
            return None
        if isinstance(exc, ast.Call):
            exc = exc.func
        match exc:
            case ast.Name(id=name):
                if Validation.check_pascal_camel_case(name):
                    return name
            case ast.Attribute(attr=name):
                if Validation.check_pascal_camel_case(name):
                    return name
        return None

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
        args_data = self.data.args
        all_positional_args = args_data.posonlyargs + args_data.args
        all_positional_defaults = [None] * (len(all_positional_args) - len(args_data.defaults)) + args_data.defaults
        for argument, default in zip(
            all_positional_args + args_data.kwonlyargs,
            all_positional_defaults + args_data.kw_defaults,
            strict=False,
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
            raise WrongValueError("Received other node than ast.Return")
        self._return_statements.append(node)

    def _parse_yield(self, node: ast.AST) -> None:
        """Parse yield statement.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, (ast.Yield, ast.YieldFrom)):
            raise WrongValueError("Received other node than ast.Yield or ast.YieldFrom")
        self._yield_statements.append(node)

    def _parse_raise(self, node: ast.AST) -> None:
        """Parse return statement.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.Raise):
            raise WrongValueError("Received wrong ast node")
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
        return self.data.returns

    def validate_name(self) -> None:
        """Validate current entity name by naming conventions."""
        if re.search(r"^__.*__$", self.name):
            if self.name not in MAGIC_METHODS:
                self.save_error(ErrorCodes.DUNDER_FUNCTION_NAME)
            return
        if not re.search(self._naming_convention_regex, self.name):
            self.save_error(self._naming_convention_code, params={"name": self.name})


@final
class FunctionParser(FunctionParserBasic):
    """Public function parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_FUNCTION
    _naming_convention_regex = re.compile(f"^{Regexes.SNAKE_CASE}$")


@final
class ProtectedFunctionParser(FunctionParserBasic):
    """Protected function parser."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_FUNCTION
    _naming_convention_regex = re.compile(f"^_{Regexes.SNAKE_CASE}$")


@dataclass
class MethodParserBasic(FunctionParserBasic, ABC):
    """Class used to parse single method data.

    Attributes:
        is_static: defines whether current method is static.
    """

    is_static: bool = False

    def filter_required_arguments(self, arguments: list[ArgumentData]) -> list[ArgumentData]:
        """Skip arguments from docstring validation.

        Skip first argument from docstring validation.

        Args:
            arguments: current function arguments data.

        Returns:
            Only arguments that are required to be checked.
        """
        return arguments if self.is_static else arguments[1:]


@final
class MethodParser(MethodParserBasic):
    """Class used to parse single method data."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_METHOD
    _naming_convention_regex = re.compile(f"^{Regexes.SNAKE_CASE}$")


@final
class PrivateMethodParser(MethodParserBasic):
    """Class used to parse single method data."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PRIVATE_METHOD
    _naming_convention_regex = re.compile(f"^__{Regexes.SNAKE_CASE}$")


@final
class ProtectedMethodParser(MethodParserBasic):
    """Class used to parse single method data."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_METHOD
    _naming_convention_regex = re.compile(f"^_{Regexes.SNAKE_CASE}$")
