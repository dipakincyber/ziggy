"""
Ziggy Core Module Permissions.

This module defines the permission and capability model used by
Ziggy Core.

This layer records and evaluates Ziggy-level authorization decisions.
It does not directly enforce operating-system permissions.
"""

from enum import Enum


class ModuleCapability(str, Enum):
    """Broad areas of access a Ziggy module may request."""

    FILESYSTEM = "filesystem"
    PROCESS = "process"
    NETWORK = "network"
    DEVICE = "device"
    SYSTEM_CONFIG = "system_config"
    CAMERA = "camera"
    MICROPHONE = "microphone"


class ModulePermission(str, Enum):
    """Specific operations a Ziggy module may request."""

    FILESYSTEM_READ = "filesystem.read"
    FILESYSTEM_WRITE = "filesystem.write"

    PROCESS_INSPECT = "process.inspect"
    PROCESS_CONTROL = "process.control"

    NETWORK_CONNECT = "network.connect"

    DEVICE_INSPECT = "device.inspect"

    SYSTEM_CONFIG_READ = "system_config.read"
    SYSTEM_CONFIG_WRITE = "system_config.write"

    CAMERA_ACCESS = "camera.access"
    MICROPHONE_ACCESS = "microphone.access"

    @property
    def capability(self) -> ModuleCapability:
        """Return the capability associated with this permission."""

        capability_name = self.value.split(".", 1)[0]
        return ModuleCapability(capability_name)


class PermissionError(RuntimeError):
    """Base error for permission operations."""


class InvalidPermissionError(PermissionError):
    """Raised when an invalid permission or capability is supplied."""


class PermissionManager:
    """
    Manage Ziggy-level permissions granted to a module.

    This manager does not enforce Linux permissions directly.
    """

    def __init__(self) -> None:
        self._granted: set[ModulePermission] = set()

    def grant(self, permission: ModulePermission) -> None:
        """Grant a permission to the module."""

        if not isinstance(permission, ModulePermission):
            raise InvalidPermissionError(
                f"Invalid module permission: {permission!r}"
            )

        self._granted.add(permission)

    def revoke(self, permission: ModulePermission) -> None:
        """Revoke a previously granted permission."""

        if not isinstance(permission, ModulePermission):
            raise InvalidPermissionError(
                f"Invalid module permission: {permission!r}"
            )

        self._granted.discard(permission)

    def is_allowed(
        self,
        permission: ModulePermission,
    ) -> bool:
        """Return whether a permission is currently granted."""

        if not isinstance(permission, ModulePermission):
            raise InvalidPermissionError(
                f"Invalid module permission: {permission!r}"
            )

        return permission in self._granted

    def list_granted(self) -> tuple[ModulePermission, ...]:
        """
        Return all granted permissions.

        Results are sorted by their stable string value.
        """

        return tuple(
            sorted(
                self._granted,
                key=lambda permission: permission.value,
            )
        )

    def clear(self) -> None:
        """Revoke all currently granted permissions."""

        self._granted.clear()

    def count(self) -> int:
        """Return the number of granted permissions."""

        return len(self._granted)
