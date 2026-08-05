from pathlib import Path


def is_valid_github_url(url: str) -> bool:
    """Check if the provided string is a non-empty GitHub URL."""
    if not url:
        return False
    return "github.com" in url or url.startswith("git@") or url.endswith(".git")


def is_valid_directory_path(path_str: str) -> bool:
    """Check if provided string is a valid directory path."""
    if not path_str or not path_str.strip():
        return False
    try:
        _ = Path(path_str.strip().strip('"'))
        return True
    except Exception:
        return False
