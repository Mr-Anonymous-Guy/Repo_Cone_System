from repo_clone_system.services.config_service import get_config_info
from repo_clone_system.ui.commands import command_config


def test_get_config_info():
    info = get_config_info()
    assert "version" in info
    assert "memory_file" in info
    assert "config_folder" in info
    assert "os" in info
    assert "python_version" in info
    assert "saved_repos" in info
    assert "saved_locations" in info
    assert "saved_aliases" in info


def test_command_config_output(capsys):
    command_config()
    captured = capsys.readouterr()
    assert "Repo_Clone_System Configuration" in captured.out
    assert "Memory File" in captured.out
    assert "Configuration Folder" in captured.out
