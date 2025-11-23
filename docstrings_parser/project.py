"""Project parsing functionality."""

from dataclasses import dataclass
from functools import cached_property
from os import listdir
from pathlib import Path

import pathspec
from treelib import Tree

from .config import Files
from .logger import logger


@dataclass
class ProjectParser:
    """Module used to parse project data."""

    module_name: str = Files.MAIN
    folder: Path = Path('.')

    def __post_init__(self) -> None:
        """Initialize project parser."""
        self.logger = logger

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

    def check_docstrings(self) -> None:
        """Check project docstrings."""
