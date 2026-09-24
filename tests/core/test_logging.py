from datetime import datetime, timezone

import pytest

from core.logging import (
    InvalidLogLevelError,
    InvalidLogSourceError,
    LogLevel,
    LogRecord,
    ModuleLogger,
)


def test_logger_starts_empty():
    logger = ModuleLogger("security")

    assert logger.module_name == "security"
    assert logger.count() == 0
    assert logger.records() == ()


def test_module_name_must_be_string():
    with pytest.raises(TypeError):
        ModuleLogger(123)


def test_module_name_cannot_be_empty():
    with pytest.raises(ValueError):
        ModuleLogger("")


def test_debug_creates_record():
    logger = ModuleLogger("security")

    record = logger.debug("Starting scan")

    assert record.level == LogLevel.DEBUG
    assert record.source == "security"
    assert record.message == "Starting scan"
    assert record.timestamp.tzinfo is not None
    assert logger.count() == 1


def test_info_creates_record():
    logger = ModuleLogger("security")

    record = logger.info("Scan started")

    assert record.level == LogLevel.INFO
    assert record.message == "Scan started"


def test_warning_creates_record():
    logger = ModuleLogger("security")

    record = logger.warning("Suspicious file detected")

    assert record.level == LogLevel.WARNING


def test_error_creates_record():
    logger = ModuleLogger("security")

    record = logger.error("Scan failed")

    assert record.level == LogLevel.ERROR


def test_critical_creates_record():
    logger = ModuleLogger("security")

    record = logger.critical("Critical security event")

    assert record.level == LogLevel.CRITICAL


def test_records_preserve_creation_order():
    logger = ModuleLogger("security")

    first = logger.info("First")
    second = logger.warning("Second")
    third = logger.error("Third")

    assert logger.records() == (
        first,
        second,
        third,
    )


def test_metadata_is_preserved():
    logger = ModuleLogger("security")

    record = logger.info(
        "Scan completed",
        {
            "files": 42,
            "duration": 1.5,
        },
    )

    assert record.metadata == {
        "files": 42,
        "duration": 1.5,
    }


def test_metadata_is_read_only():
    logger = ModuleLogger("security")

    record = logger.info(
        "Scan completed",
        {"files": 42},
    )

    with pytest.raises(TypeError):
        record.metadata["files"] = 100

    assert record.metadata["files"] == 42


def test_record_is_immutable():
    timestamp = datetime.now(timezone.utc)

    record = LogRecord(
        timestamp=timestamp,
        level=LogLevel.INFO,
        source="security",
        message="Test",
        metadata={},
    )

    with pytest.raises(Exception):
        record.message = "Changed"


def test_invalid_log_level_is_rejected():
    with pytest.raises(InvalidLogLevelError):
        LogRecord(
            timestamp=datetime.now(timezone.utc),
            level="INVALID",
            source="security",
            message="Test",
            metadata={},
        )


def test_log_source_must_be_string():
    with pytest.raises(InvalidLogSourceError):
        LogRecord(
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            source=123,
            message="Test",
            metadata={},
        )


def test_log_source_cannot_be_empty():
    with pytest.raises(InvalidLogSourceError):
        LogRecord(
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            source="",
            message="Test",
            metadata={},
        )


def test_timestamp_must_be_timezone_aware():
    with pytest.raises(ValueError):
        LogRecord(
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            source="security",
            message="Test",
            metadata={},
        )


def test_message_must_be_string():
    with pytest.raises(TypeError):
        LogRecord(
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            source="security",
            message=123,
            metadata={},
        )


def test_message_cannot_be_empty():
    with pytest.raises(ValueError):
        LogRecord(
            timestamp=datetime.now(timezone.utc),
            level=LogLevel.INFO,
            source="security",
            message="",
            metadata={},
        )


def test_loggers_are_isolated():
    security = ModuleLogger("security")
    network = ModuleLogger("network")

    security.info("Security event")

    assert security.count() == 1
    assert network.count() == 0


def test_clear_removes_records():
    logger = ModuleLogger("security")

    logger.info("One")
    logger.error("Two")

    logger.clear()

    assert logger.count() == 0
    assert logger.records() == ()
