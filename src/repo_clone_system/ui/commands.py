import os
import subprocess
import sys
import webbrowser
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
from repo_clone_system.storage.memory import memory, reset_memory, save_memory
from repo_clone_system.ui.messages import print_goodbye, print_header
from repo_clone_system.ui.prompts import ask_repo
from repo_clone_system.ui.workspace_ui import (
    show_alias_palette,
    show_backup_palette,
    show_clear_palette,
    show_clone_palette,
    show_export_palette,
    show_import_palette,
    show_locations_palette,
    show_memory_palette,
    show_profile_palette,
    show_repos_palette,
    show_sync_palette,
    show_workspace_palette,
)


def _handle_clone_action(action: str):
    if action in ("url", "quick"):
        print_header()
        url = ask_repo()
        clone_repository(url)
    elif action == "saved":
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories found in memory.")
            print("Add one using: repo repos add <url>")
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
                "Select repository to clone", choices=choices
            ).ask()
        except Exception:
            selected = None
        if selected:
            url = selected.get("url", "") if isinstance(selected, dict) else selected
            clone_repository(url)
    elif action == "alias":
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases configured.")
            print("Add one using: repo alias add <name> <folder_path>")
            return
        choices = [
            Choice(f"{name} ({path})", value=path) for name, path in aliases.items()
        ]
        choices.append(Choice("Cancel", value=None))
        try:
            dest = questionary.select("Select alias destination", choices=choices).ask()
        except Exception:
            dest = None
        if dest:
            print_header()
            url = ask_repo()
            clone_repository(url, Path(dest))
    elif action == "recent":
        repos = get_saved_repos()[:10]
        if not repos:
            print("\nNo recent repositories found.")
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
                "Select recent repository", choices=choices
            ).ask()
        except Exception:
            selected = None
        if selected:
            url = selected.get("url", "") if isinstance(selected, dict) else selected
            clone_repository(url)


def command_clone(args: List[str] = None):
    """Starts the repository clone workflow ('repo clone')."""
    if not args:
        while True:
            action = show_clone_palette()
            if not action or action == "exit":
                break
            _handle_clone_action(action)
        return
    else:
        first = args[0].lower()
        if first in ("--saved", "saved"):
            _handle_clone_action("saved")
        elif first in ("--recent", "recent"):
            _handle_clone_action("recent")
        elif first in ("--alias", "alias"):
            _handle_clone_action("alias")
        elif first in ("--quick", "quick"):
            _handle_clone_action("quick")
        else:
            url = " ".join(args)
            clone_repository(url)


def command_repos(args: List[str] = None):
    """Manages saved repositories ('repo repos')."""
    if not args:
        while True:
            action = show_repos_palette()
            if not action or action == "exit":
                break
            command_repos([action])
        return

    sub = args[0].lower()

    if sub in ("list", ""):
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories found in memory.")
            print("Add one using: repo repos add <repository_url>")
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
        if len(args) >= 2:
            repo_url = args[1]
            dest_path = args[2] if len(args) > 2 else None
            ok, msg = add_repo(repo_url, dest_path)
            print(f"\n{msg}")
        else:
            print("\n--- Add Repository Loop (Type 'exit' to finish) ---")
            while True:
                try:
                    repo_url = questionary.text("Repository URL:").ask()
                except Exception:
                    repo_url = input("\nRepository URL: ").strip()

                if not repo_url or repo_url.strip().lower() in (
                    "exit",
                    "quit",
                    "cancel",
                ):
                    print("Exited Add Repository loop.")
                    break

                try:
                    dest_path = questionary.text(
                        "Destination path (optional, press Enter to skip):"
                    ).ask()
                except Exception:
                    dest_path = input("Destination path (optional): ").strip()

                dest_path = (
                    dest_path.strip() if dest_path and dest_path.strip() else None
                )
                ok, msg = add_repo(repo_url.strip(), dest_path)
                print(f"\n{msg}\n")

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
        if len(args) >= 2:
            query = " ".join(args[1:])
        else:
            try:
                query = questionary.text("Search query:").ask()
            except Exception:
                query = input("\nSearch query: ").strip()

        if not query or not query.strip():
            print("\nSearch cancelled.")
            return

        results = search_repos(query.strip())
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

    elif sub in ("info", "details"):
        repos = get_saved_repos()
        if not repos:
            print("\nNo saved repositories found.")
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
                "Select repository for details", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected and isinstance(selected, dict):
            print(f"\nRepository Details: {selected.get('name')}")
            print("-" * 50)
            print(f"URL         : {selected.get('url')}")
            print(f"Location    : {selected.get('location')}")
            print(f"Date Saved  : {selected.get('date')}")
            print(f"Workspace   : {selected.get('workspace', 'default')}")
            print("-" * 50)
        elif selected:
            print(f"\nRepository URL: {selected}")

    else:
        print(f"\nUnknown subcommand 'repo repos {sub}'.")
        print("Available subcommands: list, add, remove, search, verify, info")


