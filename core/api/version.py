"""
Ziggy Core API Versioning

This module defines the public API version exposed by Ziggy Core.

Modules depend on this API contract rather than Core's internal
implementation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreAPIVersion:
    """
    Represents a Ziggy Core API version.

    major:
        Breaking API changes.

    minor:
        Backwards-compatible API additions.

    patch:
        Bug fixes that do not change the API contract.
    """

    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


# Current public Core API version.
CORE_API_VERSION = CoreAPIVersion(
    major=1,
    minor=0,
    patch=0,
)


def get_core_api_version() -> CoreAPIVersion:
    """Return the public Ziggy Core API version."""
    return CORE_API_VERSION
