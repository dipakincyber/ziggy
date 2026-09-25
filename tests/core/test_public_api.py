from core.api import CoreAPIVersion, get_core_api_version
from core.commands import (
    CommandDefinition,
    CommandNotFoundError,
    CommandRegistrationError,
    CommandRegistry,
)
from core.compatibility import CompatibilityChecker, CompatibilityResult
from core.dispatch import (
    CommandDispatcher,
    DispatchError,
    DispatchRequest,
    DispatchResult,
)
from core.health import HealthMonitor, HealthReport, HealthStatus


def test_api_public_exports():
    assert CoreAPIVersion is not None
    assert get_core_api_version is not None

    assert CommandDefinition is not None
    assert CommandNotFoundError is not None
    assert CommandRegistrationError is not None
    assert CommandRegistry is not None

    assert CompatibilityChecker is not None
    assert CompatibilityResult is not None

    assert CommandDispatcher is not None
    assert DispatchError is not None
    assert DispatchRequest is not None
    assert DispatchResult is not None

    assert HealthMonitor is not None
    assert HealthReport is not None
    assert HealthStatus is not None
