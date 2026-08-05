import sys

from repo_clone_system.core.exit_handler import run_with_exit_handler
from repo_clone_system.core.utils import check_git
from repo_clone_system.ui.commands import dispatch_command
from repo_clone_system.ui.palette import show_command_palette


def main():

    if not check_git():
        print("\nGit is not installed or is not in PATH.")
        print("Install Git and try again.")
        sys.exit(1)

    # If subcommands are passed as CLI arguments (e.g. 'repo clone', 'repo stats')
    if len(sys.argv) > 1:
        subcommand = sys.argv[1].strip()
        dispatch_command(subcommand)
        return

    # Interactive Command Palette Loop
    while True:

        cmd = show_command_palette()

        if cmd is None:
            cmd = "exit"

        dispatch_command(cmd)


def cli_entry_point():
    """Console script entry point for 'repo' command."""
    run_with_exit_handler(main)


if __name__ == "__main__":
    cli_entry_point()
