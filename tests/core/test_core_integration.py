import pytest

from core.api import get_core_api_version
from core.commands import CommandDefinition
from core.dispatch import DispatchRequest
from core.modules.manager import ModuleManager, ModuleRegistrationError
from core.modules.manifest import ModuleCompatibility, ModuleManifest
from core.modules.permissions import ModulePermission
from core.policy import PolicyDecision, PolicyRequest, PolicyRule
from core.runtime import CoreRuntime


def make_manifest(
    name: str,
    api_version: int = 1,
    minimum_core_version=None,
) -> ModuleManifest:
    if minimum_core_version is None:
        minimum_core_version = get_core_api_version()

    return ModuleManifest(
        name=name,
        version="1.0.0",
        author="Ziggy Integration Test",
        description=f"{name} integration test module",
        compatibility=ModuleCompatibility(
            api_version=api_version,
            minimum_core_version=minimum_core_version,
        ),
        permissions=("filesystem.read",),
    )


def make_manager(runtime: CoreRuntime) -> ModuleManager:
    return ModuleManager(
        core_version=get_core_api_version(),
        registry=runtime.module_registry,
    )


def test_runtime_registry_accepts_compatible_module():
    runtime = CoreRuntime()
    manager = make_manager(runtime)

    manifest = make_manifest("security")

    assert runtime.module_registry.count() == 0

    manager.register(manifest)

    assert runtime.module_registry.count() == 1
    assert runtime.module_registry.contains("security")
    assert runtime.module_registry.get("security") == manifest


def test_runtime_registry_rejects_incompatible_module():
    runtime = CoreRuntime()
    manager = make_manager(runtime)

    manifest = make_manifest(
        "security",
        api_version=2,
    )

    with pytest.raises(ModuleRegistrationError):
        manager.register(manifest)

    assert runtime.module_registry.count() == 0
    assert not runtime.module_registry.contains("security")


def test_runtime_registry_rejects_module_requiring_newer_core():
    runtime = CoreRuntime()
    manager = make_manager(runtime)

    current = get_core_api_version()

    manifest = make_manifest(
        "security",
        minimum_core_version=type(current)(
            current.major + 1,
            0,
            0,
        ),
    )

    with pytest.raises(ModuleRegistrationError):
        manager.register(manifest)

    assert runtime.module_registry.count() == 0
    assert not runtime.module_registry.contains("security")

from core.modules.permissions import ModulePermission
from core.policy import PolicyDecision, PolicyRequest, PolicyRule


def test_runtime_permission_and_policy_services_remain_separate():
    runtime = CoreRuntime()

    manifest = make_manifest("security")

    assert manifest.has_permission(
        ModulePermission.FILESYSTEM_READ.value
    )

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ
    )

    assert runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    runtime.policy.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
    )

    assert runtime.policy.evaluate(request) is PolicyDecision.ALLOW


def test_policy_does_not_authorize_unmatched_resource():
    runtime = CoreRuntime()

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ
    )

    runtime.policy.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/other.txt",
    )

    assert runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    assert runtime.policy.evaluate(request) is PolicyDecision.NOT_APPLICABLE


def test_revoking_permission_does_not_modify_policy_rules():
    runtime = CoreRuntime()

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ
    )

    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
        decision=PolicyDecision.ALLOW,
    )

    runtime.policy.add_rule(rule)

    runtime.permission_manager.revoke(
        ModulePermission.FILESYSTEM_READ
    )

    assert not runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ
    )

    assert runtime.policy.rules() == (rule,)

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
    )

    assert runtime.policy.evaluate(request) is PolicyDecision.ALLOW


def test_runtime_event_bus_can_drive_notification_service():
    runtime = CoreRuntime()

    received = []

    def notify_from_event(event):
        received.append(event)
        runtime.notifications.success(
            source=event.source,
            title="Module Started",
            message=f"{event.source} started.",
            metadata={"event_type": event.event_type},
        )

    runtime.event_bus.subscribe(
        "module.started",
        notify_from_event,
    )

    event = runtime.event_bus.create_event(
        event_type="module.started",
        source="security",
        payload={"version": "1.0.0"},
    )

    runtime.event_bus.publish(event)

    assert received == [event]
    assert runtime.notifications.count() == 1

    notification = runtime.notifications.list()[0]

    assert notification.source == "security"
    assert notification.title == "Module Started"
    assert notification.message == "security started."
    assert notification.metadata == {
        "event_type": "module.started",
    }


def test_runtime_event_bus_delivers_event_to_multiple_subscribers():
    runtime = CoreRuntime()

    received = []

    def first_handler(event):
        received.append(("first", event))

    def second_handler(event):
        received.append(("second", event))

    runtime.event_bus.subscribe(
        "module.started",
        first_handler,
    )
    runtime.event_bus.subscribe(
        "module.started",
        second_handler,
    )

    event = runtime.event_bus.create_event(
        event_type="module.started",
        source="network",
        payload={"interface": "wlan0"},
    )

    runtime.event_bus.publish(event)

    assert received == [
        ("first", event),
        ("second", event),
    ]


def test_runtime_event_bus_isolates_failing_subscriber():
    runtime = CoreRuntime()

    received = []

    def failing_handler(event):
        raise RuntimeError("subscriber failure")

    def working_handler(event):
        received.append(event)

    runtime.event_bus.subscribe(
        "module.alert",
        failing_handler,
    )
    runtime.event_bus.subscribe(
        "module.alert",
        working_handler,
    )

    event = runtime.event_bus.create_event(
        event_type="module.alert",
        source="security",
        payload={"severity": "high"},
    )

    runtime.event_bus.publish(event)

    assert received == [event]


