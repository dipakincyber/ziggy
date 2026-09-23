import pytest

from core.modules.permissions import (
    InvalidPermissionError,
    ModuleCapability,
    ModulePermission,
    PermissionManager,
)


def test_capabilities_are_defined():
    assert ModuleCapability.FILESYSTEM.value == "filesystem"
    assert ModuleCapability.PROCESS.value == "process"
    assert ModuleCapability.NETWORK.value == "network"
    assert ModuleCapability.DEVICE.value == "device"
    assert ModuleCapability.SYSTEM_CONFIG.value == "system_config"
    assert ModuleCapability.CAMERA.value == "camera"
    assert ModuleCapability.MICROPHONE.value == "microphone"


def test_permission_values_are_defined():
    assert (
        ModulePermission.FILESYSTEM_READ.value
        == "filesystem.read"
    )

    assert (
        ModulePermission.FILESYSTEM_WRITE.value
        == "filesystem.write"
    )

    assert (
        ModulePermission.PROCESS_INSPECT.value
        == "process.inspect"
    )

    assert (
        ModulePermission.NETWORK_CONNECT.value
        == "network.connect"
    )


def test_permission_maps_to_capability():
    assert (
        ModulePermission.FILESYSTEM_READ.capability
        == ModuleCapability.FILESYSTEM
    )

    assert (
        ModulePermission.PROCESS_CONTROL.capability
        == ModuleCapability.PROCESS
    )

    assert (
        ModulePermission.CAMERA_ACCESS.capability
        == ModuleCapability.CAMERA
    )


def test_permission_manager_starts_empty():
    manager = PermissionManager()

    assert manager.count() == 0
    assert manager.list_granted() == ()


def test_grant_permission():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)

    assert manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    assert manager.count() == 1


def test_granting_same_permission_is_idempotent():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)
    manager.grant(ModulePermission.FILESYSTEM_READ)

    assert manager.count() == 1


def test_unrelated_permission_is_not_granted():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)

    assert not manager.is_allowed(
        ModulePermission.FILESYSTEM_WRITE
    )


def test_revoke_permission():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)
    manager.revoke(ModulePermission.FILESYSTEM_READ)

    assert not manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    assert manager.count() == 0


def test_revoke_missing_permission_is_safe():
    manager = PermissionManager()

    manager.revoke(ModulePermission.FILESYSTEM_READ)

    assert manager.count() == 0


def test_list_granted_is_sorted():
    manager = PermissionManager()

    manager.grant(ModulePermission.NETWORK_CONNECT)
    manager.grant(ModulePermission.FILESYSTEM_WRITE)
    manager.grant(ModulePermission.CAMERA_ACCESS)

    assert manager.list_granted() == (
        ModulePermission.CAMERA_ACCESS,
        ModulePermission.FILESYSTEM_WRITE,
        ModulePermission.NETWORK_CONNECT,
    )


def test_clear_removes_all_permissions():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)
    manager.grant(ModulePermission.PROCESS_INSPECT)

    manager.clear()

    assert manager.count() == 0
    assert manager.list_granted() == ()


def test_invalid_grant_is_rejected():
    manager = PermissionManager()

    with pytest.raises(InvalidPermissionError):
        manager.grant("filesystem.read")


def test_invalid_revoke_is_rejected():
    manager = PermissionManager()

    with pytest.raises(InvalidPermissionError):
        manager.revoke("filesystem.read")


def test_invalid_permission_check_is_rejected():
    manager = PermissionManager()

    with pytest.raises(InvalidPermissionError):
        manager.is_allowed("filesystem.read")


def test_permissions_are_specific():
    manager = PermissionManager()

    manager.grant(ModulePermission.FILESYSTEM_READ)

    assert manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    assert not manager.is_allowed(
        ModulePermission.FILESYSTEM_WRITE
    )

    assert not manager.is_allowed(
        ModulePermission.PROCESS_INSPECT
    )
