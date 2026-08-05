# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
