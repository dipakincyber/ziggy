"""
Ziggy Core Dependency Resolution API.

Dependency resolution determines whether declared module dependencies
are available and compatible. It does not install, load, or execute
modules.
"""

from dataclasses import dataclass
from enum import Enum


class DependencyError(RuntimeError):
    """Base error for dependency resolution."""


class InvalidDependencyError(DependencyError):
    """Raised when dependency information is invalid."""


class CircularDependencyError(DependencyError):
    """Raised when dependencies contain a cycle."""


class DependencyStatus(str, Enum):
    """Result status for an individual dependency."""

    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INCOMPATIBLE = "INCOMPATIBLE"


@dataclass(frozen=True)
class ModuleVersion:
    """Simple semantic version representation."""

    major: int
    minor: int
    patch: int

    def __post_init__(self) -> None:
        if not all(
            isinstance(value, int)
            for value in (self.major, self.minor, self.patch)
        ):
            raise InvalidDependencyError(
                "Version components must be integers."
            )

        if not all(
            value >= 0
            for value in (self.major, self.minor, self.patch)
        ):
            raise InvalidDependencyError(
                "Version components cannot be negative."
            )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, ModuleVersion):
            return NotImplemented

        return (
            self.major,
            self.minor,
            self.patch,
        ) < (
            other.major,
            other.minor,
            other.patch,
        )

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, ModuleVersion):
            return NotImplemented

        return not self < other

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True)
class ModuleDependency:
    """A dependency requiring a minimum module version."""

    name: str
    minimum_version: ModuleVersion

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise InvalidDependencyError(
                "Dependency name must be a string."
            )

        if not self.name.strip():
            raise InvalidDependencyError(
                "Dependency name cannot be empty."
            )

        if not isinstance(self.minimum_version, ModuleVersion):
            raise InvalidDependencyError(
                "Minimum version must be a ModuleVersion."
            )


@dataclass(frozen=True)
class DependencyResult:
    """Result of resolving one dependency."""

    dependency: ModuleDependency
    status: DependencyStatus
    available_version: ModuleVersion | None = None
    reason: str = ""

    @property
    def is_satisfied(self) -> bool:
        """Return whether the dependency is satisfied."""

        return self.status is DependencyStatus.AVAILABLE


class DependencyResolver:
    """
    Resolve module dependencies against a known module inventory.

    The resolver does not install or execute dependencies.
    """

    def __init__(
        self,
        available_modules: dict[str, ModuleVersion] | None = None,
    ) -> None:
        self._modules: dict[str, ModuleVersion] = {}

        if available_modules is not None:
            for name, version in available_modules.items():
                self.register_module(name, version)

    def register_module(
        self,
        name: str,
        version: ModuleVersion,
    ) -> None:
        """Register an available module version."""

        if not isinstance(name, str):
            raise InvalidDependencyError(
                "Module name must be a string."
            )

        if not name.strip():
            raise InvalidDependencyError(
                "Module name cannot be empty."
            )

        if not isinstance(version, ModuleVersion):
            raise InvalidDependencyError(
                "Module version must be a ModuleVersion."
            )

        self._modules[name] = version

    def remove_module(self, name: str) -> None:
        """Remove a module from the available inventory."""

        if name not in self._modules:
            raise DependencyError(
                f"Module '{name}' is not registered."
            )

        del self._modules[name]

    def get_module_version(
        self,
        name: str,
    ) -> ModuleVersion | None:
        """Return the available module version."""

        return self._modules.get(name)

    def resolve(
        self,
        dependency: ModuleDependency,
    ) -> DependencyResult:
        """Resolve one dependency."""

        if not isinstance(dependency, ModuleDependency):
            raise InvalidDependencyError(
                "Expected a ModuleDependency."
            )

        available = self._modules.get(dependency.name)

        if available is None:
            return DependencyResult(
                dependency=dependency,
                status=DependencyStatus.MISSING,
                reason="Dependency is not available.",
            )

        if available < dependency.minimum_version:
            return DependencyResult(
                dependency=dependency,
                status=DependencyStatus.INCOMPATIBLE,
                available_version=available,
                reason=(
                    f"Available version {available} is below "
                    f"required version {dependency.minimum_version}."
                ),
            )

        return DependencyResult(
            dependency=dependency,
            status=DependencyStatus.AVAILABLE,
            available_version=available,
            reason="Dependency requirement is satisfied.",
        )

    def resolve_all(
        self,
        dependencies: tuple[ModuleDependency, ...],
    ) -> tuple[DependencyResult, ...]:
        """Resolve all dependencies deterministically."""

        if not isinstance(dependencies, tuple):
            raise InvalidDependencyError(
                "Dependencies must be provided as a tuple."
            )

        return tuple(
            self.resolve(dependency)
            for dependency in dependencies
        )

    def resolve_order(
        self,
        module_dependencies: dict[
            str,
            tuple[str, ...],
        ],
    ) -> tuple[str, ...]:
        """
        Produce a deterministic dependency-first installation order.

        The mapping contains module names and their direct dependency
        names. Missing inventory entries are not treated as an error
        here; this method only determines graph ordering.
        """

        if not isinstance(module_dependencies, dict):
            raise InvalidDependencyError(
                "Module dependencies must be a dictionary."
            )

        graph = {
            name: tuple(dependencies)
            for name, dependencies in module_dependencies.items()
        }

        for name, dependencies in graph.items():
            if not isinstance(name, str) or not name.strip():
                raise InvalidDependencyError(
                    "Module names cannot be empty."
                )

            if not isinstance(dependencies, tuple):
                raise InvalidDependencyError(
                    "Dependency lists must be tuples."
                )

            for dependency in dependencies:
                if not isinstance(dependency, str):
                    raise InvalidDependencyError(
                        "Dependency names must be strings."
                    )

        visiting: set[str] = set()
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str) -> None:
            if name in visiting:
                raise CircularDependencyError(
                    f"Circular dependency detected at '{name}'."
                )

            if name in visited:
                return

            visiting.add(name)

            for dependency in graph.get(name, ()):
                if dependency in graph:
                    visit(dependency)

            visiting.remove(name)
            visited.add(name)
            order.append(name)

        for name in graph:
            visit(name)

        return tuple(order)
