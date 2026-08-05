# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-05

### Added
- **OS-Specific Configuration Directory**: Memory storage (`memory.json`) relocated to user configuration directories (`%APPDATA%`, `~/.config`, `~/Library/Application Support`) with zero-data-loss legacy migration.
- **Config Commands (`repo config`)**: System configuration inspection, `--open` (editor), and `--folder` (explorer).
- **Location Manager (`repo locations`)**: Interactive arrow-key menus, subcommands `add`, `remove`, `rename`, and `verify` with missing path cleanup.
- **Repository Manager (`repo repos`)**: Subcommands `add`, `remove`, `search <query>` (fuzzy matching), `verify` (git reachability checks), and detailed repo inspector.
- **Memory Manager (`repo memory`)**: Memory storage metrics, timestamped `backup`, and interactive `restore`.
- **Workspace Aliases (`repo alias`)**: Named path shortcuts (`repo alias add <name> <path>`), prioritized at top of destination selection menu during clone.
- **System Doctor (`repo doctor`)**: Automated system diagnostic health suite verifying Git, Python, network, GitHub, storage, and permissions.
- **PyPI Update Checker (`repo update`)**: Non-intrusive PyPI version query displaying current version vs latest PyPI release.
- **Command Palette Expansion**: All 12 commands & subcommands integrated into the VS Code-style Command Palette with live fuzzy filtering.
- **Comprehensive Test Suite**: Unit tests expanded to 24 tests across configuration, locations, repositories, memory, aliases, and doctor.

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
