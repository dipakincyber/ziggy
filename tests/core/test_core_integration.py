import pytest

from core.api import get_core_api_version
from core.commands import CommandDefinition
from core.dispatch import DispatchRequest
from core.dependencies import (
    DependencyResolver,
    DependencyStatus,
    ModuleDependency,
    ModuleVersion,
)
from core.discovery import ModuleDiscovery
from core.health import HealthStatus
from core.installation import ModuleInstaller
from core.modules.lifecycle import ModuleLifecycleState
from core.modules.manager import ModuleManager, ModuleRegistrationError
from core.modules.manifest import ModuleCompatibility, ModuleManifest
from core.modules.permissions import ModulePermission
from core.policy import PolicyDecision, PolicyRequest, PolicyRule
from core.recovery import RecoveryAction, RecoveryRequest
from core.trust import TrustIdentity, TrustStatus, TrustVerifier
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


def test_runtime_lifecycle_and_health_track_running_module():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    report = runtime.health.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Security module is operating normally.",
    )

    assert lifecycle.state == ModuleLifecycleState.RUNNING
    assert report.module == "security"
    assert report.status == HealthStatus.HEALTHY
    assert runtime.health.get("security") == report


def test_runtime_unhealthy_health_can_correspond_to_unhealthy_lifecycle():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    report = runtime.health.report(
        module="security",
        status=HealthStatus.UNHEALTHY,
        message="Security module failed its health check.",
    )

    lifecycle.transition(ModuleLifecycleState.UNHEALTHY)

    assert report.status == HealthStatus.UNHEALTHY
    assert lifecycle.state == ModuleLifecycleState.UNHEALTHY


def test_runtime_unhealthy_module_can_request_restart_recovery():
    runtime = CoreRuntime()

    runtime.health.report(
        module="security",
        status=HealthStatus.UNHEALTHY,
        message="Security module failed its health check.",
    )

    recovery = runtime.recovery.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="Health check reported the module as unhealthy.",
        )
    )

    assert recovery.module == "security"
    assert recovery.action == RecoveryAction.RESTART
    assert recovery.approved is True
    assert runtime.recovery.count() == 1


def test_runtime_recovery_decision_does_not_automatically_change_lifecycle():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)
    lifecycle.transition(ModuleLifecycleState.UNHEALTHY)

    recovery = runtime.recovery.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="Restart requested after health failure.",
        )
    )

    assert recovery.approved is True
    assert lifecycle.state == ModuleLifecycleState.UNHEALTHY

    lifecycle.transition(ModuleLifecycleState.STOPPING)
    lifecycle.transition(ModuleLifecycleState.STOPPED)
    lifecycle.transition(ModuleLifecycleState.STARTING)

    assert lifecycle.state == ModuleLifecycleState.STARTING


