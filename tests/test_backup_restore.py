import json
import pytest
from pathlib import Path

from repo_clone_system.services.backup_service import (
    create_auto_backup,
    create_export,
    delete_backup_file,
    get_backups_dir,
    get_export_history,
    list_backups_dir,
    perform_import,
    validate_backup_file,
)
from repo_clone_system.storage.memory import (
    load_memory,
    memory,
    reset_memory,
    save_memory,
)


@pytest.fixture(autouse=True)
def clean_memory():
    reset_memory()
    yield
    reset_memory()


def test_export_default(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    memory["repositories"] = [{"url": "https://github.com/a/b.git", "name": "b"}]
    memory["locations"] = [str(tmp_path / "work")]
    memory["aliases"] = {"work": str(tmp_path / "work")}
    save_memory(memory)

    ok, msg, metadata = create_export()
    assert ok
    assert "Backup created successfully" in msg
    assert Path(metadata["path"]).exists()
    assert metadata["repo_count"] == 1
    assert metadata["location_count"] == 1
    assert metadata["alias_count"] == 1


def test_export_custom_directory(tmp_path):
    custom_dir = tmp_path / "my_backups"

    # Callback approves directory creation
    ok, msg, metadata = create_export(
        dest_input=str(custom_dir), prompt_mkdir_callback=lambda f: True
    )
    assert ok
    assert custom_dir.exists()
    assert Path(metadata["path"]).parent == custom_dir


def test_export_cancelled_when_mkdir_declined(tmp_path):
    missing_dir = tmp_path / "non_existent"
    ok, msg, metadata = create_export(
        dest_input=str(missing_dir), prompt_mkdir_callback=lambda f: False
    )
    assert not ok
    assert "cancelled" in msg.lower()
    assert not missing_dir.exists()


def test_validate_backup_file_valid(tmp_path):
    backup_file = tmp_path / "valid.json"
    payload = {
        "schema_version": 1,
        "created_at": "2026-08-05T18:00:00Z",
        "repo_clone_system_version": "2.0.0",
        "memory": {
            "last_location": "/tmp",
            "locations": ["/tmp"],
            "repositories": ["https://github.com/foo/bar.git"],
            "aliases": {"foo": "/tmp"},
        },
    }
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    ok, msg, data = validate_backup_file(backup_file)
    assert ok
    assert data["schema_version"] == 1
    assert data["memory"]["last_location"] == "/tmp"


def test_validate_backup_file_corrupted(tmp_path):
    corrupted_file = tmp_path / "corrupted.json"
    with open(corrupted_file, "w", encoding="utf-8") as f:
        f.write("{invalid_json: true,}")

    ok, msg, data = validate_backup_file(corrupted_file)
    assert not ok
    assert "Invalid JSON" in msg


def test_validate_backup_file_unsupported_schema(tmp_path):
    future_file = tmp_path / "future.json"
    payload = {
        "schema_version": 999,
        "memory": {},
    }
    with open(future_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    ok, msg, data = validate_backup_file(future_file)
    assert not ok
    assert "Unsupported schema version 999" in msg


def test_validate_backup_file_missing(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    ok, msg, data = validate_backup_file(missing_file)
    assert not ok
    assert "does not exist" in msg.lower()


def test_perform_import_merge(tmp_path):
    reset_memory()
    memory["repositories"] = [
        {"url": "https://github.com/existing/repo.git", "name": "repo"}
    ]
    memory["locations"] = [str(tmp_path / "loc1")]
    memory["aliases"] = {"loc1": str(tmp_path / "loc1")}
    save_memory(memory)

    backup_payload = {
        "schema_version": 1,
        "memory": {
            "repositories": [
                {"url": "https://github.com/existing/repo.git", "name": "repo"},
                {"url": "https://github.com/new/repo.git", "name": "new_repo"},
            ],
            "locations": [str(tmp_path / "loc1"), str(tmp_path / "loc2")],
            "aliases": {"loc1": str(tmp_path / "loc1"), "loc2": str(tmp_path / "loc2")},
        },
    }

    ok, msg = perform_import(backup_payload, mode="merge")
    assert ok

    mem = load_memory()
    assert len(mem["repositories"]) == 2
    assert len(mem["locations"]) == 2
    assert len(mem["aliases"]) == 2


def test_perform_import_replace(tmp_path):
    reset_memory()
    memory["repositories"] = [{"url": "https://github.com/old/repo.git"}]
    save_memory(memory)

    backup_payload = {
        "schema_version": 1,
        "memory": {
            "repositories": [{"url": "https://github.com/replaced/repo.git"}],
            "locations": ["/replaced"],
            "aliases": {"replaced": "/replaced"},
        },
    }

    ok, msg = perform_import(backup_payload, mode="replace")
    assert ok

    mem = load_memory()
    assert len(mem["repositories"]) == 1
    assert mem["repositories"][0]["url"] == "https://github.com/replaced/repo.git"

    # Verify automatic pre-import safety backup was created in Backups/
    backups = list_backups_dir()
    assert len(backups) >= 1
    assert "auto-backup-before-import" in backups[0].name


def test_auto_backup_creation():
    ok, msg, backup_path = create_auto_backup()
    assert ok
    assert backup_path.exists()
    assert "auto-backup-before-import" in backup_path.name


def test_backups_dir_listing_and_deletion(tmp_path):
    backups_dir = get_backups_dir()
    dummy_backup = backups_dir / "test-dummy-backup.json"
    with open(dummy_backup, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1, "memory": {}}, f)

    backups = list_backups_dir()
    assert dummy_backup in backups

    del_ok, del_msg = delete_backup_file(dummy_backup)
    assert del_ok
    assert not dummy_backup.exists()


def test_export_history_logging(tmp_path):
    dummy_file = tmp_path / "test-export.json"
    dummy_file.touch()

    ok, msg, meta = create_export(dest_input=str(dummy_file))
    assert ok

    history = get_export_history()
    assert len(history) >= 1
    assert history[0]["destination"] == str(dummy_file)
