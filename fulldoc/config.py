"""Configuration params."""

from enum import Enum, IntEnum, StrEnum
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING


class LoggerLevels(IntEnum):
    """All levels for logger."""

    DEBUG = DEBUG
    INFO = INFO
    WARNING = WARNING
    ERROR = ERROR
    CRITICAL = CRITICAL


class ErrorLevels(StrEnum):
    """All allowed parsing error levels."""

    WARNING = "WARNING"
    ERROR = "ERROR"


class DocstringTypes(StrEnum):
    """Possible docstring types."""

    GOOGLE = "Google"
    RE_STRUCTURED_TEXT = "reStructuredText"


class ProjectTypes(StrEnum):
    """Possible project types."""

    DJANGO = "Django"
    FAST_API = "FastAPI"
    FLASK = "Flask"
    LIBRARY = "Library"
    SCRIPT = "Script"


class LoggerConfig:
    """Logger config params."""

    NAME = "fulldoc"
    LEVEL = LoggerLevels.INFO
    FORMAT = "%(name)s - %(asctime)s - %(levelname)s - %(message)s"


class TerminalColors(StrEnum):
    """Special symbols for different terminal colors."""

    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


class TerminalFonts(StrEnum):
    """Special symbols for different terminal fonts."""

    HEADER = "\033[95m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ArgumentTypes(StrEnum):
    """Allowed argument types."""

    GENERAL = "general"
    ARGS = "args"
    KWARGS = "kwargs"


EMPTY_CODE = "NONE"


