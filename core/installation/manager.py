"""
Ziggy Core Module Installation API.

Installation copies a discovered module into Ziggy's managed module
directory. Installation does not register, enable, trust, or execute
the module.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

from core.discovery import ModuleCandidate


class InstallationError(RuntimeError):
    """Base error for module installation."""


class InvalidInstallationError(InstallationError):
    """Raised when installation input is invalid."""


class ModuleAlreadyInstalledError(InstallationError):
    """Raised when a module is already installed."""


@dataclass(frozen=True)
class InstallationResult:
    """
    Result of a successful module installation.
    """

    name: str
    source_path: Path
    installed_path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidInstallationError(
                "Module name cannot be empty."
            )

        if not isinstance(self.source_path, Path):
            raise TypeError("Source path must be a pathlib.Path.")

        if not isinstance(self.installed_path, Path):
            raise TypeError("Installed path must be a pathlib.Path.")


class ModuleInstaller:
    """
    Installs discovered modules into a managed installation root.

    The installer performs filesystem operations only. It does not
    import, execute, register, enable, or trust modules.
    """

    def __init__(self, installation_root: Path) -> None:
        if not isinstance(installation_root, Path):
            raise InvalidInstallationError(
                "Installation root must be a pathlib.Path."
            )

        self.installation_root = installation_root

    def install(
        self,
        candidate: ModuleCandidate,
    ) -> InstallationResult:
        """
        Install a discovered module candidate.

        The source directory must exist and contain module.yaml.
        The destination must not already exist.
        """

        if not isinstance(candidate, ModuleCandidate):
            raise InvalidInstallationError(
                "Installation requires a ModuleCandidate."
            )

        source = candidate.module_path
        manifest = candidate.manifest_path
        destination = self.installation_root / candidate.name

        self._validate_source(source, manifest)

        if destination.exists():
            raise ModuleAlreadyInstalledError(
                f"Module '{candidate.name}' is already installed."
            )

        self.installation_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            shutil.copytree(
                source,
                destination,
            )
        except Exception as exc:
            if destination.exists():
                shutil.rmtree(destination)

            raise InstallationError(
                f"Failed to install module '{candidate.name}'."
            ) from exc

        return InstallationResult(
            name=candidate.name,
            source_path=source,
            installed_path=destination,
        )

    def is_installed(self, name: str) -> bool:
        """Return whether a module directory exists."""

        if not isinstance(name, str):
            raise TypeError("Module name must be a string.")

        if not name.strip():
            raise ValueError("Module name cannot be empty.")

        return (self.installation_root / name).is_dir()

    def uninstall(self, name: str) -> None:
        """
        Remove an installed module.

        Uninstallation is filesystem-only and does not alter registry
        or lifecycle state.
        """

        if not isinstance(name, str):
            raise TypeError("Module name must be a string.")

        if not name.strip():
            raise ValueError("Module name cannot be empty.")

        destination = self.installation_root / name

        if not destination.exists():
            raise InstallationError(
                f"Module '{name}' is not installed."
            )

        if not destination.is_dir():
            raise InstallationError(
                f"Installation path for '{name}' is not a directory."
            )

        shutil.rmtree(destination)

    def _validate_source(
        self,
        source: Path,
        manifest: Path,
    ) -> None:
        """Validate the discovered module source."""

        if not source.exists():
            raise InvalidInstallationError(
                "Module source does not exist."
            )

        if not source.is_dir():
            raise InvalidInstallationError(
                "Module source must be a directory."
            )

        if not manifest.exists():
            raise InvalidInstallationError(
                "Module manifest does not exist."
            )

        if not manifest.is_file():
            raise InvalidInstallationError(
                "Module manifest must be a file."
            )
