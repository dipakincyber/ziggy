from dataclasses import FrozenInstanceError

import pytest

from core.policy import (
    InvalidPolicyValueError,
    PolicyDecision,
    PolicyEngine,
    PolicyError,
    PolicyRequest,
    PolicyRule,
)


def test_policy_request_accepts_valid_values():
    request = PolicyRequest(
        module="security",
        action="read",
        resource="/home/user/file.txt",
    )

    assert request.module == "security"
    assert request.action == "read"
    assert request.resource == "/home/user/file.txt"


def test_policy_request_is_immutable():
    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/file",
    )

    with pytest.raises(FrozenInstanceError):
        request.action = "write"


def test_policy_request_rejects_non_string_module():
    with pytest.raises(InvalidPolicyValueError):
        PolicyRequest(
            module=123,
            action="read",
            resource="/tmp/file",
        )


def test_policy_request_rejects_empty_action():
    with pytest.raises(InvalidPolicyValueError):
        PolicyRequest(
            module="security",
            action="",
            resource="/tmp/file",
        )


def test_policy_request_rejects_empty_resource():
    with pytest.raises(InvalidPolicyValueError):
        PolicyRequest(
            module="security",
            action="read",
            resource="   ",
        )


def test_policy_rule_accepts_valid_values():
    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.ALLOW,
    )

    assert rule.decision is PolicyDecision.ALLOW


def test_policy_rule_is_immutable():
    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.DENY,
    )

    with pytest.raises(FrozenInstanceError):
        rule.decision = PolicyDecision.ALLOW


def test_policy_rule_requires_valid_decision():
    with pytest.raises(InvalidPolicyValueError):
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/file",
            decision="ALLOW",
        )


def test_matching_rule_returns_allow():
    engine = PolicyEngine()

    engine.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/file",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/file",
    )

    assert engine.evaluate(request) is PolicyDecision.ALLOW


def test_matching_rule_returns_deny():
    engine = PolicyEngine()

    engine.add_rule(
        PolicyRule(
            module="security",
            action="delete",
            resource="/tmp/file",
            decision=PolicyDecision.DENY,
        )
    )

    request = PolicyRequest(
        module="security",
        action="delete",
        resource="/tmp/file",
    )

    assert engine.evaluate(request) is PolicyDecision.DENY


def test_unmatched_request_returns_not_applicable():
    engine = PolicyEngine()

    engine.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/file",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="network",
        action="connect",
        resource="example.com",
    )

    assert engine.evaluate(request) is PolicyDecision.NOT_APPLICABLE


def test_first_matching_rule_wins():
    engine = PolicyEngine()

    first = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.DENY,
    )

    second = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.ALLOW,
    )

    engine.add_rule(first)
    engine.add_rule(second)

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/file",
    )

    assert engine.evaluate(request) is PolicyDecision.DENY


def test_rules_preserve_registration_order():
    engine = PolicyEngine()

    first = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/a",
        decision=PolicyDecision.ALLOW,
    )

    second = PolicyRule(
        module="network",
        action="connect",
        resource="example.com",
        decision=PolicyDecision.DENY,
    )

    engine.add_rule(first)
    engine.add_rule(second)

    assert engine.rules() == (first, second)


def test_rule_count():
    engine = PolicyEngine()

    assert engine.count() == 0

    engine.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/file",
            decision=PolicyDecision.ALLOW,
        )
    )

    assert engine.count() == 1


def test_remove_rule():
    engine = PolicyEngine()

    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.ALLOW,
    )

    engine.add_rule(rule)
    engine.remove_rule(rule)

    assert engine.count() == 0


def test_remove_unregistered_rule_raises():
    engine = PolicyEngine()

    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.ALLOW,
    )

    with pytest.raises(PolicyError):
        engine.remove_rule(rule)


def test_clear_removes_all_rules():
    engine = PolicyEngine()

    engine.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/a",
            decision=PolicyDecision.ALLOW,
        )
    )

    engine.add_rule(
        PolicyRule(
            module="network",
            action="connect",
            resource="example.com",
            decision=PolicyDecision.DENY,
        )
    )

    engine.clear()

    assert engine.count() == 0


def test_rules_are_not_mutable_through_returned_collection():
    engine = PolicyEngine()

    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/file",
        decision=PolicyDecision.ALLOW,
    )

    engine.add_rule(rule)

    rules = engine.rules()

    assert isinstance(rules, tuple)
    assert rules == (rule,)


def test_engine_rejects_invalid_rule_type():
    engine = PolicyEngine()

    with pytest.raises(TypeError):
        engine.add_rule("not a rule")


def test_engine_rejects_invalid_request_type():
    engine = PolicyEngine()

    with pytest.raises(TypeError):
        engine.evaluate("not a request")
