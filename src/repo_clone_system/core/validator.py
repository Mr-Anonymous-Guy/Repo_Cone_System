def is_valid_github_url(url: str) -> bool:
    """Check if the provided string is a non-empty GitHub URL."""
    if not url:
        return False
    return "github.com" in url
