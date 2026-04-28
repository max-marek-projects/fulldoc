"""Docstrings parsing."""

from __future__ import annotations

import ast
import re
from abc import ABC
from dataclasses import InitVar, dataclass
from inspect import cleandoc
from textwrap import dedent
from typing import TYPE_CHECKING, ClassVar, Literal, final

from ..config import ErrorCodes
from .basic import BasicParser

if TYPE_CHECKING:
    from .basic import EntityParser


@dataclass
class _Patterns:
    """Docstring parsing patterns.

    Attributes:
        returns: Pattern for return value description.
        arg: Pattern for argument value description.
        raises: Pattern for raised exception description.
        any_sign: Pattern for any sign of current docstring type.
    """

    returns: re.Pattern[str]
    arg: re.Pattern[str]
    raises: re.Pattern[str]
    any_sign: re.Pattern[str]
    # additional
    yields_extra: InitVar[re.Pattern[str] | None] = None
    attr_extra: InitVar[re.Pattern[str] | None] = None
    attrs_section_extra: InitVar[re.Pattern[str] | None] = None
    raise_section_extra: InitVar[re.Pattern[str] | None] = None
    args_section_extra: InitVar[re.Pattern[str] | None] = None

    def __post_init__(
        self,
        yields_extra: re.Pattern[str] | None,
        attr_extra: re.Pattern[str] | None,
        attrs_section_extra: re.Pattern[str] | None,
        raise_section_extra: re.Pattern[str] | None,
        args_section_extra: re.Pattern[str] | None,
    ) -> None:
        """Initialize optional patterns.

        Args:
            yields_extra: extra pattern for yielded value description (defaults to return pattern).
            attr_extra: extra pattern for attribute value description (defaults to arg pattern).
            attrs_section_extra: extra pattern for attributes section (defaults to whole docstring).
            raise_section_extra: extra pattern for raise section (defaults to whole docstring).
            args_section_extra: extra pattern for arguments section (defaults to whole docstring).
        """
        self.yields = yields_extra or self.returns
        self.attr = attr_extra or self.arg
        self.attrs_section = attrs_section_extra or re.compile(r"(?P<section>.*)")
        self.raise_section = raise_section_extra or re.compile(r"(?P<section>.*)")
        self.args_section = args_section_extra or re.compile(r"(?P<section>.*)")


@dataclass
class DocstringParser(BasicParser[ast.Expr], ABC):
    """Parser for any docstring style.

    Attributes:
        value: docstring string value.
    """

    value: str

    _patterns: ClassVar[_Patterns]

    @classmethod
    def from_entity(cls, entity: EntityParser) -> GoogleDocstringParser | ReSTDocstringParser | None:
        """Check first entity content node.

        Args:
            entity: entity to parse docstring from.

        Returns:
            Some of known docstring type handlers.
        """
        if not entity.nodes:
            return None
        node = entity.nodes[0]
        if (
            not isinstance(node, ast.Expr)
            or not isinstance(node.value, ast.Constant)
            or not isinstance(node.value.value, str)
        ):
            return None
        value = node.value.value
        for docstring_type in (GoogleDocstringParser, ReSTDocstringParser):
            if re.search(docstring_type._patterns.any_sign, value):
                return docstring_type(node, entity, value)
        return GoogleDocstringParser(node, entity, value)  # defaults to google type

    def __post_init__(self) -> None:
        """Initialize docstring parser."""
        self._raw_value = self.get_source_segment(self.data)
        self.source = cleandoc(self.value)
        self._description = self.source
        # split docstring title and description
        parts = self._description.split("\n\n", maxsplit=1)
        if len(parts) == 2:
            self._title, self._description = parts
        elif len(parts) == 1:
            self._title = parts[0]
            self._description = ""
        else:
            self._title = parts[0]
            self._description = "\n\n".join(parts[1:])
        # parse return value
        return_value_match = re.search(self._patterns.returns, self._description)
        if return_value_match:
            self._return_value: DocstringItem | None = DocstringItem(
                return_value_match.group("type"),
                return_value_match.group("description"),
            )
            self._description = self._description.replace(return_value_match.group(), "")
        else:
            self._return_value = None
        # parse yield value
        if self.has_separate_yield_statement:
            yield_value_match = re.search(self._patterns.yields, self._description)
            if yield_value_match:
                self._yield_value: DocstringItem | None = DocstringItem(
                    yield_value_match.group("type"),
                    yield_value_match.group("description"),
                )
                self._description = self._description.replace(yield_value_match.group(), "")
            else:
                self._yield_value = None
        else:
            self._yield_value = self.return_value
        # parse arguments
        arguments_block_match = re.search(self._patterns.args_section, self._description)
        self._args_data: dict[str, DocstringItem] = {}
        if arguments_block_match:
            for arg_match in re.finditer(self._patterns.arg, dedent(arguments_block_match.group("section"))):
                self._args_data[arg_match.group("name")] = DocstringItem(
                    arg_match.group("type"),
                    arg_match.group("description"),
                )
                self._description = self._description.replace(arg_match.group(), "")
        # parse attributes
        attributes_block_match = re.search(self._patterns.attrs_section, self._description)
        self._attrs_data: dict[str, DocstringItem] = {}
        if attributes_block_match:
            for attr_match in re.finditer(self._patterns.attr, dedent(attributes_block_match.group("section"))):
                self._attrs_data[attr_match.group("name")] = DocstringItem(
                    attr_match.group("type"),
                    attr_match.group("description"),
                )
                self._description = self._description.replace(attr_match.group(), "")
        # parse raise block
        raise_section_match = re.search(self._patterns.raise_section, self._description)
        self._raise_data: list[DocstringItem] = []
        if raise_section_match:
            for raise_match in re.finditer(self._patterns.raises, dedent(raise_section_match.group())):
                self._raise_data.append(
                    DocstringItem(
                        raise_match.group("type"),
                        raise_match.group("description"),
                    ),
                )
                self._description = self._description.replace(raise_match.group(), "")

    @property
    def has_separate_yield_statement(self) -> bool:
        """Check if docstring has separate yield statement.

        Returns:
            True if regular expressions for yields and return statements are different.
        """
        return self._patterns.returns != self._patterns.yields

    @property
    def title(self) -> str:
        """Docstring title.

        Returns:
            First line of docstring title.
        """
        return self._title

    @property
    def description(self) -> str:
        """Docstring description.

        Returns:
            docstring description without special blocks.
        """
        return self._description

    @property
    def return_value(self) -> DocstringItem | None:
        """Value that is returned from current function.

        Returns:
            list with returned values descriptions.
        """
        return self._return_value

    @property
    def yield_value(self) -> DocstringItem | None:
        """Value that is yielded from current function.

        Returns:
            list with yielded values descriptions.
        """
        return self._yield_value

    @property
    def args_data(self) -> dict[str, DocstringItem]:
        """Data from docstring about function arguments.

        Returns:
            dict with argument name and it's description.
        """
        return self._args_data

    @property
    def attrs_data(self) -> dict[str, DocstringItem]:
        """Data from docstring about attributes.

        Returns:
            dict with attribute name and it's description.
        """
        return self._attrs_data

    @property
    def raise_data(self) -> list[DocstringItem]:
        """Data from docstring about raised exceptions.

        Returns:
            list with raised values descriptions.
        """
        return self._raise_data

    def validate(self) -> None:
        """Validate docstring."""
        if not self._raw_value.endswith('"""'):
            self.save_error(ErrorCodes.TRIPLE_SINGLE_QUOTES)
        if not self.source.strip():
            self.save_error(ErrorCodes.EMPTY_DOCSTRING)
        # TODO: D206-D210, D214-D215, D300-D301, D400-D405, D415, D418, D419, D420

    # abstract methods overload

    @property
    def start_line_number(self) -> int:
        """Start code row number.

        Returns:
            Number of start row for current element.
        """
        return self.data.lineno


