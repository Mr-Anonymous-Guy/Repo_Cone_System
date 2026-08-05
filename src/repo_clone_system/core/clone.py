import subprocess

from repo_clone_system.core.utils import get_repo_name
from repo_clone_system.services.repo_service import add_repo
from repo_clone_system.storage.memory import memory, save_memory


from repo_clone_system.ui.menu import choose_destination


def clone_repository(repo_url, destination=None, folder_name=None):
    if destination is None:
        destination = choose_destination()
        if not destination:
            print("\nClone cancelled.")
            return False

    if not folder_name:
        folder_name = get_repo_name(repo_url)

    print("\nCloning repository...\n")

    result = subprocess.run(
        ["git", "clone", repo_url, folder_name],
        cwd=destination,
        capture_output=True,
        text=True,
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
    dest_str = str(destination)
    memory["last_location"] = dest_str

    if dest_str not in memory.get("locations", []):
        memory["locations"].append(dest_str)

    # Use add_repo service to record rich repo details
    add_repo(repo_url, location=str(destination / folder_name))

    save_memory(memory)

    # Success
    print("=" * 60)
    print("Repository cloned successfully!")
    print("=" * 60)

    print(f"\nRepository : {get_repo_name(repo_url)}")
    print(f"Folder     : {folder_name}")
    print(f"Location   : {destination / folder_name}")

    return True