class ErrorCodes(Enum):
    """Error codes."""

    # ---------- undocumented public entities ----------
    UNDOCUMENTED_PUBLIC_MODULE = ("D100", "Missing docstring in public module")
    UNDOCUMENTED_PUBLIC_CLASS = ("D101", "Missing docstring in public class")
    UNDOCUMENTED_PUBLIC_METHOD = ("D102", "Missing docstring in public method")
    UNDOCUMENTED_PUBLIC_FUNCTION = ("D103", "Missing docstring in public function")
    UNDOCUMENTED_PUBLIC_PACKAGE = ("D104", "Missing docstring in public package")
    UNDOCUMENTED_PUBLIC_NESTED_CLASS = ("D106", "Missing docstring in public nested class")

    # ---------- undocumented protected entities ----------
    UNDOCUMENTED_PROTECTED_MODULE = (None, "Missing docstring in protected module")
    UNDOCUMENTED_PROTECTED_CLASS = (None, "Missing docstring in protected class")
    UNDOCUMENTED_PROTECTED_METHOD = (None, "Missing docstring in protected method")
    UNDOCUMENTED_PROTECTED_FUNCTION = (None, "Missing docstring in protected function")
    UNDOCUMENTED_PROTECTED_PACKAGE = (None, "Missing docstring in protected package")
    UNDOCUMENTED_PROTECTED_NESTED_CLASS = (
        None,
        "Missing docstring in protected nested class",
    )

    # ---------- undocumented private entities ----------
    UNDOCUMENTED_PRIVATE_METHOD = (None, "Missing docstring in private method")
    UNDOCUMENTED_PRIVATE_NESTED_CLASS = (
        None,
        "Missing docstring in protected nested class",
    )

    # ---------- other undocumented entities ----------
    UNDOCUMENTED_MAGIC_METHOD = ("D105", "Missing docstring in magic method")  # TODO: add usage
    UNDOCUMENTED_INIT = ("D107", "Missing docstring in __init__")  # TODO: add usage

    # ---------- one liners ----------
    UNNECESSARY_MULTILINE_DOCSTRING = ("D200", "One-line docstring should fit on one line")  # TODO: add usage
    EMPTY_DOCSTRING = ("D419", "Docstring is empty")

    # ---------- blank lines ----------
    BLANK_LINE_BEFORE_FUNCTION = (
        "D201",
        "No blank lines allowed before function docstring (found {num_lines})",
    )  # TODO: add usage
    BLANK_LINE_AFTER_FUNCTION = (
        "D202",
        "No blank lines allowed after function docstring (found {num_lines})",
    )  # TODO: add usage
    INCORRECT_BLANK_LINE_BEFORE_CLASS = ("D203", "1 blank line required before class docstring")  # TODO: add usage
    INCORRECT_BLANK_LINE_AFTER_CLASS = ("D204", "1 blank line required after class docstring")  # TODO: add usage
    MISSING_BLANK_LINE_AFTER_SUMMARY = (
        "D205",
        "1 blank line required between summary line and description",
    )  # TODO: add usage
    BLANK_LINE_BEFORE_CLASS = ("D211", "No blank lines allowed before class docstring")  # TODO: add usage
    MULTI_LINE_SUMMARY_FIRST_LINE = (
        "D212",
        "Multi-line docstring summary should start at the first line",
    )  # TODO: add usage
    MULTI_LINE_SUMMARY_SECOND_LINE = (
        "D213",
        "Multi-line docstring summary should start at the second line",
    )  # TODO: add usage
    NON_CAPITALIZED_SECTION_NAME_NEWLINE = (
        "D406",
        'Section name should end with a newline ("{name}")',
    )  # TODO: add usage
    MISSING_DASHED_UNDERLINE_AFTER_SECTION = (
        "D407",
        'Missing dashed underline after section ("{name}")',
    )  # TODO: add usage
    MISSING_SECTION_UNDERLINE_AFTER_NAME = (
        "D408",
        'Section underline should be in the line following the section\'s name ("{name}")',
    )  # TODO: add usage
    MISMATCHED_SECTION_UNDERLINE_LENGTH = (
        "D409",
        'Section underline should match the length of its name ("{name}")',
    )  # TODO: add usage
    NO_BLANK_LINE_AFTER_SECTION = ("D410", 'Missing blank line after section ("{name}")')  # TODO: add usage
    NO_BLANK_LINE_BEFORE_SECTION = ("D411", 'Missing blank line before section ("{name}")')  # TODO: add usage
    BLANK_LINES_BETWEEN_HEADER_AND_CONTENT = (
        "D412",
        'No blank lines allowed between a section header and its content ("{name}")',
    )  # TODO: add usage
    MISSING_BLANK_LINE_AFTER_LAST_SECTION = (
        "D413",
        'Missing blank line after last section ("{name}")',
    )  # TODO: add usage

    # ---------- indentation & spacing ----------
    DOCSTRING_TAB_INDENTATION = ("D206", "Docstring should be indented with spaces, not tabs")  # TODO: add usage
    UNDER_INDENTATION = ("D207", "Docstring is under-indented")  # TODO: add usage
    OVER_INDENTATION = ("D208", "Docstring is over-indented")  # TODO: add usage
    NEW_LINE_AFTER_LAST_PARAGRAPH = (
        "D209",
        "Multi-line docstring closing quotes should be on a separate line",
    )  # TODO: add usage
    SURROUNDING_WHITESPACE = ("D210", "No whitespaces allowed surrounding docstring text")  # TODO: add usage
    OVER_INDENTED_SECTION = ("D214", 'Section is over-indented ("{name}")')  # TODO: add usage
    OVER_INDENTED_SECTION_UNDERLINE = ("D215", 'Section underline is over-indented ("{name}")')  # TODO: add usage

    # ---------- quotes and escaping ----------
    TRIPLE_SINGLE_QUOTES = ("D300", 'Use triple double quotes """')  # TODO: add usage
    ESCAPE_SEQUENCE_IN_DOCSTRING = ("D301", 'Use r""" if any backslashes in a docstring')  # TODO: add usage

    # ---------- content / wording ----------
    MISSING_TRAILING_PERIOD = ("D400", "First line should end with a period")  # TODO: add usage
    NON_IMPERATIVE_MOOD = (
        "D401",
        'First line of docstring should be in imperative mood: "{first_line}"',
    )  # TODO: add usage
    SIGNATURE_IN_DOCSTRING = ("D402", "First line should not be the function's signature")  # TODO: add usage
    FIRST_WORD_UNCAPITALIZED = (
        "D403",
        "First word of the docstring should be capitalized: {original} -> {expected}",
    )  # TODO: add usage
    DOCSTRING_STARTS_WITH_THIS = ("D404", 'First word of the docstring should not be "This"')  # TODO: add usage
    NON_CAPITALIZED_SECTION_NAME = ("D405", 'Section name should be properly capitalized ("{name}")')  # TODO: add usage
    MISSING_TERMINAL_PUNCTUATION = (
        "D415",
        "First line should end with a period, question mark, or exclamation point",
    )  # TODO: add usage
    MISSING_SECTION_NAME_COLON = ("D416", 'Section name should end with a colon ("{name}")')  # TODO: add usage
    OVERLOAD_WITH_DOCSTRING = (
        "D418",
        "Function decorated with @overload shouldn't contain a docstring",
    )  # TODO: add usage
    INCORRECT_SECTION_ORDER = (
        "D420",
        'Section "{current}" appears after section "{previous}" but should be before it',
    )  # TODO: add usage

    # ---------- extraneous / missing parameters ----------
    UNDOCUMENTED_PARAM = (
        "D417",
        "Missing argument description in the docstring for {definition}: {name}",
    )
    DOCSTRING_EXTRANEOUS_PARAMETER = (
        "DOC102",
        "Documented parameter {id} is not in the function's signature",
    )

    # ---------- extraneous / missing attributes ----------
    UNDOCUMENTED_ATTRIBUTE = (
        None,
        "Missing public attribute description in the docstring for {definition}: {name}",
    )
    DOCSTRING_EXTRANEOUS_ATTRIBUTE = (
        None,
        "Documented attribute {id} is not defined as public attribute in class body",
    )

    # ---------- returns ----------
    DOCSTRING_MISSING_RETURNS = ("DOC201", "return is not documented in docstring")
    DOCSTRING_EXTRANEOUS_RETURNS = (
        "DOC202",
        "Docstring should not have a returns section because the function doesn't return anything",
    )

    # ---------- yields ----------
    DOCSTRING_MISSING_YIELDS = ("DOC402", "yield is not documented in docstring")
    DOCSTRING_EXTRANEOUS_YIELDS = (
        "DOC403",
        'Docstring has a "Yields" section but the function doesn\'t yield anything',
    )

    # ---------- exceptions ----------
    DOCSTRING_MISSING_EXCEPTION = ("DOC501", "Raised exception {id} missing from docstring")
    DOCSTRING_EXTRANEOUS_EXCEPTION = ("DOC502", "Raised exception is not explicitly raised: {id}")

    # ---------- internal ----------
    NO_MODULE_NAMED = (None, 'Module named "{module_name}" not found')

    # ---------- naming ----------

    INVALID_CLASS_NAME = ("N801", "Class name {name} should use CapWords convention")
    INVALID_FUNCTION_NAME = ("N802", "Function name {name} should be lowercase")
    INVALID_ARGUMENT_NAME = ("N803", "Argument name {name} should be lowercase")  # TODO: add usage
    INVALID_FIRST_ARGUMENT_NAME_FOR_CLASS_METHOD = (
        "N804",
        "First argument of a class method should be named cls",
    )  # TODO: add usage
    INVALID_FIRST_ARGUMENT_NAME_FOR_METHOD = (
        "N805",
        "First argument of a method should be named self",
    )  # TODO: add usage
    NON_LOWERCASE_VARIABLE_IN_FUNCTION = ("N806", "Variable {name} in function should be lowercase")  # TODO: add usage
    DUNDER_FUNCTION_NAME = ("N807", "Function name should not start and end with __")
    CONSTANT_IMPORTED_AS_NON_CONSTANT = ("N811", "Constant {name} imported as non-constant {asname}")  # TODO: add usage
    LOWERCASE_IMPORTED_AS_NON_LOWERCASE = (
        "N812",
        "Lowercase {name} imported as non-lowercase {asname}",
    )  # TODO: add usage
    CAMELCASE_IMPORTED_AS_LOWERCASE = ("N813", "Camelcase {name} imported as lowercase {asname}")  # TODO: add usage
    CAMELCASE_IMPORTED_AS_CONSTANT = ("N814", "Camelcase {name} imported as constant {asname}")  # TODO: add usage
    MIXED_CASE_VARIABLE_IN_CLASS_SCOPE = (
        "N815",
        "Variable {name} in class scope should not be mixedCase",
    )  # TODO: add usage
    MIXED_CASE_VARIABLE_IN_GLOBAL_SCOPE = (
        "N816",
        "Variable {name} in global scope should not be mixedCase",
    )  # TODO: add usage
    CAMELCASE_IMPORTED_AS_ACRONYM = ("N817", "CamelCase {name} imported as acronym {asname}")  # TODO: add usage
    ERROR_SUFFIX_ON_EXCEPTION_NAME = (
        "N818",
        "Exception name {name} should be named with an Error suffix",
    )  # TODO: add usage
    INVALID_MODULE_NAME = ("N999", "Invalid module name: '{name}'")

    # ---------- code style for proper parsing (only partially implemented) ----------

    REDEFINED_WHILE_UNUSED = ("F811", "Redefinition of unused {name} from {row}")
    UNDEFINED_NAME = ("F821", "Undefined name {name}")

    def __init__(self, code: str | None, message: str) -> None:
        """Initialize error code.

        Args:
            code: linting error code.
            message: linting error message, may be with placeholders.
        """
        self.code = code
        self.message = message


