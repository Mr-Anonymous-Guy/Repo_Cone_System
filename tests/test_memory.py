from repo_clone_system.storage.memory import DEFAULT_MEMORY, load_memory, reset_memory


def test_default_memory_structure():
    assert "last_location" in DEFAULT_MEMORY
    assert "locations" in DEFAULT_MEMORY
    assert "repositories" in DEFAULT_MEMORY


def test_reset_memory():
    reset_memory()
    mem = load_memory()
    assert mem["last_location"] == ""
    assert mem["locations"] == []
    assert mem["repositories"] == []
