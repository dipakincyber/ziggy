import pytest

from core.api.version import CoreAPIVersion
from core.modules.manifest import (
    ModuleCompatibility,
    ModuleManifest,
)
from core.modules.manager import (
    ModuleManager,
    ModuleRegistrationError,
)
from core.modules.registry import ModuleRegistry


def make_manifest(
    name: str,
    api_version: int = 1,
    minimum_core_version: CoreAPIVersion = CoreAPIVersion(
        1,
        0,
        0,
    ),
) -> ModuleManifest:
    return ModuleManifest(
        name=name,
        version="1.0.0",
        author="Dipak Yadav",
        description=f"{name} test module",
        compatibility=ModuleCompatibility(
            api_version=api_version,
            minimum_core_version=minimum_core_version,
        ),
    )


def make_manager() -> ModuleManager:
    return ModuleManager(
        core_version=CoreAPIVersion(1, 0, 0),
        registry=ModuleRegistry(),
    )


def test_manager_starts_empty():
    manager = make_manager()

    assert manager.count() == 0
    assert manager.list() == ()


def test_manager_registers_compatible_module():
    manager = make_manager()
    manifest = make_manifest("security")

    manager.register(manifest)

    assert manager.count() == 1
    assert manager.contains("security")
    assert manager.get("security") == manifest


def test_manager_rejects_incompatible_api_version():
    manager = make_manager()
    manifest = make_manifest(
        "security",
        api_version=2,
    )

    with pytest.raises(ModuleRegistrationError):
        manager.register(manifest)

    assert manager.count() == 0
    assert not manager.contains("security")


def test_manager_rejects_module_requiring_newer_core():
    manager = make_manager()
    manifest = make_manifest(
        "security",
        minimum_core_version=CoreAPIVersion(
            2,
            0,
            0,
        ),
    )

    with pytest.raises(ModuleRegistrationError):
        manager.register(manifest)

    assert manager.count() == 0
    assert not manager.contains("security")


def test_manager_preserves_compatibility_failure_reasons():
    manager = make_manager()
    manifest = make_manifest(
        "security",
        api_version=2,
        minimum_core_version=CoreAPIVersion(
            2,
            0,
            0,
        ),
    )

    with pytest.raises(ModuleRegistrationError) as error:
        manager.register(manifest)

    message = str(error.value)

    assert "Core API" in message
    assert "minimum Core version" in message


def test_manager_unregisters_module():
    manager = make_manager()

    manager.register(make_manifest("security"))
    manager.unregister("security")

    assert manager.count() == 0
    assert not manager.contains("security")


def test_manager_lists_registered_modules():
    manager = make_manager()

    manager.register(make_manifest("security"))
    manager.register(make_manifest("network"))

    modules = manager.list()

    assert [module.name for module in modules] == [
        "network",
        "security",
    ]


def test_manager_rejects_duplicate_registration():
    manager = make_manager()

    manager.register(make_manifest("security"))

    with pytest.raises(ValueError):
        manager.register(make_manifest("security"))


def test_manager_uses_supplied_registry():
    registry = ModuleRegistry()

    manager = ModuleManager(
        core_version=CoreAPIVersion(1, 0, 0),
        registry=registry,
    )

    manager.register(make_manifest("security"))

    assert registry.contains("security")
    assert registry.count() == 1
