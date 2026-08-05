import json
import urllib.request
from typing import Tuple

from repo_clone_system import __version__

PYPI_URL = "https://pypi.org/pypi/repo-clone-system/json"


def check_for_updates() -> Tuple[str, str, bool, str]:
    """Queries PyPI for the latest version of repo-clone-system.

    Returns:
        (current_version, latest_version, update_available, message)
    """
    current_ver = __version__
    latest_ver = current_ver
    update_avail = False

    try:
        req = urllib.request.Request(
            PYPI_URL, headers={"User-Agent": "repo-clone-system-cli"}
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                latest_ver = data.get("info", {}).get("version", current_ver)

        def _parse_v(v_str):
            try:
                return tuple(int(x) for x in v_str.replace("v", "").split("."))
            except Exception:
                return (0, 0, 0)

        if _parse_v(latest_ver) > _parse_v(current_ver):
            update_avail = True
            msg = f"A new release (v{latest_ver}) is available on PyPI!"
        else:
            msg = f"You are on the latest version (v{current_ver})."

    except Exception:
        msg = "Could not check PyPI for updates (offline or network timeout)."

    return current_ver, latest_ver, update_avail, msg
