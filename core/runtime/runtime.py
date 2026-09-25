from enum import Enum

from core.commands.registry import CommandRegistry
from core.config.store import ModuleConfig
from core.crypto.service import CryptoService
from core.dispatch.dispatcher import CommandDispatcher
from core.events.bus import EventBus
from core.export.service import ExportService
from core.health.monitor import HealthMonitor
from core.logging.logger import ModuleLogger
from core.modules.lifecycle import ModuleLifecycle
from core.modules.permissions import PermissionManager
from core.modules.registry import ModuleRegistry
from core.notifications.service import NotificationService
from core.policy.engine import PolicyEngine
from core.recovery.manager import RecoveryManager
from core.storage.store import ModuleStorage
from core.trust.verifier import TrustVerifier


class RuntimeState(str, Enum):
    STOPPED = "stopped"
    RUNNING = "running"


class RuntimeError(Exception):
    """Base error for Core runtime operations."""


class RuntimeAlreadyRunningError(RuntimeError):
    """Raised when the runtime is started while already running."""


class RuntimeAlreadyStoppedError(RuntimeError):
    """Raised when the runtime is stopped while already stopped."""


class CoreRuntime:
    """
    Composition root for Ziggy Core.

    The runtime owns Core-wide services and provides factories for
    module-scoped services.

    Runtime V1 does not start a daemon process, execute modules,
    manage subprocesses, or perform privileged operating-system work.
    """

    def __init__(self) -> None:
        self._state = RuntimeState.STOPPED

        # Core-wide services.
        self.module_registry = ModuleRegistry()
        self.permission_manager = PermissionManager()

        self.event_bus = EventBus()
        self.policy = PolicyEngine()
        self.crypto = CryptoService()
        self.trust = TrustVerifier()
        self.health = HealthMonitor()
        self.recovery = RecoveryManager()

        self.command_registry = CommandRegistry()
        self.dispatcher = CommandDispatcher()

        self.notifications = NotificationService()
        self.export = ExportService()

    @property
    def state(self) -> RuntimeState:
        """Return the current runtime state."""

        return self._state

    @property
    def is_running(self) -> bool:
        """Return whether the runtime is currently running."""

        return self._state == RuntimeState.RUNNING

    def start(self) -> None:
        """Start the Core runtime."""

        if self._state == RuntimeState.RUNNING:
            raise RuntimeAlreadyRunningError(
                "Core runtime is already running."
            )

        self._state = RuntimeState.RUNNING

    def stop(self) -> None:
        """Stop the Core runtime."""

        if self._state == RuntimeState.STOPPED:
            raise RuntimeAlreadyStoppedError(
                "Core runtime is already stopped."
            )

        self._state = RuntimeState.STOPPED

    def create_config(self, module_name: str) -> ModuleConfig:
        """
        Create a configuration namespace for a module.

        Each returned instance owns its own isolated configuration.
        """

        return ModuleConfig(module_name)

    def create_storage(self, module_name: str) -> ModuleStorage:
        """
        Create a storage namespace for a module.

        Each returned instance owns its own isolated storage.
        """

        return ModuleStorage(module_name)

    def create_logger(self, module_name: str) -> ModuleLogger:
        """
        Create a logger for a module.

        Each returned logger owns its own isolated log records.
        """

        return ModuleLogger(module_name)

    def create_lifecycle(self) -> ModuleLifecycle:
        """
        Create a lifecycle tracker for a module.

        Lifecycle state is intentionally owned by the caller.
        """

        return ModuleLifecycle()
