# Repo_Clone_System System Workflow (v3.0.0)

## Table of Contents

1. [System Overview & Shell-First Architecture](#system-overview--shell-first-architecture)
2. [Application Startup & Initialization Lifecycle](#application-startup--initialization-lifecycle)
3. [Command Shell Prompt Loop](#command-shell-prompt-loop)
4. [Categorized Help System](#categorized-help-system)
5. [Direct GitHub URL Auto-Detection Gate](#direct-github-url-auto-detection-gate)
6. [Parent Command Sub-Menu Navigation](#parent-command-sub-menu-navigation)
7. [Subsystem Execution Flows](#subsystem-execution-flows)
   - 7.1 [Clone Manager Subsystem](#clone-manager-subsystem)
   - 7.2 [Workspace Management Subsystem](#workspace-management-subsystem)
   - 7.3 [Repository Manager Subsystem](#repository-manager-subsystem)
   - 7.4 [Location Manager Subsystem](#location-manager-subsystem)
   - 7.5 [Alias Manager Subsystem](#alias-manager-subsystem)
   - 7.6 [Memory Manager Subsystem](#memory-manager-subsystem)
   - 7.7 [Export & Import Subsystem](#export--import-subsystem)
   - 7.8 [Managed Backup Subsystem](#managed-backup-subsystem)
   - 7.9 [Configuration & System Doctor](#configuration--system-doctor)
8. [Session Termination & Interruption Handling](#session-termination--interruption-handling)

---

## 1. System Overview & Shell-First Architecture

`Repo_Clone_System` features a professional Git-style shell-first architecture. Running `repo` opens a clean interactive prompt shell without displaying uncluttered automatic dropdown menus on launch.

```
╭──────────────────────────────────────────────────────────────╮
│ Repo_Clone_System v2.0.0                                     │
│ Type "help" to list commands or enter a GitHub URL.          │
│ Press Ctrl+C anytime to exit safely.                         │
╰──────────────────────────────────────────────────────────────╯

>
```

- **Command Shell**: `prompt_toolkit` powered with persistent history (`.repo_history`), tab completion (`WordCompleter`), and arrow key history.
- **Categorized Help**: Typing `help` outputs categorized references (General, Clone, Workspace, Repositories, Locations, Aliases, Memory, Configuration, Backup, System, Statistics, Updates).
- **Sub-Menu Isolation**: Arrow-key interactive menus appear ONLY after entering a parent command (e.g. `workspace`, `repos`, `locations`, `alias`, `memory`, `config`, `backup`, `doctor`, `stats`, `clone`).
- **Direct GitHub URL**: Typing/pasting a `https://github.com/` or `git@github.com:` URL directly bypasses all menus and triggers the clone pipeline immediately.
- **Return Flow**: Every command returns back to the `> ` shell prompt upon completion.

---

## 2. Application Startup & Initialization Lifecycle

When `repo` is invoked:
1. `cli_entry_point()` initializes `run_with_exit_handler(main)`.
2. Standard output & error streams are reconfigured for UTF-8 encoding.
3. `record_initial_memory_hash()` captures initial state for exit backup detection.
4. `check_git()` verifies Git presence in system `PATH`.
5. If command-line arguments are passed (`len(sys.argv) > 1`), `dispatch_command()` executes the single-shot command and exits.
6. If no arguments are passed, `print_startup_header()` renders the clean banner and enters the interactive prompt loop.

---

## 3. Command Shell Prompt Loop

- Prompt: `> `
- Features: Persistent history file (`.repo_history`), autocomplete via `WordCompleter`, arrow key navigation.
- Input Handling:
  - Empty input -> redisplays prompt.
  - `exit` or `quit` -> terminates safely with `Session terminated safely. Goodbye.`
  - Direct URL -> auto-detects URL and routes to `clone_repository()`.
  - Parent Command -> launches subpalette interactive menu.
  - Unknown Command -> outputs:
    ```
    Unknown command.
    Type "help" to view available commands.
    ```

---

## 4. Categorized Help System

Typing `help` outputs categorized command references:
- **[General]**: `help`, `exit`
- **[Clone]**: `clone`, `clone <url>`, `clone --saved`, `clone --recent`, `clone --alias`, `clone --quick`
- **[Workspace]**: `workspace`, `create`, `switch`, `rename`, `remove`, `list`, `info`, `export`, `import`, `backup`, `sync`
- **[Repositories]**: `repos`, `browse`, `search`, `add`, `remove`, `verify`, `info`
- **[Locations]**: `locations`, `browse`, `add`, `remove`, `rename`, `verify`, `open`
- **[Aliases]**: `alias`, `browse`, `add`, `remove`, `rename`, `test`
- **[Memory]**: `memory`, `overview`, `repair`, `optimize`, `export`
- **[Configuration]**: `config`, `config --open`, `config --folder`, `config --edit`, `config --reset`
- **[Backup]**: `backups`, `remove`, `history`
- **[System]**: `doctor`
- **[Statistics]**: `stats`
- **[Updates]**: `update`

---

## 5. Direct GitHub URL Auto-Detection Gate

If user input matches `http://`, `https://`, `git@`, or ends with `.git`:
1. Skips menu prompt entirely.
2. Prompts for destination via interactive menu (`choose_destination()`) if not specified.
3. Clones repository via `git clone`.
4. Records memory history and updates statistics.
5. Returns directly to `> ` prompt.

---

## 6. Parent Command Sub-Menu Navigation

Entering a parent command launches its dedicated subpalette:
- `clone` -> Clone Manager
- `workspace` -> Workspace Manager
- `repos` -> Repository Manager
- `locations` -> Location Manager
- `alias` -> Alias Manager
- `memory` -> Memory Manager
- `config` -> Configuration Details
- `backups` -> Managed Backups
- `doctor` -> System Doctor
- `stats` -> Statistics

Sub-menus operate inside persistent loops until selecting `Exit` or pressing `Esc`, after which execution cleanly returns to the `> ` prompt.

---

## 7. Subsystem Execution Flows

All business logic execution flows remain 100% backward compatible and unchanged.

---

## 8. Session Termination & Interruption Handling

Pressing `Ctrl+C` or `Ctrl+D` (EOF):
1. Trapped gracefully by `PromptSession` exception handler.
2. Displays:
   ```
   Session terminated safely.
   Goodbye.
   ```
3. Exits with status code `0`.
4. Triggers `auto_backup_on_exit_if_changed()` to save state changes safely.
