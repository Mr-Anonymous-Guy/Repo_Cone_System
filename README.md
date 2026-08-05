# 🚀 Repo_Clone_System

> *Because typing the same clone location over and over again is a crime against productivity.*

[![PyPI Version](https://img.shields.io/pypi/v/repo-clone-system.svg)](https://pypi.org/project/repo-clone-system/)
[![Python Versions](https://img.shields.io/pypi/pyversions/repo-clone-system.svg)](https://pypi.org/project/repo-clone-system/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI Tests](https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/actions/workflows/tests.yml/badge.svg)](https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/actions)
[![Downloads](https://pepy.tech/badge/repo-clone-system)](https://pepy.tech/project/repo-clone-system)

`Repo_Clone_System` is a professional, open-source Python CLI application designed to clone GitHub repositories while maintaining a smart memory of your workspace aliases, destination folders, and repository history. Launch `repo` from anywhere in your terminal!

---

## 📽️ Interactive Terminal Preview

```text
╭──────────────────────────────────────────────────────────────╮
│ Repo_Clone_System v2.0.0                                     │
│ Type "help" to list commands or enter a GitHub URL.          │
│ Press Ctrl+C anytime to exit safely.                         │
╰──────────────────────────────────────────────────────────────╯

>
```

*Shell-first Git-style hybrid CLI with prompt history, tab completion, direct GitHub URL auto-dispatch, and contextual sub-menus.*

---

## ✨ Features

- 💼 **Workspace Management Subsystem (`repo workspace`)**: Complete workspace isolation (`Default`, `College`, `Office`, `Laptop`, `Personal`, custom) with independent repositories, locations, aliases, settings, and statistics.
- 💼 **Multi-Profile Workspace Management**: Switch profiles instantly (`repo workspace switch <name>`) with zero-restart hot-reloading.
- 🔄 **Sync Manager & Directory Synchronization**: Configure default sync directories (`repo workspace sync config <path>`) supporting local folders, mapped drives, OneDrive, Dropbox, Google Drive, and custom directories.
- 🔄 **Incremental Exit Backups & 20-Backup Rotation**: Automatically captures incremental backups on CLI exit if workspace changes are detected, keeping the 20 newest auto-backups while preserving manual exports indefinitely.
- 💻 **Global Terminal Executable (`repo`)**: Run `repo` from any directory in your shell.
- ⚡ **CLI Subcommands**: Execute direct actions like `repo workspace`, `repo clone`, `repo repos`, `repo locations`, `repo alias`, `repo export`, `repo import`, `repo backups`, `repo config`, `repo doctor`, `repo memory`, `repo stats`, `repo update`.
- 🎨 **VS Code–Style Command Palette**: Interactive palette with real-time prefix filtering and arrow key selection.
- 📤 **Portable Export / Import**: Easily transfer complete workspace configuration between computers (`repo export` / `repo import`).
- 🔀 **Smart Merge & Replace Import Modes**:
  - **Merge**: Combines backup data with live memory, deduplicating repositories and locations.
  - **Replace**: Overwrites live memory state after creating an automatic timestamped pre-import safety backup.
- 📁 **Managed Backup Directory (`repo backups`)**: Dedicated `Backups/` folder inside configuration directory storing interactive and automatic safety backups.
- 🏷️ **Workspace Aliases**: Assign shortcut names (`work`, `learn`, `github`) to frequently used directories for one-click cloning.
- 📁 **Smart Location Manager**: Add, remove, rename, and verify saved clone destinations with automated missing folder cleanup.
- 📦 **Repository Manager & Search**: Track repository history with clone timestamps, fuzzy search (`repo repos search react`), and git reachability verification.
- 🩺 **System Doctor (`repo doctor`)**: Diagnostic health suite checking Git, Python, internet connection, GitHub reachability, and memory permissions.
- ⚙️ **Config Inspection**: Inspect OS paths (`repo config`), open `memory.json` in default editor (`--open`), or view the config directory in file explorer (`--folder`).
- 🚪 **Safe Exit & Interruption Handling**: Gracefully handles Ctrl+C and Ctrl+D/Ctrl+Z without showing tracebacks.

---

## 📦 Storage & Backup Locations

Memory (`memory.json`), profiles, and managed backups are stored in your operating system's standard user configuration directory:

| OS | Memory Path | Backups Directory |
|---|---|---|
| **Windows** | `%APPDATA%\RepoCloneSystem\memory.json` | `%APPDATA%\RepoCloneSystem\Backups\` |
| **macOS** | `~/Library/Application Support/RepoCloneSystem/memory.json` | `~/Library/Application Support/RepoCloneSystem/Backups/` |
| **Linux** | `~/.config/repo-clone-system/memory.json` | `~/.config/repo-clone-system/Backups/` |

---

## 📦 Installation

### Production Installation (PyPI)

Install the official package via `pip`:

```bash
pip install repo-clone-system
```

Launch the CLI from **any terminal**:

```bash
repo
```

---

## 💼 Workspace Management Subsystem (`repo workspace`)

The Workspace Management Subsystem provides centralized control over backups, profiles, synchronization, system info, and cloud sync providers.

```bash
# Launch interactive Workspace Manager
repo workspace

# Direct Workspace Management Subcommands
repo workspace create <workspace_name>
repo workspace switch <workspace_name>
repo workspace rename <old_name> <new_name>
repo workspace remove <workspace_name>
repo workspace export [destination_folder_or_file]
repo workspace import [backup_file_path]

# Multi-Profile Management (Default, College, Office, Laptop, Personal, Custom)
repo workspace profile list
repo workspace profile switch <profile_name>
repo workspace profile create <profile_name>
repo workspace profile rename <old_name> <new_name>
repo workspace profile remove <profile_name>

# Sync Manager & Directory Synchronization
repo workspace sync config <sync_folder_path>
repo workspace sync export
repo workspace sync import
repo workspace sync status

# Backup Manager & Auto-Backup Rotation
repo workspace backup create
repo workspace backup restore
repo workspace backup list
repo workspace backup remove
repo workspace backup history

# Workspace Information & System Metrics
repo workspace info
```

---

## 📤 Export & Import Usage

### Export Configuration

Export your complete setup to a portable JSON backup file:

```bash
# Export to current directory with timestamped filename (e.g. workspace-backup-2026-08-05-18-42-10.json)
repo export

# Export to a custom backup directory (prompts to create folder if missing)
repo export D:\Backups

# Export to a specific file path
repo export "D:\Backups\my-setup-backup.json"

# View export history log
repo export history
```

### Import Configuration

Import a configuration backup file interactively:

```bash
# Interactive mode (prompts for backup file path)
repo import

# Import specific backup file
repo import backup.json
repo import D:\Backups\my-setup-backup.json
```

**Import Modes**:
- **Merge**: Combines repositories, locations, and aliases without creating duplicates.
- **Replace**: Creates an automatic safety backup (`auto-backup-before-import-*.json`), then overwrites live memory.

### Manage Backups

Browse and manage backups stored in the system `Backups/` folder:

```bash
# Interactive backup browser (inspect backup details, version, schema)
repo backups

# Interactively select and remove a backup file
repo backups remove

# Display export history
repo backups history
```

---

## ▶️ Command Reference

| Command | Subcommands / Flags | Description | Example |
|---|---|---|---|
| `repo` | — | Opens interactive Command Palette | `repo` |
| `repo workspace` | `create`, `switch`, `rename`, `remove`, `export`, `import`, `backup`, `sync`, `info` | Workspace Management Subsystem | `repo workspace info` |
| `repo clone` | — | Starts repository clone workflow | `repo clone` |
| `repo export` | `[path]`, `history` | Export complete configuration to JSON | `repo export D:\Backups` |
| `repo import` | `[path]` | Import backup file (Merge or Replace) | `repo import backup.json` |
| `repo backups` | `remove`, `history` | Browse managed backups & export history | `repo backups` |
| `repo repos` | `add`, `remove`, `search <q>`, `verify` | Manage saved repositories & check reachability | `repo repos search react` |
| `repo locations` | `add`, `remove`, `rename`, `verify` | Manage destination folders & cleanup missing | `repo locations verify` |
| `repo alias` | `add <name> <path>`, `remove`, `rename` | Manage workspace shortcut aliases | `repo alias add work D:\Projects` |
| `repo memory` | `backup`, `restore` | Storage metrics, backup creation & restore | `repo memory backup` |
| `repo config` | `--open`, `--folder` | Inspect system paths, open editor or explorer | `repo config --open` |
| `repo doctor` | — | Run system health diagnostic checks | `repo doctor` |
| `repo stats` | — | Display memory statistics | `repo stats` |
| `repo update` | — | Query PyPI for version updates | `repo update` |
| `repo help` | — | Display command reference | `repo help` |
| `repo clear` | — | Reset memory history | `repo clear` |
| `repo exit` | — | Gracefully exit | `repo exit` |

---

## 📐 Repository Structure

```text
Repo_Clone_System/
│
├── .github/                      # GitHub workflows, templates, and dependabot
│   ├── ISSUE_TEMPLATE/
│   ├── DISCUSSION_TEMPLATE/
│   └── workflows/
│
├── docs/                         # Developer & API documentation
│   └── index.md
│
├── scripts/                      # Developer automation & pre-push scripts
│   ├── dev.py
│   ├── install_hooks.py
│   └── pre_push.py
│
├── src/
│   └── repo_clone_system/        # Core package code
│       ├── core/                 # Git execution & path validation
│       ├── services/             # Workspace, Profile, Sync, Backup, Config, Location, Repo, Alias, Doctor services
│       │   └── sync_providers/   # LocalFolder & Cloud Sync Providers architecture
│       ├── storage/              # OS-dependent config path & profile-aware memory binding
│       └── ui/                   # Workspace UI menus, Command Palette & terminal interaction
│
├── tests/                        # Pytest unit test suite (43 tests)
├── app.py                        # Dev launcher
├── pyproject.toml                # PEP 621 packaging metadata
└── README.md                     # Package documentation
```

---

## 🗺️ Roadmap

- [x] Modern `src/` layout & PyPI distribution packaging (`v0.1.0`)
- [x] VS Code-style Command Palette with live prefix filtering
- [x] CLI Subcommands (`repo clone`, `repo repos`, `repo stats`, etc.)
- [x] Global interruption handling (Ctrl+C / Ctrl+D)
- [x] Workspace Management Subsystem & Multi-Profile Workspaces (`v0.2.0`)
- [x] Workspace Sync Manager & Pluggable Provider Architecture (`v0.2.0`)
- [x] Automatic Exit Incremental Backups & 20-Backup Rotation (`v0.2.0`)
- [x] Workspace Aliases & Location Manager (`v0.2.0`)
- [x] Portable Import / Export Backup System (`v0.2.0`)
- [x] System Doctor & Diagnostic Suite (`v0.2.0`)
- [x] Repository Fuzzy Search & Reachability Verification (`v0.2.0`)
- [ ] SSH & Private Repository authentication helper
- [ ] GitHub CLI (`gh`) integration for automatic fork-and-clone

---

## 🚀 Automated Publishing

Releases are published to [PyPI](https://pypi.org/project/repo-clone-system/) automatically via **PyPI Trusted Publishing (OIDC)**.

- **No API Keys or Secrets Required**: Authentication uses short-lived OpenID Connect (OIDC) JWT tokens.
- **Automatic Releases**: Publishing triggers automatically whenever a new GitHub Release is published.

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.

```bash
git clone https://github.com/Mr-Anonymous-Guy/Repo_Cone_System.git
cd Repo_Cone_System
pip install -e ".[dev]"
python scripts/dev.py
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).
