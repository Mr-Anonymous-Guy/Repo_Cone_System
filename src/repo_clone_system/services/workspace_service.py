import datetime
import json
import platform
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple

from repo_clone_system import __version__
from repo_clone_system.services.backup_service import (
    CURRENT_SCHEMA_VERSION,
    _format_size,
    list_backups_dir,
    log_export_history,
)
from repo_clone_system.services.profile_service import get_active_profile_name
from repo_clone_system.storage.memory import (
    get_memory_file,
    load_memory,
)


def export_workspace(
    dest_input: Optional[str] = None,
    prompt_mkdir_callback: Optional[Callable[[str], bool]] = None,
) -> Tuple[bool, str, dict]:
    """Exports complete active workspace configuration to a JSON backup file."""
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    default_filename = f"workspace-backup-{timestamp_str}.json"

    if not dest_input or not dest_input.strip():
        target_folder = Path.cwd() / "workspace-backups"
        target_folder.mkdir(parents=True, exist_ok=True)
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

    active_profile = get_active_profile_name()
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
        "workspace_name": active_profile,
        "profile": active_profile,
        "memory": current_mem,
    }

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=4)

        size_bytes = target_file.stat().st_size
        size_fmt = _format_size(size_bytes)

        metadata = {
            "path": str(target_file),
            "workspace_name": active_profile,
            "repo_count": len(repos),
            "location_count": len(locations),
            "alias_count": len(aliases),
            "size_fmt": size_fmt,
            "size_bytes": size_bytes,
        }

        log_export_history(
            target_file, size_fmt, len(repos), len(locations), len(aliases)
        )

        return (
            True,
            f"✓ Workspace exported successfully to '{target_file}'.",
            metadata,
        )
    except Exception as e:
        return False, f"Failed to export workspace to '{target_file}': {e}", {}


def get_workspace_info() -> dict:
    """Returns detailed information and metrics for the active workspace."""
    active_profile = get_active_profile_name()
    current_mem = load_memory()
    repos = current_mem.get("repositories", [])
    locations = current_mem.get("locations", [])
    aliases = current_mem.get("aliases", {})
    mem_file = get_memory_file()

    file_size_bytes = mem_file.stat().st_size if mem_file.exists() else 0
    size_fmt = _format_size(file_size_bytes)

    backups = list_backups_dir()

    return {
        "workspace_name": active_profile,
        "active_profile": active_profile,
        "repo_count": len(repos),
        "location_count": len(locations),
        "alias_count": len(aliases),
        "memory_size": size_fmt,
        "backup_count": len(backups),
        "schema_version": CURRENT_SCHEMA_VERSION,
        "package_version": __version__,
        "platform": f"{platform.system()} {platform.release()}",
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
    }
