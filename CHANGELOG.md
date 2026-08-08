# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-08-08

### Added
- **Complete PyPI Package Metadata**: Extended `pyproject.toml` with PEP 621 compliant package metadata including concise project summary description, author details (`Mr. Anonymous`), license specification (`MIT`), PyPI keywords, classifiers, and project URLs (`Homepage`, `Repository`, `Issues`, `Documentation`, `Changelog`).
- **PyPI & Package Documentation**: Added `docs/PYPI_METADATA.md`, `docs/IMPLEMENTATION_VERIFICATION.md`, `docs/FEATURE_TRACEABILITY.md`, and updated `BUILD.md` checklist.

### Changed
- Standardized project version to `0.3.1` across package metadata (`pyproject.toml`), source code (`src/repo_clone_system/__init__.py`), terminal banner (`README.md`), and documentation (`docs/index.md`).
- Converted relative Markdown links in `README.md` (`LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`) to absolute GitHub repository URLs to guarantee correct PyPI package rendering.

## [0.3.0] - 2026-08-05

### Added
- **Git-Style Shell Interface**: Shell-first startup experience (`repo`) featuring a clean header banner, persistent prompt session, command history (`.repo_history`), and `WordCompleter` auto-completion.
- **Direct Git/GitHub URL Gate**: Typing any direct URL (`https://github.com/...`, `git@github.com:...`) auto-dispatches immediately to `clone_repository()` without requiring interactive navigation.
- **Sub-Menu Persistence Loops**: Parent domain commands (`workspace`, `repos`, `locations`, `alias`, `memory`, `export`, `import`, `backups`, `config`, `doctor`, `stats`, `help`, `clear`) loop interactively until `exit` or `0` is selected.
- **Categorized Command Reference**: `repo help` organized into 12 distinct domain categories with individual command help outputs (`repo help clone`, `repo help workspace`, etc.).
- **Dedicated Backup Directory Isolation**: All workspace exports automatically default to a isolated `workspace-backups/` directory, excluded from Git commits via `.gitignore`.
- **Exhaustive CLI Command Matrix Test Verification**: Verified 100% execution pass across all 74 documented commands in `Command.md` (0 exceptions / 0 tracebacks).

### Changed
- Standardized CLI startup to shell-first `>` prompt with clean Ctrl+C graceful exit (`Session terminated safely. Goodbye.`).
- Upgraded `__version__` to `3.0.0` across package metadata, `pyproject.toml`, documentation, and system diagnostics.

### Fixed
- Fixed module import in `cli.py` to resolve `get_config_dir` cleanly.
- Fixed dictionary mutation handling for memory clear commands (`repo clear repos`, `repo clear locations`, `repo clear recent`).

## [2.0.0] - 2026-08-05

