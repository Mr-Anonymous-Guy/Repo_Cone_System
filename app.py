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

        if repo.lower() == "exit":
            print("\nThanks for using Repo_Clone_System!")
            print("Goodbye.")
            raise SystemExit

        if "github.com" not in repo:
            print("Please enter a valid GitHub URL.")
            continue

        return repo


def ask_location():

    while True:

        last = memory.get("last_location", "")

        destination = input(
            "\nDestination Folder\n(Leave blank to use previous location)\n> "
        ).strip().strip('"')

        if not destination:
            if last:
                print(f"\nUsing previous location:\n{last}")
                dest_path = Path(last)
            else:
                print("No previous location saved. Please enter a destination folder.")
                continue
        else:
            dest_path = Path(destination)

        # Case B: Entire path exists
        if dest_path.exists():
            return dest_path

        # Case A: Leaf directory does not exist, but parent exists
        if dest_path.parent.exists():
            print("\nFolder does not exist.\n")
            choice = input("Would you like to create it?\n(Y/N): ").strip().lower()

            if choice in ("y", "yes"):
                dest_path.mkdir(exist_ok=True)
                print("\nFolder created successfully.")
                return dest_path
            else:
                print("\nIncorrect folder location.")
                continue

        # Case C: Parent directory does not exist
        print("\nParent directory does not exist.\nPlease enter a valid location.")
        continue


def clone_repository(repo_url, destination, folder_name):

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

        return False

    # Save Memory
    memory["last_location"] = str(destination)

    if str(destination) not in memory["locations"]:
        memory["locations"].append(str(destination))

    if repo_url not in memory["repositories"]:
        memory["repositories"].append(repo_url)

    save_memory(memory)

    # Success
    print("=" * 60)
    print("Repository cloned successfully!")
    print("=" * 60)

    print(f"\nRepository : {get_repo_name(repo_url)}")
    print(f"Folder     : {folder_name}")
    print(f"Location   : {destination / folder_name}")

    return True


# ======================================================
# Main Loop
# ======================================================

def main():

    print("=" * 60)
    print("GitHub Repository Cloner")
    print("=" * 60)

    if not check_git():

        print("\nGit is not installed or is not in PATH.")
        print("Install Git and try again.")

        raise SystemExit

    first_run = True

    while True:

        if not first_run:
            print("\n------------------------------------------")
            print("Ready for another repository.")
            print("(Type 'exit' to quit.)")
            print("------------------------------------------")

        first_run = False

        repo_url = ask_repo()

        destination = ask_location()

        repo_name = get_repo_name(repo_url)

        folder_name = repo_name

        # Folder Name Conflict Detection
        while (destination / folder_name).exists():

            print(f"\nFolder '{folder_name}' already exists.")

            folder_name = input(
                "Enter another folder name\n> "
            ).strip()

            if folder_name == "":
                folder_name = repo_name

        clone_repository(repo_url, destination, folder_name)


if __name__ == "__main__":
    main()