"""Exceptions used in current project."""


class ReadmeGeneratorException(Exception):
    """Exception used in readme generator."""

    pass


class DocstringNotFoundException(ReadmeGeneratorException):
    """Exception raised when docstring is not found."""

    pass


class NameNotFoundException(ReadmeGeneratorException):
    """Exception raised when object name is not found."""

    pass
