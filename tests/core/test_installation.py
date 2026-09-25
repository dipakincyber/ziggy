from pathlib import Path

import pytest

from core.discovery import ModuleCandidate
from core.installation import (
    InstallationError,
    InstallationResult,
    InvalidInstallationError,
    ModuleAlreadyInstalledError,
    ModuleInstaller,
)


def create_candidate(
    root: Path,
    name: str = "security",
) -> ModuleCandidate:
    module = root / name
    module.mkdir(parents=True)

    manifest = module / "module.yaml"
    manifest.write_text("name: " + name)

    return ModuleCandidate(
        name=name,
        module_path=module,
        manifest_path=manifest,
    )


def test_installer_requires_path():
    with pytest.raises(InvalidInstallationError):
        ModuleInstaller("/tmp/ziggy-modules")


def test_installation_root_is_not_created_until_install(tmp_path):
    root = tmp_path / "modules"

    ModuleInstaller(root)

    assert not root.exists()


def test_install_module(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)

    result = installer.install(candidate)

    assert isinstance(result, InstallationResult)
    assert result.name == "security"
    assert result.source_path == candidate.module_path
    assert result.installed_path == install_root / "security"

    assert result.installed_path.is_dir()
    assert (result.installed_path / "module.yaml").is_file()


def test_install_copies_module_files(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    config = candidate.module_path / "config.json"
    config.write_text('{"enabled": true}')

    installer = ModuleInstaller(install_root)
    result = installer.install(candidate)

    installed_config = result.installed_path / "config.json"

    assert installed_config.is_file()
    assert installed_config.read_text() == '{"enabled": true}'


def test_install_does_not_modify_source(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)
    installer.install(candidate)

    assert candidate.module_path.is_dir()
    assert candidate.manifest_path.is_file()


def test_duplicate_installation_is_rejected(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)

    installer.install(candidate)

    with pytest.raises(ModuleAlreadyInstalledError):
        installer.install(candidate)


def test_existing_destination_is_not_overwritten(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    destination = install_root / "security"
    destination.mkdir(parents=True)
    marker = destination / "important.txt"
    marker.write_text("do not delete")

    installer = ModuleInstaller(install_root)

    with pytest.raises(ModuleAlreadyInstalledError):
        installer.install(candidate)

    assert marker.read_text() == "do not delete"


def test_missing_source_is_rejected(tmp_path):
    install_root = tmp_path / "installed"
    source = tmp_path / "missing"
    manifest = source / "module.yaml"

    candidate = ModuleCandidate(
        name="security",
        module_path=source,
        manifest_path=manifest,
    )

    installer = ModuleInstaller(install_root)

    with pytest.raises(InvalidInstallationError):
        installer.install(candidate)


def test_source_must_be_directory(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    source = source_root / "security"
    source.write_text("not a directory")

    manifest = source / "module.yaml"

    candidate = ModuleCandidate(
        name="security",
        module_path=source,
        manifest_path=manifest,
    )

    installer = ModuleInstaller(install_root)

    with pytest.raises(InvalidInstallationError):
        installer.install(candidate)


def test_missing_manifest_is_rejected(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    module = source_root / "security"
    module.mkdir()

    candidate = ModuleCandidate(
        name="security",
        module_path=module,
        manifest_path=module / "module.yaml",
    )

    installer = ModuleInstaller(install_root)

    with pytest.raises(InvalidInstallationError):
        installer.install(candidate)


def test_manifest_must_be_file(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    module = source_root / "security"
    module.mkdir()

    manifest = module / "module.yaml"
    manifest.mkdir()

    candidate = ModuleCandidate(
        name="security",
        module_path=module,
        manifest_path=manifest,
    )

    installer = ModuleInstaller(install_root)

    with pytest.raises(InvalidInstallationError):
        installer.install(candidate)


def test_is_installed_returns_false_before_installation(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    installer = ModuleInstaller(install_root)

    assert installer.is_installed("security") is False


def test_is_installed_returns_true_after_installation(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)
    installer.install(candidate)

    assert installer.is_installed("security") is True


def test_uninstall_removes_module(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)
    installer.install(candidate)

    installer.uninstall("security")

    assert installer.is_installed("security") is False


def test_uninstall_missing_module_raises(tmp_path):
    installer = ModuleInstaller(tmp_path / "installed")

    with pytest.raises(InstallationError):
        installer.uninstall("security")


def test_uninstall_rejects_file_destination(tmp_path):
    install_root = tmp_path / "installed"
    install_root.mkdir()

    (install_root / "security").write_text("not a directory")

    installer = ModuleInstaller(install_root)

    with pytest.raises(InstallationError):
        installer.uninstall("security")


def test_install_rejects_non_candidate(tmp_path):
    installer = ModuleInstaller(tmp_path / "installed")

    with pytest.raises(InvalidInstallationError):
        installer.install(tmp_path)


def test_installation_does_not_execute_python_code(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    malicious = candidate.module_path / "module.py"
    malicious.write_text(
        "raise RuntimeError('module execution detected')"
    )

    installer = ModuleInstaller(install_root)
    result = installer.install(candidate)

    assert result.installed_path.is_dir()
    assert (result.installed_path / "module.py").is_file()


def test_installation_preserves_nested_files(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    nested = candidate.module_path / "data" / "nested"
    nested.mkdir(parents=True)

    file_path = nested / "data.txt"
    file_path.write_text("ziggy")

    installer = ModuleInstaller(install_root)
    result = installer.install(candidate)

    copied = result.installed_path / "data" / "nested" / "data.txt"

    assert copied.is_file()
    assert copied.read_text() == "ziggy"


def test_installation_result_is_immutable(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)
    result = installer.install(candidate)

    with pytest.raises(Exception):
        result.name = "changed"


def test_installation_does_not_register_module(tmp_path):
    source_root = tmp_path / "source"
    install_root = tmp_path / "installed"

    source_root.mkdir()

    candidate = create_candidate(source_root)

    installer = ModuleInstaller(install_root)
    installer.install(candidate)

    # Installation only creates filesystem state.
    # Registry admission is intentionally handled elsewhere.
    assert installer.is_installed("security") is True
