from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class RecoveryAction(str, Enum):
    RESTART = "restart"
    STOP = "stop"
    DISABLE = "disable"


@dataclass(frozen=True)
class RecoveryRequest:
    module: str
    action: RecoveryAction
    reason: str

    def __post_init__(self) -> None:
        if not self.module:
            raise ValueError("module must not be empty")

        if not self.reason:
            raise ValueError("reason must not be empty")

        if not isinstance(self.action, RecoveryAction):
            raise TypeError("action must be a RecoveryAction")


@dataclass(frozen=True)
class RecoveryDecision:
    module: str
    action: RecoveryAction
    approved: bool
    reason: str


class RecoveryManager:
    def __init__(self) -> None:
        self._decisions: list[RecoveryDecision] = []

    def request(self, request: RecoveryRequest) -> RecoveryDecision:
        if not isinstance(request, RecoveryRequest):
            raise TypeError("request must be a RecoveryRequest")

        decision = RecoveryDecision(
            module=request.module,
            action=request.action,
            approved=True,
            reason=request.reason,
        )

        self._decisions.append(decision)
        return decision

    def decisions(self) -> Tuple[RecoveryDecision, ...]:
        return tuple(self._decisions)

    def count(self) -> int:
        return len(self._decisions)

    def clear(self) -> None:
        self._decisions.clear()