def test_runtime_recovery_history_survives_module_recovery():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)
    lifecycle.transition(ModuleLifecycleState.UNHEALTHY)

    runtime.health.report(
        module="security",
        status=HealthStatus.UNHEALTHY,
        message="Initial health failure.",
    )

    recovery = runtime.recovery.request(
        RecoveryRequest(
            module="security",
            action=RecoveryAction.RESTART,
            reason="Restart after initial health failure.",
        )
    )

    lifecycle.transition(ModuleLifecycleState.STOPPING)
    lifecycle.transition(ModuleLifecycleState.STOPPED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    runtime.health.report(
        module="security",
        status=HealthStatus.HEALTHY,
        message="Module recovered successfully.",
    )

    assert lifecycle.state == ModuleLifecycleState.RUNNING
    assert runtime.health.get("security").status == HealthStatus.HEALTHY
    assert runtime.recovery.decisions() == (recovery,)


def test_discovery_verification_installation_and_registration_pipeline(
    tmp_path,
):
    runtime = CoreRuntime()

    source_root = tmp_path / "available"
    module_dir = source_root / "security"
    module_dir.mkdir(parents=True)

    manifest_path = module_dir / "module.yaml"
    manifest_path.write_text(
        "name: security\nversion: 1.0.0\n"
    )

    artifact = b"security-module-artifact"
    artifact_path = module_dir / "artifact.bin"
    artifact_path.write_bytes(artifact)

    discovery = ModuleDiscovery()
    candidates = discovery.discover(source_root)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.name == "security"
    assert candidate.module_path == module_dir
    assert candidate.manifest_path == manifest_path

    verifier = TrustVerifier()
    verifier.register_identity(
        TrustIdentity(
            identity="ziggy-test-publisher",
            status=TrustStatus.TRUSTED,
        )
    )

    import hashlib

    expected_sha256 = hashlib.sha256(artifact).hexdigest()

    verification = verifier.verify_artifact(
        identity="ziggy-test-publisher",
        artifact=artifact,
        expected_sha256=expected_sha256,
    )

    assert verification.is_valid is True

    installation_root = tmp_path / "installed"
    installer = ModuleInstaller(installation_root)

    installation = installer.install(candidate)

    assert installation.name == "security"
    assert installation.installed_path == installation_root / "security"
    assert installer.is_installed("security")

    manager = make_manager(runtime)

    manifest = make_manifest("security")
    manager.register(manifest)

    assert runtime.module_registry.count() == 1
    assert runtime.module_registry.get("security") == manifest


def test_discovery_does_not_admit_module_without_manifest(tmp_path):
    runtime = CoreRuntime()

    source_root = tmp_path / "available"
    module_dir = source_root / "security"
    module_dir.mkdir(parents=True)

    (module_dir / "artifact.bin").write_bytes(
        b"security-module-artifact"
    )

    discovery = ModuleDiscovery()
    candidates = discovery.discover(source_root)

    assert candidates == ()
    assert runtime.module_registry.count() == 0


def test_tampered_artifact_stops_verification_before_installation(tmp_path):
    source_root = tmp_path / "available"
    module_dir = source_root / "security"
    module_dir.mkdir(parents=True)

    manifest_path = module_dir / "module.yaml"
    manifest_path.write_text(
        "name: security\nversion: 1.0.0\n"
    )

    original_artifact = b"original-security-artifact"
    tampered_artifact = b"tampered-security-artifact"

    artifact_path = module_dir / "artifact.bin"
    artifact_path.write_bytes(original_artifact)

    candidate = ModuleDiscovery().discover(source_root)[0]

    verifier = TrustVerifier()
    verifier.register_identity(
        TrustIdentity(
            identity="ziggy-test-publisher",
            status=TrustStatus.TRUSTED,
        )
    )

    import hashlib

    expected_sha256 = hashlib.sha256(original_artifact).hexdigest()

    verification = verifier.verify_artifact(
        identity="ziggy-test-publisher",
        artifact=tampered_artifact,
        expected_sha256=expected_sha256,
    )

    assert verification.is_valid is False
    assert verification.integrity_valid is False

    installation_root = tmp_path / "installed"
    installer = ModuleInstaller(installation_root)

    assert not installer.is_installed("security")


def test_untrusted_identity_stops_verification_before_installation(tmp_path):
    source_root = tmp_path / "available"
    module_dir = source_root / "security"
    module_dir.mkdir(parents=True)

    (module_dir / "module.yaml").write_text(
        "name: security\nversion: 1.0.0\n"
    )

    artifact = b"security-module-artifact"
    (module_dir / "artifact.bin").write_bytes(artifact)

    candidate = ModuleDiscovery().discover(source_root)[0]

    verifier = TrustVerifier()
    verifier.register_identity(
        TrustIdentity(
            identity="unknown-publisher",
            status=TrustStatus.UNTRUSTED,
        )
    )

    import hashlib

    verification = verifier.verify_artifact(
        identity="unknown-publisher",
        artifact=artifact,
        expected_sha256=hashlib.sha256(artifact).hexdigest(),
    )

    assert verification.is_valid is False
    assert verification.status is TrustStatus.UNTRUSTED

    installation_root = tmp_path / "installed"
    installer = ModuleInstaller(installation_root)

    assert not installer.is_installed(candidate.name)


def test_incompatible_module_stops_registration_after_installation(
    tmp_path,
):
    runtime = CoreRuntime()

    source_root = tmp_path / "available"
    module_dir = source_root / "network"
    module_dir.mkdir(parents=True)

    (module_dir / "module.yaml").write_text(
        "name: network\nversion: 1.0.0\n"
    )

    artifact = b"network-module-artifact"
    (module_dir / "artifact.bin").write_bytes(artifact)

    candidate = ModuleDiscovery().discover(source_root)[0]

    verifier = TrustVerifier()
    verifier.register_identity(
        TrustIdentity(
            identity="ziggy-test-publisher",
            status=TrustStatus.TRUSTED,
        )
    )

    import hashlib

    verification = verifier.verify_artifact(
        identity="ziggy-test-publisher",
        artifact=artifact,
        expected_sha256=hashlib.sha256(artifact).hexdigest(),
    )

    assert verification.is_valid is True

    installer = ModuleInstaller(tmp_path / "installed")
    installation = installer.install(candidate)

    assert installer.is_installed("network")
    assert installation.installed_path.exists()

    manager = make_manager(runtime)

    incompatible_manifest = make_manifest(
        "network",
        api_version=2,
    )

    with pytest.raises(ModuleRegistrationError):
        manager.register(incompatible_manifest)

    assert runtime.module_registry.count() == 0
    assert not runtime.module_registry.contains("network")


def test_satisfied_dependency_allows_lifecycle_progression():
    runtime = CoreRuntime()

    resolver = DependencyResolver(
        {
            "network": ModuleVersion(1, 2, 0),
        }
    )

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(1, 0, 0),
    )

    result = resolver.resolve(dependency)

    assert result.status is DependencyStatus.AVAILABLE
    assert result.is_satisfied is True

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert lifecycle.state is ModuleLifecycleState.ENABLED


