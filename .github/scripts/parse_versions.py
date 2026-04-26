#!/usr/bin/env python3
"""Script for parsing library info from pyproject.toml."""

import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PyVersion:
    """Class for python version data storing.

    Attributes:
        major: major python version.
        minor: minor python version.
    """

    major: int
    minor: int


class TomlParser:
    """Class for toml file handling."""

    def __init__(self, path: str) -> None:
        """Load toml from current directory.

        Args:
            path: path to toml file.
        """
        pyproject_path = Path(path)
        if not pyproject_path.exists():
            sys.exit(1)
        with Path(pyproject_path).open("rb") as f:
            self.data = tomllib.load(f)
        self.parse_library_version()
        self.parse_python_versions()

    def parse_library_version(self) -> None:
        """Get library version (PEP 621 / Poetry).

        Raises:
            KeyError: if version is not present in pyproject.toml.
        """
        data = self.data
        if "project" in data and "version" in data["project"]:
            self.library_version: str = data["project"]["version"]
            return
        if "tool" in data and "poetry" in data["tool"] and "version" in data["tool"]["poetry"]:
            self.library_version = data["tool"]["poetry"]["version"]
            return
        raise KeyError("Version not found in pyproject.toml")

    def parse_python_versions(self) -> None:
        """Parse requires-python param from toml file.

        Raises:
            KeyError: if python version is not present in pyproject.toml.
            ValueError: if wrong values were parsed from toml file.
        """
        data = self.data
        requires: str | None = None
        if "project" in data and "requires-python" in data["project"]:
            requires = data["project"]["requires-python"]
        elif "tool" in data and "poetry" in data["tool"]:
            poetry = data["tool"]["poetry"]
            if "dependencies" in poetry and "python" in poetry["dependencies"]:
                requires = poetry["dependencies"]["python"]
        if not requires:
            raise KeyError(
                "Python version not specified neither in the requires-python block, "
                "nor in the tool.poetry.dependencies.python block",
            )
        requires = re.sub(r"\s+", "", requires)
        pattern = r"(?:>=|~=)(?P<major_min>\d+)\.(?P<minor_min>\d+)(?:,<=?(?P<major_max>\d+)\.(?P<minor_max>\d+))?"
        match = re.fullmatch(pattern, requires)
        if not match:
            raise ValueError(f"Specified python version doesn't correspond to regular expression: {pattern}")
        major_min: str | None = match.group("major_min")
        minor_min: str | None = match.group("minor_min")
        major_max: str | None = match.group("major_max")
        minor_max: str | None = match.group("minor_max")
        if not major_min or not minor_min:
            raise ValueError("Min python version not specified")
        min_version = PyVersion(int(major_min), int(minor_min))
        max_version = PyVersion(int(major_max), int(minor_max)) if major_max and minor_max else None
        if not max_version:
            max_version = min_version
        if min_version.major != max_version.major:
            raise ValueError("Current python version parsing script doesn't work with multiple major python versions")
        self.python_versions = [f"{min_version.major}.{i}" for i in range(min_version.minor, max_version.minor + 1)]

    @property
    def is_prerelease(self) -> bool:
        """Check if library version has test version markers (a, b, rc, dev).

        Returns:
            True if current library version if prerelease.
        """
        return bool(re.search(r"(a|b|rc|dev)", self.library_version))


def main() -> None:
    """Parse toml and validate values."""
    toml_parser = TomlParser("pyproject.toml")
    branch = os.environ.get("GITHUB_REF_NAME", "")
    prerelease = toml_parser.is_prerelease
    if branch == "main":
        if prerelease:
            sys.exit(1)
        else:
            build_enabled = "true"
    else:
        if prerelease:
            build_enabled = "true"
        else:
            build_enabled = "false"
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with Path(github_output).open("a") as f:
            f.write(f"library-version={toml_parser.library_version}\n")
            f.write(f"python-versions={json.dumps(toml_parser.python_versions)}\n")
            f.write(f"build-enabled={build_enabled}\n")


if __name__ == "__main__":
    main()
