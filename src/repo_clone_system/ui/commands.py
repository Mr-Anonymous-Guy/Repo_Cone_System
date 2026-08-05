import sys
from pathlib import Path
from typing import List, Union

import questionary
from questionary import Choice

from repo_clone_system import __version__
from repo_clone_system.core.clone import clone_repository
from repo_clone_system.core.utils import get_repo_name
from repo_clone_system.services.alias_service import (
    add_alias,
    list_aliases,
    remove_alias,
    rename_alias,
)
from repo_clone_system.services.config_service import (
    get_config_info,
    open_config_folder,
    open_memory_file,
)
from repo_clone_system.services.doctor_service import run_doctor
from repo_clone_system.services.location_service import (
    add_location,
    clean_missing_locations,
    get_saved_locations,
    remove_location,
    rename_location,
    verify_locations,
)
from repo_clone_system.services.memory_service import (
    backup_memory,
    get_memory_metrics,
    list_backups,
    restore_memory,
)
from repo_clone_system.services.repo_service import (
    add_repo,
    get_saved_repos,
    remove_repo,
    search_repos,
    verify_repos,
)
from repo_clone_system.services.update_service import check_for_updates
from repo_clone_system.storage.memory import memory, reset_memory
from repo_clone_system.ui.menu import choose_destination
from repo_clone_system.ui.messages import print_goodbye
from repo_clone_system.ui.prompts import ask_repo

# ======================================================
# Command Handlers
# ======================================================


def command_clone(args: List[str] = None):
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


def command_config(args: List[str] = None):
    """Handles 'repo config', 'repo config --open', 'repo config --folder'."""
    args = args or []
    if "--open" in args:
        ok, msg = open_memory_file()
        print(f"\n{msg}")
        return

    if "--folder" in args:
        ok, msg = open_config_folder()
        print(f"\n{msg}")
        return

    info = get_config_info()
    print("\nRepo_Clone_System Configuration")
    print("-" * 50)
    print(f"Memory File          : {info['memory_file']}")
    print(f"Configuration Folder : {info['config_folder']}")
    print(f"Package Version      : {info['version']}")
    print(f"Operating System     : {info['os']}")
    print(f"Python Version       : {info['python_version']}")
    print(f"Saved Repositories   : {info['saved_repos']}")
    print(f"Saved Locations      : {info['saved_locations']}")
    print(f"Saved Aliases        : {info['saved_aliases']}")
    print(f"Last Used Location   : {info['last_location']}")
    print("-" * 50)


