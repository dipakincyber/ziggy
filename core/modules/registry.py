"""
Ziggy Core Module Registry.

The registry keeps track of module manifests known to the running
Core instance.

The registry does not install, load, execute, or persist modules.
"""

from types import MappingProxyType
from typing import Mapping

from core.modules.manifest import ModuleManifest


class ModuleAlreadyRegisteredError(ValueError):
    """Raised when a module name is already registered."""


class ModuleNotRegisteredError(LookupError):
    """Raised when a requested module is not registered."""


class ModuleRegistry:
    """
    In-memory registry of Ziggy module manifests.

    Module names are unique within a Core runtime.
    """

    def __init__(self) -> None:
        self._modules: dict[str, ModuleManifest] = {}

    def register(self, manifest: ModuleManifest) -> None:
        """
        Register a module manifest.

        A module name may only be registered once.
        """

        if manifest.name in self._modules:
            raise ModuleAlreadyRegisteredError(
                f"Module '{manifest.name}' is already registered."
            )

        self._modules[manifest.name] = manifest

    def unregister(self, name: str) -> None:
        """
        Remove a registered module.

        Raises ModuleNotRegisteredError if the module does not exist.
        """

        if name not in self._modules:
            raise ModuleNotRegisteredError(
                f"Module '{name}' is not registered."
            )

        del self._modules[name]

    def get(self, name: str) -> ModuleManifest:
        """
        Return a registered module manifest.

        Raises ModuleNotRegisteredError if the module does not exist.
        """

        try:
            return self._modules[name]
        except KeyError as exc:
            raise ModuleNotRegisteredError(
                f"Module '{name}' is not registered."
            ) from exc

    def contains(self, name: str) -> bool:
        """Return whether a module is registered."""

        return name in self._modules

    def count(self) -> int:
        """Return the number of registered modules."""

        return len(self._modules)

    def list(self) -> tuple[ModuleManifest, ...]:
        """
        Return all registered module manifests.

        Results are sorted by module name to provide deterministic output.
        """

        return tuple(
            self._modules[name]
            for name in sorted(self._modules)
        )

    def snapshot(self) -> Mapping[str, ModuleManifest]:
        """
        Return a read-only snapshot of the registry.

        Callers cannot modify the registry through the returned mapping.
        """

        return MappingProxyType(self._modules.copy())
