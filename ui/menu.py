from pathlib import Path
import questionary
from questionary import Choice, Separator

from core.destination import validate_and_get_destination_path
from core.memory import memory


def choose_destination():

    choices = [
        Choice(title="➕ New Location", value="__NEW_LOCATION__")
    ]

    last = memory.get("last_location", "")
    if last:
        choices.append(
            Choice(title=f"  🕒 Last Used\n    {last}", value=last)
        )

    # Ensure duplicate locations never appear
    saved_locations = []
    for loc in memory.get("locations", []):
        if loc and loc not in saved_locations:
            saved_locations.append(loc)

    if saved_locations:
        choices.append(Separator("────────────────────"))
        for loc in saved_locations:
            choices.append(Choice(title=f"  {loc}", value=loc))

    selected = questionary.select(
        "\nChoose Clone Destination",
        choices=choices,
        use_indicator=True
    ).ask()

    if selected is None:
        # User pressed Esc to cancel
        return None

    if selected == "__NEW_LOCATION__":
        return validate_and_get_destination_path()

    return Path(selected)
