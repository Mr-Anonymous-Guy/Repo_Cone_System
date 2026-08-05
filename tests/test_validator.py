from repo_clone_system.core.validator import is_valid_github_url


def test_is_valid_github_url():
    assert is_valid_github_url("https://github.com/user/repo") is True
    assert is_valid_github_url("http://github.com/user/repo") is True
    assert is_valid_github_url("https://gitlab.com/user/repo") is False
    assert is_valid_github_url("") is False
    assert is_valid_github_url(None) is False
