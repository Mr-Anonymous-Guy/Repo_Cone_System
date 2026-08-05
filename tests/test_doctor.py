from repo_clone_system.services.doctor_service import CheckResult, run_doctor


def test_run_doctor():
    results = run_doctor()
    assert isinstance(results, list)
    assert len(results) >= 5

    labels = [r.label for r in results]
    assert "Git Installed" in labels
    assert "Python Version" in labels
    assert "Memory File" in labels
    assert "Configuration Folder" in labels

    for item in results:
        assert isinstance(item, CheckResult)
        assert item.status in ("✔", "✖", "⚠")
