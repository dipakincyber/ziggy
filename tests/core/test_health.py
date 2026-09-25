from datetime import datetime, timezone

import pytest

from core.health.monitor import (
    HealthMonitor,
    HealthReport,
    HealthStatus,
)


def test_health_status_values_are_defined():
    assert HealthStatus.HEALTHY.value == "healthy"
    assert HealthStatus.DEGRADED.value == "degraded"
    assert HealthStatus.UNHEALTHY.value == "unhealthy"
    assert HealthStatus.UNKNOWN.value == "unknown"


def test_health_report_stores_metadata():
    timestamp = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)

    report = HealthReport(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Module operating normally",
        timestamp=timestamp,
    )

    assert report.module == "security"
    assert report.status is HealthStatus.HEALTHY
    assert report.message == "Module operating normally"
    assert report.timestamp == timestamp


def test_health_report_is_immutable():
    timestamp = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)

    report = HealthReport(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
        timestamp=timestamp,
    )

    with pytest.raises(AttributeError):
        report.status = HealthStatus.UNHEALTHY


def test_empty_module_is_rejected():
    with pytest.raises(ValueError):
        HealthReport(
            module="",
            status=HealthStatus.HEALTHY,
            message="Healthy",
            timestamp=datetime.now(timezone.utc),
        )


def test_empty_message_is_rejected():
    with pytest.raises(ValueError):
        HealthReport(
            module="security",
            status=HealthStatus.HEALTHY,
            message="",
            timestamp=datetime.now(timezone.utc),
        )


def test_invalid_status_is_rejected():
    with pytest.raises(TypeError):
        HealthReport(
            module="security",
            status="healthy",
            message="Healthy",
            timestamp=datetime.now(timezone.utc),
        )


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError):
        HealthReport(
            module="security",
            status=HealthStatus.HEALTHY,
            message="Healthy",
            timestamp=datetime(2026, 9, 25, 12, 0),
        )


def test_monitor_starts_empty():
    monitor = HealthMonitor()

    assert monitor.count() == 0
    assert monitor.list() == ()
    assert monitor.snapshot() == ()


def test_report_creates_health_report():
    monitor = HealthMonitor()
    timestamp = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)

    report = monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Module operating normally",
        timestamp=timestamp,
    )

    assert isinstance(report, HealthReport)
    assert report.module == "security"
    assert report.status is HealthStatus.HEALTHY
    assert report.timestamp == timestamp


def test_report_is_retrievable():
    monitor = HealthMonitor()

    report = monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    assert monitor.get("security") == report
    assert monitor.contains("security")


def test_report_replaces_previous_report_for_same_module():
    monitor = HealthMonitor()

    first = monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    second = monitor.report(
        module="security",
        status=HealthStatus.DEGRADED,
        message="Performance degraded",
    )

    assert second != first
    assert monitor.get("security") == second
    assert monitor.count() == 1


def test_multiple_modules_are_isolated():
    monitor = HealthMonitor()

    security = monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    network = monitor.report(
        module="network",
        status=HealthStatus.UNHEALTHY,
        message="Network unavailable",
    )

    assert monitor.get("security") == security
    assert monitor.get("network") == network
    assert monitor.count() == 2


def test_missing_module_raises():
    monitor = HealthMonitor()

    with pytest.raises(KeyError):
        monitor.get("security")


def test_contains_returns_false_for_missing_module():
    monitor = HealthMonitor()

    assert not monitor.contains("security")


def test_list_is_deterministically_sorted():
    monitor = HealthMonitor()

    monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    monitor.report(
        module="network",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    monitor.report(
        module="database",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    assert [report.module for report in monitor.list()] == [
        "database",
        "network",
        "security",
    ]


def test_snapshot_matches_current_reports():
    monitor = HealthMonitor()

    monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    snapshot = monitor.snapshot()

    assert isinstance(snapshot, tuple)
    assert snapshot == monitor.list()


def test_clear_removes_module_report():
    monitor = HealthMonitor()

    monitor.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Healthy",
    )

    monitor.clear("security")

    assert not monitor.contains("security")
    assert monitor.count() == 0


def test_clear_missing_module_is_safe():
    monitor = HealthMonitor()

    monitor.clear("security")

    assert monitor.count() == 0


def test_report_defaults_to_timezone_aware_timestamp():
    monitor = HealthMonitor()

    report = monitor.report(
        module="security",
        status=HealthStatus.UNKNOWN,
        message="No health information available",
    )

    assert report.timestamp.tzinfo is not None
    assert report.timestamp.utcoffset() is not None


def test_report_rejects_empty_module():
    monitor = HealthMonitor()

    with pytest.raises(ValueError):
        monitor.report(
            module="",
            status=HealthStatus.HEALTHY,
            message="Healthy",
        )


def test_report_rejects_empty_message():
    monitor = HealthMonitor()

    with pytest.raises(ValueError):
        monitor.report(
            module="security",
            status=HealthStatus.HEALTHY,
            message="",
        )


def test_report_rejects_invalid_status():
    monitor = HealthMonitor()

    with pytest.raises(TypeError):
        monitor.report(
            module="security",
            status="healthy",
            message="Healthy",
        )


def test_report_rejects_naive_timestamp():
    monitor = HealthMonitor()

    with pytest.raises(ValueError):
        monitor.report(
            module="security",
            status=HealthStatus.HEALTHY,
            message="Healthy",
            timestamp=datetime(2026, 9, 25, 12, 0),
        )
