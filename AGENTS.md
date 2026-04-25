# LLM Assistant Guide for `exchange-calendars` package
This file provides context for LLM assistants (Claude Code and similar tools) working in this repository.

In all context files, a '@' prefixing a path indicates that the path is defined relative to the project root in which this `AGENTS.md` file is located.

## Skills

Identify all available skills in the @.agents\skills directory

## LLM context

Add the 'agents' label to any PR that amends:
- this @AGENT.md
- any SKILL.md file

## Project Overview

**exchange_calendars** is a Python package offering calendars for various securities exchanges. Each calendar provides information including:
- trading minutes (minutes when the exchange is open)
- trading sessions, and for each session the time of:
  - session open
  - session break start (is applicable)
  - session break end (is applicable)
  - session close
- holidays

NOTE: the package is a fork of the now unmaintained repo `trading_calendars` by quantoptian.

See @pyproject.toml for project metadata and dependencies.

### Repository Layout

```
TODO
```

## Technology Stack

| Category | Tools |
|---|---|
| Python | 3.10–3.14 (`.python-version` pins 3.10) |
| Package manager | `uv` |
| Build backend | `setuptools` + `setuptools_scm` |
| Testing | `pytest` |
| Linting/formatting | `ruff` |
| Type checking | `mypy` |
| Git hooks | `pre-commit` |
| Data Manipulation | `pandas`, `numpy` |

The current project version is managed by `setuptools_scm` and written to `src/exchange_calendars/_version.py`.
IMPORTANT: `src/exchange_calendars/_version.py` is auto-generated and you should not edit it.

## Development Workflows

### Setup

```bash
# Install dependencies using uv
uv sync

# Install pre-commit hooks
pre-commit install
```

### Testing

Each calendar has a dedicated test file containing a dedicated test suite defined on a subclass of the common base class `ExchangeCalendarTestBase` (in @tests\test_exchange_calendar.py).
- tests are in @tests/
- doctests are included to some methods/functions
- test with `pytest`
- see @pytest.ini for configuration; options are applied automatically via `addopts`.
- shared fixtures are in @tests/conftest.py

Commands to run tests:
```bash
# All tests (including doctests under src/exchange_calendars/)
pytest

# Tests in specific file
pytest tests/test_module.py

# Specific test
pytest tests/test_module.py::test_name

# With verbose output
pytest -v
```

### Pre-commit Hooks

See @.pre-commit-config.yaml for pre-commit implementation.

Pre-commit runs automatically on `git commit`.

To run manually:
```bash
pre-commit run --all-files
```

---

### Continuous Integration

GitHub Actions is used for CI. Defined workflows include:
- @.github/workflows/main.yml - runs full test suite on matrix of platforms and python versions.
- @.github/workflows/release.yml - releases a new version to PyPI.

## Code Conventions

### Architecture

Each calendar is defined as a subclass of the common base class `ExchangeCalendar` in @exchange_calendars.exchange_calendar.py.

### Formatting

- format to `ruff` (Black compatible).
- see @ruff.toml for configuration.

```bash
# Format code
ruff format .
```

### Linting

- lint with `ruff`.
- See lint sections of @ruff.toml for configuration (includes excluded files).
- type check with `mypy`.

```bash
# Check lint issues
ruff check .

# Type checking
uv run mypy src/exchange_calendars/
```

### Imports

- No wildcard imports (i.e. no `from x import *`).

### Type Annotations

- Type annotations are required on all public functions and methods.

### Docstrings

Public modules, classes, and functions MUST all have docstrings.

Docstrings should follow **NumPy convention**. Familiarise yourself with this as described at https://numpydoc.readthedocs.io/en/latest/format.html. That said, the following should always be adhered to and allowed to override any NumPy convention:
- 75 character line limit for public documentation
- 88 character line limit for private documentation
- formatted to ruff
- parameter types should not be included to the docstring unless this provides useful information that users could not otherwise ascertain from the typed function signature.
- default values should only be noted in function/module docstrings if not defined in the signature - for example if the parameter's default value is None and when received as None the default takes a concrete dynamically evaluated default value. When a default value is included to the parameter documentation it should be defined after a comma at the end of the parameter description, for example:
    - description of parameter 'whatever', defaults to 0.
- **subclasses** documentation should:
    - list only methods and attributes added by the subclass. A note should be included referring users to documentation of base classes for the methods and attributes defined there.
    - include a NOTES section documenting how to implement the subclass (only if not trivial).
- documentation of **subclass methods that extend methods of a base class** should only include any parameters added by the extension. With respect to undocumented parameters a note should be included to refer the user to the corresponding 'super' method(s)' documentation on the corresponding base class or classes.
- **documentation of exceptions and warnings** should be limited to only **unusual** exceptions and warnings that are raised directly by the function/method itself or by any private function/method that is called directly or indirectly by the function/method.
- summary line should be in the imperative mood only when sensical to do so.
- magic methods do not require documentation if their functionality is fully implied by the method name.
- unit tests do not require docstrings.

Example documentation:
```python
def my_func(param1: int, param2: str = "default", param3: None | str = None) -> bool:
    """Short summary line.

    Extended description if needed.

    Parameters
    ----------
    param1
        Description of param1.
    param2
        Description of param2.
    param3
        Description of param3, defaults to value of `param2`.

    Returns
    -------
    bool
        Description of return value.
    """
```

### Comments

- pay particular attention to comments starting with:
    - 'NOTE'
    - 'TODO'
    - 'AIDEV-NOTE' - these comments are specifically addressed to you.
    - 'AIDEV-TODO' - these comments are specifically requesting you do something.
    - 'AIDEV-QUESTION' - these comments are asking a question for specifically you to answer.

---

## Important Notes for AI Agents

1. **NEVER DO RULES**:
	- Never edit the file `src/exchange_calendars/_version.py` - this is auto-generated by the build process.

2. **NumPy docstring style** — all new public functions/classes must use NumPy-convention docstrings and rules as defined under Docstrings section of this @AGENTS.md file.

3. **Branch naming** — git branches should follow the pattern `<llm_name>/<description>` where the `<llm_name>` placeholder should be replaced with your colloquial name.
