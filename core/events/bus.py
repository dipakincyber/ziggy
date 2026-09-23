"""
Ziggy Core Event System.

This module provides the foundational event contract and in-memory
event bus used by Ziggy Core.

The event bus does not persist events and does not collect operating
system events. It only provides structured publication and subscription.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable


@dataclass(frozen=True)
class Event:
    """
    Immutable event published through the Core event bus.

    event_type:
        Namespaced event identifier, for example "module.started".

    source:
        Component that produced the event.

    payload:
        Event-specific data.

    timestamp:
        UTC timestamp assigned when the event is created.
    """

    event_type: str
    source: str
    payload: object
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate the event's required identity fields."""

        if not self.event_type.strip():
            raise ValueError("Event type cannot be empty.")

        if not self.source.strip():
            raise ValueError("Event source cannot be empty.")

        if self.timestamp.tzinfo is None:
            raise ValueError(
                "Event timestamp must be timezone-aware."
            )


EventHandler = Callable[[Event], None]


class EventBus:
    """
    In-memory publish/subscribe event bus.

    Subscriber failures are isolated: one failing subscriber does not
    prevent other subscribers from receiving the event.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = {}

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """
        Subscribe a handler to an event type.

        Duplicate subscriptions of the same handler are ignored.
        """

        self._validate_event_type(event_type)

        if not callable(handler):
            raise TypeError("Event handler must be callable.")

        subscribers = self._subscribers.setdefault(
            event_type,
            [],
        )

        if handler not in subscribers:
            subscribers.append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """
        Remove a handler from an event type.

        Removing a handler that is not subscribed is safe.
        """

        self._validate_event_type(event_type)

        subscribers = self._subscribers.get(event_type)

        if subscribers is None:
            return

        if handler in subscribers:
            subscribers.remove(handler)

        if not subscribers:
            self._subscribers.pop(event_type, None)

    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers of its event type.

        Subscriber exceptions are isolated from the remaining handlers.
        """

        if not isinstance(event, Event):
            raise TypeError("publish() requires an Event instance.")

        subscribers = tuple(
            self._subscribers.get(event.event_type, ())
        )

        for handler in subscribers:
            try:
                handler(event)
            except Exception:
                continue

    def subscriber_count(self, event_type: str) -> int:
        """Return the number of subscribers for an event type."""

        self._validate_event_type(event_type)

        return len(
            self._subscribers.get(event_type, ())
        )

    @staticmethod
    def create_event(
        event_type: str,
        source: str,
        payload: object,
    ) -> Event:
        """
        Create an event using the current UTC time.

        The timestamp is timezone-aware.
        """

        return Event(
            event_type=event_type,
            source=source,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _validate_event_type(event_type: str) -> None:
        """Validate a basic event type identifier."""

        if not isinstance(event_type, str):
            raise TypeError("Event type must be a string.")

        if not event_type.strip():
            raise ValueError("Event type cannot be empty.")
