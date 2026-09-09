# Contributing to markpublish

Thank you for your interest in improving **markpublish**!

---

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/fwdotcom/markpublish.git
   cd markpublish
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install the package in editable mode with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

---

## Running Tests & Quality Checks

- **Run all automated tests:**
  ```bash
  pytest
  ```

- **Run tests with code coverage report:**
  ```bash
  pytest --cov=markpublish
  ```

- **Run the code linter:**
  ```bash
  ruff check src tests build_manuals.py
  ```

---

## Building Documentation

To compile the user guides and quick references into `manual/`, in every language the
package ships:
```bash
python build_manuals.py
```
These PDFs are committed and carry the version from their `markpublish.yaml`, so a version
bump is only finished once they are rebuilt. `pytest` fails until then.

To render the quick reference sheet locally:
```bash
markpublish cheatsheet --target all
```

---

## Pull Request Guidelines

1. Ensure all tests pass (`pytest`) and the linter reports zero warnings (`ruff check`).
2. Add automated regression tests for any new features or bug fixes.
3. Keep documentation (`README.md`, `src/markpublish/docs/manual/{de,en}`, `src/markpublish/docs/cheatsheet/{de,en}`) in sync.

