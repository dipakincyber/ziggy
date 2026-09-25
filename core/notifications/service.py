from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Tuple


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Notification:
    source: str
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    timestamp: datetime | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source must not be empty")

        if not self.title:
            raise ValueError("title must not be empty")

        if not self.message:
            raise ValueError("message must not be empty")

        if not isinstance(self.level, NotificationLevel):
            raise TypeError("level must be a NotificationLevel")

        timestamp = self.timestamp

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
            object.__setattr__(self, "timestamp", timestamp)

        if timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        metadata = self.metadata

        if metadata is None:
            metadata = {}
            object.__setattr__(self, "metadata", metadata)

        object.__setattr__(self, "metadata", dict(metadata))


class NotificationService:
    def __init__(self) -> None:
        self._notifications: list[Notification] = []

    def notify(self, notification: Notification) -> Notification:
        if not isinstance(notification, Notification):
            raise TypeError("notification must be a Notification")

        self._notifications.append(notification)
        return notification

    def info(
        self,
        source: str,
        title: str,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Notification:
        return self.notify(
            Notification(
                source=source,
                title=title,
                message=message,
                level=NotificationLevel.INFO,
                metadata=metadata,
            )
        )

    def success(
        self,
        source: str,
        title: str,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Notification:
        return self.notify(
            Notification(
                source=source,
                title=title,
                message=message,
                level=NotificationLevel.SUCCESS,
                metadata=metadata,
            )
        )

    def warning(
        self,
        source: str,
        title: str,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Notification:
        return self.notify(
            Notification(
                source=source,
                title=title,
                message=message,
                level=NotificationLevel.WARNING,
                metadata=metadata,
            )
        )

    def error(
        self,
        source: str,
        title: str,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Notification:
        return self.notify(
            Notification(
                source=source,
                title=title,
                message=message,
                level=NotificationLevel.ERROR,
                metadata=metadata,
            )
        )

    def critical(
        self,
        source: str,
        title: str,
        message: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> Notification:
        return self.notify(
            Notification(
                source=source,
                title=title,
                message=message,
                level=NotificationLevel.CRITICAL,
                metadata=metadata,
            )
        )

    def list(self) -> Tuple[Notification, ...]:
        return tuple(self._notifications)

    def count(self) -> int:
        return len(self._notifications)

    def clear(self) -> None:
        self._notifications.clear()

    def snapshot(self) -> Tuple[Notification, ...]:
        return tuple(self._notifications)