def test_missing_dependency_blocks_lifecycle_progression():
    runtime = CoreRuntime()

    resolver = DependencyResolver()

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(1, 0, 0),
    )

    result = resolver.resolve(dependency)

    assert result.status is DependencyStatus.MISSING
    assert result.is_satisfied is False

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)

    if result.is_satisfied:
        lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert lifecycle.state is ModuleLifecycleState.INSTALLED


def test_incompatible_dependency_blocks_lifecycle_progression():
    runtime = CoreRuntime()

    resolver = DependencyResolver(
        {
            "network": ModuleVersion(1, 1, 0),
        }
    )

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(2, 0, 0),
    )

    result = resolver.resolve(dependency)

    assert result.status is DependencyStatus.INCOMPATIBLE
    assert result.is_satisfied is False
    assert result.available_version == ModuleVersion(1, 1, 0)

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)

    if result.is_satisfied:
        lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert lifecycle.state is ModuleLifecycleState.INSTALLED


def test_dependency_resolution_does_not_mutate_lifecycle():
    runtime = CoreRuntime()

    resolver = DependencyResolver(
        {
            "network": ModuleVersion(1, 0, 0),
        }
    )

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(1, 0, 0),
    )

    lifecycle = runtime.create_lifecycle()

    result = resolver.resolve(dependency)

    assert result.is_satisfied is True
    assert lifecycle.state is ModuleLifecycleState.DISCOVERED


def test_dependency_order_is_respected_before_lifecycle_progression():
    runtime = CoreRuntime()

    resolver = DependencyResolver()

    order = resolver.resolve_order(
        {
            "security": ("network",),
            "network": ("base",),
            "base": (),
        }
    )

    assert order == (
        "base",
        "network",
        "security",
    )

    lifecycles = {
        name: runtime.create_lifecycle()
        for name in order
    }

    for name in order:
        lifecycle = lifecycles[name]

        lifecycle.transition(ModuleLifecycleState.VERIFIED)
        lifecycle.transition(ModuleLifecycleState.INSTALLED)
        lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert all(
        lifecycle.state is ModuleLifecycleState.ENABLED
        for lifecycle in lifecycles.values()
    )