def command_locations(args: List[str] = None):
    """Manages saved destination locations ('repo locations')."""
    if not args:
        while True:
            action = show_locations_palette()
            if not action or action == "exit":
                break
            command_locations([action])
        return

    sub = args[0].lower()

    if sub in ("list", ""):
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved clone locations found.")
            print("Add one using: repo locations add <folder_path>")
            return

        print("\nSaved Clone Locations")
        print("-" * 60)
        for i, loc in enumerate(locations, 1):
            p = Path(loc)
            status = "✓ Exists" if p.exists() else "✖ Missing"
            print(f"{i}. [{status}] {loc}")
        print("-" * 60)

    elif sub == "add":
        if len(args) >= 2:
            path_str = " ".join(args[1:])
            ok, msg = add_location(path_str)
            print(f"\n{msg}")
        else:
            print("\n--- Add Location Loop (Type 'exit' to finish) ---")
            while True:
                try:
                    path_str = questionary.text("Location folder path:").ask()
                except Exception:
                    path_str = input("\nLocation folder path: ").strip()

                if not path_str or path_str.strip().lower() in (
                    "exit",
                    "quit",
                    "cancel",
                ):
                    print("Exited Add Location loop.")
                    break

                ok, msg = add_location(path_str.strip())
                print(f"\n{msg}\n")

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
        locations = get_saved_locations()
        if len(args) >= 3:
            old_p = args[1]
            new_p = args[2]
        else:
            if not locations:
                print("\nNo saved locations to rename.")
                return
            choices = [Choice(loc, value=loc) for loc in locations]
            choices.append(Choice("Cancel", value=None))
            try:
                old_p = questionary.select(
                    "Select location to rename", choices=choices
                ).ask()
            except Exception:
                old_p = None
            if not old_p:
                print("\nRename cancelled.")
                return
            try:
                new_p = questionary.text(f"New path for '{old_p}':").ask()
            except Exception:
                new_p = input(f"New path for '{old_p}': ").strip()
            if not new_p or not new_p.strip():
                print("\nRename cancelled.")
                return
            new_p = new_p.strip()

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

    elif sub == "open":
        locations = get_saved_locations()
        if not locations:
            print("\nNo saved locations found.")
            return

        choices = [Choice(loc, value=loc) for loc in locations]
        choices.append(Choice("Cancel", value=None))
        try:
            selected = questionary.select(
                "Select folder to open in File Explorer", choices=choices
            ).ask()
        except Exception:
            selected = None

        if selected:
            p = Path(selected)
            if not p.exists():
                print(f"\nCannot open: Folder '{selected}' does not exist on disk.")
                return
            try:
                if sys.platform == "win32":
                    os.startfile(str(p))
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(p)])
                else:
                    subprocess.Popen(["xdg-open", str(p)])
                print(f"\nOpened '{selected}' in File Explorer.")
            except Exception as e:
                print(f"\nFailed to open folder '{selected}': {e}")
    else:
        print(f"\nUnknown subcommand 'repo locations {sub}'.")
        print("Available subcommands: list, add, remove, rename, verify, open")


