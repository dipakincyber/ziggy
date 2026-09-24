import pytest

from core.storage import (
    InvalidStorageKeyError,
    ModuleStorage,
)


def test_module_storage_starts_empty():
    storage = ModuleStorage("security")

    assert storage.module_name == "security"
    assert storage.count() == 0
    assert storage.keys() == ()
    assert storage.snapshot() == {}


def test_module_name_must_be_string():
    with pytest.raises(TypeError):
        ModuleStorage(123)


def test_module_name_cannot_be_empty():
    with pytest.raises(ValueError):
        ModuleStorage("")


def test_set_and_get_value():
    storage = ModuleStorage("security")

    storage.set("scan_count", 10)

    assert storage.get("scan_count") == 10


def test_set_replaces_existing_value():
    storage = ModuleStorage("security")

    storage.set("scan_count", 10)
    storage.set("scan_count", 20)

    assert storage.get("scan_count") == 20
    assert storage.count() == 1


def test_missing_key_returns_default():
    storage = ModuleStorage("security")

    assert storage.get("missing") is None
    assert storage.get("missing", "fallback") == "fallback"


def test_exists_reports_key_presence():
    storage = ModuleStorage("security")

    assert not storage.exists("scan_count")

    storage.set("scan_count", 10)

    assert storage.exists("scan_count")


def test_delete_removes_value():
    storage = ModuleStorage("security")

    storage.set("scan_count", 10)
    storage.delete("scan_count")

    assert not storage.exists("scan_count")
    assert storage.count() == 0


def test_delete_missing_key_is_safe():
    storage = ModuleStorage("security")

    storage.delete("missing")

    assert storage.count() == 0


def test_keys_are_sorted():
    storage = ModuleStorage("security")

    storage.set("zebra", 1)
    storage.set("alpha", 2)
    storage.set("middle", 3)

    assert storage.keys() == (
        "alpha",
        "middle",
        "zebra",
    )


def test_storage_namespaces_are_isolated():
    security = ModuleStorage("security")
    network = ModuleStorage("network")

    security.set("enabled", True)

    assert security.get("enabled") is True
    assert network.get("enabled") is None


def test_snapshot_contains_current_values():
    storage = ModuleStorage("security")

    storage.set("scan_count", 10)
    storage.set("last_scan", "today")

    snapshot = storage.snapshot()

    assert snapshot == {
        "scan_count": 10,
        "last_scan": "today",
    }


def test_snapshot_cannot_modify_storage():
    storage = ModuleStorage("security")

    storage.set("scan_count", 10)

    snapshot = storage.snapshot()

    with pytest.raises(TypeError):
        snapshot["scan_count"] = 20

    assert storage.get("scan_count") == 10


def test_storage_key_must_be_string():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.set(123, "value")


def test_empty_storage_key_is_rejected():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.set("", "value")


def test_whitespace_storage_key_is_rejected():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.set("   ", "value")


def test_get_validates_key():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.get("")


def test_exists_validates_key():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.exists("")


def test_delete_validates_key():
    storage = ModuleStorage("security")

    with pytest.raises(InvalidStorageKeyError):
        storage.delete("")
