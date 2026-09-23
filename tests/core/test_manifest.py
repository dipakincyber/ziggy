import pytest

from core.api.version import CoreAPIVersion
from core.modules.manifest import (
    ModuleCompatibility,
    ModuleDependencies,
    ModuleEvents,
    ModuleManifest,
)


def make_manifest() -> ModuleManifest:
    return ModuleManifest(
        name="security",
        version="1.0.0",
        author="Dipak Yadav",
        description="Ziggy security tools",
        compatibility=ModuleCompatibility(
            api_version=1,
            minimum_core_version=CoreAPIVersion(1, 0, 0),
        ),
        dependencies=ModuleDependencies(
            modules=("core",),
            system=("clamav",),
        ),
        capabilities=(
            "filesystem.read",
            "process.inspect",
        ),
        permissions=(
            "filesystem.read",
        ),
        commands=(
            "scan",
            "scan-history",
        ),
        events=ModuleEvents(
            publishes=(
                "security.scan.completed",
            ),
            subscribes=(
                "process.started",
                "file.created",
            ),
        ),
    )


def test_manifest_can_be_created():
    manifest = make_manifest()

    assert manifest.name == "security"
    assert manifest.version == "1.0.0"
    assert manifest.author == "Dipak Yadav"


def test_manifest_compatibility():
    manifest = make_manifest()

    assert manifest.compatibility.api_version == 1
    assert manifest.compatibility.minimum_core_version == CoreAPIVersion(
        1, 0, 0
    )


def test_manifest_dependencies():
    manifest = make_manifest()

    assert "core" in manifest.dependencies.modules
    assert "clamav" in manifest.dependencies.system


def test_manifest_capabilities_and_permissions():
    manifest = make_manifest()

    assert manifest.has_capability("filesystem.read")
    assert manifest.has_capability("process.inspect")
    assert manifest.has_permission("filesystem.read")

    assert not manifest.has_permission("network.control")


def test_manifest_commands():
    manifest = make_manifest()

    assert manifest.provides_command("scan")
    assert manifest.provides_command("scan-history")

    assert not manifest.provides_command("destroy")


def test_manifest_events():
    manifest = make_manifest()

    assert manifest.publishes("security.scan.completed")
    assert manifest.subscribes_to("process.started")
    assert manifest.subscribes_to("file.created")

    assert not manifest.subscribes_to("camera.active")


def test_empty_identity_is_rejected():
    with pytest.raises(ValueError):
        ModuleManifest(
            name="",
            version="1.0.0",
            author="Dipak Yadav",
            description="Test module",
            compatibility=ModuleCompatibility(
                api_version=1,
                minimum_core_version=CoreAPIVersion(1, 0, 0),
            ),
        )


def test_invalid_api_version_is_rejected():
    with pytest.raises(ValueError):
        ModuleCompatibility(
            api_version=0,
            minimum_core_version=CoreAPIVersion(1, 0, 0),
        )


def test_module_name_cannot_contain_whitespace():
    with pytest.raises(ValueError):
        ModuleManifest(
            name="bad module",
            version="1.0.0",
            author="Dipak Yadav",
            description="Test module",
            compatibility=ModuleCompatibility(
                api_version=1,
                minimum_core_version=CoreAPIVersion(1, 0, 0),
            ),
        )