### Added
- **Workspace Management Subsystem (`repo workspace`)**: Interactive Workspace Manager command palette and subcommand matrix (`export`, `import`, `backup`, `profile`, `sync`, `info`).
- **Multi-Profile Workspace Management (`repo workspace profile`)**: Support for `Default`, `College`, `Office`, `Laptop`, `Personal`, and custom workspace profiles with isolated memory stores and instant hot-reloading on profile switch.
- **Sync Manager & Provider Architecture (`repo workspace sync`)**: Abstract `BaseSyncProvider` framework with functional `LocalFolderSyncProvider` (local folders, OneDrive, Dropbox, Google Drive, network shares) and cloud provider placeholders (`OneDriveSyncProvider`, `DropboxSyncProvider`, `GoogleDriveSyncProvider`, `GitHubGistSyncProvider`, `CustomSyncProvider`).
- **Auto-Backup Exit Trigger & 20-Backup Rotation**: Automatically captures timestamped auto-backups on CLI exit if memory changes were detected, enforcing a 20-backup rotation for auto-backups while preserving manual exports indefinitely.
- **Workspace Information Metrics (`repo workspace info`)**: Workspace summary metrics displaying active profile, repository/location/alias counts, storage size, schema version, package version, system platform, and Python version.
- **Portable Import & Export (`repo export` / `repo import`)**: Complete configuration export with metadata (`schema_version`, timestamp, platform, Python version, memory).
- **Import Modes (Merge & Replace)**: `Merge` mode combines repositories, locations, and aliases without duplicates. `Replace` mode creates an automatic safety backup before replacing live memory.
- **Managed Backup Directory (`repo backups`)**: Dedicated `Backups/` directory inside OS config folder storing interactive and automatic pre-import safety backups (`auto-backup-before-import-*.json`).
- **Export History**: Tracks export history log viewable via `repo backups history` or `repo export history`.
- **Schema Versioning & Migration Engine**: Backward and forward-compatible schema versioning infrastructure preparing for future schema migrations.
- **OS-Specific Configuration Directory**: Memory storage (`memory.json`) relocated to user configuration directories (`%APPDATA%`, `~/.config`, `~/Library/Application Support`) with zero-data-loss legacy migration.
- **Config Commands (`repo config`)**: System configuration inspection, `--open` (editor), and `--folder` (explorer).
- **Location Manager (`repo locations`)**: Interactive arrow-key menus, subcommands `add`, `remove`, `rename`, and `verify` with missing path cleanup.
- **Repository Manager (`repo repos`)**: Subcommands `add`, `remove`, `search <query>` (fuzzy matching), `verify` (git reachability checks), and detailed repo inspector.
- **Memory Manager (`repo memory`)**: Memory storage metrics, timestamped `backup`, and interactive `restore`.
- **Workspace Aliases (`repo alias`)**: Named path shortcuts (`repo alias add <name> <path>`), prioritized at top of destination selection menu during clone.
- **System Doctor (`repo doctor`)**: Automated system diagnostic health suite verifying Git, Python, network, GitHub, storage, and permissions.
- **PyPI Update Checker (`repo update`)**: Non-intrusive PyPI version query displaying current version vs latest PyPI release.
- **Command Palette Expansion**: All commands & subcommands integrated into the VS Code-style Command Palette with live fuzzy filtering.
- **Comprehensive Test Suite**: Unit tests expanded to 43 tests across configuration, locations, repositories, memory, aliases, doctor, import/export, profiles, sync, and rotation.

### Changed
- Memory system redesigned around Workspaces and multi-profile isolation.
- Configuration and backup storage relocated to OS-compliant user configuration directories.
- Backup system upgraded to support 20-backup auto-rotation and manual backup preservation.
- Interactive Command Palette expanded to include all workspace management choices.

### Improved
- Complete documentation update across `README.md`, `CHANGELOG.md`, and `docs/index.md`.
- Expanded unit test coverage and pre-push validation engine assurances.
- Clean modular architecture following SOLID principles and PEP 8 guidelines.

### Fixed
- Various stability improvements, Unicode console stream encoding fallbacks, and profile list mutation safety.

## [0.1.0] - 2026-08-05

### Added
- **`src/` Layout Package Architecture**: Refactored CLI into standard `src/repo_clone_system` layout.
- **VS Code–Style Command Palette**: Interactive palette with real-time live search filtering.
- **Global Terminal CLI (`repo`)**: Installable executable via `pip install repo-clone-system`.
- **Subcommands Support**: Direct invocation via `repo clone`, `repo repos`, `repo locations`, `repo stats`, `repo help`, `repo clear`, `repo update`, `repo exit`.
- **Safe Interruption Handling**: Graceful handling of `KeyboardInterrupt` (Ctrl+C) and `EOFError` (Ctrl+D/Ctrl+Z).
- **Automated Memory Persistence**: History memory automatically stored in `data/memory.json`.
- **Unit Test Suite**: Pytest coverage across memory, utils, validators, and commands.
- **CI/CD Automation**: GitHub Actions workflows for automated testing and PyPI publishing.
