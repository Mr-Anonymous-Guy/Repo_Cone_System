# 🚀 Repo_Clone_System

> *Because typing the same clone location over and over again is a crime against productivity.*

[![PyPI Version](https://img.shields.io/pypi/v/repo-clone-system.svg)](https://pypi.org/project/repo-clone-system/)
[![Python Versions](https://img.shields.io/pypi/pyversions/repo-clone-system.svg)](https://pypi.org/project/repo-clone-system/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI Tests](https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/actions/workflows/tests.yml/badge.svg)](https://github.com/Mr-Anonymous-Guy/Repo_Cone_System/actions)
[![Downloads](https://pepy.tech/badge/repo-clone-system)](https://pepy.tech/project/repo-clone-system)

`Repo_Clone_System` is a professional, open-source Python CLI application designed to clone GitHub repositories while maintaining a smart memory of your destination folders and repository history. Launch `repo` from anywhere in your terminal!

---

## 📽️ Interactive Terminal Preview

```text
╭──────────────────────────────────────────────────────────────╮
│ Repo_Clone_System v0.1.0                                     │
│ Press ↑ ↓ to navigate • Enter to select • Esc to cancel      │
╰──────────────────────────────────────────────────────────────╯

>
❯ Clone Repository
  Saved Repositories
  Saved Locations
  Statistics
  Help
  Clear History
  Exit
```

*Interactive VS Code-style Command Palette with real-time live filtering and arrow-key selection.*

---

## ✨ Features

- 💻 **Global Terminal Executable (`repo`)**: Run `repo` from any directory in your shell.
- ⚡ **CLI Subcommands**: Execute actions directly using `repo clone`, `repo repos`, `repo locations`, `repo stats`, `repo help`, `repo clear`, `repo update`, `repo exit`.
- 🎨 **VS Code–Style Command Palette**: Interactive palette with real-time prefix filtering and arrow key selection.
- 📂 **Automatic Destination Memory**: Instant reuse of your last used location or any previously saved destination.
- 📁 **Smart Folder Creation**: Safely prompts to create missing directory paths (Y/N).
- 📌 **Folder Conflict Protection**: Detects existing destination directories and prompts for alternative folder names.
- 🚪 **Safe Exit & Interruption Handling**: Gracefully handles Ctrl+C and Ctrl+D/Ctrl+Z without showing ugly tracebacks.

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

## ▶️ Usage & Subcommands

Run `repo` without arguments to open the interactive Command Palette:

```bash
repo
```

Or pass subcommands directly:

| Command | Description | Example |
|---|---|---|
| `repo` | Opens interactive Command Palette | `repo` |
| `repo clone` | Starts repository clone workflow | `repo clone` |
| `repo repos` | Shows saved repositories | `repo repos` |
| `repo locations` | Shows saved clone locations | `repo locations` |
| `repo stats` | Shows memory statistics | `repo stats` |
| `repo help` | Shows help page | `repo help` |
| `repo clear` | Clears memory history | `repo clear` |
| `repo update` | Shows version & PyPI update command | `repo update` |
| `repo exit` | Gracefully exits | `repo exit` |

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
├── scripts/                      # Developer automation scripts
│   └── dev.py
│
├── src/
│   └── repo_clone_system/        # Core package code
│       ├── core/                 # Git execution & path validation
│       ├── storage/              # State management & JSON memory
│       └── ui/                   # Command Palette & terminal interaction
│
├── tests/                        # Pytest suite
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
- [ ] SSH & Private Repository authentication helper
- [ ] GitHub CLI (`gh`) integration for automatic fork-and-clone
- [ ] Interactive repository search from saved history

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before submitting a pull request.

To set up your local development environment:

```bash
git clone https://github.com/Mr-Anonymous-Guy/Repo_Cone_System.git
cd Repo_Cone_System
pip install -e ".[dev]"
python scripts/dev.py
```

---

## 📜 License

Distributed under the [MIT License](LICENSE).
