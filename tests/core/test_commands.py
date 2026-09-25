import pytest

from core.commands.registry import (
    CommandDefinition,
    CommandNotFoundError,
    CommandRegistrationError,
    CommandRegistry,
)


def make_command(
    name: str = "scan",
    module: str = "security",
    description: str = "Scan a file",
    permissions: tuple[str, ...] = ("filesystem.read",),
) -> CommandDefinition:
    return CommandDefinition(
        name=name,
        module=module,
        description=description,
        permissions=permissions,
    )


def test_command_definition_stores_metadata():
    command = make_command()

    assert command.name == "scan"
    assert command.module == "security"
    assert command.description == "Scan a file"
    assert command.permissions == ("filesystem.read",)


def test_command_definition_is_immutable():
    command = make_command()

    with pytest.raises(AttributeError):
        command.name = "other"


@pytest.mark.parametrize(
    "name",
    [
        "",
        "scan file",
        "scan\tfile",
        "scan/file",
        "scan\\file",
    ],
)
def test_command_name_validation(name):
    with pytest.raises(ValueError):
        make_command(name=name)


def test_empty_module_is_rejected():
    with pytest.raises(ValueError):
        make_command(module="")


def test_empty_description_is_rejected():
    with pytest.raises(ValueError):
        make_command(description="")


def test_permissions_must_be_tuple():
    with pytest.raises(TypeError):
        CommandDefinition(
            name="scan",
            module="security",
            description="Scan a file",
            permissions=["filesystem.read"],
        )


def test_registry_starts_empty():
    registry = CommandRegistry()

    assert registry.count() == 0
    assert registry.list() == ()
    assert registry.snapshot() == ()


def test_register_command():
    registry = CommandRegistry()
    command = make_command()

    registry.register(command)

    assert registry.count() == 1
    assert registry.contains("scan")
    assert registry.get("scan") == command


def test_duplicate_command_registration_is_rejected():
    registry = CommandRegistry()
    command = make_command()

    registry.register(command)

    with pytest.raises(CommandRegistrationError):
        registry.register(command)

    assert registry.count() == 1


def test_registry_rejects_non_command_definition():
    registry = CommandRegistry()

    with pytest.raises(TypeError):
        registry.register("scan")


def test_get_missing_command_raises():
    registry = CommandRegistry()

    with pytest.raises(CommandNotFoundError):
        registry.get("scan")


def test_unregister_command():
    registry = CommandRegistry()
    registry.register(make_command())

    registry.unregister("scan")

    assert registry.count() == 0
    assert not registry.contains("scan")


def test_unregister_missing_command_raises():
    registry = CommandRegistry()

    with pytest.raises(CommandNotFoundError):
        registry.unregister("scan")


def test_list_is_deterministically_sorted():
    registry = CommandRegistry()

    registry.register(
        make_command(
            name="track",
            module="monitoring",
            description="Track an application",
        )
    )
    registry.register(
        make_command(
            name="scan",
            module="security",
            description="Scan a file",
        )
    )
    registry.register(
        make_command(
            name="network",
            module="network",
            description="Inspect network activity",
        )
    )

    assert [command.name for command in registry.list()] == [
        "network",
        "scan",
        "track",
    ]


def test_snapshot_is_read_only():
    registry = CommandRegistry()
    registry.register(make_command())

    snapshot = registry.snapshot()

    assert isinstance(snapshot, tuple)
    assert snapshot == registry.list()


def test_unregister_module_removes_only_owned_commands():
    registry = CommandRegistry()

    registry.register(
        make_command(
            name="scan",
            module="security",
            description="Scan a file",
        )
    )
    registry.register(
        make_command(
            name="inspect",
            module="security",
            description="Inspect security state",
        )
    )
    registry.register(
        make_command(
            name="track",
            module="monitoring",
            description="Track an application",
        )
    )

    registry.unregister_module("security")

    assert not registry.contains("scan")
    assert not registry.contains("inspect")
    assert registry.contains("track")
    assert registry.count() == 1


def test_unregister_module_when_module_has_no_commands_is_safe():
    registry = CommandRegistry()

    registry.register(
        make_command(
            name="scan",
            module="security",
            description="Scan a file",
        )
    )

    registry.unregister_module("network")

    assert registry.count() == 1
    assert registry.contains("scan")
