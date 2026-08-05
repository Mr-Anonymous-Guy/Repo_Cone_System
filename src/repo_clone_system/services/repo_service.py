import datetime
import subprocess
from typing import Dict, List, Tuple

from repo_clone_system.core.utils import get_repo_name
from repo_clone_system.core.validator import is_valid_github_url
from repo_clone_system.storage.memory import memory, save_memory


def get_repo_details(entry) -> dict:
    """Extracts structured details from a repository memory entry (string or dict)."""
    if isinstance(entry, dict):
        url = entry.get("url", "")
        name = entry.get("name") or get_repo_name(url)
        location = entry.get("location", "Unknown")
        date = entry.get("date", "Unknown")
    else:
        url = str(entry)
        name = get_repo_name(url)
        location = "Unknown"
        date = "Unknown"

    return {
        "url": url,
        "name": name,
        "location": location,
        "date": date,
    }


def get_saved_repos() -> List[dict]:
    """Returns all saved repositories formatted as detailed dictionaries."""
    raw_repos = memory.get("repositories", [])
    return [get_repo_details(r) for r in raw_repos]


def add_repo(repo_url: str, location: str = None) -> Tuple[bool, str]:
    """Validates and adds a repository URL to memory. Ignores duplicates."""
    clean_url = repo_url.strip()
    if not clean_url:
        return False, "Repository URL cannot be empty."

    if not is_valid_github_url(clean_url):
        return False, f"'{clean_url}' is not a valid GitHub or Git repository URL."

    repos = memory.get("repositories", [])

    # Check for duplicate URL
    for entry in repos:
        existing_url = entry.get("url") if isinstance(entry, dict) else str(entry)
        if existing_url.lower() == clean_url.lower():
            return False, f"Repository '{clean_url}' is already in memory."

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    name = get_repo_name(clean_url)

    new_entry = {
        "url": clean_url,
        "name": name,
        "location": location or "Unknown",
        "date": now_str,
    }

    repos.append(new_entry)
    memory["repositories"] = repos
    save_memory(memory)
    return True, f"✓ Added repository '{name}' ({clean_url})."


def remove_repo(target: str) -> Tuple[bool, str]:
    """Removes a repository by URL or name from memory."""
    clean_target = target.strip().lower()
    repos = memory.get("repositories", [])
    matched_entry = None

    for entry in repos:
        details = get_repo_details(entry)
        if (
            details["url"].lower() == clean_target
            or details["name"].lower() == clean_target
        ):
            matched_entry = entry
            break

    if matched_entry is None:
        return False, f"Repository '{target}' not found in memory."

    repos.remove(matched_entry)
    memory["repositories"] = repos
    save_memory(memory)
    return True, "✓ Removed repository."


def search_repos(query: str) -> List[dict]:
    """Performs substring / fuzzy matching on saved repositories by name or URL."""
    clean_query = query.strip().lower()
    if not clean_query:
        return get_saved_repos()

    results = []
    for entry in get_saved_repos():
        if (
            clean_query in entry["name"].lower()
            or clean_query in entry["url"].lower()
            or clean_query in entry["location"].lower()
        ):
            results.append(entry)

    return results


def verify_repos() -> Dict[str, dict]:
    """Checks reachability / accessibility of every stored repository URL.

    Uses `git ls-remote` with a 5-second timeout.
    """
    repos = get_saved_repos()
    results = {}

    for repo in repos:
        url = repo["url"]
        try:
            r = subprocess.run(
                ["git", "ls-remote", "--exit-code", url, "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if r.returncode == 0:
                results[url] = {
                    "status": "✔ Accessible",
                    "accessible": True,
                    "name": repo["name"],
                }
            elif (
                "Permission denied" in r.stderr
                or "Authentication failed" in r.stderr
                or "Could not read from remote" in r.stderr
            ):
                results[url] = {
                    "status": "🔒 Private / Auth Required",
                    "accessible": False,
                    "name": repo["name"],
                }
            else:
                results[url] = {
                    "status": "✖ Not Found / Invalid",
                    "accessible": False,
                    "name": repo["name"],
                }
        except subprocess.TimeoutExpired:
            results[url] = {
                "status": "⏱ Timeout",
                "accessible": False,
                "name": repo["name"],
            }
        except Exception:
            results[url] = {
                "status": "✖ Verification Error",
                "accessible": False,
                "name": repo["name"],
            }

    return results
