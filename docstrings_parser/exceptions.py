"""Exceptions used in current project."""


class ReadmeGeneratorException(Exception):
    """Exception used in readme generator."""

    pass


class DocstringNotFoundException(ReadmeGeneratorException):
    """Exception raised when docstring is not found."""

    pass


class LogicError(ReadmeGeneratorException):
    """Exception raised when logic error occures."""

    pass


class ModuleNotFoundException(ReadmeGeneratorException):
    """Exception raised when module is not found."""

    pass


class WrongValueError(ReadmeGeneratorException):
    """Exception raised when wrong value found."""

    pass
