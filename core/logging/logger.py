"""
Ziggy Core Logging API.

This module provides the foundational structured logging contract
for Ziggy modules.

The initial implementation stores records in memory.
Persistence and log routing are deliberately left to later Core layers.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping


class LoggingError(RuntimeError):
    """Base error for logging operations."""


class InvalidLogLevelError(LoggingError):
    """Raised when an invalid log level is supplied."""


class InvalidLogSourceError(LoggingError):
    """Raised when a log source is invalid."""


class LogLevel:
    """Supported Ziggy log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    _VALUES = frozenset(
        {
            DEBUG,
            INFO,
            WARNING,
            ERROR,
            CRITICAL,
        }
    )

    @classmethod
    def is_valid(cls, level: str) -> bool:
        """Return whether the supplied level is supported."""

        return level in cls._VALUES


@dataclass(frozen=True)
class LogRecord:
    """
    Immutable structured log record.
    """

    timestamp: datetime
    level: str
    source: str
    message: str
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None:
            raise ValueError(
                "Log timestamp must be timezone-aware."
            )

        if not LogLevel.is_valid(self.level):
            raise InvalidLogLevelError(
                f"Invalid log level: {self.level}"
            )

        if not isinstance(self.source, str):
            raise InvalidLogSourceError(
                "Log source must be a string."
            )

        if not self.source.strip():
            raise InvalidLogSourceError(
                "Log source cannot be empty."
            )

        if not isinstance(self.message, str):
            raise TypeError(
                "Log message must be a string."
            )

        if not self.message.strip():
            raise ValueError(
                "Log message cannot be empty."
            )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )


class ModuleLogger:
    """
    Logger belonging to one Ziggy module.

    Each ModuleLogger instance owns an isolated collection of log records.
    """

    def __init__(self, module_name: str) -> None:
        if not isinstance(module_name, str):
            raise TypeError("Module name must be a string.")

        if not module_name.strip():
            raise ValueError("Module name cannot be empty.")

        self._module_name = module_name
        self._records: list[LogRecord] = []

    @property
    def module_name(self) -> str:
        """Return the owning module name."""

        return self._module_name

    def debug(
        self,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> LogRecord:
        """Create a DEBUG log record."""

        return self._log(
            LogLevel.DEBUG,
            message,
            metadata,
        )

    def info(
        self,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> LogRecord:
        """Create an INFO log record."""

        return self._log(
            LogLevel.INFO,
            message,
            metadata,
        )

    def warning(
        self,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> LogRecord:
        """Create a WARNING log record."""

        return self._log(
            LogLevel.WARNING,
            message,
            metadata,
        )

    def error(
        self,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> LogRecord:
        """Create an ERROR log record."""

        return self._log(
            LogLevel.ERROR,
            message,
            metadata,
        )

    def critical(
        self,
        message: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> LogRecord:
        """Create a CRITICAL log record."""

        return self._log(
            LogLevel.CRITICAL,
            message,
            metadata,
        )

    def records(self) -> tuple[LogRecord, ...]:
        """Return all records in creation order."""

        return tuple(self._records)

    def count(self) -> int:
        """Return the number of stored log records."""

        return len(self._records)

    def clear(self) -> None:
        """Remove all log records from this logger."""

        self._records.clear()

    def _log(
        self,
        level: str,
        message: str,
        metadata: Mapping[str, Any] | None,
    ) -> LogRecord:
        """Create and store a log record."""

        if metadata is None:
            metadata = {}

        record = LogRecord(
            timestamp=datetime.now(timezone.utc),
            level=level,
            source=self._module_name,
            message=message,
            metadata=metadata,
        )

        self._records.append(record)

        return record
