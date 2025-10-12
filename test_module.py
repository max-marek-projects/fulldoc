"""Some module."""


def some_function() -> None:
    """Get smth."""
    ...


class SomeClass:
    """Some class."""

    class SomeSubClass:
        """Some subclass."""

        def some_subclass_method(self) -> None:
            """Get smth."""
            ...

    def some_method(self) -> None:
        """Get smth."""
        ...

    @classmethod
    def some_classmethod(self) -> None:
        """Get smth."""
        ...

    @staticmethod
    def some_staticmethod() -> None:
        """Get smth."""
        ...

    @property
    def some_property(self) -> None:
        """Some property."""
        ...
