# fulldoc

`fulldoc` is a Python docstring content checker focused on completeness and consistency.

It validates that docstrings are not only present, but also contain the required structured content for your public and internal API.

## What it checks

`fulldoc` enforces:

- full argument documentation for all callable parameters, even when no `Args` / `Attributes` section is present
- `Attributes` section validation for classes and data containers
- docstrings for private and protected entities, so internal APIs are documented for other developers

## Supported docstring styles

- `Google`
- `reStructuredText`

## What makes `fulldoc` different

Most docstring tools only check whether a docstring exists.

`fulldoc` checks whether the docstring is actually complete.

That includes:

- required parameter descriptions
- attribute documentation
- internal API documentation
- consistent parsing of common docstring formats

## Requirements

`fulldoc` is designed for Python projects that want stricter documentation standards.

It is especially useful when you want to enforce documentation for:

- public functions and classes
- protected members
- private members
- dataclasses and other attribute-heavy classes
- library code maintained by multiple developers

## Status codes

`fulldoc` reports findings using status codes.

### Main status groups

- `D` — docstring structure or content issue
- `DOC` — missing, incomplete, or invalid documentation
- `N` — naming or entity-related issue
- `F` — parser or formatting support code used for internal parsing only

### Example meanings

| Code     | Meaning                                           |
|----------|---------------------------------------------------|
| `D...`   | documentation rule violation                      |
| `DOC...` | docstring content problem                         |
| `N...`   | naming or entity classification issue             |
| `F...`   | parsing helper / internal formatting-related code |

> Exact code meanings depend on the rule set configured in your project.

## Installation

```bash
pip install fulldoc
```

## Usage

Run `fulldoc` against your project source tree from the root directory:

```bash
fulldoc
```

Or integrate it into your CI pipeline:

```yml
- name: Check docstrings
  run: fulldoc
```

Or you can help debug library errors running it from python file:

```python
from fulldoc import ProjectParser

ProjectParser().check()
```

## Rules enforced by `fulldoc`

### Arguments

All callable arguments must be documented.

This includes cases where:

- the docstring has no `Args` / `Attributes` section
- the section exists but is incomplete
- some parameters are documented and others are missing

### Attributes

Class attributes are checked against the docstring `Attributes` section.

`fulldoc` can detect missing documentation for class state and related fields.

### Private and protected members

`fulldoc` can require docstrings for internal APIs such as:

- protected members like `_name`
- private members like `__name`

This helps teams keep internal code understandable and maintainable.

## Examples

### Google style

```python
def add_user(name: str, age: int) -> None:
    """Add a user.

    Args:
        name: User name.
        age: User age.
    """
```

### reStructuredText style

```python
def add_user(name: str, age: int) -> None:
    """Add a user.

    :param name: User name.
    :param age: User age.
    """
```

## Notes

- `fulldoc` is strict by design.
- It is intended for teams that want documentation quality checks, not just docstring presence checks.
- Internal and protected code can be included in the documentation policy.

## License

MIT
