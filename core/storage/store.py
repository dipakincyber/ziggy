"""
Ziggy Core Storage API.

This module provides the foundational storage contract for
Ziggy modules.

The initial implementation is in-memory. Persistence is deliberately
left to a later Core layer.
"""

from types import MappingProxyType
from typing import Any, Mapping


class StorageError(RuntimeError):
    """Base error for storage operations."""


class InvalidStorageKeyError(StorageError):
    """Raised when a storage key is invalid."""


class ModuleStorage:
    """
    Storage namespace belonging to one module.

    Each ModuleStorage instance owns an isolated key/value namespace.
    """

    def __init__(self, module_name: str) -> None:
        if not isinstance(module_name, str):
            raise TypeError("Module name must be a string.")

        if not module_name.strip():
            raise ValueError("Module name cannot be empty.")

        self._module_name = module_name
        self._values: dict[str, Any] = {}

    @property
    def module_name(self) -> str:
        """Return the owning module name."""

        return self._module_name

    def set(self, key: str, value: Any) -> None:
        """Set or replace a stored value."""

        self._validate_key(key)
        self._values[key] = value

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a stored value or the supplied default."""

        self._validate_key(key)

        return self._values.get(key, default)

    def exists(self, key: str) -> bool:
        """Return whether a storage key exists."""

        self._validate_key(key)

        return key in self._values

    def delete(self, key: str) -> None:
        """Delete a stored value if it exists."""

        self._validate_key(key)
        self._values.pop(key, None)

    def keys(self) -> tuple[str, ...]:
        """Return all storage keys in deterministic order."""

        return tuple(sorted(self._values))

    def count(self) -> int:
        """Return the number of stored values."""

        return len(self._values)

    def snapshot(self) -> Mapping[str, Any]:
        """
        Return a read-only snapshot of the stored values.

        Mutating the returned mapping cannot modify the storage.
        """

        return MappingProxyType(self._values.copy())

    @staticmethod
    def _validate_key(key: str) -> None:
        """Validate a storage key."""

        if not isinstance(key, str):
            raise InvalidStorageKeyError(
                "Storage key must be a string."
            )

        if not key.strip():
            raise InvalidStorageKeyError(
                "Storage key cannot be empty."
            )
