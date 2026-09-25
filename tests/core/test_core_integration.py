import pytest

from core.api import get_core_api_version
from core.modules.manager import ModuleManager, ModuleRegistrationError
from core.modules.manifest import ModuleCompatibility, ModuleManifest
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
