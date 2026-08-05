import json
from pathlib import Path

# ======================================================
# Configuration
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
MEMORY_FILE = STORAGE_DIR / "memory.json"

DEFAULT_MEMORY = {
    "last_location": "",
    "locations": [],
    "repositories": []
}


def load_memory():
    """Load memory.json or create it inside storage/ if missing."""
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        # If the JSON is corrupted, recreate it.
        save_memory(DEFAULT_MEMORY)
        return DEFAULT_MEMORY.copy()


def save_memory(memory_data):
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=4)


def reset_memory():
    """Reset memory dict to DEFAULT_MEMORY and overwrite memory.json."""
    global memory
    memory.clear()
    memory.update({
        "last_location": "",
        "locations": [],
        "repositories": []
    })
    save_memory(memory)


memory = load_memory()
