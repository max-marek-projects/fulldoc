"""Readme handling."""

import re
import tomllib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from dominate.tags import a, code, pre  # type: ignore[import-untyped]
from pandas import DataFrame
from treelib import Tree

from ..config import Files
from ..logger import get_logger

if TYPE_CHECKING:
    from ..project import ProjectParser


@dataclass
class ReadmeHandler(ABC):
    """Readme handler.

    Attributes:
        _project: current project handler.
    """

    _project: 'ProjectParser'

    def __post_init__(self) -> None:
        """Initializa readme handler."""
        self.logger = get_logger()

    @staticmethod
    def href_from_title(title: str) -> str:
        """Get href based on title in readme.

        Args:
            title: original title from readme.

        Returns:
            Formatted href value which leads to this title.
        """
        # lower register
        title = title.lower()
        # remove punctuation marks
        title = re.sub(r'[^\w\s-]', '', title)
        # replace spaces with dash
        title = re.sub(r'\s+', '-', title)
        # remove mutual dashes
        title = re.sub(r'-+', '-', title)
        # remove trailing dashes
        title = title.strip('-')
        return '#' + title

    @property
    def text(self) -> str:
        """Get readme text.

        Returns:
            Readme text completed from project information.
        """
        readme_content: dict[str, str] = {}
        readme_content['Tree'] = str(pre('\n' + str(self.get_tree()) + '\n'))
        readme_content['Libraries'] = self.libraries_table
        readme_text = f'# {self._project.name}\n\n'
        readme_text += '## Content\n\n'
        for index, title in enumerate(tuple(readme_content.keys()), start=1):
            # add index to title
            readme_content[f'{index}. {title}'] = readme_content.pop(title)
        readme_text += str(code([a(title, _href=self.href_from_title(title))] for title in readme_content))
        readme_text += '\n\n'
        for title, content in readme_content.items():
            readme_text += f'## {title}\n\n'
            readme_text += content
            readme_text += '\n\n'
        return readme_text

    @abstractmethod
    def get_readme_content(self) -> dict[str, str]:
        """Get content for readme file with.

        dict with keys - sections title, values - sections content.
        """
        ...

    @property
    def libraries_table(self) -> str:
        """Get project libraries table markdown representation.

        Returns:
            String representation of pandas Dataframe containing the whole libraries information.
        """
        builtin_libraries, installed_libraries = self._project.libraries
        return DataFrame(
            data={
                'Built in': [
                    re.sub(r'\n\s*', '', DataFrame(data={'Name': builtin_libraries}).to_html(index=False, border=0)),
                ],
                'Installed': [
                    re.sub(
                        r'\n\s*',
                        '',
                        DataFrame(
                            data={
                                'Name': [
                                    distribution.name
                                    for import_name, distributions in installed_libraries.items()
                                    for distribution in distributions
                                ],
                                'Version': [
                                    distribution.version
                                    for import_name, distributions in installed_libraries.items()
                                    for distribution in distributions
                                ],
                            },
                        ).to_html(index=False, border=0),
                    ),
                ],
            },
        ).to_html(index=False, escape=False)

    def get_tree(self) -> Tree:
        """Get current project files tree.

        Returns:
            Tree of current project ignoring files from gitignore.
        """
        tree = Tree()
        root = tree.create_node(self._project.name, self._project.name)
        for path in self._project.files:
            last_parent = root
            path_parts = path.parts
            for slice_size in range(1, len(path_parts) + 1):
                path_slice = '/'.join(path_parts[:slice_size])
                current_node = tree.get_node(path_slice)
                if not current_node:
                    current_node = tree.create_node(path_parts[slice_size - 1], path_slice, parent=last_parent)
                last_parent = current_node
        return tree

    def write(self, path: Path = Path(Files.README)) -> None:
        """Write readme content to file.

        Args:
            path: desired path to readme.
        """
        with open(path, 'w') as file:
            file.write(self.text)

    @classmethod
    def determine(cls, project: 'ProjectParser') -> 'ReadmeHandler':
        """Determine current project type and get readme handler.

        Args:
            project: project handler.

        Returns:
            Suitable readme handler for current project type.

        Raises:
            NotImplementedError: if project type is not defined.
        """
        from .library import LibraryReadmeHandler

        toml_path = Path.cwd() / Files.TOML
        if toml_path.exists():
            with open(toml_path, 'rb') as f:
                toml_data = tomllib.load(f)
            if 'project' in toml_data:
                return LibraryReadmeHandler(project)
        raise NotImplementedError('This type of project if not yet implemented')