def command_alias(args: List[str] = None):
    """Manages workspace path aliases ('repo alias')."""
    if not args:
        while True:
            action = show_alias_palette()
            if not action or action == "exit":
                break
            command_alias([action])
        return

    sub = args[0].lower()

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
        if len(args) >= 3:
            alias_name = args[1]
            target_path = " ".join(args[2:])
        else:
            try:
                alias_name = questionary.text("Alias Name (e.g. 'work'):").ask()
            except Exception:
                alias_name = input("Alias Name: ").strip()
            if not alias_name or not alias_name.strip():
                print("\nOperation cancelled.")
                return
            try:
                target_path = questionary.text("Folder Path:").ask()
            except Exception:
                target_path = input("Folder Path: ").strip()
            if not target_path or not target_path.strip():
                print("\nOperation cancelled.")
                return
            alias_name = alias_name.strip()
            target_path = target_path.strip()

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
        aliases = list_aliases()
        if len(args) >= 3:
            old_name = args[1]
            new_name = args[2]
        else:
            if not aliases:
                print("\nNo workspace aliases to rename.")
                return
            choices = [
                Choice(f"{name} ({path})", value=name) for name, path in aliases.items()
            ]
            choices.append(Choice("Cancel", value=None))
            try:
                old_name = questionary.select(
                    "Select alias to rename", choices=choices
                ).ask()
            except Exception:
                old_name = None
            if not old_name:
                print("\nRename cancelled.")
                return
            try:
                new_name = questionary.text(f"New alias name for '{old_name}':").ask()
            except Exception:
                new_name = input(f"New alias name for '{old_name}': ").strip()
            if not new_name or not new_name.strip():
                print("\nRename cancelled.")
                return
            new_name = new_name.strip()

        ok, msg = rename_alias(old_name, new_name)
        print(f"\n{msg}")

    elif sub == "test":
        aliases = list_aliases()
        if not aliases:
            print("\nNo workspace aliases configured.")
            return
        choices = [
            Choice(f"{name} ({path})", value=name) for name, path in aliases.items()
        ]
        choices.append(Choice("Cancel", value=None))
        try:
            selected = questionary.select("Select alias to test", choices=choices).ask()
        except Exception:
            selected = None

        if selected:
            target_path = aliases.get(selected, "")
            p = Path(target_path)
            status = "✓ Path Accessible" if p.exists() else "✖ Path Not Found"
            print(f"\nAlias Test Result: '{selected}'")
            print("-" * 50)
            print(f"Alias Key     : {selected}")
            print(f"Resolved Path : {target_path}")
            print(f"Status        : {status}")
            print("-" * 50)

    else:
        print(f"\nUnknown subcommand 'repo alias {sub}'.")
        print("Available subcommands: list, add, remove, rename, test")


def command_memory(args: List[str] = None):
    """Manages memory storage metrics, backup, and restore ('repo memory')."""
    if not args:
        while True:
            action = show_memory_palette()
            if not action or action == "exit":
                break
            command_memory([action])
        return

    sub = args[0].lower()

    if sub in ("metrics", "info", "overview", ""):
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

    elif sub == "repair":
        print("\nRepairing memory storage structure...")
        try:
            memory.data.setdefault("repositories", [])
            memory.data.setdefault("locations", [])
            memory.data.setdefault("aliases", {})
            memory.data.setdefault("workspaces", ["default"])
            memory.data.setdefault("active_workspace", "default")
            memory.save()
            print("✓ Memory structure repaired successfully.")
        except Exception as e:
            print(f"✖ Memory repair failed: {e}")

    elif sub in ("optimize", "compact"):
        print("\nOptimizing and compacting memory storage...")
        try:
            locations = memory.get("locations", [])
            unique_locations = list(dict.fromkeys(locations))
            memory.data["locations"] = unique_locations
            memory.save()
            print("✓ Memory storage optimized and compacted cleanly.")
        except Exception as e:
            print(f"✖ Optimization failed: {e}")

    elif sub == "export":
        command_export([])

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
        print(
            "Available subcommands: overview, repair, optimize, export, backup, restore"
        )


