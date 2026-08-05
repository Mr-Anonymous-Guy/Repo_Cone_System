import questionary
from questionary import Choice

PALETTE_HEADER = (
    "╭──────────────────────────────────────────────────────────────╮\n"
    "│ Repo_Clone_System v0.1.0                                     │\n"
    "│ Press ↑ ↓ to navigate • Enter to select • Esc to cancel      │\n"
    "╰──────────────────────────────────────────────────────────────╯"
)

COMMAND_CHOICES = [
    Choice(title="Clone Repository", value="clone"),
    Choice(title="Saved Repositories", value="repos"),
    Choice(title="Saved Locations", value="locations"),
    Choice(title="Statistics", value="stats"),
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
