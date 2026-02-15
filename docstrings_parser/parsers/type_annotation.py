"""Type annotation handling."""

from ast import AST, Name
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities import EntityParser


@dataclass
class AnnotationParser:
    """Parse type annotation.

    Attributes:
        data: type comment as text or ast node.
        source: object that type annotation is from.
    """

    data: AST | str
    source: EntityParser

    def get_representation(self) -> str:
        """Get type annotation representation."""
        match self.data:
            case Name():
                ...
