import pytest

from core.config import (
    InvalidConfigKeyError,
    ModuleConfig,
)


def test_module_config_starts_empty():
    config = ModuleConfig("security")

    assert config.module_name == "security"
    assert config.count() == 0
    assert config.snapshot() == {}


def test_module_name_must_be_string():
    with pytest.raises(TypeError):
        ModuleConfig(123)


def test_module_name_cannot_be_empty():
    with pytest.raises(ValueError):
        ModuleConfig("")


def test_set_and_get_value():
    config = ModuleConfig("security")

    config.set("scan_uploads", False)

    assert config.get("scan_uploads") is False


def test_set_replaces_existing_value():
    config = ModuleConfig("security")

    config.set("scan_timeout", 30)
    config.set("scan_timeout", 60)

    assert config.get("scan_timeout") == 60
    assert config.count() == 1


def test_missing_key_returns_default():
    config = ModuleConfig("security")

    assert config.get("missing") is None
    assert config.get("missing", "fallback") == "fallback"


def test_exists_reports_key_presence():
    config = ModuleConfig("security")

    assert not config.exists("scan_uploads")

    config.set("scan_uploads", True)

    assert config.exists("scan_uploads")


def test_delete_removes_value():
    config = ModuleConfig("security")

    config.set("scan_uploads", True)
    config.delete("scan_uploads")

    assert not config.exists("scan_uploads")
    assert config.count() == 0


def test_delete_missing_key_is_safe():
    config = ModuleConfig("security")

    config.delete("missing")

    assert config.count() == 0


def test_configuration_namespaces_are_isolated():
    security = ModuleConfig("security")
    network = ModuleConfig("network")

    security.set("enabled", True)

    assert security.get("enabled") is True
    assert network.get("enabled") is None


def test_snapshot_contains_current_values():
    config = ModuleConfig("security")

    config.set("scan_uploads", False)
    config.set("timeout", 30)

    snapshot = config.snapshot()

    assert snapshot == {
        "scan_uploads": False,
        "timeout": 30,
    }


def test_snapshot_cannot_modify_configuration():
    config = ModuleConfig("security")

    config.set("timeout", 30)

    snapshot = config.snapshot()

    with pytest.raises(TypeError):
        snapshot["timeout"] = 60

    assert config.get("timeout") == 30


def test_configuration_key_must_be_string():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.set(123, "value")


def test_empty_configuration_key_is_rejected():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.set("", "value")


def test_whitespace_configuration_key_is_rejected():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.set("   ", "value")


def test_get_validates_key():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.get("")


def test_exists_validates_key():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.exists("")


def test_delete_validates_key():
    config = ModuleConfig("security")

    with pytest.raises(InvalidConfigKeyError):
        config.delete("")
