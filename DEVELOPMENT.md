# Development

This document describes how to set up a local development environment
for markpublish, e.g. for your own fork.

---

## Development Setup

1. **Clone the repository:**

   ```
   git clone https://github.com/fwdotcom/markpublish.git
   cd markpublish
   ```

2. **Create and activate a virtual environment:**

   ```
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install the package in editable mode with development dependencies:**

   ```
   pip install -e ".[dev]"
   ```

---

## Running Tests & Quality Checks

- **Run all automated tests:**

  ```
  pytest
  ```

- **Run tests with code coverage report:**

  ```
  pytest --cov=markpublish
  ```

- **Run the code linter:**

  ```
  ruff check src tests scripts
  ```

---

## Building Documentation

To compile the user guides and quick references into `manual/`, in every
language the package ships:

```
python scripts/build_manuals.py
```

These PDFs are committed and carry the version from their `markpublish.yaml`,
so a version bump is only finished once they are rebuilt. `pytest` fails
until then.

To render the quick reference sheet locally:

```
markpublish cheatsheet --target all
```

---

## Conventions

1. All tests pass (`pytest`) and the linter reports zero warnings (`ruff check`).
2. New features and bug fixes come with automated regression tests.
3. Documentation (`README.md`, `src/markpublish/docs/manual/{de,en}`,
   `src/markpublish/docs/cheatsheet/{de,en}`) is kept in sync.
