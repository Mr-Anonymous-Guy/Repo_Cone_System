import json
import subprocess
from pathlib import Path


# ======================================================
# Configuration
# ======================================================

BASE_DIR = Path(__file__).parent
MEMORY_FILE = BASE_DIR / "memory.json"


# ======================================================
# Memory
# ======================================================

DEFAULT_MEMORY = {
    "last_location": "",
    "locations": [],
    "repositories": []
}


def load_memory():
    """Load memory.json or create it if missing."""

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


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4)


memory = load_memory()


# ======================================================
# Helpers
# ======================================================

def check_git():
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            check=True
        )
        return True

    except Exception:
        return False


def get_repo_name(url):
    url = url.rstrip("/")

    if url.endswith(".git"):
        url = url[:-4]

    return url.split("/")[-1]


def ask_repo():

    while True:

        repo = input("\nGitHub Repository URL\n> ").strip()

        if repo == "":
            print("Repository URL cannot be empty.")
            continue

        if "github.com" not in repo:
            print("Please enter a valid GitHub URL.")
            continue

        return repo


def ask_location():

    last = memory["last_location"]

    destination = input(
        "\nDestination Folder\n(Leave blank to use previous location)\n> "
    ).strip().strip('"')

    if destination:
        return destination

    if last:

        while True:

            choice = input(
                f"\nUse previous location?\n{last}\n(Y/N): "
            ).lower().strip()

            if choice in ("y", "yes"):
                return last

            if choice in ("n", "no"):
                break

    while True:

        destination = input("\nEnter destination folder\n> ").strip().strip('"')

        if destination:
            return destination


# ======================================================
# Start
# ======================================================

print("=" * 60)
print("GitHub Repository Cloner")
print("=" * 60)

if not check_git():

    print("\nGit is not installed or is not in PATH.")
    print("Install Git and try again.")

    raise SystemExit


repo_url = ask_repo()

destination = Path(ask_location())

destination.mkdir(parents=True, exist_ok=True)

repo_name = get_repo_name(repo_url)

folder_name = repo_name


# ======================================================
# Folder Name
# ======================================================

while (destination / folder_name).exists():

    print(f"\nFolder '{folder_name}' already exists.")

    folder_name = input(
        "Enter another folder name\n> "
    ).strip()

    if folder_name == "":
        folder_name = repo_name


# ======================================================
# Clone
# ======================================================

print("\nCloning repository...\n")

result = subprocess.run(
    [
        "git",
        "clone",
        repo_url,
        folder_name
    ],
    cwd=destination,
    capture_output=True,
    text=True
)

if result.returncode != 0:

    error = result.stderr.lower()

    print("=" * 60)

    if "repository not found" in error:
        print("Repository does not exist.")

    elif "authentication failed" in error:
        print("Authentication failed.")
        print("Repository may be private.")

    elif "permission denied" in error:
        print("Permission denied.")

    elif "could not resolve host" in error:
        print("No internet connection.")

    elif "unable to access" in error:
        print("Unable to access GitHub.")

    else:
        print("Git returned an unknown error:\n")
        print(result.stderr)

    raise SystemExit


# ======================================================
# Save Memory
# ======================================================

memory["last_location"] = str(destination)

if str(destination) not in memory["locations"]:
    memory["locations"].append(str(destination))

if repo_url not in memory["repositories"]:
    memory["repositories"].append(repo_url)

save_memory(memory)


# ======================================================
# Success
# ======================================================

print("=" * 60)
print("Repository cloned successfully!")
print("=" * 60)

print(f"\nRepository : {repo_name}")
print(f"Folder     : {folder_name}")
print(f"Location   : {destination / folder_name}")