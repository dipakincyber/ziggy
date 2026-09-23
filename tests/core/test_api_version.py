from core.api.version import (
    CORE_API_VERSION,
    CoreAPIVersion,
    get_core_api_version,
)


def test_core_api_version_is_valid():
    assert isinstance(CORE_API_VERSION, CoreAPIVersion)
    assert CORE_API_VERSION.major == 1
    assert CORE_API_VERSION.minor == 0
    assert CORE_API_VERSION.patch == 0


def test_get_core_api_version_returns_current_version():
    version = get_core_api_version()

    assert version == CORE_API_VERSION


def test_core_api_version_string():
    assert str(CORE_API_VERSION) == "1.0.0"