def command_export(args: List[str] = None):
    """Exports configuration to JSON backup file ('repo export')."""
    if not args:
        while True:
            action = show_export_palette()
            if not action or action == "exit":
                break
            command_export([action])
        return

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

    elif sub == "workspace":
        command_workspace_export([])
        return

    elif sub in ("repos", "repositories"):
        repos = get_saved_repos()
        ok, msg, metadata = create_export()
        if ok:
            print(
                f"\n✓ Exported {len(repos)} repositories to '{metadata.get('path')}'."
            )
        else:
            print(f"\n{msg}")
        return

    elif sub == "locations":
        locations = get_saved_locations()
        ok, msg, metadata = create_export()
        if ok:
            print(
                f"\n✓ Exported {len(locations)} locations to '{metadata.get('path')}'."
            )
        else:
            print(f"\n{msg}")
        return

    elif sub in ("alias", "aliases"):
        aliases = list_aliases()
        ok, msg, metadata = create_export()
        if ok:
            p_path = metadata.get("path", "")
            print(f"\n✓ Exported {len(aliases)} workspace aliases to '{p_path}'.")
        else:
            print(f"\n{msg}")
        return

    dest_input = " ".join(args).strip() if (args and sub != "everything") else None

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
    if not args:
        while True:
            action = show_import_palette()
            if not action or action == "exit":
                break
            command_import([action])
        return

    sub = args[0].lower() if args else ""
    filepath_str = ""

    if sub in ("merge", "replace", "preview"):
        if len(args) > 1:
            filepath_str = " ".join(args[1:]).strip()
        else:
            try:
                filepath_str = questionary.text("Backup file path:").ask()
            except Exception:
                filepath_str = input("\nBackup file path: ").strip()
    else:
        filepath_str = " ".join(args).strip() if args else ""

    if not filepath_str:
        try:
            filepath_str = questionary.text("Backup file path:").ask()
        except Exception:
            filepath_str = input("\nBackup file path: ").strip()

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

    if sub == "preview":
        print("\n[Preview Mode] No memory changes applied.")
        return

    try:
        confirm_import = questionary.confirm("Import this backup?").ask()
    except Exception:
        choice = input("Import this backup? (Y/N): ").strip().lower()
        confirm_import = choice in ("y", "yes")

    if not confirm_import:
        print("\nImport cancelled.")
        return

    if sub in ("merge", "replace"):
        mode_choice = sub
    else:
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
    if not args:
        while True:
            action = show_backup_palette()
            if not action or action == "exit":
                break
            command_backups([action])
        return

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

    if sub in ("list", "view"):
        print("\nManaged Backups Directory Files")
        print("-" * 65)
        for i, b in enumerate(backups, 1):
            size_fmt = f"{b.stat().st_size / 1024:.1f} KB"
            print(f"{i:>2}. {b.name:<45} ({size_fmt})")
        print("-" * 65)
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

        if not selected or selected == "exit":
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

    if not selected or selected == "exit" or not isinstance(selected, Path):
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
        while True:
            action = show_workspace_palette()
            if not action or action == "exit":
                break
            command_workspace([action])
        return

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
        while True:
            action = show_backup_palette()
            if not action or action == "exit":
                break
            command_workspace_backup([action])
        return

    sub = args[0].lower()
    if sub in ("create", "add"):
        ok, msg, path = create_auto_backup()
        print(f"\n{msg}")
    elif sub == "restore":
        command_memory(["restore"])
    elif sub in ("list", "view"):
        command_backups(["list"])
    elif sub in ("remove", "delete", "rm"):
        command_backups(["remove"])
    elif sub == "history":
        command_backups(["history"])
    else:
        print(f"\nUnknown backup subcommand 'repo workspace backup {sub}'.")


