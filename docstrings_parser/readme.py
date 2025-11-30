"""Readme handling."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from dominate.tags import a, br, code, pre  # type: ignore[import-untyped]

from .config import Files

if TYPE_CHECKING:
    from .project import ProjectParser


@dataclass
class ReadmeHandler:
    """Readme handler."""

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
        return readme_text

    def write(self, path: Path = Path(Files.README)) -> None:
        """Write readme content to file.

        Args:
            path: desired path to readme.
        """
        with open(path, 'w') as file:
            file.write(self.text)
