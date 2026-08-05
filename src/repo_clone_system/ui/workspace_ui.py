import questionary
from questionary import Choice

WORKSPACE_HEADER = (
    "╭──────────────────────────────────────────────────────────────╮\n"
    "│ Repo_Clone_System Workspace Manager                          │\n"
    "│ Press ↑ ↓ to navigate • Enter to select • Esc to cancel      │\n"
    "╰──────────────────────────────────────────────────────────────╯"
)


def show_workspace_palette():
    """Displays interactive Workspace Manager menu palette."""
    print(WORKSPACE_HEADER)
    choices = [
        Choice(title="Switch Workspace", value="switch"),
        Choice(title="Create Workspace", value="create"),
        Choice(title="Rename Workspace", value="rename"),
        Choice(title="Remove Workspace", value="remove"),
        Choice(title="Export Workspace", value="export"),
        Choice(title="Import Workspace", value="import"),
        Choice(title="Backup Manager", value="backup"),
        Choice(title="Synchronization", value="sync"),
        Choice(title="Workspace Information", value="info"),
        Choice(title="Exit Workspace Manager", value="exit"),
    ]

    try:
        return questionary.select(
            "",
            choices=choices,
            use_search_filter=True,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()
    except Exception:
        return None


def show_profile_palette():
    """Displays interactive Profile Manager menu palette."""
    choices = [
        Choice(title="Switch Profile", value="switch"),
        Choice(title="Create Profile", value="create"),
        Choice(title="Rename Profile", value="rename"),
        Choice(title="Remove Profile", value="remove"),
        Choice(title="List Profiles", value="list"),
        Choice(title="Exit Profile Manager", value="exit"),
    ]

    try:
        return questionary.select(
            "Profile Manager Menu",
            choices=choices,
            use_search_filter=True,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()
    except Exception:
        return None


def show_sync_palette():
    """Displays interactive Sync Manager menu palette."""
    choices = [
        Choice(title="Configure Sync Folder", value="config"),
        Choice(title="Export Workspace to Sync Folder", value="export"),
        Choice(title="Import Latest Workspace from Sync Folder", value="import"),
        Choice(title="Sync Status", value="status"),
        Choice(title="Exit Sync Manager", value="exit"),
    ]

    try:
        return questionary.select(
            "Sync Manager Menu",
            choices=choices,
            use_search_filter=True,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()
    except Exception:
        return None


def show_backup_palette():
    """Displays interactive Backup Manager menu palette."""
    choices = [
        Choice(title="Create Backup", value="create"),
        Choice(title="Restore Backup", value="restore"),
        Choice(title="View Backups", value="list"),
        Choice(title="Delete Backup", value="remove"),
        Choice(title="Backup History", value="history"),
        Choice(title="Exit Backup Manager", value="exit"),
    ]

    try:
        return questionary.select(
            "Backup Manager Menu",
            choices=choices,
            use_search_filter=True,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()
    except Exception:
        return None