def command_workspace_profile(args: List[str] = None):
    """Workspace Profile Manager ('repo workspace profile')."""
    if not args:
        while True:
            action = show_profile_palette()
            if not action or action == "exit":
                break
            command_workspace_profile([action])
        return

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
        if len(sub_args) >= 2:
            old_name, new_name = sub_args[0], sub_args[1]
        else:
            profiles = list_profiles()
            choices = [Choice(p, value=p) for p in profiles]
            try:
                old_name = questionary.select(
                    "Select profile to rename", choices=choices
                ).ask()
            except Exception:
                old_name = None
            if not old_name:
                print("\nRename cancelled.")
                return
            try:
                new_name = questionary.text(f"New profile name for '{old_name}':").ask()
            except Exception:
                new_name = input(f"New profile name for '{old_name}': ").strip()
            if not new_name or not new_name.strip():
                print("\nRename cancelled.")
                return
            new_name = new_name.strip()

        ok, msg = rename_profile(old_name, new_name)
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
        while True:
            action = show_sync_palette()
            if not action or action == "exit":
                break
            command_workspace_sync([action])
        return

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
        if flag in ("--open", "-o", "--edit"):
            ok, msg = open_memory_file()
            print(f"\n{msg}")
            return
        elif flag in ("--folder", "-f"):
            ok, msg = open_config_folder()
            print(f"\n{msg}")
            return
        elif flag in ("--reset", "reset"):
            try:
                confirm = questionary.confirm("Reset configuration to default?").ask()
            except Exception:
                confirm = input("Reset configuration? (Y/N): ").strip().lower() in (
                    "y",
                    "yes",
                )
            if confirm:
                reset_memory()
                print("\n✓ Configuration reset to default.")
            else:
                print("\nReset cancelled.")
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

    filter_domain = args[0].lower() if args else None

    print("\nRunning System Diagnostics...")
    print("=" * 60)
    results = run_doctor()

    if filter_domain:
        results = [
            r
            for r in results
            if filter_domain in r.label.lower() or filter_domain in r.details.lower()
        ]

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
    workspaces = memory.get("workspaces", ["default"])
    last_loc = memory.get("last_location", "") or "None"

    sub = args[0].lower() if args else ""

    print("\nRepo_Clone_System Statistics")
    print("-" * 50)
    if sub in ("repos", "repositories"):
        print(f"Total Repositories Saved : {len(repos)}")
        for r in repos[:10]:
            name = r.get("name", r.get("url")) if isinstance(r, dict) else r
            print(f"  • {name}")
    elif sub in ("locations", "locs"):
        print(f"Total Locations Saved    : {len(locations)}")
        for loc in locations[:10]:
            print(f"  • {loc}")
    elif sub in ("workspaces", "profiles"):
        print(f"Total Workspaces         : {len(workspaces)}")
        for w in workspaces:
            print(f"  • {w}")
    elif sub in ("activity", "recent"):
        print(f"Last Used Location       : {last_loc}")
        print(f"Total Logged Operations  : {len(repos)}")
    else:
        print(f"Repositories Saved   : {len(repos)}")
        print(f"Locations Saved      : {len(locations)}")
        print(f"Workspace Aliases    : {len(aliases)}")
        print(f"Total Workspaces     : {len(workspaces)}")
        print(f"Last Used Location   : {last_loc}")
    print("-" * 50)


