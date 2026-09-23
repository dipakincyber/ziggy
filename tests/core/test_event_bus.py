from datetime import datetime, timezone

import pytest

from core.events import Event, EventBus


def test_event_is_immutable():
    event = Event(
        event_type="module.started",
        source="core",
        payload={"module": "security"},
        timestamp=datetime.now(timezone.utc),
    )

    with pytest.raises(AttributeError):
        event.source = "other"


def test_event_requires_nonempty_type():
    with pytest.raises(ValueError):
        Event(
            event_type="",
            source="core",
            payload={},
            timestamp=datetime.now(timezone.utc),
        )


def test_event_requires_nonempty_source():
    with pytest.raises(ValueError):
        Event(
            event_type="module.started",
            source="",
            payload={},
            timestamp=datetime.now(timezone.utc),
        )


def test_event_requires_timezone_aware_timestamp():
    with pytest.raises(ValueError):
        Event(
            event_type="module.started",
            source="core",
            payload={},
            timestamp=datetime.now(),
        )


def test_create_event_uses_timezone_aware_utc_timestamp():
    event = EventBus.create_event(
        event_type="module.started",
        source="core",
        payload={"module": "security"},
    )

    assert event.event_type == "module.started"
    assert event.source == "core"
    assert event.payload == {"module": "security"}
    assert event.timestamp.tzinfo == timezone.utc


def test_subscriber_receives_matching_event():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("module.started", handler)

    event = EventBus.create_event(
        "module.started",
        "core",
        {"module": "security"},
    )

    bus.publish(event)

    assert received == [event]


def test_subscriber_does_not_receive_other_event_types():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("module.started", handler)

    event = EventBus.create_event(
        "module.stopped",
        "core",
        {"module": "security"},
    )

    bus.publish(event)

    assert received == []


def test_duplicate_subscription_is_ignored():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("module.started", handler)
    bus.subscribe("module.started", handler)

    assert bus.subscriber_count("module.started") == 1

    bus.publish(
        EventBus.create_event(
            "module.started",
            "core",
            {},
        )
    )

    assert len(received) == 1


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received = []

    def handler(event):
        received.append(event)

    bus.subscribe("module.started", handler)
    bus.unsubscribe("module.started", handler)

    bus.publish(
        EventBus.create_event(
            "module.started",
            "core",
            {},
        )
    )

    assert received == []
    assert bus.subscriber_count("module.started") == 0


def test_unsubscribe_missing_handler_is_safe():
    bus = EventBus()

    def handler(event):
        pass

    bus.unsubscribe("module.started", handler)

    assert bus.subscriber_count("module.started") == 0


def test_multiple_subscribers_receive_event():
    bus = EventBus()
    first = []
    second = []

    def first_handler(event):
        first.append(event)

    def second_handler(event):
        second.append(event)

    bus.subscribe("security.finding", first_handler)
    bus.subscribe("security.finding", second_handler)

    event = EventBus.create_event(
        "security.finding",
        "security",
        {"severity": "high"},
    )

    bus.publish(event)

    assert first == [event]
    assert second == [event]


def test_subscriber_failure_does_not_stop_other_subscribers():
    bus = EventBus()
    received = []

    def failing_handler(event):
        raise RuntimeError("subscriber failure")

    def working_handler(event):
        received.append(event)

    bus.subscribe("security.finding", failing_handler)
    bus.subscribe("security.finding", working_handler)

    event = EventBus.create_event(
        "security.finding",
        "security",
        {"severity": "high"},
    )

    bus.publish(event)

    assert received == [event]


def test_publish_requires_event_instance():
    bus = EventBus()

    with pytest.raises(TypeError):
        bus.publish("module.started")


def test_subscribe_requires_callable_handler():
    bus = EventBus()

    with pytest.raises(TypeError):
        bus.subscribe("module.started", "not-callable")


def test_event_type_must_be_string():
    bus = EventBus()

    with pytest.raises(TypeError):
        bus.subscribe(123, lambda event: None)


def test_empty_event_type_is_rejected():
    bus = EventBus()

    with pytest.raises(ValueError):
        bus.subscribe("", lambda event: None)


def test_event_payload_can_be_any_object():
    bus = EventBus()
    received = []

    payload = {
        "module": "security",
        "items": [1, 2, 3],
    }

    bus.subscribe(
        "security.finding",
        lambda event: received.append(event.payload),
    )

    bus.publish(
        EventBus.create_event(
            "security.finding",
            "security",
            payload,
        )
    )

    assert received == [payload]
