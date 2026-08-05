import json
import re
import shutil
from pathlib import Path
from typing import List, Tuple

from repo_clone_system.storage.memory import (
    DEFAULT_MEMORY,
    get_config_dir,
    get_memory_file,
    memory,
    save_memory,
)

PRESET_PROFILES = ["Default", "College", "Office", "Laptop", "Personal"]


def get_profiles_file() -> Path:
    """Returns path to profiles.json configuration file."""
    return get_config_dir() / "profiles.json"


def get_profiles_dir() -> Path:
    """Returns path to profiles directory."""
    p_dir = get_config_dir() / "profiles"
    p_dir.mkdir(parents=True, exist_ok=True)
    return p_dir


def get_profile_memory_file(profile_name: str) -> Path:
    """Returns memory.json path for a specific profile name."""
    if profile_name.lower() == "default":
        return get_memory_file()
    return get_profiles_dir() / profile_name / "memory.json"


def load_profiles_config() -> dict:
    """Loads profiles.json configuration."""
    p_file = get_profiles_file()
    default_config = {
        "active_profile": "Default",
        "profiles": PRESET_PROFILES.copy(),
    }

    if not p_file.exists():
        save_profiles_config(default_config)
        return default_config

    try:
        with open(p_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return default_config

        if "active_profile" not in data:
            data["active_profile"] = "Default"
        if "profiles" not in data or not isinstance(data["profiles"], list):
            data["profiles"] = PRESET_PROFILES.copy()

        # Ensure active_profile is in profiles list
        if data["active_profile"] not in data["profiles"]:
            data["profiles"].append(data["active_profile"])

        return data
    except Exception:
        save_profiles_config(default_config)
        return default_config


def save_profiles_config(data: dict):
    """Saves data to profiles.json."""
    p_file = get_profiles_file()
    get_config_dir().mkdir(parents=True, exist_ok=True)
    with open(p_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_active_profile_name() -> str:
    """Returns currently active profile name."""
    config = load_profiles_config()
    return config.get("active_profile", "Default")


def list_profiles() -> List[str]:
    """Returns list of all available profile names."""
    config = load_profiles_config()
    profile_list = list(config.get("profiles", PRESET_PROFILES))
    for p in PRESET_PROFILES:
        if p not in profile_list:
            profile_list.append(p)
    return profile_list


def create_profile(profile_name: str, copy_current: bool = False) -> Tuple[bool, str]:
    """Creates a new workspace profile."""
    clean_name = profile_name.strip()
    if not clean_name:
        return False, "Profile name cannot be empty."

    if not re.match(r"^[a-zA-Z0-9_\-]+$", clean_name):
        return (
            False,
            "Profile name must contain only letters, numbers, underscores, or hyphens.",
        )

    config = load_profiles_config()
    existing_profiles = [p.lower() for p in config.get("profiles", [])]
    if clean_name.lower() in existing_profiles:
        return False, f"Profile '{clean_name}' already exists."

    target_file = get_profile_memory_file(clean_name)
    target_file.parent.mkdir(parents=True, exist_ok=True)

    if copy_current:
        current_data = memory.copy()
    else:
        current_data = DEFAULT_MEMORY.copy()

    try:
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=4)
    except Exception as e:
        return False, f"Failed to initialize profile memory file: {e}"

    config["profiles"].append(clean_name)
    save_profiles_config(config)
    return True, f"✓ Created profile '{clean_name}' successfully."


def switch_profile(target_name: str) -> Tuple[bool, str]:
    """Switches active profile and hot-reloads memory without restarting CLI."""
    clean_name = target_name.strip()
    config = load_profiles_config()
    current_active = config.get("active_profile", "Default")

    if clean_name == current_active:
        return True, f"Profile '{clean_name}' is already active."

    available = list_profiles()
    match = None
    for p in available:
        if p.lower() == clean_name.lower():
            match = p
            break

    if not match:
        # If it's a preset profile that hasn't been created yet, create it
        if clean_name in PRESET_PROFILES:
            ok, msg = create_profile(clean_name)
            if not ok:
                return False, msg
            match = clean_name
        else:
            return False, f"Profile '{clean_name}' does not exist."

    # Step 1: Save current live memory to current profile's memory file
    curr_mem_file = get_profile_memory_file(current_active)
    curr_mem_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(curr_mem_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=4)
    except Exception:
        pass

    # Step 2: Update active_profile in config
    config["active_profile"] = match
    if match not in config["profiles"]:
        config["profiles"].append(match)
    save_profiles_config(config)

    # Step 3: Load target profile's memory
    target_mem_file = get_profile_memory_file(match)
    new_data = DEFAULT_MEMORY.copy()
    if target_mem_file.exists():
        try:
            with open(target_mem_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                for k, v in DEFAULT_MEMORY.items():
                    if k not in loaded:
                        loaded[k] = v.copy() if isinstance(v, (list, dict)) else v
                new_data = loaded
        except Exception:
            pass

    # Step 4: Hot reload live memory reference
    memory.clear()
    memory.update(new_data)
    save_memory(memory)

    return True, f"✓ Switched active profile to '{match}'."


def rename_profile(old_name: str, new_name: str) -> Tuple[bool, str]:
    """Renames an existing profile."""
    clean_old = old_name.strip()
    clean_new = new_name.strip()

    if clean_old.lower() == "default":
        return False, "The 'Default' profile cannot be renamed."

    if not clean_new:
        return False, "New profile name cannot be empty."

    if not re.match(r"^[a-zA-Z0-9_\-]+$", clean_new):
        return (
            False,
            "New profile name must contain only letters, numbers, or hyphens.",
        )

    config = load_profiles_config()
    profiles = config.get("profiles", [])

    match_old = None
    for p in profiles:
        if p.lower() == clean_old.lower():
            match_old = p
            break

    if not match_old:
        return False, f"Profile '{clean_old}' does not exist."

    for p in profiles:
        if p.lower() == clean_new.lower() and p.lower() != clean_old.lower():
            return False, f"Profile name '{clean_new}' is already in use."

    old_dir = get_profiles_dir() / match_old
    new_dir = get_profiles_dir() / clean_new

    if old_dir.exists():
        try:
            old_dir.rename(new_dir)
        except Exception as e:
            return False, f"Failed to rename profile directory: {e}"

    # Update config list
    config["profiles"] = [clean_new if p == match_old else p for p in profiles]
    if config.get("active_profile") == match_old:
        config["active_profile"] = clean_new

    save_profiles_config(config)
    return True, f"✓ Renamed profile '{match_old}' to '{clean_new}'."


def remove_profile(profile_name: str) -> Tuple[bool, str]:
    """Removes a workspace profile."""
    clean_name = profile_name.strip()

    if clean_name.lower() == "default":
        return False, "The 'Default' profile cannot be removed."

    config = load_profiles_config()
    active_profile = config.get("active_profile", "Default")

    if clean_name.lower() == active_profile.lower():
        return (
            False,
            f"Cannot remove profile '{clean_name}' while active. "
            "Switch to another profile first.",
        )

    profiles = config.get("profiles", [])
    match = None
    for p in profiles:
        if p.lower() == clean_name.lower():
            match = p
            break

    if not match:
        return False, f"Profile '{clean_name}' does not exist."

    # Delete profile folder if exists
    p_dir = get_profiles_dir() / match
    if p_dir.exists():
        try:
            shutil.rmtree(p_dir)
        except Exception as e:
            return False, f"Failed to remove profile data folder: {e}"

    config["profiles"] = [p for p in profiles if p.lower() != clean_name.lower()]
    save_profiles_config(config)
    return True, f"✓ Removed profile '{match}'."
