"""
Ziggy Core Compatibility Checker.

This module compares a module's declared requirements against
the capabilities and version of the running Ziggy Core.

It only evaluates compatibility.

It does not install, load, execute, or modify modules.
"""

from dataclasses import dataclass
from typing import Tuple

from core.api.version import CoreAPIVersion
from core.modules.manifest import ModuleManifest


@dataclass(frozen=True)
class CompatibilityResult:
    """
    Result of a module compatibility check.

    compatible:
        True when all checked requirements are satisfied.

    reasons:
        Human-readable explanations for compatibility failures.
    """

    compatible: bool
    reasons: Tuple[str, ...] = ()

    @property
    def is_compatible(self) -> bool:
        """Return whether the module is compatible."""
        return self.compatible


class CompatibilityChecker:
    """
    Checks whether a module can communicate with a given Core version.
    """

    def __init__(self, core_version: CoreAPIVersion) -> None:
        self.core_version = core_version

    def check(self, manifest: ModuleManifest) -> CompatibilityResult:
        """
        Check a module against the current Core version.

        The check currently verifies:

        - Core API version
        - minimum Core version
        """

        reasons: list[str] = []

        self._check_api_version(manifest, reasons)
        self._check_minimum_core_version(manifest, reasons)

        return CompatibilityResult(
            compatible=not reasons,
            reasons=tuple(reasons),
        )

    def _check_api_version(
        self,
        manifest: ModuleManifest,
        reasons: list[str],
    ) -> None:
        """Check whether the module's requested API is supported."""

        if manifest.compatibility.api_version != self.core_version.major:
            reasons.append(
                "Module requires Core API "
                f"{manifest.compatibility.api_version}, "
                f"but Core provides API {self.core_version.major}."
            )

    def _check_minimum_core_version(
        self,
        manifest: ModuleManifest,
        reasons: list[str],
    ) -> None:
        """Check whether Core meets the module's minimum version."""

        required = manifest.compatibility.minimum_core_version
        current = self.core_version

        if self._version_less_than(current, required):
            reasons.append(
                "Module requires minimum Core version "
                f"{required}, but current Core version is {current}."
            )

    @staticmethod
    def _version_less_than(
        current: CoreAPIVersion,
        required: CoreAPIVersion,
    ) -> bool:
        """Return True when current is older than required."""

        return (
            current.major,
            current.minor,
            current.patch,
        ) < (
            required.major,
            required.minor,
            required.patch,
        )