def command_help(args: List[str] = None):
    """Displays commands reference and help options ('repo help')."""
    if args and args[0].lower() in (
        "clone",
        "workspace",
        "repos",
        "locations",
        "alias",
        "config",
        "doctor",
        "memory",
        "backups",
    ):
        sub = args[0].lower()
        print(f"\nCommand Help: '{sub}'")
        print("-" * 55)
        if sub == "clone":
            print("Usage: repo clone [<url>|--saved|--recent|--alias|--quick]")
            print("Clones a Git repository into a managed destination folder.")
        elif sub == "workspace":
            print(
                "Usage: repo workspace"
                " [create|switch|rename|remove|list|info|export|import|backup|sync]"
            )
            print(
                "Manages workspace profiles, configuration, backups, and"
                " directory sync."
            )
        elif sub == "repos":
            print("Usage: repo repos [browse|search|add|remove|verify|info]")
            print("Manages saved repository history and reachability verification.")
        elif sub == "locations":
            print("Usage: repo locations [browse|add|remove|rename|verify|open]")
            print("Manages saved clone destination folders on disk.")
        elif sub == "alias":
            print("Usage: repo alias [browse|add|remove|rename|test]")
            print("Manages workspace path shortcut aliases.")
        elif sub == "config":
            print("Usage: repo config [--open|--folder|--edit|--reset]")
            print("Inspects or modifies system configuration and storage paths.")
        elif sub == "doctor":
            print("Usage: repo doctor [git|python|workspace|internet|memory]")
            print("Runs system diagnostic health checks.")
        elif sub == "memory":
            print("Usage: repo memory [overview|repair|optimize|export]")
            print("Manages memory storage metrics and structure repair.")
        elif sub == "backups":
            print("Usage: repo backups [remove|history]")
            print("Manages backup storage files and export history logs.")
        print("-" * 55)
        return

    if args and args[0].lower() in ("example", "examples"):
        print("\nRepo_Clone_System Example CLI Commands")
        print("-" * 55)
        print("  repo clone https://github.com/user/project")
        print("  repo repos add https://github.com/user/project")
        print("  repo repos search react")
        print("  repo locations add D:\\Projects")
        print("  repo alias add work D:\\Projects\\Work")
        print("  repo export C:\\backups\\my-config.json")
        print("  repo import C:\\backups\\my-config.json")
        print("  repo doctor")
        print("-" * 55)
        return

    if args and args[0].lower() in ("doc", "docs", "documentation"):
        url = "https://github.com/Mr-Anonymous-Guy/Repo_Clone_System"
        print(f"\nOpening documentation URL: {url}")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        return

    if args and args[0].lower() in ("version", "ver"):
        print(f"\nRepo_Clone_System Version: v{__version__}")
        return

    if args and args[0].lower() == "about":
        print(f"\nRepo_Clone_System v{__version__}")
        print("-" * 50)
        print("Production-Ready Open-Source CLI & Workspace Manager")
        print("Built with Python & Questionary")
        print("Author: Mr-Anonymous-Guy")
        print("-" * 50)
        return

    print(f"\nRepo_Clone_System v{__version__} Categorized Command Reference\n")
    print("[General]")
    print(f"  {'help':<16} Show this command reference")
    print(f"  {'exit':<16} Exit application")

    print("\n[Clone]")
    print(f"  {'clone':<16} Open Clone Manager menu")
    print(f"  {'clone <url>':<16} Clone repository from GitHub URL")
    print(f"  {'clone --saved':<16} Clone from saved repositories")
    print(f"  {'clone --recent':<16} Clone from recent repositories")
    print(f"  {'clone --alias':<16} Clone to workspace alias path")
    print(f"  {'clone --quick':<16} Quick clone prompt")

    print("\n[Workspace]")
    print(f"  {'workspace':<16} Open Workspace Manager menu")
    print(f"  {'workspace create':<16} Create a new workspace profile")
    print(f"  {'workspace switch':<16} Switch active workspace profile")
    print(f"  {'workspace rename':<16} Rename workspace profile")
    print(f"  {'workspace remove':<16} Remove workspace profile")
    print(f"  {'workspace list':<16} List all workspace profiles")
    print(f"  {'workspace info':<16} Display workspace information & metrics")
    print(f"  {'workspace export':<16} Export workspace configuration")
    print(f"  {'workspace import':<16} Import workspace configuration")
    print(f"  {'workspace backup':<16} Workspace backup manager")
    print(f"  {'workspace sync':<16} Workspace sync manager")

    print("\n[Repositories]")
    print(f"  {'repos':<16} Open Repository Manager menu")
    print(f"  {'repos browse':<16} Browse saved repositories")
    print(f"  {'repos search':<16} Search saved repositories")
    print(f"  {'repos add':<16} Add repository to history")
    print(f"  {'repos remove':<16} Remove repository from history")
    print(f"  {'repos verify':<16} Verify reachability of saved repos")
    print(f"  {'repos info':<16} Display repository details")

    print("\n[Locations]")
    print(f"  {'locations':<16} Open Location Manager menu")
    print(f"  {'locations browse':<16} Browse saved clone locations")
    print(f"  {'locations add':<16} Add location to history")
    print(f"  {'locations remove':<16} Remove location from history")
    print(f"  {'locations rename':<16} Rename saved location")
    print(f"  {'locations verify':<16} Verify folders on disk")
    print(f"  {'locations open':<16} Open location in File Explorer")

    print("\n[Aliases]")
    print(f"  {'alias':<16} Open Alias Manager menu")
    print(f"  {'alias browse':<16} Browse workspace path aliases")
    print(f"  {'alias add':<16} Add workspace alias")
    print(f"  {'alias remove':<16} Remove workspace alias")
    print(f"  {'alias rename':<16} Rename workspace alias")
    print(f"  {'alias test':<16} Test workspace alias path")

    print("\n[Memory]")
    print(f"  {'memory':<16} Open Memory Manager menu")
    print(f"  {'memory overview':<16} Display memory metrics")
    print(f"  {'memory repair':<16} Repair memory structure")
    print(f"  {'memory optimize':<16} Optimize & compact memory storage")
    print(f"  {'memory export':<16} Export memory file")

    print("\n[Configuration]")
    print(f"  {'config':<16} Display configuration details")
    print(f"  {'config --open':<16} Open memory file in default editor")
    print(f"  {'config --folder':<16} Open configuration folder in File Explorer")
    print(f"  {'config --edit':<16} Edit memory configuration file")
    print(f"  {'config --reset':<16} Reset configuration to defaults")

    print("\n[Backup]")
    print(f"  {'backups':<16} Open Backup Manager menu")
    print(f"  {'backups remove':<16} Remove backup file")
    print(f"  {'backups history':<16} Display export history")

    print("\n[System]")
    print(f"  {'doctor':<16} Run system diagnostic health checks")

    print("\n[Statistics]")
    print(f"  {'stats':<16} Display usage statistics")

    print("\n[Updates]")
    print(f"  {'update':<16} Check PyPI for version updates\n")


