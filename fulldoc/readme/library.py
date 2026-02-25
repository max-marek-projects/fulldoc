"""Process library readme."""

import shutil
from pathlib import Path
from typing import final

from ..config import Files
from .basic import ReadmeHandler


@final
class LibraryReadmeHandler(ReadmeHandler):
    """Readme handler for python-library."""

    def get_readme_content(self) -> dict[str, str]:
        """Get content for readme file with.

        Returns:
            dict with keys - sections title, values - sections content.
        """
        return {}

    def write(self, path: Path = Path(Files.README)) -> None:
        """Write readme content to file.

        Args:
            path: desired path to readme.
        """
        super().write(path)
        default_read_the_docs_yml_path = Path.cwd() / Files.READ_THE_DOCS_YML
        if not default_read_the_docs_yml_path.exists():
            shutil.copy(
                Path(__file__).parent / 'library_data' / Files.READ_THE_DOCS_YML,
                default_read_the_docs_yml_path,
            )
