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
from repo_clone_system.services.backup_service import (
    create_auto_backup,
    create_export,
    delete_backup_file,
    get_backup_summary,
    get_export_history,
    list_backups_dir,
    perform_import,
    validate_backup_file,
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
from repo_clone_system.services.profile_service import (
    create_profile,
    get_active_profile_name,
    list_profiles,
    remove_profile,
    rename_profile,
    switch_profile,
)
from repo_clone_system.services.repo_service import (
    add_repo,
    get_saved_repos,
    remove_repo,
    search_repos,
    verify_repos,
)
from repo_clone_system.services.sync_service import (
    configure_sync_folder,
    export_sync,
    get_sync_status,
    locate_latest_sync_backup,
)
from repo_clone_system.services.update_service import check_for_updates
from repo_clone_system.services.workspace_service import (
    export_workspace,
    get_workspace_info,
)
from repo_clone_system.storage.memory import memory, reset_memory
from repo_clone_system.ui.messages import print_goodbye, print_header
from repo_clone_system.ui.prompts import ask_repo
from repo_clone_system.ui.workspace_ui import (
    show_backup_palette,
    show_profile_palette,
    show_sync_palette,
    show_workspace_palette,
)


def command_clone(args: List[str] = None):
    """Starts the repository clone workflow ('repo clone')."""
    print_header()
    url = ask_repo()
    clone_repository(url)


def command_repos(args: List[str] = None):
    """Manages saved repositories ('repo repos')."""
    sub = args[0].lower() if args else ""

    if sub in ("list", ""):
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories found in memory.")
            return

        print("\nSaved Repositories History")
        print("-" * 60)
        for i, item in enumerate(repos, 1):
            if isinstance(item, dict):
                url = item.get("url", "")
                loc = item.get("location", "Unknown")
                dt = item.get("date", "Unknown")
                name = item.get("name", get_repo_name(url))
                print(f"{i}. {name}")
                print(f"   URL      : {url}")
                print(f"   Location : {loc}")
                print(f"   Date     : {dt}\n")
            else:
                print(f"{i}. {item}")
        print("-" * 60)

    elif sub == "add":
        if len(args) < 2:
            print("\nUsage: repo repos add <repository_url> [destination_path]")
            return
        repo_url = args[1]
        dest_path = args[2] if len(args) > 2 else None
        ok, msg = add_repo(repo_url, dest_path)
        print(f"\n{msg}")

    elif sub in ("remove", "delete", "rm"):
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories to remove.")
            return

        choices = [
            Choice(
                f"{r.get('name', r.get('url')) if isinstance(r, dict) else r}",
                value=r,
            )
            for r in repos
        ]
        choices.append(Choice("Cancel", value=None))

        try:
            selected = questionary.select(
                "Select repository to remove", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected:
            target_url = (
                selected.get("url", "") if isinstance(selected, dict) else selected
            )
            ok, msg = remove_repo(target_url)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif sub in ("search", "find"):
        if len(args) < 2:
            print("\nUsage: repo repos search <query>")
            return
        query = " ".join(args[1:])
        results = search_repos(query)
        if not results:
            print(f"\nNo repositories matching '{query}' found.")
            return

        print(f"\nSearch Results for '{query}' ({len(results)} matches)")
        print("-" * 50)
        for i, item in enumerate(results, 1):
            url = item.get("url", "")
            loc = item.get("location", "Unknown")
            dt = item.get("date", "Unknown")
            name = item.get("name", get_repo_name(url))
            print(f"{i}. {name}")
            print(f"   URL      : {url}")
            print(f"   Location : {loc}")
            print(f"   Date     : {dt}\n")

    elif sub == "verify":
        print("\nVerifying reachability of saved repositories...")
        results = verify_repos()
        if not results:
            print("No saved repositories to verify.")
            return

        print("-" * 60)
        for item in results:
            status = "✓ Reachable" if item["reachable"] else "✖ Unreachable"
            print(f"{status:<15} : {item['name']} ({item['url']})")
        print("-" * 60)

    else:
        print(f"\nUnknown subcommand 'repo repos {sub}'.")
        print("Available subcommands: list, add, remove, search, verify")


def command_locations(args: List[str] = None):
    """Manages saved destination locations ('repo locations')."""
    sub = args[0].lower() if args else ""

    if sub in ("list", ""):
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved clone locations found.")
            return

        print("\nSaved Clone Locations")
        print("-" * 60)
        for i, loc in enumerate(locations, 1):
            p = Path(loc)
            status = "✓ Exists" if p.exists() else "✖ Missing"
            print(f"{i}. [{status}] {loc}")
        print("-" * 60)

    elif sub == "add":
        if len(args) < 2:
            print("\nUsage: repo locations add <folder_path>")
            return
        path_str = " ".join(args[1:])
        ok, msg = add_location(path_str)
        print(f"\n{msg}")

    elif sub in ("remove", "delete", "rm"):
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved locations to remove.")
            return

        choices = [Choice(loc, value=loc) for loc in locations]
        choices.append(Choice("Cancel", value=None))

        try:
            selected = questionary.select(
                "Select location to remove", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected:
            ok, msg = remove_location(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif sub == "rename":
        if len(args) < 3:
            print("\nUsage: repo locations rename <old_path> <new_path>")
            return
        old_p = args[1]
        new_p = args[2]
        ok, msg = rename_location(old_p, new_p)
        print(f"\n{msg}")

    elif sub in ("verify", "clean"):
        print("\nVerifying saved clone locations...")
        valid, missing = verify_locations()
        print(f"Valid Locations   : {len(valid)}")
        print(f"Missing Locations : {len(missing)}")

        if missing:
            print("\nMissing Folders:")
            for m in missing:
                print(f"  - {m}")

            try:
                clean = questionary.confirm(
                    "Would you like to remove missing folders from history?"
                ).ask()
            except Exception:
                clean = input(
                    "\nRemove missing folders from history? (Y/N): "
                ).strip().lower() in ("y", "yes")

            if clean:
                ok, msg = clean_missing_locations()
                print(f"\n{msg}")

    else:
        print(f"\nUnknown subcommand 'repo locations {sub}'.")
        print("Available subcommands: list, add, remove, rename, verify")


def command_alias(args: List[str] = None):
    """Manages workspace path aliases ('repo alias')."""
    sub = args[0].lower() if args else ""

    if sub in ("list", ""):
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases configured.")
            print("Add one using: repo alias add <name> <folder_path>")
            return

        print("\nWorkspace Aliases")
        print("-" * 50)
        for name, path in aliases.items():
            print(f"  🏷️  {name:<15} -> {path}")
        print("-" * 50)

    elif sub == "add":
        if len(args) < 3:
            print("\nUsage: repo alias add <alias_name> <folder_path>")
            return
        alias_name = args[1]
        target_path = " ".join(args[2:])
        ok, msg = add_alias(alias_name, target_path)
        print(f"\n{msg}")

    elif sub in ("remove", "delete", "rm"):
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases to remove.")
            return

        choices = [
            Choice(f"{name} ({path})", value=name) for name, path in aliases.items()
        ]
        choices.append(Choice("Cancel", value=None))

        try:
            selected = questionary.select(
                "Select alias to remove", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected:
            ok, msg = remove_alias(selected)
            print(f"\n{msg}")
        else:
            print("\nOperation cancelled.")

    elif sub == "rename":
        if len(args) < 3:
            print("\nUsage: repo alias rename <old_name> <new_name>")
            return
        old_name = args[1]
        new_name = args[2]
        ok, msg = rename_alias(old_name, new_name)
        print(f"\n{msg}")

    else:
        print(f"\nUnknown subcommand 'repo alias {sub}'.")
        print("Available subcommands: list, add, remove, rename")


def command_memory(args: List[str] = None):
    """Manages memory storage metrics, backup, and restore ('repo memory')."""
    sub = args[0].lower() if args else ""

    if sub in ("metrics", "info", ""):
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

    elif sub == "backup":
        ok, msg, backup_path = backup_memory()
        print(f"\n{msg}")

    elif sub == "restore":
        backups = list_backups()
        if not backups:
            print("\nNo memory backup files found in configuration directory.")
            return

        choices = [Choice(b.name, value=b) for b in backups]
        choices.append(Choice("Cancel", value=None))

        try:
            selected = questionary.select(
                "Select backup file to restore", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected:
            ok, msg = restore_memory(selected)
            print(f"\n{msg}")
        else:
            print("\nRestore cancelled.")

    else:
        print(f"\nUnknown subcommand 'repo memory {sub}'.")
        print("Available subcommands: metrics, backup, restore")


def command_export(args: List[str] = None):
    """Exports complete configuration to JSON backup file ('repo export')."""
    if args and args[0].lower() in ("history", "--history"):
        history = get_export_history()
        if not history:
            print("\nNo export history recorded yet.")
            return
        print("\nExport History")
        print("-" * 65)
        for h in history:
            print(f" Date        : {h.get('date')}")
            print(f" Destination : {h.get('destination')}")
            print(
                f" Size        : {h.get('size')} | Repos: {h.get('repositories')} "
                f"| Locations: {h.get('locations')} | Aliases: {h.get('aliases')}"
            )
            print(f" {'-' * 65}")
        return

    dest_input = " ".join(args).strip() if args else None

    def _prompt_mkdir(folder_path: str) -> bool:
        print(f"\nFolder '{folder_path}' does not exist.")
        try:
            return questionary.confirm("Create it?").ask()
        except Exception:
            choice = input("Create it? (Y/N): ").strip().lower()
            return choice in ("y", "yes")

    ok, msg, metadata = create_export(
        dest_input=dest_input, prompt_mkdir_callback=_prompt_mkdir
    )
    if not ok:
        print(f"\n{msg}")
        return

    print("\nBackup created successfully.")
    print("-" * 50)
    print(f"Path                  : {metadata.get('path')}")
    print(f"Number of repositories: {metadata.get('repo_count')}")
    print(f"Number of locations   : {metadata.get('location_count')}")
    print(f"Number of aliases     : {metadata.get('alias_count')}")
    print(f"Backup size           : {metadata.get('size_fmt')}")
    print("-" * 50)


def command_import(args: List[str] = None):
    """Imports configuration from a JSON backup file ('repo import')."""
    filepath_str = " ".join(args).strip() if args else ""

    if not filepath_str:
        try:
            filepath_str = questionary.text("Backup file path\n>").ask()
        except Exception:
            filepath_str = input("\nBackup file path\n> ").strip()

    if not filepath_str or not filepath_str.strip():
        print("\nImport cancelled: No file path provided.")
        return

    filepath = Path(filepath_str.strip().strip('"'))
    ok, err_msg, data = validate_backup_file(filepath)
    if not ok:
        print(f"\n{err_msg}")
        return

    summary = get_backup_summary(data)
    print("\nBackup Summary")
    print("-" * 50)
    print(f"Created     : {summary.get('created_at')}")
    print(f"Repositories: {summary.get('repo_count')}")
    print(f"Locations   : {summary.get('location_count')}")
    print(f"Aliases     : {summary.get('alias_count')}")
    print(f"Version     : {summary.get('version')}")
    print(f"Schema      : {summary.get('schema_version')}")
    print("-" * 50)

    try:
        confirm_import = questionary.confirm("Import this backup?").ask()
    except Exception:
        choice = input("Import this backup? (Y/N): ").strip().lower()
        confirm_import = choice in ("y", "yes")

    if not confirm_import:
        print("\nImport cancelled.")
        return

    try:
        mode_choice = questionary.select(
            "Choose import mode",
            choices=[
                Choice(
                    "Merge (combine with existing memory, avoid duplicates)",
                    value="merge",
                ),
                Choice(
                    "Replace (replace all existing memory with backup)",
                    value="replace",
                ),
            ],
        ).ask()
    except Exception:
        print(
            "\nChoose import mode:\n 1. Merge (Combine, avoid duplicates)\n"
            " 2. Replace (Overwrite memory)"
        )
        c = input("Choice (1/2): ").strip()
        mode_choice = "replace" if c == "2" else "merge"

    if not mode_choice:
        print("\nImport cancelled.")
        return

    imp_ok, imp_msg = perform_import(data, mode=mode_choice)
    print(f"\n{imp_msg}")


def command_backups(args: List[str] = None):
    """Manages system backups ('repo backups', 'repo backups remove/history')."""
    sub = args[0].lower() if args else ""

    if sub in ("history", "--history"):
        history = get_export_history()
        if not history:
            print("\nNo export history recorded yet.")
            return
        print("\nExport History")
        print("-" * 65)
        for h in history:
            print(f" Date        : {h.get('date')}")
            print(f" Destination : {h.get('destination')}")
            print(
                f" Size        : {h.get('size')} | Repos: {h.get('repositories')} "
                f"| Locations: {h.get('locations')} | Aliases: {h.get('aliases')}"
            )
            print(f" {'-' * 65}")
        return

    backups = list_backups_dir()
    if not backups:
        print("\nNo backups found in Backups directory.")
        return

    if sub in ("remove", "delete", "rm"):
        choices = [Choice(f"{b.name} ({b.stat().st_size} B)", value=b) for b in backups]
        choices.append(Choice("Cancel", value=None))

        try:
            selected = questionary.select(
                "Select backup file to remove", choices=choices
            ).ask()
        except Exception:
            selected = None

        if not selected:
            print("\nOperation cancelled.")
            return

        try:
            confirm_del = questionary.confirm(f"Delete backup '{selected.name}'?").ask()
        except Exception:
            choice = input(f"Delete backup '{selected.name}'? (Y/N): ").strip().lower()
            confirm_del = choice in ("y", "yes")

        if confirm_del:
            del_ok, del_msg = delete_backup_file(selected)
            print(f"\n{del_msg}")
        else:
            print("\nDeletion cancelled.")
        return

    # Interactive backups menu
    choices = [Choice(f"{b.name}", value=b) for b in backups]
    choices.append(Choice("Exit Backups Menu", value=None))

    try:
        selected = questionary.select(
            "Managed Backups (Select to inspect)", choices=choices
        ).ask()
    except Exception:
        selected = None

    if not selected:
        return

    ok, msg, data = validate_backup_file(selected)
    if not ok:
        print(f"\n{msg}")
        return

    summary = get_backup_summary(data)
    print(f"\nBackup File Details: {selected.name}")
    print("-" * 50)
    print(f"Path        : {selected}")
    print(f"Date        : {summary.get('created_at')}")
    print(f"Repositories: {summary.get('repo_count')}")
    print(f"Locations   : {summary.get('location_count')}")
    print(f"Aliases     : {summary.get('alias_count')}")
    print(f"Version     : {summary.get('version')}")
    print(f"Schema      : {summary.get('schema_version')}")
    print("-" * 50)


def command_workspace(args: List[str] = None):
    """Central handler for Workspace Management subsystem ('repo workspace')."""
    if not args:
        action = show_workspace_palette()
        if not action or action == "exit":
            return
        args = [action]

    sub = args[0].lower()
    sub_args = args[1:]

    if sub in ("switch", "use"):
        command_workspace_profile(["switch"] + sub_args)
    elif sub in ("create", "add"):
        command_workspace_profile(["create"] + sub_args)
    elif sub == "rename":
        command_workspace_profile(["rename"] + sub_args)
    elif sub in ("remove", "delete", "rm"):
        command_workspace_profile(["remove"] + sub_args)
    elif sub == "list":
        command_workspace_profile(["list"] + sub_args)
    elif sub == "export":
        command_workspace_export(sub_args)
    elif sub == "import":
        command_workspace_import(sub_args)
    elif sub in ("backup", "backups"):
        command_workspace_backup(sub_args)
    elif sub in ("profile", "profiles"):
        command_workspace_profile(sub_args)
    elif sub in ("sync", "synchronization"):
        command_workspace_sync(sub_args)
    elif sub in ("info", "metrics"):
        command_workspace_info(sub_args)
    else:
        print(f"\nUnknown workspace subcommand 'repo workspace {sub}'.")
        print(
            "Available: create, switch, rename, remove, export, import, "
            "backup, sync, info"
        )


def command_workspace_export(args: List[str] = None):
    """Exports complete active workspace configuration."""
    dest_input = " ".join(args).strip() if args else None

    def _prompt_mkdir(folder_path: str) -> bool:
        print(f"\nFolder '{folder_path}' does not exist.")
        try:
            return questionary.confirm("Create it?").ask()
        except Exception:
            choice = input("Create it? (Y/N): ").strip().lower()
            return choice in ("y", "yes")

    ok, msg, metadata = export_workspace(
        dest_input=dest_input, prompt_mkdir_callback=_prompt_mkdir
    )
    if not ok:
        print(f"\n{msg}")
        return

    print("\nWorkspace exported successfully.")
    print("-" * 50)
    print(f"Workspace Name : {metadata.get('workspace_name')}")
    print(f"Repositories   : {metadata.get('repo_count')}")
    print(f"Locations      : {metadata.get('location_count')}")
    print(f"Aliases        : {metadata.get('alias_count')}")
    print(f"Backup Size    : {metadata.get('size_fmt')}")
    print(f"Export Path    : {metadata.get('path')}")
    print("-" * 50)


def command_workspace_import(args: List[str] = None):
    """Imports workspace backup file."""
    command_import(args)


def command_workspace_backup(args: List[str] = None):
    """Workspace Backup Manager ('repo workspace backup')."""
    if not args:
        action = show_backup_palette()
        if not action or action == "exit":
            return
        args = [action]

    sub = args[0].lower()
    if sub in ("create", "add"):
        ok, msg, path = create_auto_backup()
        print(f"\n{msg}")
    elif sub == "restore":
        command_memory(["restore"])
    elif sub in ("list", "view"):
        command_backups([])
    elif sub in ("remove", "delete", "rm"):
        command_backups(["remove"])
    elif sub == "history":
        command_backups(["history"])
    else:
        print(f"\nUnknown backup subcommand 'repo workspace backup {sub}'.")


def command_workspace_profile(args: List[str] = None):
    """Workspace Profile Manager ('repo workspace profile')."""
    if not args:
        action = show_profile_palette()
        if not action or action == "exit":
            return
        args = [action]

    sub = args[0].lower()
    sub_args = args[1:]

    if sub in ("list", ""):
        profiles = list_profiles()
        active = get_active_profile_name()
        print("\nWorkspace Profiles")
        print("-" * 40)
        for p in profiles:
            marker = "❯ * (active)" if p.lower() == active.lower() else "  "
            print(f"  {marker:<12} {p}")
        print("-" * 40)

    elif sub in ("switch", "use"):
        if not sub_args:
            profiles = list_profiles()
            choices = [Choice(p, value=p) for p in profiles]
            try:
                target = questionary.select(
                    "Select profile to switch to", choices=choices
                ).ask()
            except Exception:
                target = None
        else:
            target = sub_args[0]

        if target:
            ok, msg = switch_profile(target)
            print(f"\n{msg}")

    elif sub in ("create", "add"):
        if not sub_args:
            try:
                name = questionary.text("Enter new profile name:").ask()
            except Exception:
                name = input("Enter new profile name: ").strip()
        else:
            name = sub_args[0]

        if name:
            ok, msg = create_profile(name)
            print(f"\n{msg}")

    elif sub == "rename":
        if len(sub_args) < 2:
            print("\nUsage: repo workspace profile rename <old_name> <new_name>")
            return
        ok, msg = rename_profile(sub_args[0], sub_args[1])
        print(f"\n{msg}")

    elif sub in ("remove", "delete", "rm"):
        if not sub_args:
            profiles = [p for p in list_profiles() if p.lower() != "default"]
            choices = [Choice(p, value=p) for p in profiles]
            try:
                target = questionary.select(
                    "Select profile to remove", choices=choices
                ).ask()
            except Exception:
                target = None
        else:
            target = sub_args[0]

        if target:
            ok, msg = remove_profile(target)
            print(f"\n{msg}")

    else:
        print(f"\nUnknown profile subcommand 'repo workspace profile {sub}'.")


def command_workspace_sync(args: List[str] = None):
    """Workspace Sync Manager ('repo workspace sync')."""
    if not args:
        action = show_sync_palette()
        if not action or action == "exit":
            return
        args = [action]

    sub = args[0].lower()
    sub_args = args[1:]

    if sub in ("config", "configure"):
        if not sub_args:
            try:
                folder = questionary.text("Enter sync folder path:").ask()
            except Exception:
                folder = input("Enter sync folder path: ").strip()
        else:
            folder = " ".join(sub_args)

        if folder:
            ok, msg = configure_sync_folder(folder)
            print(f"\n{msg}")

    elif sub == "export":
        ok, msg, path = export_sync()
        print(f"\n{msg}")

    elif sub == "import":
        ok, msg, path, data = locate_latest_sync_backup()
        if not ok:
            print(f"\n{msg}")
            return
        command_import([str(path)])

    elif sub == "status":
        status = get_sync_status()
        print("\nWorkspace Sync Status")
        print("-" * 50)
        print(f"Configured Folder : {status['sync_folder']}")
        print(f"Provider          : {status['provider']}")
        print(f"Active Profile    : {status['active_profile']}")
        print(f"Latest Backup     : {status['latest_backup']}")
        print(f"Backup Size       : {status['backup_size']}")
        print(f"Last Sync Export  : {status['last_export']}")
        print(f"Last Sync Import  : {status['last_import']}")
        print("-" * 50)

    else:
        print(f"\nUnknown sync subcommand 'repo workspace sync {sub}'.")


def command_workspace_info(args: List[str] = None):
    """Displays comprehensive workspace information ('repo workspace info')."""
    info = get_workspace_info()
    print("\nRepo_Clone_System Workspace Information")
    print("-" * 55)
    print(f"Workspace Name    : {info['workspace_name']}")
    print(f"Current Profile   : {info['active_profile']}")
    print(f"Repositories      : {info['repo_count']}")
    print(f"Locations         : {info['location_count']}")
    print(f"Workspace Aliases : {info['alias_count']}")
    print(f"Workspace Size    : {info['memory_size']}")
    print(f"Backup Count      : {info['backup_count']}")
    print(f"Schema Version    : {info['schema_version']}")
    print(f"Package Version   : {info['package_version']}")
    print(f"Platform          : {info['platform']}")
    print(f"Python Version    : {info['python_version']}")
    print("-" * 55)


def command_config(args: List[str] = None):
    """Displays system configuration and opens config directory/file ('repo config')."""
    if args:
        flag = args[0].lower()
        if flag in ("--open", "-o"):
            ok, msg = open_memory_file()
            print(f"\n{msg}")
            return
        elif flag in ("--folder", "-f"):
            ok, msg = open_config_folder()
            print(f"\n{msg}")
            return

    info = get_config_info()
    print("\nRepo_Clone_System Configuration")
    print("-" * 50)
    print(f"Memory File          : {info['memory_file']}")
    print(f"Configuration Folder : {info['storage_location']}")
    print(f"Package Version      : {info['package_version']}")
    print(f"Operating System     : {info['os']}")
    print(f"Python Version       : {info['python_version']}")
    print(f"Saved Repositories   : {info['saved_repos']}")
    print(f"Saved Locations      : {info['saved_locations']}")
    print(f"Saved Aliases        : {info['saved_aliases']}")
    print(f"Last Used Location   : {info['last_location']}")
    print("-" * 50)


def command_doctor(args: List[str] = None):
    """Runs system diagnostic health checks ('repo doctor')."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
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
        f"{'workspace':<15} Workspace manager (subcommands: export, import, "
        "backup, profile, sync, info)"
    )
    print(
        f"{'repos':<15} Repository manager (subcommands: add, remove, search, verify)"
    )
    print(
        f"{'locations':<15} Location manager (subcommands: add, remove, rename, verify)"
    )
    print(f"{'alias':<15} Workspace alias manager (subcommands: add, remove, rename)")
    print(f"{'memory':<15} Memory storage manager (subcommands: backup, restore)")
    print(f"{'export':<15} Export complete configuration (repo export [path])")
    print(f"{'import':<15} Import configuration backup (repo import [path])")
    print(f"{'backups':<15} Managed backups & export history (remove, history)")
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
    "workspace": command_workspace,
    "repos": command_repos,
    "locations": command_locations,
    "alias": command_alias,
    "memory": command_memory,
    "export": command_export,
    "import": command_import,
    "backups": command_backups,
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
        print(f"\nUnknown command '{main_cmd}'. Type 'repo help' to see all commands.")
