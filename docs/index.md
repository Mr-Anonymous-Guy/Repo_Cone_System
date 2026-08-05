# Repo_Clone_System Documentation (v2.0.0)

Welcome to the official developer documentation for `Repo_Clone_System`.

## Architecture Overview

`Repo_Clone_System` follows a clean modular layout (`src/` layout):

- **`src/repo_clone_system/core/`**: Core logic for Git execution, path validation, and global interruption handling.
- **`src/repo_clone_system/services/`**: Business logic services:
  - `backup_service.py`: Import / Export system, backup directory management, schema versioning, export history, and auto-backups.
  - `config_service.py`: OS config inspection, opening memory file/folder.
  - `location_service.py`: Location manager, path validation, missing folder cleanup.
  - `repo_service.py`: Repository tracking, fuzzy search, reachability check.
  - `alias_service.py`: Workspace shortcut aliases (`repo alias`).
  - `memory_service.py`: Storage metrics, backup, interactive restore.
  - `doctor_service.py`: System diagnostic health suite (`repo doctor`).
  - `update_service.py`: PyPI update checker.
- **`src/repo_clone_system/storage/`**: OS-dependent state management & JSON memory persistence (`memory.json`).
- **`src/repo_clone_system/ui/`**: Interactive Command Palette, prompt handlers, and formatted console banners.
- **`tests/`**: Unit test suite powered by Pytest (36 tests).

## Available Subcommands

Run `repo <subcommand>` directly or execute `repo` to open the interactive Command Palette.

- `repo clone`: Launches repository URL input and destination picker.
- `repo export`: Export configuration backup (`repo export [path]`, `repo export history`).
- `repo import`: Import configuration backup (`repo import [path]`) with Merge vs Replace choices.
- `repo backups`: Managed backups & export history (`repo backups remove`, `repo backups history`).
- `repo repos`: Repository manager (`add`, `remove`, `search <q>`, `verify`).
- `repo locations`: Location manager (`add`, `remove`, `rename`, `verify`).
- `repo alias`: Workspace alias manager (`add <name> <path>`, `remove`, `rename`).
- `repo memory`: Memory storage manager (`backup`, `restore`).
- `repo config`: Configuration details (`--open` editor, `--folder` explorer).
- `repo doctor`: System health diagnostic suite.
- `repo stats`: Displays repository and location count metrics.
- `repo update`: Queries PyPI for version updates.
- `repo help`: Prints the command list.
- `repo clear`: Erases saved memory history.
- `repo exit`: Exits the application.

## Storage & Backup Locations

- **Windows**:
  - Memory: `%APPDATA%\RepoCloneSystem\memory.json`
  - Backups: `%APPDATA%\RepoCloneSystem\Backups\`
- **macOS**:
  - Memory: `~/Library/Application Support/RepoCloneSystem/memory.json`
  - Backups: `~/Library/Application Support/RepoCloneSystem/Backups/`
- **Linux**:
  - Memory: `~/.config/repo-clone-system/memory.json`
  - Backups: `~/.config/repo-clone-system/Backups/`

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

## Release & Publishing

Package releases are published to PyPI automatically via **PyPI Trusted Publishing (OIDC)**:

- Uses short-lived OpenID Connect (OIDC) identity tokens.
- No long-lived `PYPI_API_TOKEN` API keys, usernames, or passwords stored in GitHub Secrets.
- Publishing triggers automatically whenever a new GitHub Release is created.
