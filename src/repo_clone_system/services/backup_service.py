import datetime
import json
import platform
import sys
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from repo_clone_system import __version__
from repo_clone_system.storage.memory import (
    get_config_dir,
    load_memory,
    memory,
    save_memory,
)

CURRENT_SCHEMA_VERSION = 1
INITIAL_MEMORY_HASH: Optional[str] = None


def record_initial_memory_hash():
    """Records initial state of memory for exit change detection."""
    global INITIAL_MEMORY_HASH
    try:
        current_mem = load_memory()
        INITIAL_MEMORY_HASH = json.dumps(current_mem, sort_keys=True)
    except Exception:
        INITIAL_MEMORY_HASH = None


def get_backups_dir() -> Path:
    """Returns platform-specific Backups directory inside config directory."""
    backups_dir = get_config_dir() / "Backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir


def _format_size(size_bytes: int) -> str:
    """Formats byte size into readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def create_export(
    dest_input: Optional[str] = None,
    prompt_mkdir_callback: Optional[Callable[[str], bool]] = None,
) -> Tuple[bool, str, dict]:
    """Exports complete configuration to a JSON backup file."""
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    default_filename = f"repo-backup-{timestamp_str}.json"

    if not dest_input or not dest_input.strip():
        target_folder = Path.cwd()
        target_file = target_folder / default_filename
    else:
        clean_input = dest_input.strip().strip('"')
        path_obj = Path(clean_input)

        if clean_input.lower().endswith(".json"):
            target_file = path_obj
            target_folder = path_obj.parent
        else:
            target_folder = path_obj
            target_file = target_folder / default_filename

    # Handle missing destination folder
    if not target_folder.exists():
        if prompt_mkdir_callback:
            approved = prompt_mkdir_callback(str(target_folder))
            if not approved:
                return (
                    False,
                    f"Export cancelled: Folder '{target_folder}' does not exist.",
                    {},
                )

        try:
            target_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            return (
                False,
                f"Failed to create folder '{target_folder}': {e}",
                {},
            )

    current_mem = load_memory()
    repos = current_mem.get("repositories", [])
    locations = current_mem.get("locations", [])
    aliases = current_mem.get("aliases", {})

    export_data = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo_clone_system_version": __version__,
        "platform": f"{platform.system()} {platform.release()}",
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        "memory": current_mem,
    }

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4)

        size_bytes = target_file.stat().st_size
        size_fmt = _format_size(size_bytes)

        metadata = {
            "path": str(target_file),
            "repo_count": len(repos),
            "location_count": len(locations),
            "alias_count": len(aliases),
            "size_fmt": size_fmt,
            "size_bytes": size_bytes,
        }

        log_export_history(
            target_file, size_fmt, len(repos), len(locations), len(aliases)
        )

        return True, f"✓ Backup created successfully at '{target_file}'.", metadata
    except Exception as e:
        return False, f"Failed to write export file '{target_file}': {e}", {}


def validate_backup_file(filepath: Path) -> Tuple[bool, str, dict]:
    """Validates backup file existence, JSON structure, and schema."""
    if not filepath.exists() or not filepath.is_file():
        return False, f"Backup file '{filepath}' does not exist.", {}

    try:
        size_bytes = filepath.stat().st_size
        if size_bytes == 0:
            return False, f"Backup file '{filepath.name}' is empty (0 bytes).", {}
    except Exception:
        pass

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return (
            False,
            f"Invalid JSON syntax in backup file '{filepath.name}': {e}",
            {},
        )
    except Exception as e:
        return False, f"Failed to read backup file '{filepath.name}': {e}", {}

    if not isinstance(data, dict):
        return False, "Backup file payload is not a valid JSON object.", {}

    # Support raw legacy memory files or structured backups
    if "schema_version" not in data and "memory" not in data:
        if "repositories" in data or "locations" in data:
            # Interpret as raw legacy memory object
            data = {
                "schema_version": 1,
                "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "repo_clone_system_version": __version__,
                "memory": data,
            }
        else:
            return False, "File is not a valid Repo_Clone_System backup.", {}

    schema_ver = data.get("schema_version", 1)
    if not isinstance(schema_ver, int):
        return False, "Invalid 'schema_version' field in backup file.", {}

    if schema_ver > CURRENT_SCHEMA_VERSION:
        return (
            False,
            f"Unsupported schema version {schema_ver}. "
            "Please update Repo_Clone_System.",
            {},
        )

    memory_payload = data.get("memory")
    if not isinstance(memory_payload, dict):
        return False, "Backup file is missing valid 'memory' payload.", {}

    data = migrate_backup_data(data)
    return True, "Backup file is valid.", data


def migrate_backup_data(data: dict) -> dict:
    """Infrastructure for schema migrations across versions."""

    memory_payload = data.get("memory", {})

    if "repositories" not in memory_payload:
        memory_payload["repositories"] = []
    if "locations" not in memory_payload:
        memory_payload["locations"] = []
    if "aliases" not in memory_payload:
        memory_payload["aliases"] = {}
    if "last_location" not in memory_payload:
        memory_payload["last_location"] = ""

    data["memory"] = memory_payload
    return data


def get_backup_summary(data: dict) -> dict:
    """Extracts high-level summary metrics from a validated backup payload."""
    created_at = data.get("created_at", "Unknown")
    version = data.get("repo_clone_system_version", "Unknown")
    schema_ver = data.get("schema_version", 1)

    mem = data.get("memory", {})
    repos_count = len(mem.get("repositories", []))
    locs_count = len(mem.get("locations", []))
    aliases_count = len(mem.get("aliases", {}))

    return {
        "created_at": created_at,
        "version": version,
        "schema_version": schema_ver,
        "repo_count": repos_count,
        "location_count": locs_count,
        "alias_count": aliases_count,
    }


def create_auto_backup() -> Tuple[bool, str, Path]:
    """Creates an automatic pre-import safety backup in the Backups directory."""
    backups_dir = get_backups_dir()
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"auto-backup-before-import-{timestamp_str}.json"
    target_path = backups_dir / filename

    counter = 1
    while target_path.exists():
        filename = f"auto-backup-before-import-{timestamp_str}_{counter}.json"
        target_path = backups_dir / filename
        counter += 1

    current_mem = load_memory()
    export_data = {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "repo_clone_system_version": __version__,
        "platform": f"{platform.system()} {platform.release()}",
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        "memory": current_mem,
    }

    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4)
        return True, f"Created automatic safety backup '{filename}'.", target_path
    except Exception as e:
        return False, f"Failed to create automatic safety backup: {e}", None


def perform_import(data: dict, mode: str = "merge") -> Tuple[bool, str]:
    """Performs import into live memory using either 'merge' or 'replace' mode."""
    backup_memory = data.get("memory", {})

    if mode == "replace":
        auto_ok, auto_msg, auto_path = create_auto_backup()
        memory.clear()
        memory.update(backup_memory)
        save_memory(memory)
        if auto_ok:
            return (
                True,
                f"✓ Successfully replaced memory. Safety backup: '{auto_path.name}'.",
            )
        return True, "✓ Successfully replaced memory state."

    # Merge mode
    current_mem = load_memory()
    curr_repos = current_mem.get("repositories", [])
    curr_locs = current_mem.get("locations", [])
    curr_aliases = current_mem.get("aliases", {})

    new_repos = backup_memory.get("repositories", [])
    new_locs = backup_memory.get("locations", [])
    new_aliases = backup_memory.get("aliases", {})

    def _repo_url(r):
        return r.get("url") if isinstance(r, dict) else r

    existing_urls = {_repo_url(r) for r in curr_repos if _repo_url(r)}
    added_repos_count = 0
    for r in new_repos:
        u = _repo_url(r)
        if u and u not in existing_urls:
            curr_repos.append(r)
            existing_urls.add(u)
            added_repos_count += 1

    existing_locs = {str(Path(loc_item).resolve()) for loc_item in curr_locs}
    added_locs_count = 0
    for loc_item in new_locs:
        try:
            norm = str(Path(loc_item).resolve())
        except Exception:
            norm = str(loc_item)
        if norm not in existing_locs and loc_item not in curr_locs:
            curr_locs.append(loc_item)
            existing_locs.add(norm)
            added_locs_count += 1

    added_aliases_count = 0
    for name, path in new_aliases.items():
        if name not in curr_aliases:
            curr_aliases[name] = path
            added_aliases_count += 1

    current_mem["repositories"] = curr_repos
    current_mem["locations"] = curr_locs
    current_mem["aliases"] = curr_aliases

    if backup_memory.get("last_location") and not current_mem.get("last_location"):
        current_mem["last_location"] = backup_memory["last_location"]

    memory.clear()
    memory.update(current_mem)
    save_memory(memory)

    msg = (
        f"✓ Merge complete. Added {added_repos_count} repos, "
        f"{added_locs_count} locations, {added_aliases_count} aliases."
    )
    return True, msg


def list_backups_dir() -> List[Path]:
    """Returns sorted list of all backup files in Backups/ directory."""
    backups_dir = get_backups_dir()
    if not backups_dir.exists():
        return []

    files = list(backups_dir.glob("*.json"))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def delete_backup_file(filepath: Path) -> Tuple[bool, str]:
    """Deletes a backup file from the Backups directory."""
    if not filepath.exists():
        return False, f"Backup file '{filepath}' does not exist."

    try:
        filepath.unlink()
        return True, f"✓ Deleted backup '{filepath.name}'."
    except Exception as e:
        return False, f"Failed to delete backup '{filepath.name}': {e}"


def get_export_history_file() -> Path:
    """Returns absolute path to export_history.json."""
    return get_config_dir() / "export_history.json"


def log_export_history(
    dest_path: Path,
    size_fmt: str,
    repo_count: int,
    loc_count: int,
    alias_count: int,
):
    """Appends an export event to export_history.json."""
    history_file = get_export_history_file()
    history = get_export_history()

    entry = {
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "destination": str(dest_path),
        "size": size_fmt,
        "repositories": repo_count,
        "locations": loc_count,
        "aliases": alias_count,
    }

    history.insert(0, entry)
    try:
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
    except Exception:
        pass


def get_export_history() -> List[dict]:
    """Reads and returns export history list."""
    history_file = get_export_history_file()
    if not history_file.exists():
        return []

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def rotate_auto_backups(max_keep: int = 20):
    """Keep only max_keep newest automatic backups in Backups directory.

    Manual exports (workspace-backup-*, repo-backup-*, custom files) are NEVER deleted.
    """
    backups_dir = get_backups_dir()
    if not backups_dir.exists():
        return

    auto_files = [
        f for f in backups_dir.glob("*.json") if f.name.startswith("auto-backup-")
    ]
    auto_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    if len(auto_files) > max_keep:
        to_delete = auto_files[max_keep:]
        for f in to_delete:
            try:
                f.unlink()
            except Exception:
                pass


def auto_backup_on_exit_if_changed():
    """Triggered on CLI exit.

    Creates auto-backup if memory changed and rotates auto-backups to 20.
    """
    global INITIAL_MEMORY_HASH
    try:
        current_mem = load_memory()
        curr_json = json.dumps(current_mem, sort_keys=True)
        if INITIAL_MEMORY_HASH is not None and curr_json != INITIAL_MEMORY_HASH:
            create_auto_backup()
            rotate_auto_backups(max_keep=20)
    except Exception:
        pass
