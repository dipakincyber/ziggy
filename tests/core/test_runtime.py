import pytest

from core.runtime import (
    CoreRuntime,
    RuntimeAlreadyRunningError,
    RuntimeAlreadyStoppedError,
    RuntimeState,
)


def test_runtime_starts_stopped():
    runtime = CoreRuntime()

    assert runtime.state == RuntimeState.STOPPED
    assert runtime.is_running is False


def test_runtime_starts():
    runtime = CoreRuntime()

    runtime.start()

    assert runtime.state == RuntimeState.RUNNING
    assert runtime.is_running is True


def test_runtime_cannot_start_twice():
    runtime = CoreRuntime()

    runtime.start()

    with pytest.raises(RuntimeAlreadyRunningError):
        runtime.start()


def test_runtime_stops():
    runtime = CoreRuntime()

    runtime.start()
    runtime.stop()

    assert runtime.state == RuntimeState.STOPPED
    assert runtime.is_running is False


def test_runtime_cannot_stop_twice():
    runtime = CoreRuntime()

    with pytest.raises(RuntimeAlreadyStoppedError):
        runtime.stop()


def test_runtime_can_restart_after_stop():
    runtime = CoreRuntime()

    runtime.start()
    runtime.stop()
    runtime.start()

    assert runtime.state == RuntimeState.RUNNING


def test_runtime_exposes_core_services():
    runtime = CoreRuntime()

    assert runtime.module_registry is not None
    assert runtime.permission_manager is not None
    assert runtime.event_bus is not None
    assert runtime.policy is not None
    assert runtime.crypto is not None
    assert runtime.trust is not None
    assert runtime.health is not None
    assert runtime.recovery is not None
    assert runtime.command_registry is not None
    assert runtime.dispatcher is not None
    assert runtime.notifications is not None
    assert runtime.export is not None


def test_runtime_creates_module_config():
    runtime = CoreRuntime()

    config = runtime.create_config("security")

    config.set("enabled", True)

    assert config.get("enabled") is True
    assert config.module_name == "security"


def test_runtime_creates_module_storage():
    runtime = CoreRuntime()

    storage = runtime.create_storage("security")

    storage.set("scan_count", 5)

    assert storage.get("scan_count") == 5


def test_runtime_creates_module_logger():
    runtime = CoreRuntime()

    logger = runtime.create_logger("security")

    logger.info("test message")

    assert logger.count() == 1


def test_runtime_creates_module_lifecycle():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    assert lifecycle is not None
    assert lifecycle.state.value == "discovered"
