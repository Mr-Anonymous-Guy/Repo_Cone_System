import sys
import questionary
from repo_clone_system.ui.messages import print_goodbye


def ask_repo():
    """Interactively prompts user for a valid repository URL."""
    while True:
        try:
            repo = questionary.text("GitHub Repository URL:").ask()
        except Exception:
            try:
                repo = input("\nGitHub Repository URL\n> ").strip()
            except (KeyboardInterrupt, EOFError):
                print_goodbye()
                sys.exit(0)

        if repo is None or repo.strip() == "":
            print("Repository URL cannot be empty.")
            if not sys.stdin.isatty():
                return "https://github.com/Mr-Anonymous-Guy/Repo_Clone_System"
            continue

        repo = repo.strip()

        if repo.lower() in ("exit", "cancel", "quit"):
            print_goodbye()
            sys.exit(0)

        if (
            not repo.startswith(("http://", "https://", "git@"))
            and not repo.endswith(".git")
            and "github.com" not in repo
        ):
            print(
                "Please enter a valid GitHub repository URL (e.g. https://github.com/user/repo)."
            )
            if not sys.stdin.isatty():
                return "https://github.com/Mr-Anonymous-Guy/Repo_Clone_System"
            continue

        return repo
