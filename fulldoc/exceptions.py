"""Exceptions used in current project."""


class FullDocError(Exception):
    """Exception used in fulldoc lib."""

    pass


class DocstringNotFoundError(FullDocError):
    """Exception raised when docstring is not found."""

    pass


class LogicError(FullDocError):
    """Exception raised when logic error occurs."""

    pass


class ModuleNotFoundError(FullDocError):
    """Exception raised when module is not found."""

    pass


class WrongValueError(FullDocError):
    """Exception raised when wrong value found."""

    pass


class MutuallyExclusiveArgumentsError(FullDocError):
    """Exception raised when mutually exclusive arguments received."""

    pass
