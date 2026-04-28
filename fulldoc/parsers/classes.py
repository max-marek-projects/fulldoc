"""Classes parsing."""

import ast
import re
from abc import ABC
from typing import final

from fulldoc.utils import Validation

from ..config import ErrorCodes, Regexes
from ..exceptions import WrongValueError
from .basic import EntityNameParser
from .docstrings import DocstringParser


class ClassParserBasic(EntityNameParser[ast.ClassDef], ABC):
    """Parser for any class."""

    _naming_convention_code = ErrorCodes.INVALID_CLASS_NAME

    def validate_docstring(self, docstring: DocstringParser | None) -> None:
        """Validate class docstring.

        Args:
            docstring: parsed for class docstring.
        """
        super().validate_docstring(docstring)
        if not docstring:
            return
        attrs_data = docstring.attrs_data.copy()
        for attribute in self.attributes:
            if (
                not attrs_data.pop(attribute.name, None)
                and not Validation.check_upper_snake_case(attribute.name)
                and not attribute.name.startswith("_")
                and not (
                    isinstance(attribute.annotation, ast.Subscript)
                    and isinstance(attribute.annotation.value, ast.Name)
                    and attribute.annotation.value.id == "InitVar"
                )
            ):
                self.save_error(
                    ErrorCodes.UNDOCUMENTED_ATTRIBUTE, params={"definition": self.name, "name": attribute.name}
                )
        for left_attr_name in attrs_data:
            self.save_error(ErrorCodes.DOCSTRING_EXTRANEOUS_ATTRIBUTE, params={"id": left_attr_name})

    def _parse_function(self, node: ast.AST) -> None:
        """Parse function node in class.

        Args:
            node: parsed ast node.

        Raises:
            WrongValueError: if received node is not ast.FunctionDef or ast.AsyncFunctionDef.
        """
        from .functions import (
            MethodParser,
            PrivateMethodParser,
            ProtectedMethodParser,
        )

        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            raise WrongValueError("Received other node than ast.FunctionDef or ast.AsyncFunctionDef")
        is_static = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id == "staticmethod":
                    is_static = True
                    break
        if node.name.startswith("__"):
            self._entities.append(PrivateMethodParser(node, self, is_static=is_static))
            return
        if node.name.startswith("_"):
            self._entities.append(ProtectedMethodParser(node, self, is_static=is_static))
            return
        self._entities.append(MethodParser(node, self, is_static=is_static))

    def _parse_class(self, node: ast.AST) -> None:
        """Parse single node.

        Args:
            node: single node.

        Raises:
            WrongValueError: if received wrong ast node.
        """
        if not isinstance(node, ast.ClassDef):
            raise WrongValueError("Wrong ast node received")
        if node.name.startswith("__"):
            self._entities.append(PrivateNestedClassParser(node, self))
            return
        if node.name.startswith("_"):
            self._entities.append(ProtectedNestedClassParser(node, self))
            return
        self._entities.append(NestedClassParser(node, self))


@final
class ClassParser(ClassParserBasic):
    """Parser for public class."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_CLASS
    _naming_convention_regex = re.compile(f"^{Regexes.UPPER_CAMEL_CASE}$")


@final
class ProtectedClassParser(ClassParserBasic):
    """Parser for protected class."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_CLASS
    _naming_convention_regex = re.compile(f"^_{Regexes.UPPER_CAMEL_CASE}")


@final
class NestedClassParser(ClassParserBasic):
    """Parser for nested class."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PUBLIC_NESTED_CLASS
    _naming_convention_regex = re.compile(f"^{Regexes.UPPER_CAMEL_CASE}$")


@final
class PrivateNestedClassParser(ClassParserBasic):
    """Parser for nested class."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PRIVATE_NESTED_CLASS
    _naming_convention_regex = re.compile(f"^__{Regexes.UPPER_CAMEL_CASE}")


@final
class ProtectedNestedClassParser(ClassParserBasic):
    """Parser for nested class."""

    _missing_docstring_code = ErrorCodes.UNDOCUMENTED_PROTECTED_NESTED_CLASS
    _naming_convention_regex = re.compile(f"^_{Regexes.UPPER_CAMEL_CASE}")
