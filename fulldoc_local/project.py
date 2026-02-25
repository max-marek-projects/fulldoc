"""Project parsing functionality."""

import subprocess
import sys
from dataclasses import dataclass
from importlib.metadata import Distribution
from pathlib import Path

from .config import DocstringTypes
from .logger import get_logger
from .parsers.entities import ModuleParser
from .readme.basic import ReadmeHandler
from .utils import ErrorData


@dataclass
class ProjectParser:
    """Module used to parse project data.

    Attributes:
        docstrings_type: type of docstrings in current module.
    """

    docstrings_type: DocstringTypes = DocstringTypes.GOOGLE

    def __post_init__(self) -> None:
        """Initialize project parser."""
        self.logger = get_logger()
        self._builtin_libraries: set[str] = set()
        self._installed_libraries: dict[str, list[Distribution]] = {}
        self._modules: list[ModuleParser] = []
        self.errors: list[ErrorData] = []
        self.files = self.get_all_files()
        self._modules = self.get_all_modules()
        for module in self.modules:
            module.parse()
            builtin_libraries, installed_libraries = module.libraries
            self._builtin_libraries.update(builtin_libraries)
            self._installed_libraries.update(installed_libraries)
        self.name = Path.cwd().name

    def get_all_files(self) -> list[Path]:
        """Parse all project files.

        Returns:
            All files that are in current repository (not gitignored).
        """
        return [
            file_path
            for file in sorted(
                subprocess.check_output(
                    ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
                    universal_newlines=True,
                    stderr=subprocess.PIPE,
                ).splitlines(),
            )
            if (file_path := Path(file)).exists()
        ]

    @property
    def modules(self) -> list[ModuleParser]:
        """Get all project modules.

        Returns:
            List of all modules in this project.
        """
        return self._modules

    def get_all_modules(self) -> list[ModuleParser]:
        """Parse all modules from tree.

        Returns:
            List of all python-modules handlers.
        """
        modules: list[ModuleParser] = []
        for file in self.files:
            if file.suffix == '.py':
                modules.append(ModuleParser(file, self))
        return modules

    def get_not_imported_files(self, main_module: Path) -> list[ModuleParser]:
        """Get list of not imported modules.

        Args:
            main_module: path to main module to search all unused files.

        Returns:
            List of modules that were not imported from main module.
        """
        next_modules = {ModuleParser(main_module, self)}
        parsed_modules: set[ModuleParser] = set()
        while next_modules:
            current_module = next_modules.pop()
            parsed_modules.add(current_module)
            for imported_module in current_module.imported_modules:
                if imported_module not in parsed_modules:
                    next_modules.add(imported_module)
        return [module for module in self.modules if module not in parsed_modules]

    @property
    def readme(self) -> ReadmeHandler:
        """Get readme handler for current project.

        Returns:
            Readme file handler.
        """
        return ReadmeHandler.determine(self)

    @property
    def libraries(self) -> tuple[list[str], dict[str, list[Distribution]]]:
        """Get libraries used in the whole project.

        Returns:
            Two values:
            - list of buil-in libraries names;
            - dict with installed libraries names and dictributions.
        """
        return sorted(self._builtin_libraries), dict(sorted(self._installed_libraries.items()))

    def check(self) -> None:
        """Провести проверку докстрингов."""
        for module in self.modules:
            module.check_docstrings()
        error_level_found = False
        for error in self.errors:
            if error.level == 'ERROR':
                error_level_found = True
            error.show()
        if error_level_found:
            sys.exit(1)
