"""Different functions parsing."""

from ast import FunctionDef, arguments, expr
from typing import final

from .entities import EntityNameParser


@final
class FunctionParser(EntityNameParser[FunctionDef]):
    """Class used to parse single function data."""

    TITLE = 'Function'

    @property
    def arguments(self) -> arguments:
        """Get function arguments.

        Returns:
            Node for function arguments.
        """
        return self._data.args

    @property
    def return_value(self) -> expr | None:
        """Get current function return value.

        Returns:
            Return value of current function.
        """
        return self._data.returns
