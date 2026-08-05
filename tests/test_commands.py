from repo_clone_system.ui.commands import COMMAND_MAP, dispatch_command


def test_command_map_keys():
    expected_commands = {
        "clone",
        "repos",
        "locations",
        "alias",
        "memory",
        "export",
        "import",
        "backups",
        "config",
        "doctor",
        "stats",
        "help",
        "clear",
        "update",
        "exit",
    }
    assert expected_commands.issubset(set(COMMAND_MAP.keys()))


def test_dispatch_unknown_command(capsys):
    dispatch_command("unknown_xyz_cmd")
    captured = capsys.readouterr()
    assert "Unknown command" in captured.out
