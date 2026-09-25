"""
Ziggy Core Module Installation API.
"""

from core.installation.manager import (
    InstallationError,
    InstallationResult,
    InvalidInstallationError,
    ModuleAlreadyInstalledError,
    ModuleInstaller,
)

__all__ = [
    "InstallationError",
    "InstallationResult",
    "InvalidInstallationError",
    "ModuleAlreadyInstalledError",
    "ModuleInstaller",
]
