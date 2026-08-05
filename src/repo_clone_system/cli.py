import sys

from repo_clone_system.core.exit_handler import run_with_exit_handler
from repo_clone_system.core.utils import check_git
from repo_clone_system.services.backup_service import (
    auto_backup_on_exit_if_changed,
    record_initial_memory_hash,
)
from repo_clone_system.ui.commands import dispatch_command
from repo_clone_system.ui.palette import show_command_palette


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

    # If subcommands / arguments are passed as CLI arguments
    # (e.g. 'repo clone', 'repo config --open')
    if len(sys.argv) > 1:
        dispatch_command(sys.argv[1:])
        auto_backup_on_exit_if_changed()
        return

    # Interactive Command Palette Loop
    while True:
        cmd = show_command_palette()

        if cmd is None:
            cmd = "exit"

        dispatch_command([cmd])


def cli_entry_point():
    """Console script entry point for 'repo' command."""
    try:
        run_with_exit_handler(main)
    finally:
        auto_backup_on_exit_if_changed()


if __name__ == "__main__":
    cli_entry_point()
