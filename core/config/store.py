"""
Ziggy Core Configuration API.

This module provides the foundational configuration contract for
Ziggy modules.

The initial implementation is in-memory. Persistence is deliberately
left to a later Core layer.
"""

from types import MappingProxyType
from typing import Any, Mapping


class ConfigError(RuntimeError):
    """Base error for configuration operations."""


class InvalidConfigKeyError(ConfigError):
    """Raised when a configuration key is invalid."""


class ModuleConfig:
    """
    Configuration namespace belonging to one module.

    Each ModuleConfig instance owns an isolated key/value namespace.
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
        """Set or replace a configuration value."""

        self._validate_key(key)
        self._values[key] = value

    def get(
        self,
        key: str,
        default: Any = None,
    ) -> Any:
        """Return a configuration value or the supplied default."""

        self._validate_key(key)

        return self._values.get(key, default)

    def exists(self, key: str) -> bool:
        """Return whether a configuration key exists."""

        self._validate_key(key)

        return key in self._values

    def delete(self, key: str) -> None:
        """Delete a configuration key if it exists."""

        self._validate_key(key)
        self._values.pop(key, None)

    def count(self) -> int:
        """Return the number of configuration values."""

        return len(self._values)

    def snapshot(self) -> Mapping[str, Any]:
        """
        Return a read-only snapshot of the configuration.

        Mutating the returned mapping cannot modify the configuration.
        """

        return MappingProxyType(self._values.copy())

    @staticmethod
    def _validate_key(key: str) -> None:
        """Validate a configuration key."""

        if not isinstance(key, str):
            raise InvalidConfigKeyError(
                "Configuration key must be a string."
            )

        if not key.strip():
            raise InvalidConfigKeyError(
                "Configuration key cannot be empty."
            )
