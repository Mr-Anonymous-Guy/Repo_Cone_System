from repo_clone_system.services.repo_service import (
    add_repo,
    get_saved_repos,
    remove_repo,
    search_repos,
)
from repo_clone_system.storage.memory import reset_memory


def setup_function():
    reset_memory()


def test_add_and_get_repos():
    repo_url = "https://github.com/torvalds/linux.git"
    ok, msg = add_repo(repo_url, location="/tmp/linux")
    assert ok

    repos = get_saved_repos()
    assert len(repos) == 1
    assert repos[0]["name"] == "linux"
    assert repos[0]["url"] == repo_url
    assert repos[0]["location"] == "/tmp/linux"

    # Duplicate check
    ok_dup, msg_dup = add_repo(repo_url)
    assert not ok_dup
    assert "already in memory" in msg_dup


def test_add_invalid_repo_url():
    ok, msg = add_repo("not_a_valid_url")
    assert not ok
    assert "not a valid" in msg


def test_remove_repo():
    url = "https://github.com/pallets/flask.git"
    add_repo(url)
    assert len(get_saved_repos()) == 1

    ok, msg = remove_repo("flask")
    assert ok
    assert len(get_saved_repos()) == 0


def test_search_repos():
    add_repo("https://github.com/facebook/react.git")
    add_repo("https://github.com/vuejs/vue.git")

    results = search_repos("react")
    assert len(results) == 1
    assert results[0]["name"] == "react"

    results_empty = search_repos("angular_xyz")
    assert len(results_empty) == 0
