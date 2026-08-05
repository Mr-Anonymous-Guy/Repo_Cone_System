import questionary
from questionary import Choice

from repo_clone_system import __version__

PALETTE_HEADER = (
    "╭──────────────────────────────────────────────────────────────╮\n"
    f"│ Repo_Clone_System v{__version__:<41} │\n"
    "│ Press ↑ ↓ to navigate • Enter to select • Esc to cancel      │\n"
    "╰──────────────────────────────────────────────────────────────╯"
)

COMMAND_CHOICES = [
    Choice(title="Clone Repository", value="clone"),
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


def show_command_palette():
    """Displays VS Code-style Command Palette with live search filter."""
    print(PALETTE_HEADER)

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

        if selected is None:
            return "exit"

        return selected

    except Exception:
        # Fallback for non-interactive / unbuffered environments
        try:
            cmd = input("\n> ").strip().lower()
            return cmd if cmd else "help"
        except (KeyboardInterrupt, EOFError):
            return "exit"
