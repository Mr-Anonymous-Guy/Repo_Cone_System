import questionary
from questionary import Choice

from repo_clone_system import __version__

STARTUP_HEADER = (
    "╭──────────────────────────────────────────────────────────────╮\n"
    f"│ Repo_Clone_System v{__version__:<41} │\n"
    '│ Type "help" to list commands or enter a GitHub URL.          │\n'
    "│ Press Ctrl+C anytime to exit safely.                         │\n"
    "╰──────────────────────────────────────────────────────────────╯"
)

PALETTE_HEADER = STARTUP_HEADER

COMMAND_CHOICES = [
    Choice(title="➕ Custom URL / Direct Command...", value="__CUSTOM__"),
    Choice(title="Clone Repository", value="clone"),
    Choice(title="Workspace Manager", value="workspace"),
    Choice(title="Saved Repositories", value="repos"),
    Choice(title="Saved Locations", value="locations"),
    Choice(title="Workspace Aliases", value="alias"),
    Choice(title="Memory Manager", value="memory"),
    Choice(title="Export Configuration", value="export"),
    Choice(title="Import Configuration", value="import"),
    Choice(title="Managed Backups", value="backups"),
    Choice(title="Configuration Details", value="config"),
    Choice(title="System Doctor", value="doctor"),
    Choice(title="Statistics", value="stats"),
    Choice(title="Check Updates", value="update"),
    Choice(title="Help", value="help"),
    Choice(title="Clear History", value="clear"),
    Choice(title="Exit", value="exit"),
]


def print_startup_header():
    """Prints the clean startup banner."""
    print(STARTUP_HEADER)


def show_command_palette():
    """Displays VS Code-style Hybrid Command Palette (used for interactive menus)."""
    try:
        selected = questionary.select(
            "",
            choices=COMMAND_CHOICES,
            use_search_filter=True,
            use_jk_keys=False,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()

        if selected == "__CUSTOM__":
            try:
                user_input = questionary.text("Command or URL >").ask()
            except Exception:
                user_input = input("\nCommand or URL > ").strip()
            return user_input.strip() if user_input and user_input.strip() else "help"

        if selected is None:
            return "exit"

        return selected

    except Exception:
        try:
            cmd = input("\nCommand or URL > ").strip()
            return cmd if cmd else "help"
        except (KeyboardInterrupt, EOFError):
            return "exit"