@final
class GoogleDocstringParser(DocstringParser):
    """Parser for google docstring style."""

    _patterns = _Patterns(
        returns=re.compile(
            r"Returns:\n\s+(?:(?P<type>\w+): )?(?P<description>[\s\S]*?)(?=\n\S|\Z)",
            re.MULTILINE,
        ),
        arg=re.compile(
            r"(?P<name>\**\w+?)(?: *\((?P<type>.+?)?\))?(?:[ ]*:[ ]*)(?P<description>[\s\S]*?)(?=\n\S|\Z)",
            re.DOTALL | re.MULTILINE,
        ),
        raises=re.compile(
            r"(?=^|\n[ \t]*)(?P<type>\w+?)(?:[ ]*:[ ]*)(?P<description>[\s\S]*?)(?=\n\S|\Z)",
            re.DOTALL | re.MULTILINE,
        ),
        any_sign=re.compile(r"^(Attributes|Raises|Args|Returns|Yields):\n"),
        # additional
        yields_extra=re.compile(
            r"Yields:\n\s+(?:(?P<type>\w+): )?(?P<description>[\s\S]*?)(?=\n\S|\Z)",
            re.MULTILINE,
        ),
        attrs_section_extra=re.compile(r"Attributes:\n(?P<section>[\s\S]*?)(?=\n\S|\Z)", re.MULTILINE),
        raise_section_extra=re.compile(
            r"Raises:\n\s+(\w+)(?: \((.+)\))?: ([\s\S]*?)(?=\n\S|\Z)",
            re.MULTILINE,
        ),
        args_section_extra=re.compile(r"Args:\n(?P<section>[\s\S]*?)(?=\n\S|$)"),
    )


@final
class ReSTDocstringParser(DocstringParser):
    """Parser for reStructuredText docstring style."""

    _patterns = _Patterns(
        returns=re.compile(
            r"(?<=:return: )(?P<description>[\S\s]*?)(?=\n:(?:rtype: (?P<type>[\S\s]*?)(?=\n:|$))?|$)",
        ),
        arg=re.compile(
            r"(?<=:param )(?P<name>\w+) *: *(?P<description>[\S\s]*?)(?=\n:(?:type \1: (?P<type>[\S\s]*?)(?=\n:|$)|$))",
        ),
        raises=re.compile(r"(?<=:raises )(?P<type>\w+) *: *(?P<description>[\S\s]*?)(?=\n:|$)"),
        any_sign=re.compile(r"^:(raises|param|return|rtype|type)"),
    )


DocstringTypes = Literal["google", "rest", "numpy"]


@dataclass
class DocstringItem:
    """Python docstring item data.

    Attributes:
        type: type comment inside docstring item description.
        description: docstring item text description.
    """

    type: str | None
    description: str
