"""Project parsing functionality."""

import heapq
from dataclasses import dataclass
from functools import cached_property
from importlib.metadata import Distribution
from os import listdir
from pathlib import Path

import pathspec
from tomli import load
from treelib import Tree
from treelib.node import Node

from .config import Files
from .entities import ModuleParser
from .exceptions import ModuleNotFoundException
from .logger import logger
from .readme import ReadmeHandler


@dataclass
class ProjectParser:
    """Module used to parse project data."""

    module_name: str = Files.MAIN
    folder: Path = Path('.')
    parse_all_files: bool = False

    def __post_init__(self) -> None:
        """Initialize project parser."""
        self.logger = logger
        self.folder = self.folder.absolute()
        self._builtin_libraries: set[str] = set()
        self._installed_libraries: dict[str, list[Distribution]] = {}
        for module in self.modules:
            builtin_libraries, installed_libraries = module.libraries
            self._builtin_libraries.update(builtin_libraries)
            self._installed_libraries.update(installed_libraries)

    @cached_property
    def tree(self) -> Tree:
        """Get current project files tree.

        Returns:
            Tree of current project ignoring files from gitignore.
        """
        return self._tree_from_folder(self.folder)

    def _tree_from_folder(self, folder: Path) -> Tree:
        """Get tree from current folder path."""
        tree = Tree()
        tree.create_node(folder.name, str(folder))
        for file in listdir(folder):
            local_path = folder / file
            if self.gitignore_patterns.match_file(local_path):
                continue
            if local_path.is_dir() and self.gitignore_patterns.match_file(str(local_path) + '/'):
                continue
            if local_path.is_file():
                tree.create_node(local_path.name, str(local_path), parent=str(folder))
                continue
            subtree = self._tree_from_folder(local_path)
            if subtree.size() <= 1:
                continue
            tree.paste(str(folder), subtree)
            continue
        return tree

    @cached_property
    def gitignore_patterns(self) -> pathspec.PathSpec:
        """Reads patterns from a .gitignore file."""
        try:
            with open(Files.GITIGNORE, 'r') as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            self.logger.info(f"'{Files.GITIGNORE}' not found. No patterns loaded.")
            lines = []
        lines.extend(['.git', '.idea'])
        spec = pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)
        return spec

    @property
    def name(self) -> str:
        """Get name of current project.

        Returns:
            Current directory name.
        """
        if Path(Files.TOML).exists():
            with open(Files.TOML, 'rb') as file:
                try:
                    return load(file)['project']['name']
                except KeyError:
                    self.logger.info('Project name not found in toml file')
        return self.folder.absolute().name

    @cached_property
    def modules(self) -> list[ModuleParser]:
        """Get all project modules."""
        if self.parse_all_files:
            new_nodes = {node for node in self.tree.all_nodes_itr() if node.tag.endswith('.py')}
        else:
            main_node = self.tree.get_node(str(self.folder / self.module_name))
            if not main_node:
                raise ModuleNotFoundException(
                    f'Main module named "{self.folder / self.module_name}" is not found in git scope',
                )
            new_nodes = {main_node}
        previously_parsed_nodes: set[Node] = set()
        modules: list[ModuleParser] = []
        while new_nodes:
            node = new_nodes.pop()
            if Path(node.identifier).is_dir():
                continue
            module = ModuleParser(Path(node.identifier), folder=self.folder)
            heapq.heappush(modules, module)
            for imported_module in module.imported_modules:
                new_node = self.tree.get_node(str(imported_module.path))
                if new_node not in new_nodes and new_node not in previously_parsed_nodes:
                    new_nodes.add(new_node)
            previously_parsed_nodes.add(node)
        return [heapq.heappop(modules) for _ in range(len(modules))]

    @property
    def readme(self) -> ReadmeHandler:
        """Get readme handler for current project."""
        return ReadmeHandler(self)

    @property
    def libraries(self) -> tuple[list[str], dict[str, list[Distribution]]]:
        """Get libraries used in the whole project."""
        return sorted(self._builtin_libraries), dict(sorted(self._installed_libraries.items()))
