"""Readme handling."""

import re
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from dominate.tags import a, br, code, pre  # type: ignore[import-untyped]
from pandas import DataFrame

from .config import Files

if TYPE_CHECKING:
    from .project import ProjectParser


@dataclass
class ReadmeHandler:
    """Readme handler.

    Attributes:
        _project: current project handler.
    """

    _project: 'ProjectParser'

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
        readme_content['Tree'] = str(pre(item for file in str(self._project.tree).split('\n') for item in [file, br()]))
        readme_content['Libraries'] = self.libraries_table
        readme_content['Files'] = '\n'.join([module.name for module in self._project.modules])
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

    @cached_property
    def libraries_table(self) -> str:
        """Get project libraries table markdown representation."""
        builtin_libraries, installed_libraries = self._project.libraries
        return (
            DataFrame(
                data={
                    'Built in': [
                        '\n\n' + DataFrame(data={'Name': builtin_libraries}).to_markdown(index=False) + '\n\n',
                    ],
                    'Installed': [
                        '\n\n'
                        + DataFrame(
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
                        ).to_markdown(index=False)
                        + '\n\n',
                    ],
                },
            )
            .to_html(index=False)
            .replace('\\n', '\n')
        )

    def write(self, path: Path = Path(Files.README)) -> None:
        """Write readme content to file.

        Args:
            path: desired path to readme.
        """
        with open(path, 'w') as file:
            file.write(self.text)
