"""
Ziggy Core Module Discovery API.

Discovery identifies possible module locations without installing,
executing, importing, or trusting them.
"""

from dataclasses import dataclass
from pathlib import Path


class DiscoveryError(RuntimeError):
    """Base error for module discovery."""


class InvalidDiscoveryPathError(DiscoveryError):
    """Raised when a discovery path is invalid."""


@dataclass(frozen=True)
class ModuleCandidate:
    """
    A discovered module candidate.

    Discovery only identifies the location and manifest. It does not
    establish trust, compatibility, installation, or executability.
    """

    name: str
    module_path: Path
    manifest_path: Path

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("Module name must be a string.")

        if not self.name.strip():
            raise ValueError("Module name cannot be empty.")

        if not isinstance(self.module_path, Path):
            raise TypeError("Module path must be a pathlib.Path.")

        if not isinstance(self.manifest_path, Path):
            raise TypeError("Manifest path must be a pathlib.Path.")


class ModuleDiscovery:
    """
    Filesystem-based module discovery.

    A directory is considered a candidate when it contains a
    module.yaml manifest.

    Discovery never imports or executes module code.
    """

    MANIFEST_NAME = "module.yaml"

    def discover(self, root: Path) -> tuple[ModuleCandidate, ...]:
        """
        Discover module candidates directly beneath a root directory.

        The root itself may also be a module directory.
        """

        if not isinstance(root, Path):
            raise InvalidDiscoveryPathError(
                "Discovery root must be a pathlib.Path."
            )

        if not root.exists():
            raise InvalidDiscoveryPathError(
                "Discovery root does not exist."
            )

        if not root.is_dir():
            raise InvalidDiscoveryPathError(
                "Discovery root must be a directory."
            )

        candidates: list[ModuleCandidate] = []

        if (root / self.MANIFEST_NAME).is_file():
            candidates.append(
                self._candidate_from_directory(root)
            )

        for child in sorted(root.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue

            manifest = child / self.MANIFEST_NAME

            if manifest.is_file():
                candidates.append(
                    self._candidate_from_directory(child)
                )

        return tuple(candidates)

    def _candidate_from_directory(
        self,
        directory: Path,
    ) -> ModuleCandidate:
        """Create a candidate from a module directory."""

        manifest = directory / self.MANIFEST_NAME

        return ModuleCandidate(
            name=directory.name,
            module_path=directory,
            manifest_path=manifest,
        )
