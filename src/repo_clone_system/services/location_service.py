from pathlib import Path
from typing import Dict, List, Tuple

from repo_clone_system.core.validator import is_valid_directory_path
from repo_clone_system.storage.memory import memory, save_memory


def get_saved_locations() -> List[str]:
    """Returns the list of saved location strings."""
    return list(memory.get("locations", []))


def add_location(
    path_input: str, auto_create_missing: bool = False
) -> Tuple[bool, str]:
    """Validates and adds a location to memory.

    - Ignores duplicates.
    - Validates directory path.
    - If parent does not exist, explains why.
    """
    clean_str = path_input.strip()
    if not clean_str:
        return False, "Location path cannot be empty."

    if not is_valid_directory_path(clean_str):
        return False, f"'{clean_str}' is not a valid directory path."

    p = Path(clean_str)

    try:
        resolved_path = str(p.resolve())
    except Exception:
        resolved_path = str(p)

    locations = memory.get("locations", [])

    # Check duplicate
    for loc in locations:
        try:
            if Path(loc).resolve() == Path(resolved_path).resolve():
                return False, f"Location '{resolved_path}' is already saved."
        except Exception:
            if loc == resolved_path:
                return False, f"Location '{resolved_path}' is already saved."

    # Check existence
    if not p.exists():
        parent = p.parent
        if not parent.exists():
            return (
                False,
                f"Parent directory '{parent}' does not exist.",
            )

        if auto_create_missing:
            try:
                p.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return False, f"Could not create folder '{p}': {e}"
        else:
            return (
                False,
                f"Directory '{p}' does not exist. (Can be created if requested).",
            )

    locations.append(resolved_path)
    memory["locations"] = locations
    save_memory(memory)
    return True, f"✓ Added location '{resolved_path}'."


def remove_location(path_str: str) -> Tuple[bool, str]:
    """Removes a location from memory."""
    locations = memory.get("locations", [])
    matched = None
    for loc in locations:
        if loc == path_str or str(Path(loc)) == str(Path(path_str)):
            matched = loc
            break

    if not matched:
        return False, f"Location '{path_str}' not found in memory."

    locations.remove(matched)
    memory["locations"] = locations

    if memory.get("last_location") == matched:
        memory["last_location"] = ""

    save_memory(memory)
    return True, f"✓ Removed location '{matched}'."


def rename_location(old_path_str: str, new_path_str: str) -> Tuple[bool, str]:
    """Renames an existing location path in memory."""
    new_clean = new_path_str.strip()
    if not new_clean:
        return False, "New path cannot be empty."

    if not is_valid_directory_path(new_clean):
        return False, f"'{new_clean}' is not a valid directory path."

    try:
        resolved_new = str(Path(new_clean).resolve())
    except Exception:
        resolved_new = new_clean

    locations = memory.get("locations", [])
    idx = -1
    for i, loc in enumerate(locations):
        if loc == old_path_str or str(Path(loc)) == str(Path(old_path_str)):
            idx = i
            break

    if idx == -1:
        return False, f"Location '{old_path_str}' not found."

    locations[idx] = resolved_new
    memory["locations"] = locations

    if memory.get("last_location") == old_path_str:
        memory["last_location"] = resolved_new

    save_memory(memory)
    return True, f"✓ Renamed location to '{resolved_new}'."


def verify_locations() -> Dict[str, dict]:
    """Checks every stored location for existence.

    Returns dict mapping path -> {"exists": bool, "status": str}.
    """
    locations = memory.get("locations", [])
    results = {}

    for loc in locations:
        exists = Path(loc).exists()
        results[loc] = {
            "exists": exists,
            "status": "✔ Exists" if exists else "✖ Missing",
        }

    return results


def clean_missing_locations(missing_paths: List[str]) -> Tuple[int, str]:
    """Removes a list of missing paths from memory."""
    locations = memory.get("locations", [])
    removed_count = 0

    for path in missing_paths:
        if path in locations:
            locations.remove(path)
            removed_count += 1
            if memory.get("last_location") == path:
                memory["last_location"] = ""

    memory["locations"] = locations
    save_memory(memory)
    return removed_count, f"Removed {removed_count} missing location(s)."
