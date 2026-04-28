"""Project parsing functionality."""

import sys
from dataclasses import dataclass
from importlib.metadata import Distribution
from pathlib import Path

import git

from . import common
from .config import DocstringTypes, TerminalColors
from .logger import get_logger
from .parsers.modules import (
    ModuleParser,
    ModuleParserBasic,
    PackageParser,
    ProtectedModuleParser,
    ProtectedPackageParser,
)
from .utils import FormatTerminal


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
        self._libraries: set[str | Distribution] = set()
        self._modules: list[ModuleParserBasic] = []
        self.files = self.get_all_files()
        self._modules = self.get_all_modules()
        for module in self.modules:
            module.parse()
            self._libraries.update(module.libraries)
        self.name = Path.cwd().name

    def get_all_files(self) -> list[Path]:
        """Parse all project files.

        Returns:
            All files that are in current repository (not gitignored).
        """
        return [
            file_path
            for file in sorted(
                git.Repo(search_parent_directories=True)
                .git.ls_files("--cached", "--others", "--exclude-standard")
                .splitlines(),
            )
            if (file_path := Path(file)).exists()
        ]

    @property
    def modules(self) -> list[ModuleParserBasic]:
        """Get all project modules.

        Returns:
            List of all modules in this project.
        """
        return self._modules

    def get_all_modules(self) -> list[ModuleParserBasic]:
        """Parse all modules from tree.

        Returns:
            List of all python-modules handlers.
        """
        modules: list[ModuleParserBasic] = []
        for file in self.files:
            if file.suffix == ".py":
                if file.stem == "__init__":
                    if file.parent.stem.startswith("_"):
                        module_parser: ModuleParserBasic = ProtectedPackageParser(file)
                    else:
                        module_parser = PackageParser(file)
                elif file.stem.startswith("_"):
                    module_parser = ProtectedModuleParser(file)
                else:
                    module_parser = ModuleParser(file)
                modules.append(module_parser)
        return modules

    def get_not_imported_files(self, main_module: Path) -> list[ModuleParserBasic]:
        """Get list of not imported modules.

        Args:
            main_module: path to main module to search all unused files.

        Returns:
            List of modules that were not imported from main module.
        """
        next_modules: set[ModuleParserBasic] = {ModuleParser(main_module)}
        parsed_modules: set[ModuleParserBasic] = set()
        while next_modules:
            current_module = next_modules.pop()
            parsed_modules.add(current_module)
            for imported_module in current_module.imported_modules:
                if imported_module not in parsed_modules:
                    next_modules.add(imported_module)
        return [module for module in self.modules if module not in parsed_modules]

    @property
    def libraries(self) -> tuple[list[str], list[Distribution]]:
        """Get libraries used in the whole project.

        Returns:
            Two values:
            - list of built-in libraries names;
            - dict with installed libraries names and distributions.
        """
        builtin_libraries: list[str] = []
        installed_libraries: list[Distribution] = []
        for module in self._libraries:
            if isinstance(module, str):
                builtin_libraries.append(module)
                continue
            installed_libraries.append(module)
        return sorted(builtin_libraries), sorted(installed_libraries, key=lambda library: library.name)

    def check(self, all_entities: bool = False) -> None:
        """Check docstrings.

        Args:
            all_entities: parse all entities (including private and protected).
        """
        for module in self.modules:
            module.check()
        error_level_found = False
        for error in common.errors:
            if error.level == "ERROR":
                error_level_found = True
            error.show()
        if error_level_found:
            print(FormatTerminal.color(f"{len(common.errors)} documentation error found", TerminalColors.RED))  # noqa: T201
            sys.exit(1)
        print(FormatTerminal.color("No issues with documentation found", TerminalColors.GREEN))  # noqa: T201
