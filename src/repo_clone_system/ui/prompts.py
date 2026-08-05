import sys

from repo_clone_system.ui.messages import print_goodbye


def ask_repo():

    while True:

        repo = input("\nGitHub Repository URL\n> ").strip()

        if repo == "":
            print("Repository URL cannot be empty.")
            continue

        if repo.lower() == "exit":
            print_goodbye()
            sys.exit(0)

        if "github.com" not in repo:
            print("Please enter a valid GitHub URL.")
            continue

        return repo
