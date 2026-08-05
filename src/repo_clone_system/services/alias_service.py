import re
from pathlib import Path
from typing import Dict, Tuple

from repo_clone_system.core.validator import is_valid_directory_path
from repo_clone_system.storage.memory import memory, save_memory


def list_aliases() -> Dict[str, str]:
    """Returns dictionary of all defined workspace aliases {alias_name: path}."""
    return dict(memory.get("aliases", {}))


def add_alias(alias_name: str, path_input: str) -> Tuple[bool, str]:
    """Adds a new workspace alias mapping alias_name -> path."""
    name_clean = alias_name.strip().lower()
    path_clean = path_input.strip()

    if not name_clean:
        return False, "Alias name cannot be empty."

    if not re.match(r"^[a-zA-Z0-9_\-]+$", name_clean):
        return (
            False,
            "Alias name must contain only letters, numbers, underscores, or hyphens.",
        )

    if not path_clean:
        return False, "Target path cannot be empty."

    if not is_valid_directory_path(path_clean):
        return False, f"'{path_clean}' is not a valid directory path."

    try:
        resolved_path = str(Path(path_clean).resolve())
    except Exception:
        resolved_path = path_clean

    aliases = memory.get("aliases", {})
    aliases[name_clean] = resolved_path
    memory["aliases"] = aliases
    save_memory(memory)

    return True, f"✓ Added workspace alias '{name_clean}' -> '{resolved_path}'."


def remove_alias(alias_name: str) -> Tuple[bool, str]:
    """Removes a workspace alias by name."""
    name_clean = alias_name.strip().lower()
    aliases = memory.get("aliases", {})

    if name_clean not in aliases:
        return False, f"Alias '{alias_name}' does not exist."

    del aliases[name_clean]
    memory["aliases"] = aliases
    save_memory(memory)
    return True, f"✓ Removed alias '{name_clean}'."


def rename_alias(old_name: str, new_name: str) -> Tuple[bool, str]:
    """Renames an existing alias to new_name."""
    old_clean = old_name.strip().lower()
    new_clean = new_name.strip().lower()

    if not re.match(r"^[a-zA-Z0-9_\-]+$", new_clean):
        return (
            False,
            "New alias name must contain only letters, numbers, or hyphens.",
        )

    aliases = memory.get("aliases", {})
    if old_clean not in aliases:
        return False, f"Alias '{old_name}' does not exist."

    path = aliases.pop(old_clean)
    aliases[new_clean] = path
    memory["aliases"] = aliases
    save_memory(memory)

    return True, f"✓ Renamed alias '{old_clean}' to '{new_clean}'."


def get_alias_path(alias_name: str) -> str:
    """Returns target path for an alias or None if not found."""
    aliases = memory.get("aliases", {})
    return aliases.get(alias_name.strip().lower())
