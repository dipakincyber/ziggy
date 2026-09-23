import pytest

from core.api.version import CoreAPIVersion
from core.modules.manifest import (
    ModuleCompatibility,
    ModuleManifest,
)
from core.modules.registry import (
    ModuleAlreadyRegisteredError,
    ModuleNotRegisteredError,
    ModuleRegistry,
)


def make_manifest(name: str) -> ModuleManifest:
    return ModuleManifest(
        name=name,
        version="1.0.0",
        author="Dipak Yadav",
        description=f"{name} test module",
        compatibility=ModuleCompatibility(
            api_version=1,
            minimum_core_version=CoreAPIVersion(1, 0, 0),
        ),
    )


def test_registry_starts_empty():
    registry = ModuleRegistry()

    assert registry.count() == 0
    assert registry.list() == ()


def test_register_module():
    registry = ModuleRegistry()
    manifest = make_manifest("security")

    registry.register(manifest)

    assert registry.count() == 1
    assert registry.contains("security")
    assert registry.get("security") == manifest


def test_register_multiple_modules():
    registry = ModuleRegistry()

    security = make_manifest("security")
    network = make_manifest("network")

    registry.register(security)
    registry.register(network)

    assert registry.count() == 2
    assert registry.contains("security")
    assert registry.contains("network")


def test_duplicate_module_is_rejected():
    registry = ModuleRegistry()

    registry.register(make_manifest("security"))

    with pytest.raises(ModuleAlreadyRegisteredError):
        registry.register(make_manifest("security"))


def test_missing_module_lookup_is_rejected():
    registry = ModuleRegistry()

    with pytest.raises(ModuleNotRegisteredError):
        registry.get("security")


def test_unregister_module():
    registry = ModuleRegistry()

    registry.register(make_manifest("security"))

    registry.unregister("security")

    assert registry.count() == 0
    assert not registry.contains("security")


def test_unregister_missing_module_is_rejected():
    registry = ModuleRegistry()

    with pytest.raises(ModuleNotRegisteredError):
        registry.unregister("security")


def test_list_is_sorted_by_module_name():
    registry = ModuleRegistry()

    registry.register(make_manifest("security"))
    registry.register(make_manifest("network"))
    registry.register(make_manifest("sandbox"))

    modules = registry.list()

    assert [module.name for module in modules] == [
        "network",
        "sandbox",
        "security",
    ]


def test_snapshot_cannot_modify_registry():
    registry = ModuleRegistry()

    registry.register(make_manifest("security"))

    snapshot = registry.snapshot()

    assert snapshot["security"].name == "security"

    with pytest.raises(TypeError):
        snapshot["network"] = make_manifest("network")

    assert registry.count() == 1
