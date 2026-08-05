# Contributing to Repo_Clone_System

Thank you for considering contributing to `Repo_Clone_System`!

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/Mr-Anonymous-Guy/Repo_Cone_System.git
   cd Repo_Cone_System
   ```

2. Create a virtual environment and install in editable mode with development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -e ".[dev]"
   ```

3. Run tests:
   ```bash
   pytest
   ```

## Code Quality & Formatting

We use `black` for formatting and `ruff` for linting.

```bash
black --check .
ruff check .
```

## Pull Request Guidelines

- Ensure unit tests pass (`pytest`).
- Keep code clean and follow existing modular architecture (`src/repo_clone_system/`).
- Update documentation when adding or modifying features.