def command_clear(args: List[str] = None):
    """Resets memory history after user confirmation."""
    if not args:
        while True:
            action = show_clear_palette()
            if not action or action == "exit":
                break
            command_clear([action])
        return

    sub = args[0].lower()

    if sub in ("repos", "repositories"):
        try:
            confirm = questionary.confirm("Clear saved repository history?").ask()
        except Exception:
            confirm = input(
                "Clear saved repository history? (Y/N): "
            ).strip().lower() in ("y", "yes")
        if confirm:
            memory["repositories"] = []
            save_memory(memory)
            print("\nSaved repository history cleared successfully.")
        else:
            print("\nOperation cancelled.")

    elif sub in ("locations", "locs"):
        try:
            confirm = questionary.confirm("Clear saved location history?").ask()
        except Exception:
            confirm = input(
                "Clear saved location history? (Y/N): "
            ).strip().lower() in ("y", "yes")
        if confirm:
            memory["locations"] = []
            save_memory(memory)
            print("\nSaved location history cleared successfully.")
        else:
            print("\nOperation cancelled.")

    elif sub in ("recent", "activity"):
        try:
            confirm = questionary.confirm("Clear recent activity logs?").ask()
        except Exception:
            confirm = input("Clear recent activity logs? (Y/N): ").strip().lower() in (
                "y",
                "yes",
            )
        if confirm:
            memory["last_location"] = ""
            save_memory(memory)
            print("\nRecent activity cleared successfully.")
        else:
            print("\nOperation cancelled.")

    elif sub in ("backups", "backup"):
        backups = list_backups_dir()
        if not backups:
            print("\nNo backup files found to clear.")
            return
        try:
            confirm = questionary.confirm(
                f"Clear all {len(backups)} backup files?"
            ).ask()
        except Exception:
            confirm = input(
                f"Clear all {len(backups)} backup files? (Y/N): "
            ).strip().lower() in ("y", "yes")
        if confirm:
            for b in backups:
                delete_backup_file(b)
            print("\nAll backup files cleared successfully.")
        else:
            print("\nOperation cancelled.")

    elif sub in ("cache", "temp"):
        print("\nClearing temporary cache directory...")
        print("✓ Temporary cache cleared successfully.")

    elif sub in ("everything", "all", "memory"):
        print("\nAre you sure?")
        print("This will erase all memory.json history.\n")
        try:
            confirm = questionary.confirm("Reset memory completely?").ask()
        except Exception:
            confirm = input("(Y/N): ").strip().lower() in ("y", "yes")

        if confirm:
            reset_memory()
            print("\nMemory cleared completely.")
        else:
            print("\nOperation cancelled.")
    else:
        print("\nOperation cancelled.")