def command_locations(args: List[str] = None):
    """Handles 'repo locations' and subcommands: add, remove, rename, verify."""
    args = args or []
    subcmd = args[0].lower() if args else ""

    if subcmd == "add":
        if len(args) > 1:
            loc_arg = " ".join(args[1:])
            ok, msg = add_location(loc_arg, auto_create_missing=True)
            print(f"\n{msg}")
            return

        print("\nLocation Manager — Add Locations (Type 'exit' to finish)\n")
        while True:
            loc_input = input("Location\n> ").strip()
            if not loc_input or loc_input.lower() == "exit":
                print("\nFinished adding locations.")
                break

            ok, msg = add_location(loc_input, auto_create_missing=True)
            print(f"{msg}\n")

    elif subcmd in ("remove", "delete"):
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved locations to remove.")
            return

        choices = [Choice(title=loc, value=loc) for loc in locations]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Location to Remove", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        confirm = input(f"\nRemove '{selected}'? (Y/N): ").strip().lower()
        if confirm in ("y", "yes"):
            ok, msg = remove_location(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif subcmd == "rename":
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved locations to rename.")
            return

        choices = [Choice(title=loc, value=loc) for loc in locations]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Location to Rename", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        new_path = input(f"\nEnter new path for '{selected}'\n> ").strip()
        if new_path:
            ok, msg = rename_location(selected, new_path)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif subcmd == "verify":
        print("\nVerifying Saved Locations...")
        print("-" * 50)
        report = verify_locations()
        missing = []

        for loc, data in report.items():
            status_str = data["status"]
            print(f"{status_str:<12} {loc}")
            if not data["exists"]:
                missing.append(loc)
        print("-" * 50)

        if missing:
            confirm = (
                input(
                    f"\nRemove {len(missing)} missing location(s) from memory? (Y/N): "
                )
                .strip()
                .lower()
            )
            if confirm in ("y", "yes"):
                count, msg = clean_missing_locations(missing)
                print(f"\n{msg}")

    else:
        # Default: display interactive locations menu or clean list
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved locations.")
            return

        try:
            choices = [Choice(title=f"📁  {loc}", value=loc) for loc in locations]
            choices.append(Choice(title="Back", value="__BACK__"))
            selected = questionary.select("\nSaved Locations", choices=choices).ask()
            if selected and selected != "__BACK__":
                print(f"\nSelected Location: {selected}")
                exists = Path(selected).exists()
                print(f"Status            : {'✔ Exists' if exists else '✖ Missing'}")
        except Exception:
            print("\nSaved Locations")
            print("-" * 30)
            for idx, loc in enumerate(locations, start=1):
                print(f"{idx}. {loc}")


def command_repos(args: List[str] = None):
    """Handles 'repo repos' and subcommands: add, remove, search, verify."""
    args = args or []
    subcmd = args[0].lower() if args else ""

    if subcmd == "add":
        if len(args) > 1:
            url_arg = args[1]
            ok, msg = add_repo(url_arg)
            print(f"\n{msg}")
            return

        print("\nRepository Manager — Add Repositories (Type 'exit' to finish)\n")
        while True:
            repo_input = input("Repository URL\n> ").strip()
            if not repo_input or repo_input.lower() == "exit":
                print("\nFinished adding repositories.")
                break

            ok, msg = add_repo(repo_input)
            print(f"{msg}\n")

    elif subcmd in ("remove", "delete"):
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories to remove.")
            return

        choices = [
            Choice(title=f"{r['name']} ({r['url']})", value=r["url"]) for r in repos
        ]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Repository to Remove", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        confirm = input(f"\nRemove repository '{selected}'? (Y/N): ").strip().lower()
        if confirm in ("y", "yes"):
            ok, msg = remove_repo(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif subcmd == "search":
        query = " ".join(args[1:]) if len(args) > 1 else ""
        if not query:
            query = input("Enter search query\n> ").strip()

        matches = search_repos(query)
        if not matches:
            print(f"\nNo repositories matching '{query}'.")
            return

        print(f"\nSearch Results for '{query}' ({len(matches)} matches)")
        print("-" * 50)
        for idx, r in enumerate(matches, start=1):
            print(f"{idx}. {r['name']}")
            print(f"   URL      : {r['url']}")
            print(f"   Location : {r['location']}")
            print(f"   Date     : {r['date']}\n")

    elif subcmd == "verify":
        print("\nVerifying Repository Reachability...")
        print("-" * 50)
        report = verify_repos()
        for url, data in report.items():
            name = data["name"]
            status = data["status"]
            print(f"{status:<26} {name} ({url})")
        print("-" * 50)

    else:
        # Default: interactive selection of repository to view details
        repos = get_saved_repos()
        if not repos:
            print("\nNo repositories saved.")
            return

        try:
            choices = [Choice(title=f"📦  {r['name']}", value=r["url"]) for r in repos]
            choices.append(Choice(title="Back", value="__BACK__"))

            selected = questionary.select(
                "\nSaved Repositories (Select for details)", choices=choices
            ).ask()

            if selected and selected != "__BACK__":
                matched = next((r for r in repos if r["url"] == selected), None)
                if matched:
                    print("\nRepository Details")
                    print("-" * 40)
                    print(f"Repository Name  : {matched['name']}")
                    print(f"Repository URL   : {matched['url']}")
                    print(f"Clone Location   : {matched['location']}")
                    print(f"Clone Date       : {matched['date']}")
                    print("-" * 40)
        except Exception:
            print("\nSaved Repositories")
            print("-" * 40)
            for idx, r in enumerate(repos, start=1):
                print(f"{idx}. {r['name']} ({r['url']})")


def command_memory(args: List[str] = None):
    """Handles 'repo memory', 'repo memory backup', 'repo memory restore'."""
    args = args or []
    subcmd = args[0].lower() if args else ""

    if subcmd == "backup":
        ok, msg, path = backup_memory()
        print(f"\n{msg}")
        return

    elif subcmd == "restore":
        backups = list_backups()
        if not backups:
            print("\nNo memory backup files found.")
            return

        choices = [Choice(title=f"💾  {b.name}", value=b) for b in backups]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Backup to Restore", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        confirm = (
            input(f"\nRestore memory from '{selected.name}'? (Y/N): ").strip().lower()
        )
        if confirm in ("y", "yes"):
            ok, msg = restore_memory(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    else:
        metrics = get_memory_metrics()
        print("\nRepo_Clone_System Memory Metrics")
        print("-" * 50)
        print(f"Memory File Path   : {metrics['memory_file_path']}")
        print(f"Memory File Size   : {metrics['memory_file_size']}")
        print(f"Total Repositories : {metrics['total_repos']}")
        print(f"Total Locations    : {metrics['total_locations']}")
        print(f"Total Aliases      : {metrics['total_aliases']}")
        print(f"Newest Repository  : {metrics['newest_entry']}")
        print(f"Oldest Repository  : {metrics['oldest_entry']}")
        print("-" * 50)


def command_alias(args: List[str] = None):
    """Handles 'repo alias' and subcommands: add, remove, rename."""
    args = args or []
    subcmd = args[0].lower() if args else ""

    if subcmd == "add":
        if len(args) >= 3:
            alias_name = args[1]
            path_val = " ".join(args[2:])
            ok, msg = add_alias(alias_name, path_val)
            print(f"\n{msg}")
            return

        alias_name = input("\nEnter alias name (e.g. work)\n> ").strip()
        if not alias_name:
            print("\nOperation cancelled.")
            return
        path_val = input(f"Enter target path for '{alias_name}'\n> ").strip()
        if not path_val:
            print("\nOperation cancelled.")
            return

        ok, msg = add_alias(alias_name, path_val)
        print(f"\n{msg}")

    elif subcmd in ("remove", "delete"):
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases to remove.")
            return

        if len(args) > 1:
            alias_name = args[1]
            ok, msg = remove_alias(alias_name)
            print(f"\n{msg}")
            return

        choices = [
            Choice(title=f"🏷️  {name:<12} ({path})", value=name)
            for name, path in aliases.items()
        ]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Workspace Alias to Remove", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        confirm = input(f"\nRemove alias '{selected}'? (Y/N): ").strip().lower()
        if confirm in ("y", "yes"):
            ok, msg = remove_alias(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif subcmd == "rename":
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases to rename.")
            return

        if len(args) >= 3:
            ok, msg = rename_alias(args[1], args[2])
            print(f"\n{msg}")
            return

        choices = [
            Choice(title=f"🏷️  {name:<12} ({path})", value=name)
            for name, path in aliases.items()
        ]
        choices.append(Choice(title="Cancel", value="__CANCEL__"))

        selected = questionary.select(
            "\nSelect Workspace Alias to Rename", choices=choices
        ).ask()
        if not selected or selected == "__CANCEL__":
            print("\nOperation cancelled.")
            return

        new_name = input(f"\nEnter new alias name for '{selected}'\n> ").strip()
        if new_name:
            ok, msg = rename_alias(selected, new_name)
            print(f"\n{msg}")

    else:
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases defined.")
            print("Add one using: repo alias add <name> <path>")
            return

        print("\nWorkspace Aliases")
        print("-" * 50)
        for name, path in aliases.items():
            print(f"  🏷️  {name:<14} -> {path}")
        print("-" * 50)


def command_doctor(args: List[str] = None):
    """Runs system diagnostic health checks ('repo doctor')."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    print("\nRunning System Diagnostics...")
    print("=" * 60)
    results = run_doctor()
    passed_all = True

    for item in results:
        status_disp = item.status
        try:
            print(f" {status_disp:<3} {item.label:<25} : {item.details}")
            if item.suggestion:
                print(f"     💡 Suggestion: {item.suggestion}")
        except UnicodeEncodeError:
            safe_status = (
                "[OK]"
                if item.status == "✔"
                else ("[FAIL]" if item.status == "✖" else "[WARN]")
            )
            print(f" {safe_status:<6} {item.label:<25} : {item.details}")
            if item.suggestion:
                print(f"     Suggestion: {item.suggestion}")

        if not item.passed and item.status == "✖":
            passed_all = False
    print("=" * 60)

    if passed_all:
        print("\nAll system diagnostics passed cleanly!")
    else:
        print("\nSome issues were detected. Please review recommendations above.")


def command_stats(args: List[str] = None):
    """Displays repository and location memory statistics."""
    repos = memory.get("repositories", [])
    locations = memory.get("locations", [])
    aliases = memory.get("aliases", {})
    last_loc = memory.get("last_location", "") or "None"

    print("\nRepo_Clone_System Statistics")
    print("-" * 40)
    print(f"Repositories Saved   : {len(repos)}")
    print(f"Locations Saved      : {len(locations)}")
    print(f"Workspace Aliases    : {len(aliases)}")
    print(f"Last Used Location   : {last_loc}")
    print("-" * 40)


def command_help(args: List[str] = None):
    """Displays all available commands and subcommands."""
    print(f"\nRepo_Clone_System v{__version__} Commands Reference\n")
    print(f"{'clone':<15} Start repository clone workflow")
    print(
        f"{'repos':<15} Repository manager (subcommands: add, remove, search, verify)"
    )
    print(
        f"{'locations':<15} Location manager (subcommands: add, remove, rename, verify)"
    )
    print(f"{'alias':<15} Workspace alias manager (subcommands: add, remove, rename)")
    print(f"{'memory':<15} Memory storage manager (subcommands: backup, restore)")
    print(f"{'config':<15} Configuration & storage info (flags: --open, --folder)")
    print(f"{'doctor':<15} Run system diagnostic health checks")
    print(f"{'stats':<15} Show memory statistics")
    print(f"{'update':<15} Query PyPI for version updates")
    print(f"{'help':<15} Show this command reference")
    print(f"{'clear':<15} Clear saved memory history")
    print(f"{'exit':<15} Exit application")


def command_clear(args: List[str] = None):
    """Resets memory history after user confirmation."""
    print("\nAre you sure?")
    print("This will erase memory.json history.\n")
    choice = input("(Y/N): ").strip().lower()

    if choice in ("y", "yes"):
        reset_memory()
        print("\nMemory cleared successfully.")
        return

    print("\nOperation cancelled.")


def command_update(args: List[str] = None):
    """Displays version details and checks PyPI for updates."""
    print(f"\nRepo_Clone_System v{__version__}")
    print("-" * 50)
    curr, latest, avail, msg = check_for_updates()
    print(f"Current Version : {curr}")
    print(f"Latest PyPI Ver : {latest}")
    print(f"\n{msg}")

    if avail:
        print("\nTo update, run:\n")
        print("  pip install -U repo-clone-system")
    print("-" * 50)


def command_exit(args: List[str] = None):
    """Gracefully exits the CLI application."""
    print_goodbye()
    sys.exit(0)


COMMAND_MAP = {
    "clone": command_clone,
    "repos": command_repos,
    "locations": command_locations,
    "alias": command_alias,
    "memory": command_memory,
    "config": command_config,
    "doctor": command_doctor,
    "stats": command_stats,
    "help": command_help,
    "clear": command_clear,
    "update": command_update,
    "exit": command_exit,
}


def dispatch_command(cmd_input: Union[str, List[str]]):
    """Routes command input (string or list of tokens) to handler function."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    if isinstance(cmd_input, str):
        tokens = cmd_input.strip().split()
    else:
        tokens = [str(t).strip() for t in cmd_input if str(t).strip()]

    if not tokens:
        return

    main_cmd = tokens[0].lower()
    sub_args = tokens[1:]

    handler = COMMAND_MAP.get(main_cmd)
    if handler:
        handler(sub_args)
    else:
        print(f"\nUnknown command '{main_cmd}'.")
        print('Type "help" to view available commands.')
