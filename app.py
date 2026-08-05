import sys

from core.clone import clone_repository
from core.exit_handler import run_with_exit_handler
from core.utils import check_git, get_repo_name
from ui.menu import choose_destination
from ui.messages import print_header, print_ready_banner
from ui.prompts import ask_repo


def main():

    print_header()

    if not check_git():
        print("\nGit is not installed or is not in PATH.")
        print("Install Git and try again.")
        sys.exit(1)

    first_run = True

    while True:

        if not first_run:
            print_ready_banner()

        first_run = False

        repo_url = ask_repo()

        destination = choose_destination()

        if destination is None:
            continue

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
    run_with_exit_handler(main)