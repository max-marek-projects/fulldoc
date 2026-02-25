"""Process library readme."""

import shutil
from pathlib import Path
from typing import final

from ..config import Files
from .basic import ReadmeHandler


@final
class LibraryReadmeHandler(ReadmeHandler):
    """Readme handler for python-library."""

    def __post_init__(self) -> None:
        """Initialize python library readme handler."""
        super().__post_init__()
        self.logger.info('Project type - Python library')

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
        library_data_folder = Path(__file__).parent / 'library_data'
        for library_doc_file_path in library_data_folder.rglob('*'):
            if library_doc_file_path.is_dir() or '__pycache__' in library_doc_file_path.parts:
                continue
            library_doc_file_path = library_doc_file_path.relative_to(Path(__file__).parent / 'library_data')
            self.logger.debug(f'Checking if {library_doc_file_path} needs to be added to the project')
            default_library_doc_file_path = Path.cwd() / library_doc_file_path
            if not default_library_doc_file_path.exists():
                default_library_doc_file_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(
                    library_data_folder / library_doc_file_path,
                    default_library_doc_file_path,
                )
                self.logger.info(f'Added file {default_library_doc_file_path}')
            else:
                self.logger.debug(f'File {default_library_doc_file_path} already exists')
