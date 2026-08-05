from repo_clone_system.services.alias_service import (
    add_alias,
    get_alias_path,
    list_aliases,
    remove_alias,
    rename_alias,
)
from repo_clone_system.storage.memory import reset_memory


def setup_function():
    reset_memory()


def test_add_and_list_alias(tmp_path):
    ok, msg = add_alias("work", str(tmp_path))
    assert ok

    aliases = list_aliases()
    assert "work" in aliases
    assert get_alias_path("work") == str(tmp_path.resolve())


def test_add_invalid_alias_name(tmp_path):
    ok, msg = add_alias("invalid name!", str(tmp_path))
    assert not ok
    assert "letters, numbers" in msg


def test_remove_alias(tmp_path):
    add_alias("learn", str(tmp_path))
    assert "learn" in list_aliases()

    ok, msg = remove_alias("learn")
    assert ok
    assert "learn" not in list_aliases()


def test_rename_alias(tmp_path):
    add_alias("oldname", str(tmp_path))
    ok, msg = rename_alias("oldname", "newname")
    assert ok

    aliases = list_aliases()
    assert "newname" in aliases
    assert "oldname" not in aliases
