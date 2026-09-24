"""
Ziggy Core Policy Engine.

This module provides the foundational policy decision contract
for Ziggy.

The initial implementation evaluates explicit in-memory rules.
It does not enforce permissions at the operating-system level.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class PolicyError(RuntimeError):
    """Base error for policy operations."""


class InvalidPolicyValueError(PolicyError):
    """Raised when a policy value is invalid."""


class PolicyDecision(str, Enum):
    """Possible outcomes of a policy evaluation."""

    ALLOW = "ALLOW"
    DENY = "DENY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class PolicyRequest:
    """
    Request for a policy decision.

    A request identifies the module, action, and resource involved.
    """

    module: str
    action: str
    resource: str

    def __post_init__(self) -> None:
        self._validate_value(self.module, "Module")
        self._validate_value(self.action, "Action")
        self._validate_value(self.resource, "Resource")

    @staticmethod
    def _validate_value(value: str, name: str) -> None:
        if not isinstance(value, str):
            raise InvalidPolicyValueError(
                f"{name} must be a string."
            )

        if not value.strip():
            raise InvalidPolicyValueError(
                f"{name} cannot be empty."
            )


@dataclass(frozen=True)
class PolicyRule:
    """
    Explicit rule matching a module, action, and resource.

    Rules are evaluated in registration order.
    The first matching rule determines the decision.
    """

    module: str
    action: str
    resource: str
    decision: PolicyDecision

    def __post_init__(self) -> None:
        self._validate_value(self.module, "Module")
        self._validate_value(self.action, "Action")
        self._validate_value(self.resource, "Resource")

        if not isinstance(self.decision, PolicyDecision):
            raise InvalidPolicyValueError(
                "Decision must be a PolicyDecision."
            )

    def matches(self, request: PolicyRequest) -> bool:
        """Return whether this rule matches the supplied request."""

        return (
            self.module == request.module
            and self.action == request.action
            and self.resource == request.resource
        )

    @staticmethod
    def _validate_value(value: str, name: str) -> None:
        if not isinstance(value, str):
            raise InvalidPolicyValueError(
                f"{name} must be a string."
            )

        if not value.strip():
            raise InvalidPolicyValueError(
                f"{name} cannot be empty."
            )


class PolicyEngine:
    """
    In-memory deterministic policy engine.

    Rules are evaluated in registration order.
    The first matching rule wins.
    """

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []

    def add_rule(self, rule: PolicyRule) -> None:
        """Register a policy rule."""

        if not isinstance(rule, PolicyRule):
            raise TypeError("Rule must be a PolicyRule.")

        self._rules.append(rule)

    def remove_rule(self, rule: PolicyRule) -> None:
        """Remove a previously registered rule."""

        if rule not in self._rules:
            raise PolicyError("Policy rule is not registered.")

        self._rules.remove(rule)

    def evaluate(self, request: PolicyRequest) -> PolicyDecision:
        """
        Evaluate a request against registered rules.

        The first matching rule determines the decision.
        If no rule matches, NOT_APPLICABLE is returned.
        """

        if not isinstance(request, PolicyRequest):
            raise TypeError(
                "Request must be a PolicyRequest."
            )

        for rule in self._rules:
            if rule.matches(request):
                return rule.decision

        return PolicyDecision.NOT_APPLICABLE

    def rules(self) -> Tuple[PolicyRule, ...]:
        """Return registered rules in evaluation order."""

        return tuple(self._rules)

    def count(self) -> int:
        """Return the number of registered rules."""

        return len(self._rules)

    def clear(self) -> None:
        """Remove all registered policy rules."""

        self._rules.clear()
