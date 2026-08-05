from pathlib import Path
import questionary
from questionary import Choice, Separator

from repo_clone_system.core.destination import validate_and_get_destination_path
from repo_clone_system.services.alias_service import list_aliases
from repo_clone_system.storage.memory import memory


def choose_destination():
    """Interactive destination menu displaying aliases, saved locations, and recent."""
    choices = []

    # 1. Aliases
    aliases = list_aliases()
    if aliases:
        choices.append(Separator("── Workspace Aliases ──"))
        for name, path_str in aliases.items():
            choices.append(
                Choice(title=f"  🏷️  {name:<12} ({path_str})", value=path_str)
            )

    # 2. Saved Locations
    saved_locations = []
    for loc in memory.get("locations", []):
        if loc and loc not in saved_locations:
            saved_locations.append(loc)

    if saved_locations:
        choices.append(Separator("── Saved Locations ──"))
        for loc in saved_locations:
            choices.append(Choice(title=f"  📁  {loc}", value=loc))

    # 3. Last Used Location
    last = memory.get("last_location", "")
    if last and last not in saved_locations and last not in aliases.values():
        choices.append(Separator("── Recent ──"))
        choices.append(Choice(title=f"  🕒  Last Used: {last}", value=last))

    # 4. New Location & Cancel
    choices.append(Separator("────────────────────"))
    choices.append(Choice(title="➕  New Location...", value="__NEW_LOCATION__"))
    choices.append(Choice(title="❌  Cancel", value="__CANCEL__"))

    selected = questionary.select(
        "\nChoose Clone Destination", choices=choices, use_indicator=True
    ).ask()

    if selected is None or selected == "__CANCEL__":
        return None

    if selected == "__NEW_LOCATION__":
        return validate_and_get_destination_path()

    return Path(selected)
