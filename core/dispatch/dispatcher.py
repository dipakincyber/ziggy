from dataclasses import dataclass
from typing import Any, Callable


CommandHandler = Callable[..., Any]


@dataclass(frozen=True)
class DispatchRequest:
    command: str
    arguments: tuple[Any, ...] = ()
    options: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.command:
            raise ValueError("Command cannot be empty.")

        if any(char.isspace() for char in self.command):
            raise ValueError("Command cannot contain whitespace.")

        if "/" in self.command or "\\" in self.command:
            raise ValueError("Command cannot contain path separators.")

        if not isinstance(self.arguments, tuple):
            raise TypeError("Arguments must be a tuple.")

        if self.options is not None and not isinstance(self.options, dict):
            raise TypeError("Options must be a dictionary or None.")


@dataclass(frozen=True)
class DispatchResult:
    command: str
    value: Any


class DispatchError(Exception):
    """Raised when a command cannot be dispatched."""


class CommandDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, CommandHandler] = {}

    def bind(self, command: str, handler: CommandHandler) -> None:
        if not command:
            raise ValueError("Command cannot be empty.")

        if any(char.isspace() for char in command):
            raise ValueError("Command cannot contain whitespace.")

        if "/" in command or "\\" in command:
            raise ValueError("Command cannot contain path separators.")

        if not callable(handler):
            raise TypeError("Handler must be callable.")

        if command in self._handlers:
            raise DispatchError(
                f"Handler for command '{command}' is already bound."
            )

        self._handlers[command] = handler

    def unbind(self, command: str) -> None:
        if command not in self._handlers:
            raise DispatchError(
                f"No handler is bound to command '{command}'."
            )

        del self._handlers[command]

    def dispatch(self, request: DispatchRequest) -> DispatchResult:
        try:
            handler = self._handlers[request.command]
        except KeyError as exc:
            raise DispatchError(
                f"No handler is bound to command '{request.command}'."
            ) from exc

        options = request.options or {}
        value = handler(*request.arguments, **options)

        return DispatchResult(
            command=request.command,
            value=value,
        )

    def contains(self, command: str) -> bool:
        return command in self._handlers

    def count(self) -> int:
        return len(self._handlers)
