import os
import platform
import subprocess
import sys

from repo_clone_system import __version__
from repo_clone_system.storage.memory import get_config_dir, get_memory_file, memory


def get_config_info() -> dict:
    """Returns system configuration and memory info for 'repo config'."""
    config_dir = get_config_dir()
    memory_file = get_memory_file()

    repos = memory.get("repositories", [])
    locations = memory.get("locations", [])
    aliases = memory.get("aliases", {})
    last_loc = memory.get("last_location", "") or "None"

    return {
        "version": __version__,
        "memory_file": str(memory_file),
        "config_folder": str(config_dir),
        "package_version": __version__,
        "storage_location": str(config_dir),
        "os": f"{platform.system()} {platform.release()}",
        "python_version": (
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        ),
        "saved_repos": len(repos),
        "saved_locations": len(locations),
        "saved_aliases": len(aliases),
        "last_location": last_loc,
    }


def open_memory_file() -> tuple[bool, str]:
    """Opens memory.json in the default system text editor."""
    memory_file = get_memory_file()
    if not memory_file.exists():
        return False, f"Memory file does not exist at {memory_file}"

    try:
        if os.name == "nt":  # Windows
            os.startfile(str(memory_file))
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(memory_file)], check=True)
        else:  # Linux / Unix
            subprocess.run(["xdg-open", str(memory_file)], check=True)
        return True, f"Opened memory file: {memory_file}"
    except Exception as e:
        return False, f"Failed to open memory file: {e}"


def open_config_folder() -> tuple[bool, str]:
    """Opens the configuration folder in the platform's default file explorer."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == "nt":  # Windows
            os.startfile(str(config_dir))
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", str(config_dir)], check=True)
        else:  # Linux / Unix
            subprocess.run(["xdg-open", str(config_dir)], check=True)
        return True, f"Opened configuration folder: {config_dir}"
    except Exception as e:
        return False, f"Failed to open configuration folder: {e}"