class Regexes(StrEnum):
    """Basic regexes."""

    SNAKE_CASE = r"[a-z]+(_[a-z]+)*"
    UPPER_SNAKE_CASE = r"[A-Z]+(_[A-Z]+)*"
    CAMEL_CASE = r"[a-z]+([A-Z][a-z]*)*"
    UPPER_CAMEL_CASE = r"([A-Z][a-z]*)+"


MAGIC_METHODS = {
    # Object lifecycle / representation / comparison
    "__new__",
    "__init__",
    "__del__",
    "__repr__",
    "__str__",
    "__bytes__",
    "__format__",
    "__lt__",
    "__le__",
    "__eq__",
    "__ne__",
    "__gt__",
    "__ge__",
    "__hash__",
    "__bool__",
    # Attribute access / descriptors / module customization
    "__getattr__",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__dir__",
    "__get__",
    "__set__",
    "__delete__",
    "__set_name__",
    # Class creation / subclassing / generic classes
    "__init_subclass__",
    "__prepare__",
    "__mro_entries__",
    "__instancecheck__",
    "__subclasscheck__",
    "__class_getitem__",
    "__match_args__",  # special class attribute used in pattern matching
    # Callable / container / sequence
    "__call__",
    "__len__",
    "__length_hint__",
    "__getitem__",
    "__setitem__",
    "__delitem__",
    "__missing__",
    "__iter__",
    "__reversed__",
    "__contains__",
    # Numeric
    "__add__",
    "__sub__",
    "__mul__",
    "__matmul__",
    "__truediv__",
    "__floordiv__",
    "__mod__",
    "__divmod__",
    "__pow__",
    "__lshift__",
    "__rshift__",
    "__and__",
    "__xor__",
    "__or__",
    # Reflected numeric
    "__radd__",
    "__rsub__",
    "__rmul__",
    "__rmatmul__",
    "__rtruediv__",
    "__rfloordiv__",
    "__rmod__",
    "__rdivmod__",
    "__rpow__",
    "__rlshift__",
    "__rrshift__",
    "__rand__",
    "__rxor__",
    "__ror__",
    # In-place numeric
    "__iadd__",
    "__isub__",
    "__imul__",
    "__imatmul__",
    "__itruediv__",
    "__ifloordiv__",
    "__imod__",
    "__ipow__",
    "__ilshift__",
    "__irshift__",
    "__iand__",
    "__ixor__",
    "__ior__",
    # Unary / conversion / rounding
    "__neg__",
    "__pos__",
    "__abs__",
    "__invert__",
    "__complex__",
    "__int__",
    "__float__",
    "__index__",
    "__round__",
    "__trunc__",
    "__floor__",
    "__ceil__",
    # Context managers / async / iteration
    "__enter__",
    "__exit__",
    "__aenter__",
    "__aexit__",
    "__await__",
    "__aiter__",
    "__anext__",
    "__next__",
    # Buffer / annotations
    "__buffer__",
    "__release_buffer__",
    "__annotations__",
    "__annotate__",
    # Dataclasses
    "__post_init__",
}
