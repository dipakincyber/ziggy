from core.recovery.manager import (
    RecoveryAction,
    RecoveryDecision,
    RecoveryManager,
    RecoveryRequest,
)


def test_recovery_actions_exist():
    assert RecoveryAction.RESTART.value == "restart"
    assert RecoveryAction.STOP.value == "stop"
    assert RecoveryAction.DISABLE.value == "disable"


def test_recovery_request_is_immutable():
    request = RecoveryRequest(
        module="security",
        action=RecoveryAction.RESTART,
        reason="module became unhealthy",
    )

    try:
        request.module = "network"
        assert False
    except AttributeError:
        pass


def test_recovery_request_requires_module():
    try:
        RecoveryRequest(
            module="",
            action=RecoveryAction.RESTART,
            reason="failure",
        )
        assert False
    except ValueError:
        pass


def test_recovery_request_requires_reason():
    try:
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="",
        )
        assert False
    except ValueError:
        pass


def test_recovery_request_requires_valid_action():
    try:
        RecoveryRequest(
            module="security",
            action="restart",
            reason="failure",
        )
        assert False
    except TypeError:
        pass


def test_request_produces_approved_decision():
    manager = RecoveryManager()

    request = RecoveryRequest(
        module="security",
        action=RecoveryAction.RESTART,
        reason="module became unhealthy",
    )

    decision = manager.request(request)

    assert decision == RecoveryDecision(
        module="security",
        action=RecoveryAction.RESTART,
        approved=True,
        reason="module became unhealthy",
    )


def test_decisions_are_recorded():
    manager = RecoveryManager()

    manager.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="unhealthy",
        )
    )

    manager.request(
        RecoveryRequest(
            module="network",
            action=RecoveryAction.STOP,
            reason="manual recovery request",
        )
    )

    assert manager.count() == 2
    assert len(manager.decisions()) == 2


def test_decisions_are_read_only_snapshot():
    manager = RecoveryManager()

    manager.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="unhealthy",
        )
    )

    decisions = manager.decisions()

    assert isinstance(decisions, tuple)
    assert len(decisions) == 1


def test_clear_removes_decisions():
    manager = RecoveryManager()

    manager.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="unhealthy",
        )
    )

    manager.clear()

    assert manager.count() == 0
    assert manager.decisions() == ()


def test_invalid_request_type_is_rejected():
    manager = RecoveryManager()

    try:
        manager.request("restart")
        assert False
    except TypeError:
        pass
