import sys

from repo_clone_system import __version__
from repo_clone_system.core.clone import clone_repository
from repo_clone_system.core.utils import get_repo_name
from repo_clone_system.storage.memory import memory, reset_memory
from repo_clone_system.ui.menu import choose_destination
from repo_clone_system.ui.messages import print_goodbye
from repo_clone_system.ui.prompts import ask_repo


def command_clone():
    """Starts the interactive repository clone workflow."""
    repo_url = ask_repo()
    if not repo_url:
        return

    destination = choose_destination()
    if destination is None:
        return

    repo_name = get_repo_name(repo_url)
    folder_name = repo_name

    # Folder Name Conflict Detection
    while (destination / folder_name).exists():
        print(f"\nFolder '{folder_name}' already exists.")
        folder_name = input("Enter another folder name\n> ").strip()
        if folder_name == "":
            folder_name = repo_name

    clone_repository(repo_url, destination, folder_name)


def command_repos():
    """Displays saved repositories, with optional full URL view."""
    repos = memory.get("repositories", [])
    if not repos:
        print("\nNo repositories saved.")
        return

    print("\nSaved Repositories")
    print("-" * 40)
    for idx, repo_url in enumerate(repos, start=1):
        name = get_repo_name(repo_url)
        print(f"{idx}. {name}")
    print("-" * 40)

    choice = input("\nView repository URLs?\n(Y/N): ").strip().lower()
    if choice in ("y", "yes"):
        print("\n" + "-" * 40)
        for idx, repo_url in enumerate(repos, start=1):
            name = get_repo_name(repo_url)
            print(f"\n{idx}.")
            print(f"Repository Name : {name}")
            print(f"Repository URL  : {repo_url}")
        print("-" * 40)


def command_locations():
    """Displays every saved clone location."""
    locations = memory.get("locations", [])
    if not locations:
        print("\nNo saved locations.")
        return

    print("\nSaved Locations")
    print("-" * 20)
    for idx, loc in enumerate(locations, start=1):
        print(f"\n{idx}.\n{loc}")


def command_stats():
    """Displays repository and location memory statistics."""
    repos = memory.get("repositories", [])
    locations = memory.get("locations", [])
    last_loc = memory.get("last_location", "") or "None"
    recent_repo = repos[-1] if repos else "None"

    print("\nRepo_Clone_System Statistics")
    print("-" * 20)
    print(f"Repositories Saved   : {len(repos)}")
    print(f"Locations Saved      : {len(locations)}")
    print(f"Last Used Location   : {last_loc}")
    print(f"Most Recent Repo     : {recent_repo}")


def command_help():
    """Displays all available commands and their descriptions."""
    print("\nAvailable Commands\n")
    print(f"{'clone':<12} Clone a repository")
    print(f"{'repos':<12} Show saved repositories")
    print(f"{'locations':<12} Show saved clone locations")
    print(f"{'stats':<12} Show memory statistics")
    print(f"{'update':<12} Show version & update command")
    print(f"{'help':<12} Show this help page")
    print(f"{'clear':<12} Clear saved history")
    print(f"{'exit':<12} Exit Repo_Clone_System")


def command_clear():
    """Resets memory history after user confirmation."""
    print("\nAre you sure?")
    print("This will erase memory.json\n")
    choice = input("(Y/N): ").strip().lower()

    if choice in ("y", "yes"):
        reset_memory()
        print("\nMemory cleared successfully.")
        return

    print("\nOperation cancelled.")


def command_update():
    """Displays version details and update instructions."""
    print(f"\nRepo_Clone_System v{__version__}")
    print("-" * 40)
    print("To update to the latest release on PyPI, run:\n")
    print("  pip install --upgrade repo-clone-system")
    print("-" * 40)


def command_exit():
    """Gracefully exits the CLI application."""
    print_goodbye()
    sys.exit(0)


COMMAND_MAP = {
    "clone": command_clone,
    "repos": command_repos,
    "locations": command_locations,
    "stats": command_stats,
    "help": command_help,
    "clear": command_clear,
    "update": command_update,
    "exit": command_exit,
}


def dispatch_command(cmd_input: str):
    """Routes command string to appropriate handler function."""
    cmd = cmd_input.strip().lower()
    if not cmd:
        return

    handler = COMMAND_MAP.get(cmd)
    if handler:
        handler()
    else:
        print("\nUnknown command.")
        print('Type "help" to view available commands.')
