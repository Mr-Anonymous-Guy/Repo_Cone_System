import datetime
import json
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple

from repo_clone_system import __version__
from repo_clone_system.services.backup_service import (
    CURRENT_SCHEMA_VERSION,
    _format_size,
    validate_backup_file,
)
from repo_clone_system.services.profile_service import get_active_profile_name
from repo_clone_system.services.sync_providers.local_folder_provider import (
    LocalFolderSyncProvider,
)
from repo_clone_system.storage.memory import (
    get_config_dir,
    load_memory,
)


def get_sync_config_file() -> Path:
    """Returns absolute path to sync_config.json."""
    return get_config_dir() / "sync_config.json"


def get_sync_config() -> dict:
    """Reads sync_config.json configuration."""
    s_file = get_sync_config_file()
    default_cfg = {
        "provider": "local_folder",
        "sync_folder": "",
        "last_sync_export": None,
        "last_sync_import": None,
    }

    if not s_file.exists():
        save_sync_config(default_cfg)
        return default_cfg

    try:
        with open(s_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for k, v in default_cfg.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        pass

    return default_cfg


def save_sync_config(data: dict):
    """Saves data to sync_config.json."""
    s_file = get_sync_config_file()
    get_config_dir().mkdir(parents=True, exist_ok=True)
    with open(s_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def configure_sync_folder(folder_path_str: str) -> Tuple[bool, str]:
    """Configures the default sync folder location."""
    clean_path = folder_path_str.strip().strip('"')
    if not clean_path:
        return False, "Sync folder path cannot be empty."

    p = Path(clean_path)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return False, f"Failed to create sync folder '{p}': {e}"

    cfg = get_sync_config()
    cfg["sync_folder"] = str(p.resolve())
    cfg["provider"] = "local_folder"
    save_sync_config(cfg)

    return True, f"✓ Configured sync folder to '{p.resolve()}'."


def export_sync() -> Tuple[bool, str, Optional[Path]]:
    """Exports active workspace to configured sync directory."""
    cfg = get_sync_config()
    sync_folder = cfg.get("sync_folder")

    if not sync_folder:
        return (
            False,
            "No sync folder configured. Run 'repo workspace sync config <path>' first.",
            None,
        )

    provider = LocalFolderSyncProvider(sync_folder)
    if not provider.is_configured():
        return False, f"Sync directory '{sync_folder}' is not accessible.", None

    current_mem = load_memory()
    active_profile = get_active_profile_name()

    export_payload = {
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

    ok, msg, target_path = provider.export_sync(export_payload)
    if ok:
        cfg["last_sync_export"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_sync_config(cfg)

    return ok, msg, target_path


def locate_latest_sync_backup() -> Tuple[bool, str, Optional[Path], Optional[dict]]:
    """Locates newest backup in configured sync directory and returns validated data."""
    cfg = get_sync_config()
    sync_folder = cfg.get("sync_folder")

    if not sync_folder:
        return (
            False,
            "No sync folder configured. Run 'repo workspace sync config <path>' first.",
            None,
            None,
        )

    provider = LocalFolderSyncProvider(sync_folder)
    ok, msg, latest_path = provider.locate_latest_backup()
    if not ok or not latest_path:
        return False, msg, None, None

    v_ok, v_msg, data = validate_backup_file(latest_path)
    if not v_ok:
        return False, f"Latest sync backup is invalid: {v_msg}", latest_path, None

    return True, f"Found latest backup '{latest_path.name}'.", latest_path, data


def get_sync_status() -> dict:
    """Returns details and metrics for sync status."""
    cfg = get_sync_config()
    sync_folder = cfg.get("sync_folder", "Not configured")
    active_profile = get_active_profile_name()

    latest_file = "None"
    latest_size = "None"

    if sync_folder and Path(sync_folder).exists():
        provider = LocalFolderSyncProvider(sync_folder)
        ok, msg, latest_path = provider.locate_latest_backup()
        if ok and latest_path:
            latest_file = latest_path.name
            try:
                latest_size = _format_size(latest_path.stat().st_size)
            except Exception:
                latest_size = "Unknown"

    return {
        "sync_folder": sync_folder if sync_folder else "Not configured",
        "provider": cfg.get("provider", "local_folder"),
        "active_profile": active_profile,
        "latest_backup": latest_file,
        "backup_size": latest_size,
        "last_export": cfg.get("last_sync_export", "Never"),
        "last_import": cfg.get("last_sync_import", "Never"),
    }
