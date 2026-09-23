"""
Ziggy Core Module Manager.

The module manager coordinates module validation, compatibility checks,
and registration.

It does not install, load, execute, or persist modules.
"""

from typing import Tuple

from core.api.version import CoreAPIVersion
from core.compatibility.checker import (
    CompatibilityChecker,
)
from core.modules.manifest import ModuleManifest
from core.modules.registry import (
    ModuleRegistry,
)


class ModuleRegistrationError(RuntimeError):
    """Raised when a module cannot be registered."""


class ModuleManager:
    """
    Coordinates module admission into the Core registry.

    The manager does not execute module code.
    """

    def __init__(
        self,
        core_version: CoreAPIVersion,
        registry: ModuleRegistry,
    ) -> None:
        self._registry = registry
        self._compatibility_checker = CompatibilityChecker(
            core_version
        )

    def register(self, manifest: ModuleManifest) -> None:
        """
        Validate and register a module.

        A module is registered only when it is compatible with
        the running Core.
        """

        compatibility = self._compatibility_checker.check(
            manifest
        )

        if not compatibility.compatible:
            reasons = "; ".join(compatibility.reasons)

            raise ModuleRegistrationError(
                f"Module '{manifest.name}' is not compatible: "
                f"{reasons}"
            )

        self._registry.register(manifest)

    def unregister(self, name: str) -> None:
        """Remove a module from the Core registry."""

        self._registry.unregister(name)

    def get(self, name: str) -> ModuleManifest:
        """Return a registered module manifest."""

        return self._registry.get(name)

    def contains(self, name: str) -> bool:
        """Return whether a module is registered."""

        return self._registry.contains(name)

    def count(self) -> int:
        """Return the number of registered modules."""

        return self._registry.count()

    def list(self) -> Tuple[ModuleManifest, ...]:
        """Return all registered module manifests."""

        return self._registry.list()
