# Repo_Clone_System Documentation

Welcome to the official developer documentation for `Repo_Clone_System`.

## Architecture Overview

`Repo_Clone_System` follows a clean modular layout (`src/` layout):

- **`src/repo_clone_system/core/`**: Core logic for Git execution, path validation, and global interruption handling.
- **`src/repo_clone_system/storage/`**: State management & JSON memory persistence (`memory.json`).
- **`src/repo_clone_system/ui/`**: Interactive Command Palette, prompt handlers, and formatted console banners.
- **`tests/`**: Unit test suite powered by Pytest.

## Available Subcommands

Run `repo <subcommand>` directly or execute `repo` to open the interactive Command Palette.

- `repo clone`: Launches repository URL input and destination picker.
- `repo repos`: Lists all saved repositories in history.
- `repo locations`: Lists all saved destination folders.
- `repo stats`: Displays repository and location count metrics.
- `repo help`: Prints the command list.
- `repo update`: Shows current version and PyPI upgrade command.
- `repo clear`: Erases saved memory history.
- `repo exit`: Exits the application.

## Developer Quickstart

```bash
# Clone the repository
git clone https://github.com/Mr-Anonymous-Guy/Repo_Cone_System.git
cd Repo_Cone_System

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Run test suite
python -m pytest

# Execute developer script
python scripts/dev.py
```
