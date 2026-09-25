from datetime import datetime, timezone

from core.notifications import (
    Notification,
    NotificationLevel,
    NotificationService,
)


def test_notification_levels_exist():
    assert NotificationLevel.INFO.value == "info"
    assert NotificationLevel.SUCCESS.value == "success"
    assert NotificationLevel.WARNING.value == "warning"
    assert NotificationLevel.ERROR.value == "error"
    assert NotificationLevel.CRITICAL.value == "critical"


def test_notification_requires_source():
    try:
        Notification(
            source="",
            title="Test",
            message="Message",
        )
        assert False
    except ValueError:
        pass


def test_notification_requires_title():
    try:
        Notification(
            source="core",
            title="",
            message="Message",
        )
        assert False
    except ValueError:
        pass


def test_notification_requires_message():
    try:
        Notification(
            source="core",
            title="Test",
            message="",
        )
        assert False
    except ValueError:
        pass


def test_notification_requires_valid_level():
    try:
        Notification(
            source="core",
            title="Test",
            message="Message",
            level="warning",
        )
        assert False
    except TypeError:
        pass


def test_notification_gets_utc_timestamp():
    notification = Notification(
        source="core",
        title="Test",
        message="Message",
    )

    assert notification.timestamp is not None
    assert notification.timestamp.tzinfo is not None
    assert notification.timestamp.utcoffset() is not None


def test_naive_timestamp_is_rejected():
    try:
        Notification(
            source="core",
            title="Test",
            message="Message",
            timestamp=datetime(2026, 1, 1),
        )
        assert False
    except ValueError:
        pass


def test_notification_metadata_defaults_to_empty_mapping():
    notification = Notification(
        source="core",
        title="Test",
        message="Message",
    )

    assert notification.metadata == {}


def test_notification_metadata_is_copied():
    metadata = {"module": "security"}

    notification = Notification(
        source="security",
        title="Scan complete",
        message="The scan finished.",
        metadata=metadata,
    )

    metadata["module"] = "network"

    assert notification.metadata == {"module": "security"}


def test_notification_is_immutable():
    notification = Notification(
        source="core",
        title="Test",
        message="Message",
    )

    try:
        notification.title = "Changed"
        assert False
    except AttributeError:
        pass


def test_notification_service_stores_notifications():
    service = NotificationService()

    notification = Notification(
        source="core",
        title="Test",
        message="Message",
    )

    result = service.notify(notification)

    assert result == notification
    assert service.count() == 1
    assert service.list() == (notification,)


def test_notification_service_rejects_invalid_type():
    service = NotificationService()

    try:
        service.notify("notification")
        assert False
    except TypeError:
        pass


def test_info_notification():
    service = NotificationService()

    notification = service.info(
        "core",
        "System Ready",
        "Ziggy Core is ready.",
    )

    assert notification.level == NotificationLevel.INFO
    assert notification.source == "core"


def test_success_notification():
    service = NotificationService()

    notification = service.success(
        "security",
        "Scan Complete",
        "The scan completed successfully.",
    )

    assert notification.level == NotificationLevel.SUCCESS


def test_warning_notification():
    service = NotificationService()

    notification = service.warning(
        "health",
        "Module Degraded",
        "The module reported degraded health.",
    )

    assert notification.level == NotificationLevel.WARNING


def test_error_notification():
    service = NotificationService()

    notification = service.error(
        "network",
        "Connection Failed",
        "The connection could not be established.",
    )

    assert notification.level == NotificationLevel.ERROR


def test_critical_notification():
    service = NotificationService()

    notification = service.critical(
        "security",
        "Critical Event",
        "A critical security event was reported.",
    )

    assert notification.level == NotificationLevel.CRITICAL


def test_notification_metadata_is_supported():
    service = NotificationService()

    notification = service.warning(
        "security",
        "Warning",
        "Suspicious activity detected.",
        metadata={"event_id": 42},
    )

    assert notification.metadata == {"event_id": 42}


def test_list_returns_read_only_snapshot():
    service = NotificationService()

    service.info(
        "core",
        "Test",
        "Message",
    )

    notifications = service.list()

    assert isinstance(notifications, tuple)
    assert len(notifications) == 1


def test_snapshot_returns_current_state():
    service = NotificationService()

    service.info(
        "core",
        "First",
        "Message",
    )

    snapshot = service.snapshot()

    service.info(
        "core",
        "Second",
        "Message",
    )

    assert len(snapshot) == 1
    assert service.count() == 2


def test_clear_removes_notifications():
    service = NotificationService()

    service.info(
        "core",
        "Test",
        "Message",
    )

    service.clear()

    assert service.count() == 0
    assert service.list() == ()


def test_notifications_preserve_order():
    service = NotificationService()

    first = service.info(
        "core",
        "First",
        "First message",
    )

    second = service.warning(
        "core",
        "Second",
        "Second message",
    )

    third = service.error(
        "core",
        "Third",
        "Third message",
    )

    assert service.list() == (first, second, third)
