import datetime
import json
import shutil
from pathlib import Path
from typing import List, Tuple

from repo_clone_system.services.repo_service import get_saved_repos
from repo_clone_system.storage.memory import (
    get_config_dir,
    get_memory_file,
    load_memory,
    memory,
    save_memory,
)


def get_memory_metrics() -> dict:
    """Calculates statistics and metrics about memory storage."""
    memory_file = get_memory_file()
    repos = get_saved_repos()
    locations = memory.get("locations", [])
    aliases = memory.get("aliases", {})

    file_size_bytes = memory_file.stat().st_size if memory_file.exists() else 0
    if file_size_bytes < 1024:
        size_fmt = f"{file_size_bytes} B"
    else:
        size_fmt = f"{file_size_bytes / 1024:.2f} KB"

    oldest = repos[0]["name"] if repos else "None"
    newest = repos[-1]["name"] if repos else "None"

    return {
        "total_repos": len(repos),
        "total_locations": len(locations),
        "total_aliases": len(aliases),
        "newest_entry": newest,
        "oldest_entry": oldest,
        "memory_file_size": size_fmt,
        "memory_file_bytes": file_size_bytes,
        "memory_file_path": str(memory_file),
    }


def backup_memory() -> Tuple[bool, str, Path]:
    """Creates a timestamped backup copy of memory.json in the config directory."""
    config_dir = get_config_dir()
    memory_file = get_memory_file()
    config_dir.mkdir(parents=True, exist_ok=True)

    if not memory_file.exists():
        save_memory(memory)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")
    backup_filename = f"memory-backup-{timestamp}.json"
    backup_path = config_dir / backup_filename

    try:
        shutil.copy2(memory_file, backup_path)
        return True, f"✓ Created backup '{backup_filename}'.", backup_path
    except Exception as e:
        return False, f"Failed to create backup: {e}", None


def list_backups() -> List[Path]:
    """Returns a sorted list of memory backup files found in the config directory."""
    config_dir = get_config_dir()
    if not config_dir.exists():
        return []

    backups = list(config_dir.glob("memory-backup-*.json"))
    backups.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return backups


def restore_memory(backup_path: Path) -> Tuple[bool, str]:
    """Restores memory.json from a backup file."""
    memory_file = get_memory_file()

    if not backup_path.exists():
        return False, f"Backup file '{backup_path}' does not exist."

    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate basic structure
        if not isinstance(data, dict):
            return False, "Invalid backup file structure."

        shutil.copy2(backup_path, memory_file)

        # Update live memory reference
        reloaded = load_memory()
        memory.clear()
        memory.update(reloaded)

        return True, f"✓ Restored memory from '{backup_path.name}'."
    except Exception as e:
        return False, f"Failed to restore memory: {e}"
