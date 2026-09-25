from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CommandDefinition:
    name: str
    module: str
    description: str
    permissions: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Command name cannot be empty.")

        if any(char.isspace() for char in self.name):
            raise ValueError("Command name cannot contain whitespace.")

        if "/" in self.name or "\\" in self.name:
            raise ValueError("Command name cannot contain path separators.")

        if not self.module:
            raise ValueError("Command module cannot be empty.")

        if not self.description:
            raise ValueError("Command description cannot be empty.")

        if not isinstance(self.permissions, tuple):
            raise TypeError("Permissions must be a tuple.")


class CommandRegistrationError(Exception):
    """Raised when a command cannot be registered."""


class CommandNotFoundError(Exception):
    """Raised when a requested command does not exist."""


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: dict[str, CommandDefinition] = {}

    def register(self, command: CommandDefinition) -> None:
        if not isinstance(command, CommandDefinition):
            raise TypeError("Expected a CommandDefinition.")

        if command.name in self._commands:
            raise CommandRegistrationError(
                f"Command '{command.name}' is already registered."
            )

        self._commands[command.name] = command

    def unregister(self, name: str) -> None:
        if name not in self._commands:
            raise CommandNotFoundError(
                f"Command '{name}' is not registered."
            )

        del self._commands[name]

    def get(self, name: str) -> CommandDefinition:
        try:
            return self._commands[name]
        except KeyError as exc:
            raise CommandNotFoundError(
                f"Command '{name}' is not registered."
            ) from exc

    def contains(self, name: str) -> bool:
        return name in self._commands

    def list(self) -> Tuple[CommandDefinition, ...]:
        return tuple(
            self._commands[name]
            for name in sorted(self._commands)
        )

    def count(self) -> int:
        return len(self._commands)

    def snapshot(self) -> Tuple[CommandDefinition, ...]:
        return self.list()

    def unregister_module(self, module: str) -> None:
        names_to_remove = [
            name
            for name, command in self._commands.items()
            if command.module == module
        ]

        for name in names_to_remove:
            del self._commands[name]
