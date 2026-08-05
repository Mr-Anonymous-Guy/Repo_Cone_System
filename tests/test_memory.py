from repo_clone_system.services.memory_service import (
    backup_memory,
    get_memory_metrics,
    list_backups,
    restore_memory,
)
from repo_clone_system.storage.memory import DEFAULT_MEMORY, load_memory, reset_memory


def setup_function():
    reset_memory()


def test_default_memory_structure():
    assert "last_location" in DEFAULT_MEMORY
    assert "locations" in DEFAULT_MEMORY
    assert "repositories" in DEFAULT_MEMORY
    assert "aliases" in DEFAULT_MEMORY


def test_reset_memory():
    reset_memory()
    mem = load_memory()
    assert mem["last_location"] == ""
    assert mem["locations"] == []
    assert mem["repositories"] == []
    assert mem["aliases"] == {}


def test_memory_backup_and_restore():
    metrics = get_memory_metrics()
    assert "total_repos" in metrics
    assert "total_locations" in metrics
    assert "total_aliases" in metrics

    ok, msg, backup_path = backup_memory()
    assert ok
    assert backup_path.exists()

    backups = list_backups()
    assert backup_path in backups

    ok_rest, msg_rest = restore_memory(backup_path)
    assert ok_rest
