import sys
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import FileHistory

from repo_clone_system.core.exit_handler import run_with_exit_handler
from repo_clone_system.core.utils import check_git
from repo_clone_system.services.backup_service import (
    auto_backup_on_exit_if_changed,
    record_initial_memory_hash,
)
from repo_clone_system.storage.memory import get_config_dir
from repo_clone_system.ui.commands import dispatch_command
from repo_clone_system.ui.palette import print_startup_header

COMPLETER_WORDS = [
    "help",
    "clone",
    "workspace",
    "repos",
    "locations",
    "alias",
    "memory",
    "config",
    "backup",
    "backups",
    "doctor",
    "stats",
    "update",
    "clear",
    "exit",
    "quit",
    "switch",
    "create",
    "rename",
    "remove",
    "list",
    "info",
    "export",
    "import",
    "sync",
    "status",
    "browse",
    "search",
    "add",
    "verify",
    "open",
    "test",
    "overview",
    "repair",
    "optimize",
    "check",
    "version",
]


def main():
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    record_initial_memory_hash()

    if not check_git():
        print("\nGit is not installed or is not in PATH.")
        print("Install Git and try again.")
        sys.exit(1)

    # Single-shot execution if arguments are passed via CLI
    if len(sys.argv) > 1:
        dispatch_command(sys.argv[1:])
        auto_backup_on_exit_if_changed()
        return

    # Clean Shell-First Startup
    print_startup_header()

    # Initialize Prompt Toolkit session with persistent history & completer
    history_file = Path(get_config_dir()) / ".repo_history"
    history = FileHistory(str(history_file))
    completer = WordCompleter(COMPLETER_WORDS, ignore_case=True)
    session = PromptSession(history=history, completer=completer)

    # Primary Interactive Shell Loop
    while True:
        try:
            print()
            user_input = session.prompt("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated safely.")
            print("Goodbye.")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("\nSession terminated safely.")
            print("Goodbye.")
            sys.exit(0)

        try:
            dispatch_command(user_input)
        except Exception as e:
            print(f"\nError executing command: {e}")
            print('Type "help" to view available commands.')


def cli_entry_point():
    """Console script entry point for 'repo' command."""
    try:
        run_with_exit_handler(main)
    finally:
        auto_backup_on_exit_if_changed()


if __name__ == "__main__":
    cli_entry_point()
