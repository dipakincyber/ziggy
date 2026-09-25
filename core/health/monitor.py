from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class HealthReport:
    module: str
    status: HealthStatus
    message: str
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.module:
            raise ValueError("Module cannot be empty.")

        if not self.message:
            raise ValueError("Health message cannot be empty.")

        if not isinstance(self.status, HealthStatus):
            raise TypeError("Status must be a HealthStatus.")

        if self.timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware.")


class HealthMonitor:
    def __init__(self) -> None:
        self._reports: dict[str, HealthReport] = {}

    def report(
        self,
        module: str,
        status: HealthStatus,
        message: str,
        timestamp: datetime | None = None,
    ) -> HealthReport:
        if not module:
            raise ValueError("Module cannot be empty.")

        if not isinstance(status, HealthStatus):
            raise TypeError("Status must be a HealthStatus.")

        if not message:
            raise ValueError("Health message cannot be empty.")

        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        if timestamp.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware.")

        health_report = HealthReport(
            module=module,
            status=status,
            message=message,
            timestamp=timestamp,
        )

        self._reports[module] = health_report
        return health_report

    def get(self, module: str) -> HealthReport:
        try:
            return self._reports[module]
        except KeyError as exc:
            raise KeyError(
                f"No health report exists for module '{module}'."
            ) from exc

    def contains(self, module: str) -> bool:
        return module in self._reports

    def list(self) -> tuple[HealthReport, ...]:
        return tuple(
            self._reports[module]
            for module in sorted(self._reports)
        )

    def count(self) -> int:
        return len(self._reports)

    def clear(self, module: str) -> None:
        self._reports.pop(module, None)

    def snapshot(self) -> tuple[HealthReport, ...]:
        return self.list()