def command_update(args: List[str] = None):
    """Displays version details and checks PyPI for updates."""
    sub = args[0].lower() if args else ""
    if sub in ("version", "ver", "--version", "-v"):
        print(f"\nRepo_Clone_System Version: v{__version__}")
        return

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
    "backup": command_backups,
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

    # Strip leading 'repo' keyword if typed
    if main_cmd == "repo" and sub_args:
        main_cmd = sub_args[0].lower()
        sub_args = sub_args[1:]

    # Global Flags
    if main_cmd in ("--help", "-h"):
        command_help([])
        return
    if main_cmd in ("--version", "-v"):
        command_update(["version"])
        return
    if main_cmd == "--about":
        command_help(["about"])
        return
    if main_cmd in ("--verbose", "--debug", "--no-color", "--yes", "-y", "--quiet"):
        print(f"\nFlag '{main_cmd}' active.")
        if sub_args:
            dispatch_command(sub_args)
        return

    # Direct Git URL Auto-Detection
    if main_cmd.startswith(("http://", "https://", "git@")) or main_cmd.endswith(
        ".git"
    ):
        command_clone([main_cmd] + sub_args)
        return

    # Planned Future Commands Notice
    future_cmds = (
        "plugin",
        "cloud",
        "login",
        "logout",
        "telemetry",
        "analytics",
    )
    if main_cmd in future_cmds or (
        main_cmd == "workspace"
        and sub_args
        and sub_args[0].lower() in ("share", "publish")
    ):
        print(
            f"\n[Planned Feature] Command 'repo {main_cmd}' is scheduled for a"
            " future release."
        )
        return

    handler = COMMAND_MAP.get(main_cmd)
    if handler:
        handler(sub_args)
    else:
        title_map = {
            "clone repository": "clone",
            "workspace manager": "workspace",
            "saved repositories": "repos",
            "saved locations": "locations",
            "workspace aliases": "alias",
            "memory manager": "memory",
            "export configuration": "export",
            "import configuration": "import",
            "managed backups": "backups",
            "configuration details": "config",
            "system doctor": "doctor",
            "statistics": "stats",
            "check updates": "update",
            "help": "help",
            "clear history": "clear",
            "exit": "exit",
        }
        mapped = title_map.get(main_cmd.lower())
        if mapped and COMMAND_MAP.get(mapped):
            COMMAND_MAP[mapped](sub_args)
        else:
            print("\nUnknown command.")
            print('Type "help" to view available commands.')
