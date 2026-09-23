from core.api.version import CoreAPIVersion
from core.compatibility.checker import CompatibilityChecker
from core.modules.manifest import (
    ModuleCompatibility,
    ModuleManifest,
)


def make_manifest(
    api_version: int = 1,
    minimum_core_version: CoreAPIVersion = CoreAPIVersion(1, 0, 0),
) -> ModuleManifest:
    return ModuleManifest(
        name="test-module",
        version="1.0.0",
        author="Dipak Yadav",
        description="Compatibility test module",
        compatibility=ModuleCompatibility(
            api_version=api_version,
            minimum_core_version=minimum_core_version,
        ),
    )


def test_compatible_module():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 2, 0)
    )

    result = checker.check(make_manifest())

    assert result.compatible
    assert result.is_compatible
    assert result.reasons == ()


def test_incompatible_api_version():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 2, 0)
    )

    manifest = make_manifest(api_version=2)

    result = checker.check(manifest)

    assert not result.compatible
    assert not result.is_compatible

    assert (
        "Module requires Core API 2, "
        "but Core provides API 1."
    ) in result.reasons


def test_core_below_minimum_version():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 0, 0)
    )

    manifest = make_manifest(
        minimum_core_version=CoreAPIVersion(1, 2, 0)
    )

    result = checker.check(manifest)

    assert not result.compatible

    assert (
        "Module requires minimum Core version 1.2.0, "
        "but current Core version is 1.0.0."
    ) in result.reasons


def test_core_above_minimum_version():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 5, 0)
    )

    manifest = make_manifest(
        minimum_core_version=CoreAPIVersion(1, 2, 0)
    )

    result = checker.check(manifest)

    assert result.compatible


def test_exact_core_version_is_compatible():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 2, 0)
    )

    manifest = make_manifest(
        minimum_core_version=CoreAPIVersion(1, 2, 0)
    )

    result = checker.check(manifest)

    assert result.compatible


def test_multiple_compatibility_failures_are_reported():
    checker = CompatibilityChecker(
        CoreAPIVersion(1, 0, 0)
    )

    manifest = make_manifest(
        api_version=2,
        minimum_core_version=CoreAPIVersion(1, 5, 0),
    )

    result = checker.check(manifest)

    assert not result.compatible
    assert len(result.reasons) == 2
