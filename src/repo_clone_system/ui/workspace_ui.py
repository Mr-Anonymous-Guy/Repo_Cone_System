import questionary
from questionary import Choice

WORKSPACE_HEADER = (
    "╭──────────────────────────────────────────────────────────────╮\n"
    "│ Repo_Clone_System Workspace Manager                          │\n"
    "│ Press ↑ ↓ to navigate • Enter to select • Esc to cancel      │\n"
    "╰──────────────────────────────────────────────────────────────╯"
)


def _safe_select(title: str, choices: list):
    try:
        return questionary.select(
            title,
            choices=choices,
            use_search_filter=True,
            use_indicator=True,
            qmark=">",
            pointer="❯",
        ).ask()
    except Exception:
        return None


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
    return _safe_select("", choices)


def show_clone_palette():
    """Displays interactive Clone Repository menu palette."""
    choices = [
        Choice(title="Clone from GitHub URL", value="url"),
        Choice(title="Clone Saved Repository", value="saved"),
        Choice(title="Clone using Alias", value="alias"),
        Choice(title="Clone Recent Repository", value="recent"),
        Choice(title="Quick Clone", value="quick"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Clone Repository Menu", choices)


def show_repos_palette():
    """Displays interactive Saved Repositories menu palette."""
    choices = [
        Choice(title="Browse", value="list"),
        Choice(title="Search", value="search"),
        Choice(title="Add", value="add"),
        Choice(title="Remove", value="remove"),
        Choice(title="Verify", value="verify"),
        Choice(title="Information", value="info"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Saved Repositories Menu", choices)


def show_locations_palette():
    """Displays interactive Saved Locations menu palette."""
    choices = [
        Choice(title="Browse", value="list"),
        Choice(title="Add", value="add"),
        Choice(title="Remove", value="remove"),
        Choice(title="Rename", value="rename"),
        Choice(title="Verify", value="verify"),
        Choice(title="Open", value="open"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Saved Locations Menu", choices)


def show_alias_palette():
    """Displays interactive Workspace Aliases menu palette."""
    choices = [
        Choice(title="Browse", value="list"),
        Choice(title="Add", value="add"),
        Choice(title="Remove", value="remove"),
        Choice(title="Rename", value="rename"),
        Choice(title="Test", value="test"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Workspace Aliases Menu", choices)


def show_memory_palette():
    """Displays interactive Memory Manager menu palette."""
    choices = [
        Choice(title="Overview", value="overview"),
        Choice(title="Repair", value="repair"),
        Choice(title="Optimize", value="optimize"),
        Choice(title="Export", value="export"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Memory Manager Menu", choices)


def show_export_palette():
    """Displays interactive Export Configuration menu palette."""
    choices = [
        Choice(title="Export Workspace", value="workspace"),
        Choice(title="Export Repositories", value="repos"),
        Choice(title="Export Locations", value="locations"),
        Choice(title="Export Aliases", value="aliases"),
        Choice(title="Export Everything", value="everything"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Export Configuration Menu", choices)


def show_import_palette():
    """Displays interactive Import Configuration menu palette."""
    choices = [
        Choice(title="Merge", value="merge"),
        Choice(title="Replace", value="replace"),
        Choice(title="Preview", value="preview"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Import Configuration Menu", choices)


def show_help_palette():
    """Displays interactive Help menu palette."""
    choices = [
        Choice(title="Commands", value="commands"),
        Choice(title="Examples", value="examples"),
        Choice(title="Documentation", value="documentation"),
        Choice(title="GitHub", value="github"),
        Choice(title="Issues", value="issues"),
        Choice(title="Version", value="version"),
        Choice(title="About", value="about"),
        Choice(title="Back", value="exit"),
    ]
    return _safe_select("Help Menu", choices)


def show_clear_palette():
    """Displays interactive Clear History menu palette."""
    choices = [
        Choice(title="Repository History", value="repos"),
        Choice(title="Location History", value="locations"),
        Choice(title="Recent Activity", value="recent"),
        Choice(title="Everything", value="everything"),
        Choice(title="Cancel", value="exit"),
    ]
    return _safe_select("Clear History Menu", choices)


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
    return _safe_select("Profile Manager Menu", choices)


def show_sync_palette():
    """Displays interactive Sync Manager menu palette."""
    choices = [
        Choice(title="Configure Sync Folder", value="config"),
        Choice(title="Export Workspace to Sync Folder", value="export"),
        Choice(title="Import Latest Workspace from Sync Folder", value="import"),
        Choice(title="Sync Status", value="status"),
        Choice(title="Exit Sync Manager", value="exit"),
    ]
    return _safe_select("Sync Manager Menu", choices)


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
    return _safe_select("Backup Manager Menu", choices)
