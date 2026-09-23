from core.modules.lifecycle import (
    InvalidLifecycleTransitionError,
    ModuleLifecycle,
    ModuleLifecycleState,
)


def test_default_state_is_discovered():
    lifecycle = ModuleLifecycle()

    assert lifecycle.state == ModuleLifecycleState.DISCOVERED


def test_custom_initial_state():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.VERIFIED
    )

    assert lifecycle.state == ModuleLifecycleState.VERIFIED


def test_valid_transition():
    lifecycle = ModuleLifecycle()

    assert lifecycle.can_transition(
        ModuleLifecycleState.VERIFIED
    )

    lifecycle.transition(ModuleLifecycleState.VERIFIED)

    assert lifecycle.state == ModuleLifecycleState.VERIFIED


def test_invalid_transition_is_rejected():
    lifecycle = ModuleLifecycle()

    assert not lifecycle.can_transition(
        ModuleLifecycleState.RUNNING
    )


def test_invalid_transition_does_not_change_state():
    lifecycle = ModuleLifecycle()

    try:
        lifecycle.transition(ModuleLifecycleState.RUNNING)
    except InvalidLifecycleTransitionError:
        pass

    assert lifecycle.state == ModuleLifecycleState.DISCOVERED


def test_invalid_transition_raises_specific_error():
    lifecycle = ModuleLifecycle()

    try:
        lifecycle.transition(ModuleLifecycleState.RUNNING)
    except InvalidLifecycleTransitionError as exc:
        assert "discovered -> running" in str(exc)
    else:
        raise AssertionError(
            "Expected InvalidLifecycleTransitionError"
        )


def test_module_can_reach_running_state():
    lifecycle = ModuleLifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    assert lifecycle.state == ModuleLifecycleState.RUNNING


def test_module_can_stop_from_running_state():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.RUNNING
    )

    lifecycle.transition(ModuleLifecycleState.STOPPING)
    lifecycle.transition(ModuleLifecycleState.STOPPED)

    assert lifecycle.state == ModuleLifecycleState.STOPPED


def test_failed_module_can_restart():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.STARTING
    )

    lifecycle.transition(ModuleLifecycleState.FAILED)
    lifecycle.transition(ModuleLifecycleState.STARTING)

    assert lifecycle.state == ModuleLifecycleState.STARTING


def test_removed_module_has_no_valid_transitions():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.REMOVED
    )

    assert not lifecycle.can_transition(
        ModuleLifecycleState.STARTING
    )


def test_removed_module_cannot_transition():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.REMOVED
    )

    try:
        lifecycle.transition(ModuleLifecycleState.STARTING)
    except InvalidLifecycleTransitionError:
        pass
    else:
        raise AssertionError(
            "Expected InvalidLifecycleTransitionError"
        )


def test_unhealthy_module_can_be_stopped():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.UNHEALTHY
    )

    lifecycle.transition(ModuleLifecycleState.STOPPING)

    assert lifecycle.state == ModuleLifecycleState.STOPPING


def test_disabled_module_can_be_enabled():
    lifecycle = ModuleLifecycle(
        ModuleLifecycleState.DISABLED
    )

    lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert lifecycle.state == ModuleLifecycleState.ENABLED
