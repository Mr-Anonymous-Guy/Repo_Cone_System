import json
import pytest
from pathlib import Path

from repo_clone_system.services.backup_service import (
    get_backups_dir,
    rotate_auto_backups,
)
from repo_clone_system.services.profile_service import (
    create_profile,
    get_active_profile_name,
    list_profiles,
    remove_profile,
    rename_profile,
    switch_profile,
)
from repo_clone_system.services.sync_providers import (
    CustomSyncProvider,
    DropboxSyncProvider,
    GitHubGistSyncProvider,
    GoogleDriveSyncProvider,
    LocalFolderSyncProvider,
    OneDriveSyncProvider,
)
from repo_clone_system.services.sync_service import (
    configure_sync_folder,
    export_sync,
    get_sync_status,
    locate_latest_sync_backup,
)
from repo_clone_system.services.workspace_service import (
    export_workspace,
    get_workspace_info,
)
from repo_clone_system.storage.memory import (
    memory,
    reset_memory,
    save_memory,
)


@pytest.fixture(autouse=True)
def clean_memory():
    reset_memory()
    yield
    reset_memory()


def test_export_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory["repositories"] = [{"url": "https://github.com/foo/bar.git", "name": "bar"}]
    memory["locations"] = [str(tmp_path / "work")]
    memory["aliases"] = {"work": str(tmp_path / "work")}
    save_memory(memory)

    ok, msg, metadata = export_workspace()
    assert ok
    assert "exported successfully" in msg.lower()
    assert metadata["repo_count"] == 1
    assert metadata["location_count"] == 1
    assert metadata["alias_count"] == 1
    assert Path(metadata["path"]).exists()


def test_get_workspace_info():
    info = get_workspace_info()
    assert info["workspace_name"] == "Default"
    assert info["active_profile"] == "Default"
    assert "schema_version" in info
    assert "package_version" in info


def test_profile_lifecycle(tmp_path):
    profiles = list_profiles()
    assert "Default" in profiles

    ok, msg = create_profile("Corporate")
    assert ok

    ok_sw, msg_sw = switch_profile("Corporate")
    assert ok_sw
    assert get_active_profile_name() == "Corporate"

    # Add data to Office profile
    memory["aliases"] = {"office_docs": str(tmp_path / "docs")}
    save_memory(memory)

    # Switch back to Default profile
    ok_sw_def, _ = switch_profile("Default")
    assert ok_sw_def
    assert get_active_profile_name() == "Default"
    assert "office_docs" not in memory.get("aliases", {})

    # Rename Corporate to WorkCorporate
    ok_rn, _ = rename_profile("Corporate", "WorkCorporate")
    assert ok_rn
    assert "WorkCorporate" in list_profiles()

    # Remove WorkCorporate
    ok_rm, _ = remove_profile("WorkCorporate")
    assert ok_rm
    assert "WorkCorporate" not in list_profiles()


def test_sync_manager(tmp_path):
    sync_folder = tmp_path / "SyncFolder"
    ok_cfg, msg_cfg = configure_sync_folder(str(sync_folder))
    assert ok_cfg
    assert sync_folder.exists()

    ok_exp, msg_exp, sync_file = export_sync()
    assert ok_exp
    assert sync_file.exists()

    ok_loc, msg_loc, latest_path, data = locate_latest_sync_backup()
    assert ok_loc
    assert latest_path == sync_file
    assert data["schema_version"] == 1

    status = get_sync_status()
    assert status["sync_folder"] == str(sync_folder.resolve())
    assert status["latest_backup"] == sync_file.name


def test_sync_providers_architecture(tmp_path):
    local_p = LocalFolderSyncProvider(str(tmp_path))
    assert local_p.is_configured()

    onedrive_p = OneDriveSyncProvider()
    dropbox_p = DropboxSyncProvider()
    gdrive_p = GoogleDriveSyncProvider()
    gist_p = GitHubGistSyncProvider()
    custom_p = CustomSyncProvider()

    for provider in (onedrive_p, dropbox_p, gdrive_p, gist_p, custom_p):
        assert not provider.is_configured()
        ok, msg, _ = provider.export_sync({})
        assert not ok


def test_auto_backup_rotation():
    backups_dir = get_backups_dir()

    # Create 25 dummy auto-backups and 1 manual export
    for i in range(25):
        f_path = backups_dir / f"auto-backup-test-{i:02d}.json"
        with open(f_path, "w", encoding="utf-8") as f:
            json.dump({"schema_version": 1}, f)

    manual_file = backups_dir / "workspace-backup-manual.json"
    with open(manual_file, "w", encoding="utf-8") as f:
        json.dump({"schema_version": 1}, f)

    rotate_auto_backups(max_keep=20)

    auto_files = [
        f for f in backups_dir.glob("*.json") if f.name.startswith("auto-backup-")
    ]
    assert len(auto_files) == 20
    assert manual_file.exists()


def test_workspace_cli_commands(capsys):
    from repo_clone_system.ui.commands import command_workspace

    command_workspace(["create", "TestEnv"])
    assert "TestEnv" in list_profiles()

    command_workspace(["switch", "TestEnv"])
    assert get_active_profile_name() == "TestEnv"

    command_workspace(["info"])
    captured = capsys.readouterr().out
    assert "Workspace Information" in captured
    assert "TestEnv" in captured

    command_workspace(["switch", "Default"])
    assert get_active_profile_name() == "Default"

    command_workspace(["remove", "TestEnv"])
    assert "TestEnv" not in list_profiles()
