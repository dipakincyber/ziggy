from pathlib import Path

import pytest

from core.discovery import (
    InvalidDiscoveryPathError,
    ModuleCandidate,
    ModuleDiscovery,
)


def test_discovery_manifest_name():
    assert ModuleDiscovery.MANIFEST_NAME == "module.yaml"


def test_candidate_requires_name():
    candidate = ModuleCandidate(
        name="security",
        module_path=Path("/modules/security"),
        manifest_path=Path("/modules/security/module.yaml"),
    )

    assert candidate.name == "security"


def test_candidate_rejects_empty_name():
    with pytest.raises(ValueError):
        ModuleCandidate(
            name="",
            module_path=Path("/modules/security"),
            manifest_path=Path("/modules/security/module.yaml"),
        )


def test_candidate_requires_path_objects():
    with pytest.raises(TypeError):
        ModuleCandidate(
            name="security",
            module_path="/modules/security",
            manifest_path=Path("/modules/security/module.yaml"),
        )


def test_discovery_rejects_non_path():
    discovery = ModuleDiscovery()

    with pytest.raises(InvalidDiscoveryPathError):
        discovery.discover("/modules")


def test_discovery_rejects_missing_root(tmp_path):
    discovery = ModuleDiscovery()

    missing = tmp_path / "does-not-exist"

    with pytest.raises(InvalidDiscoveryPathError):
        discovery.discover(missing)


def test_discovery_rejects_file_root(tmp_path):
    discovery = ModuleDiscovery()

    file_path = tmp_path / "file.txt"
    file_path.write_text("not a directory")

    with pytest.raises(InvalidDiscoveryPathError):
        discovery.discover(file_path)


def test_empty_directory_returns_no_candidates(tmp_path):
    discovery = ModuleDiscovery()

    result = discovery.discover(tmp_path)

    assert result == ()


def test_directory_without_manifest_is_ignored(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    result = discovery.discover(tmp_path)

    assert result == ()


def test_module_with_manifest_is_discovered(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    manifest = module_dir / "module.yaml"
    manifest.write_text("name: security")

    result = discovery.discover(tmp_path)

    assert len(result) == 1
    assert result[0].name == "security"
    assert result[0].module_path == module_dir
    assert result[0].manifest_path == manifest


def test_multiple_modules_are_discovered(tmp_path):
    discovery = ModuleDiscovery()

    security = tmp_path / "security"
    network = tmp_path / "network"

    security.mkdir()
    network.mkdir()

    (security / "module.yaml").write_text("name: security")
    (network / "module.yaml").write_text("name: network")

    result = discovery.discover(tmp_path)

    assert [candidate.name for candidate in result] == [
        "network",
        "security",
    ]


def test_root_itself_can_be_a_module(tmp_path):
    discovery = ModuleDiscovery()

    manifest = tmp_path / "module.yaml"
    manifest.write_text("name: security")

    result = discovery.discover(tmp_path)

    assert len(result) == 1
    assert result[0].name == tmp_path.name
    assert result[0].module_path == tmp_path
    assert result[0].manifest_path == manifest


def test_nested_modules_are_not_scanned_recursively(tmp_path):
    discovery = ModuleDiscovery()

    parent = tmp_path / "modules"
    nested = parent / "security"

    parent.mkdir()
    nested.mkdir()

    (nested / "module.yaml").write_text("name: security")

    result = discovery.discover(tmp_path)

    assert result == ()


def test_non_manifest_files_are_ignored(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    (module_dir / "README.md").write_text("Security module")

    result = discovery.discover(tmp_path)

    assert result == ()


def test_manifest_must_be_a_file(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    (module_dir / "module.yaml").mkdir()

    result = discovery.discover(tmp_path)

    assert result == ()


def test_discovery_does_not_read_manifest_contents(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    manifest = module_dir / "module.yaml"
    manifest.write_text("this is intentionally invalid yaml")

    result = discovery.discover(tmp_path)

    assert len(result) == 1
    assert result[0].name == "security"


def test_discovery_does_not_import_module_code(tmp_path):
    discovery = ModuleDiscovery()

    module_dir = tmp_path / "security"
    module_dir.mkdir()

    (module_dir / "module.yaml").write_text("name: security")
    (module_dir / "dangerous.py").write_text(
        "raise RuntimeError('This must never execute')"
    )

    result = discovery.discover(tmp_path)

    assert len(result) == 1
    assert result[0].name == "security"
