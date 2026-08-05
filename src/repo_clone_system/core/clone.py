import subprocess

from repo_clone_system.core.utils import get_repo_name
from repo_clone_system.storage.memory import memory, save_memory


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