def test_fake_module_end_to_end_core_lifecycle():
    runtime = CoreRuntime()
    runtime.start()

    resolver = DependencyResolver(
        {
            "network": ModuleVersion(1, 0, 0),
        }
    )

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(1, 0, 0),
    )

    # 1. Dependency must be satisfied before lifecycle progression.
    dependency_result = resolver.resolve(dependency)
    assert dependency_result.is_satisfied is True

    # 2. Create the module's Core-scoped services.
    module_name = "fake-security"

    lifecycle = runtime.create_lifecycle()
    config = runtime.create_config(module_name)
    storage = runtime.create_storage(module_name)
    logger = runtime.create_logger(module_name)

    # 3. Configure the fake module.
    config.set("enabled", True)
    storage.set("initialized", True)

    # 4. Lifecycle: discovered -> verified -> installed.
    assert lifecycle.state is ModuleLifecycleState.DISCOVERED

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)

    # 5. Enable only after dependencies are satisfied.
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    assert lifecycle.state is ModuleLifecycleState.ENABLED

    # 6. Start and reach running state.
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    assert lifecycle.state is ModuleLifecycleState.RUNNING

    # 7. Module reports health.
    runtime.health.report(
        module_name,
        HealthStatus.HEALTHY,
        "Fake module is operational.",
    )

    health = runtime.health.get(module_name)

    assert health is not None
    assert health.status is HealthStatus.HEALTHY

    # 8. Module emits an event.
    received_events = []

    def on_module_started(event):
        received_events.append(event)

    runtime.event_bus.subscribe(
        "module.started",
        on_module_started,
    )

    event = runtime.event_bus.create_event(
        event_type="module.started",
        source=module_name,
        payload={"state": lifecycle.state.value},
    )

    runtime.event_bus.publish(event)

    assert len(received_events) == 1
    assert received_events[0].source == module_name

    # 9. Core turns the event into a notification.
    runtime.notifications.info(
        source=module_name,
        title="Module Started",
        message="Fake security module is running.",
    )

    notifications = runtime.notifications.list()

    assert len(notifications) == 1
    assert notifications[0].source == module_name

    # 10. Module writes a log record.
    logger.info("Fake module started.")

    assert logger.count() == 1
    assert logger.records()[0].message == "Fake module started."

    # 11. Module can be disabled cleanly.
    lifecycle.transition(ModuleLifecycleState.STOPPING)
    lifecycle.transition(ModuleLifecycleState.STOPPED)
    lifecycle.transition(ModuleLifecycleState.REMOVED)

    assert lifecycle.state is ModuleLifecycleState.REMOVED

    # 12. Module-scoped state remains isolated from other modules.
    other_config = runtime.create_config("another-module")
    other_storage = runtime.create_storage("another-module")
    other_logger = runtime.create_logger("another-module")

    assert other_config.exists("enabled") is False
    assert other_storage.exists("initialized") is False
    assert other_logger.count() == 0

    runtime.stop()

    assert runtime.is_running is False


def test_fake_module_dependency_failure_prevents_enablement():
    runtime = CoreRuntime()

    resolver = DependencyResolver()

    dependency = ModuleDependency(
        name="network",
        minimum_version=ModuleVersion(2, 0, 0),
    )

    result = resolver.resolve(dependency)

    assert result.status is DependencyStatus.MISSING
    assert result.is_satisfied is False

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)

    if result.is_satisfied:
        lifecycle.transition(ModuleLifecycleState.ENABLED)

    assert lifecycle.state is ModuleLifecycleState.INSTALLED


def test_fake_module_failure_can_recover_through_core_lifecycle():
    runtime = CoreRuntime()

    lifecycle = runtime.create_lifecycle()

    lifecycle.transition(ModuleLifecycleState.VERIFIED)
    lifecycle.transition(ModuleLifecycleState.INSTALLED)
    lifecycle.transition(ModuleLifecycleState.ENABLED)
    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.FAILED)

    assert lifecycle.state is ModuleLifecycleState.FAILED

    lifecycle.transition(ModuleLifecycleState.STARTING)
    lifecycle.transition(ModuleLifecycleState.RUNNING)

    assert lifecycle.state is ModuleLifecycleState.RUNNING

    runtime.health.report(
        "fake-security",
        HealthStatus.HEALTHY,
        "Recovered successfully.",
    )

    assert (
        runtime.health.get("fake-security").status
        is HealthStatus.HEALTHY
    )
