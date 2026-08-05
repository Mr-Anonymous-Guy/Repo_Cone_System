from pathlib import Path
from repo_clone_system.services.location_service import (
    add_location,
    clean_missing_locations,
    get_saved_locations,
    remove_location,
    rename_location,
    verify_locations,
)
from repo_clone_system.storage.memory import memory, reset_memory


def setup_function():
    reset_memory()


def test_add_and_get_locations(tmp_path):
    ok, msg = add_location(str(tmp_path))
    assert ok
    assert str(tmp_path.resolve()) in get_saved_locations()

    # Duplicate check
    ok_dup, msg_dup = add_location(str(tmp_path))
    assert not ok_dup
    assert "already saved" in msg_dup


def test_add_location_missing_parent():
    bad_path = str(Path("/nonexistent_folder_abc123/sub_dir_xyz"))
    ok, msg = add_location(bad_path, auto_create_missing=False)
    assert not ok
    assert "does not exist" in msg


def test_remove_location(tmp_path):
    loc_path = str(tmp_path.resolve())
    add_location(loc_path)
    assert loc_path in get_saved_locations()

    ok, msg = remove_location(loc_path)
    assert ok
    assert loc_path not in get_saved_locations()


def test_rename_location(tmp_path):
    loc_path = str(tmp_path.resolve())
    add_location(loc_path)

    new_dir = tmp_path / "renamed_dir"
    new_dir.mkdir()
    new_path = str(new_dir.resolve())

    ok, msg = rename_location(loc_path, new_path)
    assert ok
    assert new_path in get_saved_locations()
    assert loc_path not in get_saved_locations()


def test_verify_and_clean_locations(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    add_location(str(real_dir))

    fake_path = str(tmp_path / "fake_dir_123")
    memory["locations"].append(fake_path)

    report = verify_locations()
    assert report[str(real_dir.resolve())]["exists"]
    assert not report[fake_path]["exists"]

    count, msg = clean_missing_locations([fake_path])
    assert count == 1
    assert fake_path not in get_saved_locations()
