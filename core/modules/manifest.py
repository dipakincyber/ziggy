"""
Ziggy Core Module Manifest

Defines the structured contract used by Ziggy Core to understand
and validate modules before they are loaded.
"""

from dataclasses import dataclass, field
from typing import Tuple

from core.api.version import CoreAPIVersion


@dataclass(frozen=True)
class ModuleCompatibility:
    """Compatibility requirements declared by a module."""

    api_version: int
    minimum_core_version: CoreAPIVersion

    def __post_init__(self) -> None:
        if self.api_version < 1:
            raise ValueError("Module API version must be at least 1.")


@dataclass(frozen=True)
class ModuleDependencies:
    """Dependencies required by a module."""

    modules: Tuple[str, ...] = field(default_factory=tuple)
    system: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ModuleEvents:
    """Events a module publishes and subscribes to."""

    publishes: Tuple[str, ...] = field(default_factory=tuple)
    subscribes: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ModuleManifest:
    """
    Complete identity and requirements of a Ziggy module.

    This object describes a module. It does not load or execute it.
    """

    name: str
    version: str
    author: str
    description: str

    compatibility: ModuleCompatibility

    dependencies: ModuleDependencies = field(
        default_factory=ModuleDependencies
    )

    capabilities: Tuple[str, ...] = field(default_factory=tuple)

    permissions: Tuple[str, ...] = field(default_factory=tuple)

    commands: Tuple[str, ...] = field(default_factory=tuple)

    events: ModuleEvents = field(default_factory=ModuleEvents)

    def __post_init__(self) -> None:
        self._validate_identity()

    def _validate_identity(self) -> None:
        """Validate the module's basic identity fields."""

        if not self.name.strip():
            raise ValueError("Module name cannot be empty.")

        if not self.version.strip():
            raise ValueError("Module version cannot be empty.")

        if not self.author.strip():
            raise ValueError("Module author cannot be empty.")

        if not self.description.strip():
            raise ValueError("Module description cannot be empty.")

        if "/" in self.name or "\\" in self.name:
            raise ValueError("Module name cannot contain path separators.")

        if any(character.isspace() for character in self.name):
            raise ValueError("Module name cannot contain whitespace.")

    def has_permission(self, permission: str) -> bool:
        """Return whether the module declares a specific permission."""

        return permission in self.permissions

    def has_capability(self, capability: str) -> bool:
        """Return whether the module declares a specific capability."""

        return capability in self.capabilities

    def provides_command(self, command: str) -> bool:
        """Return whether the module declares a specific command."""

        return command in self.commands

    def subscribes_to(self, event: str) -> bool:
        """Return whether the module subscribes to an event."""

        return event in self.events.subscribes

    def publishes(self, event: str) -> bool:
        """Return whether the module publishes an event."""

        return event in self.events.publishes
