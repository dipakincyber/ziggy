"""
Ziggy Core Module Lifecycle.

This module defines the lifecycle states and valid state transitions
for Ziggy modules.

The lifecycle model does not install, execute, start, stop, or remove
modules. It only represents and validates lifecycle state.
"""

from enum import Enum


class ModuleLifecycleState(str, Enum):
    """States a Ziggy module can occupy during its lifecycle."""

    DISCOVERED = "discovered"
    VERIFIED = "verified"
    INSTALLED = "installed"
    DISABLED = "disabled"
    ENABLED = "enabled"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    REMOVED = "removed"


class InvalidLifecycleTransitionError(RuntimeError):
    """Raised when a lifecycle transition is not allowed."""


class ModuleLifecycle:
    """
    Tracks and validates the lifecycle state of one module.

    This class contains no module execution or process-management logic.
    """

    _VALID_TRANSITIONS = {
        ModuleLifecycleState.DISCOVERED: {
            ModuleLifecycleState.VERIFIED,
        },
        ModuleLifecycleState.VERIFIED: {
            ModuleLifecycleState.INSTALLED,
        },
        ModuleLifecycleState.INSTALLED: {
            ModuleLifecycleState.ENABLED,
            ModuleLifecycleState.DISABLED,
        },
        ModuleLifecycleState.DISABLED: {
            ModuleLifecycleState.ENABLED,
            ModuleLifecycleState.REMOVED,
        },
        ModuleLifecycleState.ENABLED: {
            ModuleLifecycleState.DISABLED,
            ModuleLifecycleState.STARTING,
        },
        ModuleLifecycleState.STARTING: {
            ModuleLifecycleState.RUNNING,
            ModuleLifecycleState.FAILED,
        },
        ModuleLifecycleState.RUNNING: {
            ModuleLifecycleState.STOPPING,
            ModuleLifecycleState.UNHEALTHY,
        },
        ModuleLifecycleState.STOPPING: {
            ModuleLifecycleState.STOPPED,
            ModuleLifecycleState.FAILED,
        },
        ModuleLifecycleState.STOPPED: {
            ModuleLifecycleState.STARTING,
            ModuleLifecycleState.REMOVED,
        },
        ModuleLifecycleState.UNHEALTHY: {
            ModuleLifecycleState.STOPPING,
            ModuleLifecycleState.FAILED,
        },
        ModuleLifecycleState.FAILED: {
            ModuleLifecycleState.STARTING,
        },
        ModuleLifecycleState.REMOVED: set(),
    }

    def __init__(
        self,
        initial_state: ModuleLifecycleState = (
            ModuleLifecycleState.DISCOVERED
        ),
    ) -> None:
        """Create a lifecycle tracker with the supplied initial state."""

        self._state = initial_state

    @property
    def state(self) -> ModuleLifecycleState:
        """Return the current lifecycle state."""

        return self._state

    def can_transition(
        self,
        target_state: ModuleLifecycleState,
    ) -> bool:
        """Return whether a transition to target_state is allowed."""

        return target_state in self._VALID_TRANSITIONS[self._state]

    def transition(
        self,
        target_state: ModuleLifecycleState,
    ) -> None:
        """
        Move the module to target_state.

        Raises InvalidLifecycleTransitionError when the transition
        is not permitted.
        """

        if not self.can_transition(target_state):
            raise InvalidLifecycleTransitionError(
                f"Invalid lifecycle transition: "
                f"{self._state.value} -> {target_state.value}"
            )

        self._state = target_state
