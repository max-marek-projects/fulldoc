"""Docstrings parsing."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import cleandoc
from textwrap import dedent
from typing import final


@dataclass
class DocstringItem:
    """Python docstring item data."""

    type: str | None
    description: str


class DocstringParser(ABC):
    """Parser for any docstring style."""

    class _Patterns(ABC):
        """Patterns used to parse current docstring style."""

        @property
        @abstractmethod
        def RETURN(self) -> re.Pattern:
            """Pattern for return value description."""
            ...

        @property
        @abstractmethod
        def ARGS_SECTION(self) -> re.Pattern:
            """Pattern for arguments section."""
            ...

        @property
        @abstractmethod
        def ARG(self) -> re.Pattern:
            """Pattern for argument value description."""
            ...

        @property
        @abstractmethod
        def ATTR_SECTION(self) -> re.Pattern:
            """Pattern for arguments section."""
            ...

        @property
        @abstractmethod
        def ATTR(self) -> re.Pattern:
            """Pattern for argument value description."""
            ...

        @property
        @abstractmethod
        def RAISE_SECTION(self) -> re.Pattern:
            """Pattern for raise section."""
            ...

        @property
        @abstractmethod
        def RAISE(self) -> re.Pattern:
            """Pattern for raised exception description."""
            ...

        @property
        @abstractmethod
        def ANY_SIGN(self) -> re.Pattern:
            """Pattern for any sign of current docstring type."""
            ...

    def __init__(self, docstring: str) -> None:
        """Initialize docstring parser.

        Args:
            docstring: docstring data from any python entity.
        """
        self._description = cleandoc(docstring)
        # split docstring title and description
        parts = self._description.split('\n\n', maxsplit=1)
        if len(parts) == 2:
            self._title, self._description = parts
        elif len(parts) == 1:
            self._title = parts[0]
            self._description = ''
        else:
            self._title = parts[0]
            self._description = '\n\n'.join(parts[1:])
        patterns = self._Patterns()  # type: ignore[abstract]
        # parse return value
        return_value_match = re.search(patterns.RETURN, self._description)
        if return_value_match:
            self._return_value: DocstringItem | None = DocstringItem(
                return_value_match.group('type'),
                return_value_match.group('description'),
            )
            self._description = self._description.replace(return_value_match.group(), '')
        else:
            self._return_value = None
        # parse arguments
        arguments_block_match = re.search(patterns.ARGS_SECTION, self._description)
        self._args_data: dict[str, DocstringItem] = {}
        if arguments_block_match:
            for arg_match in re.finditer(patterns.ARG, dedent(arguments_block_match.group('section'))):
                self._args_data[arg_match.group('name')] = DocstringItem(
                    arg_match.group('type'),
                    arg_match.group('description'),
                )
            self._description = self._description.replace(arguments_block_match.group(), '')
        # parse attributes
        attributes_block_match = re.search(patterns.ATTR_SECTION, self._description)
        self._attrs_data: dict[str, DocstringItem] = {}
        if attributes_block_match:
            for attr_match in re.finditer(patterns.ATTR, dedent(attributes_block_match.group('section'))):
                self._attrs_data[attr_match.group('name')] = DocstringItem(
                    attr_match.group('type'),
                    attr_match.group('description'),
                )
            self._description = self._description.replace(attributes_block_match.group(), '')
        # parse raise block
        raise_section_match = re.search(patterns.RAISE_SECTION, self._description)
        self._raise_data: list[DocstringItem] = []
        if raise_section_match:
            for raise_match in re.finditer(patterns.RAISE, dedent(raise_section_match.group())):
                self._raise_data.append(DocstringItem(raise_match.group('type'), raise_match.group('description')))
            self._description = self._description.replace(raise_section_match.group(), '')

    @staticmethod
    def determine(docstring: str) -> 'GoogleDocstringParser | ReSTDocstringParser':
        """Determine docstring type.

        Args:
            docstring: docstring to determin style.

        Returns:
            GoogleDocstringParser: for docstring with googlestyle.
            ReSTDocstringParser: for docstring with reStructuredText style.
        """
        for docstring_type in (GoogleDocstringParser, ReSTDocstringParser):
            if re.search(docstring_type._Patterns().ANY_SIGN, docstring):
                return docstring_type(docstring)
        return GoogleDocstringParser(docstring)

    @property
    def title(self) -> str:
        """Docstring title."""
        return self._title

    @property
    def description(self) -> str:
        """Docstring description."""
        return self._description

    @property
    def return_value(self) -> DocstringItem | None:
        """Value that is returned from curren function."""
        return self._return_value

    @property
    def args_data(self) -> dict[str, DocstringItem]:
        """Data from docstring about function arguments."""
        return self._args_data

    @property
    def attrs_data(self) -> dict[str, DocstringItem]:
        """Data from docstring about attributes."""
        return self._attrs_data

    @property
    def raise_data(self) -> list[DocstringItem]:
        """Data from docstring about raised exceptions."""
        return self._raise_data


@final
class GoogleDocstringParser(DocstringParser):
    """Parser for google docstring style."""

    @final
    class _Patterns(DocstringParser._Patterns):
        """Patterns for google docstring style."""

        RETURN = re.compile(r'(Returns|Yields):\n\s+(?:(?P<type>\w+): )?(?P<description>[\s\S]*?)(?=\n\S|$)')
        ARGS_SECTION = re.compile(r'Args:\n(?P<section>[\s\S]*?)(?=\n\S|$)')
        ARG = re.compile(
            r'(?P<name>\**\w+?)(?: *\((?P<type>.+?)?\))?(?:[ ]*:[ ]*)(?P<description>[\s\S]*?)(?=\n\S|\z)',
            re.DOTALL | re.MULTILINE,
        )
        ATTR_SECTION = re.compile(r'Attributes:\n(?P<section>[\s\S]*?)(?=\n\S|$)')
        ATTR = ARG
        RAISE_SECTION = re.compile(r'Raises:\n\s+(\w+)(?: \((.+)\))?: ([\s\S]*?)(?=\n\S|$)')
        RAISE = re.compile(
            r'(?=^|\n[ \t]*)(?P<type>\w+?)(?:[ ]*:[ ]*)(?P<description>[\s\S]*?)(?=\n\S|$)',
            re.DOTALL,
        )
        ANY_SIGN = re.compile(r'^(Attributes|Raises|Args|Returns|Yields):\n')


@final
class ReSTDocstringParser(DocstringParser):
    """Parser for reStructuredText docstring style."""

    @final
    class _Patterns(DocstringParser._Patterns):
        """Patterns for reStructuredText docstring style."""

        RETURN = re.compile(r'(?<=:return: )(?P<description>[\S\s]*?)(?=\n:(?:rtype: (?P<type>[\S\s]*?)(?=\n:|$))?|$)')
        RAISE_SECTION = ATTR_SECTION = ARGS_SECTION = re.compile(r'(?P<section>.*)')
        ARG = re.compile(
            r'(?<=:param )(?P<name>\w+) *: *(?P<description>[\S\s]*?)(?=\n:(?:type \1: (?P<type>[\S\s]*?)(?=\n:|$)|$))',
        )
        ATTR = ARG
        RAISE = re.compile(r'(?<=:raises )(?P<type>\w+) *: *(?P<description>[\S\s]*?)(?=\n:|$)')
        ANY_SIGN = re.compile(r'^:(raises|param|return|rtype|type)')
