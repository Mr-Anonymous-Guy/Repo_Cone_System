import json
import os
import shutil
import sys
from pathlib import Path

# ======================================================
# OS-Specific Configuration Directory Resolution
# ======================================================


def get_config_dir() -> Path:
    """Returns platform-specific configuration directory for RepoCloneSystem.

    Windows : %APPDATA%\\RepoCloneSystem
    macOS   : ~/Library/Application Support/RepoCloneSystem
    Linux   : ~/.config/repo-clone-system or $XDG_CONFIG_HOME/repo-clone-system
    """
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            base = Path(appdata)
        else:
            base = Path.home() / "AppData" / "Roaming"
        return base / "RepoCloneSystem"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "RepoCloneSystem"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / "repo-clone-system"
        return Path.home() / ".config" / "repo-clone-system"


def get_memory_file() -> Path:
    """Returns the absolute path to memory.json for the active profile."""
    config_dir = get_config_dir()
    profiles_file = config_dir / "profiles.json"
    if profiles_file.exists():
        try:
            with open(profiles_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            active = data.get("active_profile", "Default")
            if active and active.lower() != "default":
                return config_dir / "profiles" / active / "memory.json"
        except Exception:
            pass
    return config_dir / "memory.json"


CONFIG_DIR = get_config_dir()
MEMORY_FILE = get_memory_file()

DEFAULT_MEMORY = {
    "last_location": "",
    "locations": [],
    "repositories": [],
    "aliases": {},
}


def _migrate_legacy_memory(target_file: Path):
    """Migrates memory.json from legacy package or root location."""
    if target_file.exists():
        return

    # Check potential legacy locations
    base_dir = Path(__file__).resolve().parent.parent
    candidates = [
        base_dir / "storage" / "memory.json",
        base_dir.parent.parent / "memory.json",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.resolve() != target_file.resolve():
            try:
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(candidate, target_file)
                return
            except Exception:
                pass


def load_memory() -> dict:
    """Load memory.json from OS config directory with migration and fallback."""
    config_dir = get_config_dir()
    memory_file = get_memory_file()

    config_dir.mkdir(parents=True, exist_ok=True)
    _migrate_legacy_memory(memory_file)

    if not memory_file.exists():
        new_mem = DEFAULT_MEMORY.copy()
        save_memory(new_mem)
        return new_mem

    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Ensure all required default keys exist
        for key, val in DEFAULT_MEMORY.items():
            if key not in data:
                data[key] = val.copy() if isinstance(val, (list, dict)) else val

        return data

    except Exception:
        # If corrupted, preserve defaults safely
        new_mem = DEFAULT_MEMORY.copy()
        save_memory(new_mem)
        return new_mem


def save_memory(memory_data: dict):
    """Saves memory data dictionary to memory.json."""
    config_dir = get_config_dir()
    memory_file = get_memory_file()
    config_dir.mkdir(parents=True, exist_ok=True)

    with open(memory_file, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=4)


def reset_memory():
    """Resets memory dict to DEFAULT_MEMORY and overwrites memory.json."""
    global memory
    memory.clear()
    memory.update(
        {
            "last_location": "",
            "locations": [],
            "repositories": [],
            "aliases": {},
        }
    )
    config_dir = get_config_dir()
    for fname in ("profiles.json", "sync_config.json"):
        f_path = config_dir / fname
        if f_path.exists():
            try:
                f_path.unlink()
            except Exception:
                pass
    save_memory(memory)


memory = load_memory()