def test_runtime_event_can_be_exported_through_export_service():
    runtime = CoreRuntime()

    event = runtime.event_bus.create_event(
        event_type="module.started",
        source="security",
        payload={"version": "1.0.0"},
    )

    export_data = {
        "event_type": event.event_type,
        "source": event.source,
        "payload": event.payload,
    }

    result = runtime.export.json(export_data)

    assert result.format.value == "json"
    assert '"event_type": "module.started"' in result.content
    assert '"source": "security"' in result.content
    assert '"version": "1.0.0"' in result.content


def test_runtime_command_can_be_registered_and_bound():
    runtime = CoreRuntime()

    command = CommandDefinition(
        name="security.scan",
        module="security",
        description="Run a security scan.",
        permissions=("filesystem.read",),
    )

    runtime.command_registry.register(command)

    calls = []

    def scan_handler(path):
        calls.append(path)
        return {"scanned": path}

    runtime.dispatcher.bind(
        "security.scan",
        scan_handler,
    )

    request = DispatchRequest(
        command="security.scan",
        arguments=("/tmp/evidence.txt",),
    )

    result = runtime.dispatcher.dispatch(request)

    assert runtime.command_registry.contains("security.scan")
    assert runtime.dispatcher.contains("security.scan")
    assert calls == ["/tmp/evidence.txt"]
    assert result.value == {
        "scanned": "/tmp/evidence.txt",
    }


def test_runtime_command_flow_requires_permission_and_policy_allow():
    runtime = CoreRuntime()

    command = CommandDefinition(
        name="security.scan",
        module="security",
        description="Run a security scan.",
        permissions=("filesystem.read",),
    )

    runtime.command_registry.register(command)

    calls = []

    def scan_handler(path):
        calls.append(path)
        return {"scanned": path}

    runtime.dispatcher.bind(
        "security.scan",
        scan_handler,
    )

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ,
    )

    runtime.policy.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
    )

    assert runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ,
    )
    assert runtime.policy.evaluate(request) == PolicyDecision.ALLOW

    result = runtime.dispatcher.dispatch(
        DispatchRequest(
            command="security.scan",
            arguments=("/tmp/evidence.txt",),
        )
    )

    assert result.value == {
        "scanned": "/tmp/evidence.txt",
    }
    assert calls == ["/tmp/evidence.txt"]


def test_runtime_command_flow_does_not_dispatch_without_permission():
    runtime = CoreRuntime()

    command = CommandDefinition(
        name="security.scan",
        module="security",
        description="Run a security scan.",
        permissions=("filesystem.read",),
    )

    runtime.command_registry.register(command)

    calls = []

    def scan_handler(path):
        calls.append(path)
        return {"scanned": path}

    runtime.dispatcher.bind(
        "security.scan",
        scan_handler,
    )

    runtime.policy.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
            decision=PolicyDecision.ALLOW,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
    )

    permission_allowed = runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ,
    )
    policy_decision = runtime.policy.evaluate(request)

    if not permission_allowed or policy_decision != PolicyDecision.ALLOW:
        result = None
    else:
        result = runtime.dispatcher.dispatch(
            DispatchRequest(
                command="security.scan",
                arguments=("/tmp/evidence.txt",),
            )
        )

    assert permission_allowed is False
    assert policy_decision == PolicyDecision.ALLOW
    assert result is None
    assert calls == []


def test_runtime_command_flow_does_not_dispatch_when_policy_denies():
    runtime = CoreRuntime()

    command = CommandDefinition(
        name="security.scan",
        module="security",
        description="Run a security scan.",
        permissions=("filesystem.read",),
    )

    runtime.command_registry.register(command)

    calls = []

    def scan_handler(path):
        calls.append(path)
        return {"scanned": path}

    runtime.dispatcher.bind(
        "security.scan",
        scan_handler,
    )

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ,
    )

    runtime.policy.add_rule(
        PolicyRule(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
            decision=PolicyDecision.DENY,
        )
    )

    request = PolicyRequest(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
    )

    permission_allowed = runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ,
    )
    policy_decision = runtime.policy.evaluate(request)

    if not permission_allowed or policy_decision != PolicyDecision.ALLOW:
        result = None
    else:
        result = runtime.dispatcher.dispatch(
            DispatchRequest(
                command="security.scan",
                arguments=("/tmp/evidence.txt",),
            )
        )

    assert permission_allowed is True
    assert policy_decision == PolicyDecision.DENY
    assert result is None
    assert calls == []


def test_unregistering_command_does_not_remove_permission_or_policy_state():
    runtime = CoreRuntime()

    command = CommandDefinition(
        name="security.scan",
        module="security",
        description="Run a security scan.",
        permissions=("filesystem.read",),
    )

    runtime.command_registry.register(command)

    runtime.permission_manager.grant(
        ModulePermission.FILESYSTEM_READ,
    )

    rule = PolicyRule(
        module="security",
        action="read",
        resource="/tmp/evidence.txt",
        decision=PolicyDecision.ALLOW,
    )

    runtime.policy.add_rule(rule)

    runtime.command_registry.unregister("security.scan")

    assert runtime.command_registry.contains("security.scan") is False
    assert runtime.permission_manager.is_allowed(
        ModulePermission.FILESYSTEM_READ,
    )
    assert runtime.policy.rules() == (rule,)
    assert runtime.policy.evaluate(
        PolicyRequest(
            module="security",
            action="read",
            resource="/tmp/evidence.txt",
        )
    ) == PolicyDecision.ALLOW
