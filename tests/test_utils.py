from repo_clone_system.core.utils import get_repo_name, check_git


def test_get_repo_name():
    assert get_repo_name("https://github.com/user/repository.git") == "repository"
    assert get_repo_name("https://github.com/user/repository") == "repository"
    assert get_repo_name("https://github.com/user/repository/") == "repository"


def test_check_git():
    assert check_git() is True
