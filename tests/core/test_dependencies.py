import pytest

from core.dependencies import (
    CircularDependencyError,
    DependencyError,
    DependencyResolver,
    DependencyStatus,
    InvalidDependencyError,
    ModuleDependency,
    ModuleVersion,
)


def version(major, minor, patch):
    return ModuleVersion(major, minor, patch)


def dependency(name, major, minor, patch):
    return ModuleDependency(
        name=name,
        minimum_version=version(major, minor, patch),
    )


def test_module_version():
    current = version(1, 2, 3)

    assert current.major == 1
    assert current.minor == 2
    assert current.patch == 3
    assert str(current) == "1.2.3"


def test_module_version_comparison():
    assert version(1, 0, 0) < version(1, 1, 0)
    assert version(1, 1, 0) < version(2, 0, 0)
    assert version(1, 2, 3) >= version(1, 2, 3)


def test_module_version_rejects_non_integer():
    with pytest.raises(InvalidDependencyError):
        ModuleVersion("1", 0, 0)


def test_module_version_rejects_negative():
    with pytest.raises(InvalidDependencyError):
        ModuleVersion(-1, 0, 0)


def test_dependency_requires_name():
    with pytest.raises(InvalidDependencyError):
        ModuleDependency(
            "",
            version(1, 0, 0),
        )


def test_dependency_requires_version():
    with pytest.raises(InvalidDependencyError):
        ModuleDependency(
            "network",
            "1.0.0",
        )


def test_resolver_starts_empty():
    resolver = DependencyResolver()

    assert resolver.get_module_version("network") is None


def test_register_module():
    resolver = DependencyResolver()

    resolver.register_module(
        "network",
        version(1, 2, 0),
    )

    assert resolver.get_module_version("network") == version(1, 2, 0)


def test_register_module_replaces_version():
    resolver = DependencyResolver()

    resolver.register_module(
        "network",
        version(1, 0, 0),
    )

    resolver.register_module(
        "network",
        version(2, 0, 0),
    )

    assert resolver.get_module_version("network") == version(2, 0, 0)


def test_remove_module():
    resolver = DependencyResolver()

    resolver.register_module(
        "network",
        version(1, 0, 0),
    )

    resolver.remove_module("network")

    assert resolver.get_module_version("network") is None


def test_remove_missing_module_raises():
    resolver = DependencyResolver()

    with pytest.raises(DependencyError):
        resolver.remove_module("network")


def test_available_dependency_is_satisfied():
    resolver = DependencyResolver(
        {
            "network": version(1, 5, 0),
        }
    )

    result = resolver.resolve(
        dependency("network", 1, 0, 0)
    )

    assert result.status is DependencyStatus.AVAILABLE
    assert result.available_version == version(1, 5, 0)
    assert result.is_satisfied is True


def test_missing_dependency():
    resolver = DependencyResolver()

    result = resolver.resolve(
        dependency("network", 1, 0, 0)
    )

    assert result.status is DependencyStatus.MISSING
    assert result.available_version is None
    assert result.is_satisfied is False


def test_incompatible_dependency():
    resolver = DependencyResolver(
        {
            "network": version(1, 0, 0),
        }
    )

    result = resolver.resolve(
        dependency("network", 2, 0, 0)
    )

    assert result.status is DependencyStatus.INCOMPATIBLE
    assert result.available_version == version(1, 0, 0)
    assert result.is_satisfied is False


def test_exact_minimum_version_is_available():
    resolver = DependencyResolver(
        {
            "network": version(1, 0, 0),
        }
    )

    result = resolver.resolve(
        dependency("network", 1, 0, 0)
    )

    assert result.status is DependencyStatus.AVAILABLE


def test_resolve_all_dependencies():
    resolver = DependencyResolver(
        {
            "network": version(1, 2, 0),
            "crypto": version(2, 0, 0),
        }
    )

    results = resolver.resolve_all(
        (
            dependency("network", 1, 0, 0),
            dependency("crypto", 1, 5, 0),
        )
    )

    assert len(results) == 2
    assert results[0].status is DependencyStatus.AVAILABLE
    assert results[1].status is DependencyStatus.AVAILABLE


def test_resolve_all_requires_tuple():
    resolver = DependencyResolver()

    with pytest.raises(InvalidDependencyError):
        resolver.resolve_all([])


def test_resolve_requires_dependency_object():
    resolver = DependencyResolver()

    with pytest.raises(InvalidDependencyError):
        resolver.resolve("network")


def test_dependency_order():
    resolver = DependencyResolver()

    order = resolver.resolve_order(
        {
            "security": ("network", "crypto"),
            "network": (),
            "crypto": (),
        }
    )

    assert order.index("network") < order.index("security")
    assert order.index("crypto") < order.index("security")


def test_dependency_order_handles_shared_dependency():
    resolver = DependencyResolver()

    order = resolver.resolve_order(
        {
            "security": ("network",),
            "monitoring": ("network",),
            "network": (),
        }
    )

    assert order.index("network") < order.index("security")
    assert order.index("network") < order.index("monitoring")


def test_dependency_order_detects_cycle():
    resolver = DependencyResolver()

    with pytest.raises(CircularDependencyError):
        resolver.resolve_order(
            {
                "security": ("network",),
                "network": ("security",),
            }
        )


def test_dependency_order_detects_long_cycle():
    resolver = DependencyResolver()

    with pytest.raises(CircularDependencyError):
        resolver.resolve_order(
            {
                "security": ("network",),
                "network": ("crypto",),
                "crypto": ("security",),
            }
        )


def test_dependency_order_is_deterministic():
    resolver = DependencyResolver()

    graph = {
        "security": ("network",),
        "network": (),
        "crypto": (),
    }

    first = resolver.resolve_order(graph)
    second = resolver.resolve_order(graph)

    assert first == second


def test_dependency_order_allows_external_dependency_name():
    resolver = DependencyResolver()

    order = resolver.resolve_order(
        {
            "security": ("network",),
        }
    )

    assert order == ("security",)


def test_resolver_does_not_install_modules():
    resolver = DependencyResolver()

    resolver.resolve(
        dependency("network", 1, 0, 0)
    )

    assert resolver.get_module_version("network") is None
