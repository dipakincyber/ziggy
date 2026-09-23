# Ziggy Core — Engineering Constitution

## 1. Purpose

Ziggy Core is the stable platform that powers the entire Ziggy ecosystem.

Core is responsible for providing:

- module lifecycle management
- module compatibility
- module discovery and installation
- permissions and capabilities
- event communication
- configuration
- storage
- logging
- cryptographic services
- policy enforcement
- command registration
- module health monitoring
- security and trust verification
- shared APIs
- Core lifecycle management

Core is NOT responsible for implementing the functionality of every Ziggy module.

Core provides the infrastructure that modules use.

---

# 2. Fundamental Principle

> Ziggy Core must be stable enough to support the entire Ziggy ecosystem without requiring Core to understand the internal implementation of individual modules.

Modules depend on Core.

Core does not depend on module-specific implementation.

---

# 3. Module Independence

Every module must be independently implementable, testable, enableable, disableable, updateable, and removable.

A failure in one module must not crash Core or unrelated modules.

Example:

    Sherlock crashes
        ↓
    Core detects failure
        ↓
    Sherlock becomes unhealthy
        ↓
    Core continues running
        ↓
    Network continues running
        ↓
    Security continues running

---

# 4. Public API Boundary

Modules MUST communicate with Core through documented public APIs.

Modules MUST NOT depend directly on Core's internal implementation.

Internal Core code may change without requiring modules to change, provided the public API contract remains compatible.

Public APIs include:

- Module API
- Event API
- Storage API
- Configuration API
- Logging API
- Permission API
- Policy API
- Crypto API
- Registry API
- Export API
- Lifecycle API

---

# 5. API Versioning

Every Core API has a version.

Core must support backwards compatibility where reasonably possible.

Breaking API changes require:

1. a new API version
2. a documented migration path
3. a deprecation period where practical
4. compatibility tests
5. documentation

A module must never silently break because an internal Core implementation changed.

---

# 6. Module Contract

Every module must provide a machine-readable manifest.

The manifest must define at minimum:

- module name
- module version
- API version
- author
- description
- minimum Core version
- dependencies
- capabilities
- permissions
- commands
- events
- configuration requirements
- lifecycle requirements

Core must validate the manifest before loading the module.

---

# 7. Compatibility Checking

Before a module is loaded, Core must verify:

- module format
- Core API compatibility
- module API compatibility
- dependency availability
- dependency compatibility
- operating-system requirements
- required capabilities
- requested permissions
- trust state
- signature/hash where applicable
- configuration compatibility

If validation fails, the module must not load.

Core must provide a clear explanation of the failure.

Example:

    Module cannot be loaded.

    Module: security
    Required Core API: 2
    Available Core API: 1

    Reason:
    This module requires a newer Core API.

    No changes were made.

---

# 8. No Silent Failure

Core must never silently ignore:

- module loading failures
- compatibility failures
- dependency failures
- permission failures
- security verification failures
- configuration failures
- lifecycle failures

Failures must produce structured diagnostic information.

---

# 9. Module Isolation

Core must isolate module failures wherever technically possible.

A module must not be able to:

- crash the entire Core runtime
- corrupt unrelated module state
- bypass Core permission controls
- modify another module's private state without permission
- silently change Core configuration
- register conflicting commands without detection

---

# 10. Permissions

Modules must explicitly declare the capabilities they require.

Examples:

    filesystem.read
    filesystem.write
    process.inspect
    process.control
    network.read
    network.control
    device.read
    device.control
    privileged.execute

Core decides whether those capabilities are permitted.

Modules must never receive unrestricted system access simply because they are installed.

---

# 11. Least Privilege

Ziggy must operate with the minimum privileges required for an operation.

Core must not require the entire Ziggy process to run as root.

Privileged operations should request privilege only when required.

Core must never store a user's sudo password.

---

# 12. Security Boundary

Cryptographic security must use established, well-reviewed primitives and libraries.

Ziggy must never implement cryptographic algorithms from scratch unless there is an exceptional, documented reason.

Security mechanisms must not depend on secrecy of Ziggy's implementation.

---

# 13. Event System

Core provides a common event system.

Modules may:

- publish events
- subscribe to permitted events
- inspect event metadata according to permissions

Events must have stable schemas.

Example:

    process.started
    process.stopped
    file.created
    file.modified
    network.connection
    device.connected
    module.loaded
    module.failed

Event schemas must be versioned when necessary.

---

# 14. Storage

Core provides a controlled storage interface.

Modules must not directly depend on Core's database implementation.

A module should request storage through the Storage API.

Example:

    module → Storage API → storage backend

This allows the backend to change without requiring every module to be rewritten.

---

# 15. Configuration

Core provides configuration management.

Configuration must be:

- structured
- validated
- versioned where necessary
- permission-aware
- recoverable where practical

Modules own their module-specific configuration.

Core owns Core configuration.

---

# 16. Logging

Core provides structured logging.

Logs should include:

- timestamp
- component
- severity
- event/message
- relevant identifiers
- module identity where applicable

Modules must not bypass Core logging for important operational events.

---

# 17. Lifecycle

Modules have explicit lifecycle states.

Possible states:

    discovered
    verified
    installed
    disabled
    enabled
    starting
    running
    stopping
    stopped
    unhealthy
    failed
    removed

Illegal state transitions must be rejected.

---

# 18. Health Monitoring

Core must be able to determine whether a module is functioning.

Health checks must not falsely report a module as healthy merely because its process exists.

Where applicable, health should verify:

- API communication
- required services
- dependencies
- internal module status

---

# 19. Crash Recovery

If a module crashes:

1. Core detects the failure.
2. Core records the failure.
3. Core determines whether recovery is safe.
4. Core may restart the module when configured.
5. Repeated failures trigger protection against restart loops.
6. The module may be disabled automatically when necessary.
7. Core remains operational.

---

# 20. Command Registration

Modules may register commands through the Core Command API.

Commands must include:

- command name
- description
- arguments
- options
- required permissions
- owning module
- API version

Command conflicts must be detected before registration.

A module must not silently replace another module's command.

---

# 21. Natural Language Layer

Natural-language interaction is NOT the source of truth.

The architecture must remain:

    User
      ↓
    Language / Intent Layer
      ↓
    Command / Intent
      ↓
    Module
      ↓
    Core APIs
      ↓
    Linux

If the natural-language layer is removed, explicit Ziggy commands must continue working.

---

# 22. Registry and Module Trust

Core must support module verification.

Verification may include:

- module identity
- signed releases
- cryptographic hashes
- compatibility information
- dependency verification
- revocation status

Integrity verification does not automatically mean that software is safe.

Trust decisions must therefore be represented separately from simple hash matching.

---

# 23. External Modules

Third-party modules must be clearly identified.

Core must distinguish between:

- Ziggy Official
- Ziggy Verified
- External / Unaffiliated

External modules must never silently receive official Ziggy trust status.

---

# 24. No Hidden Functionality

Core must never claim that a capability exists when the implementation does not exist.

Documentation, CLI output, and UI must reflect actual implementation state.

---

# 25. Data Ownership

Modules must have clearly defined ownership of their data.

Removing a module must not unexpectedly destroy Core data or unrelated module data.

If removal deletes module data, the user must be informed.

---

# 26. Backwards Compatibility

When possible:

    Existing module
          ↓
    Older API
          ↓
    Compatibility layer
          ↓
    New Core

Core upgrades should not unnecessarily force simultaneous upgrades of the entire Ziggy ecosystem.

---

# 27. Testing Requirement

Every Core subsystem must have tests.

Core releases must test:

- module loading
- module unloading
- compatibility
- dependency resolution
- permissions
- command registration
- event delivery
- storage
- configuration
- logging
- crash handling
- API compatibility
- security boundaries

---

# 28. Failure Testing

Core must intentionally test failure conditions.

Test modules should include:

- compatible module
- incompatible module
- missing dependency
- invalid manifest
- invalid permission
- crashing module
- repeatedly crashing module
- slow module
- malformed event
- conflicting command
- invalid configuration

Core must remain operational during module failures.

---

# 29. Core Must Remain Small

Core must not become a collection of every Ziggy feature.

If functionality belongs to a module, it belongs in a module.

Core provides infrastructure.

Modules provide specialized functionality.

---

# 30. No Circular Architecture

The dependency direction must remain:

    Module
       ↓
    Core API
       ↓
    Core implementation

Never:

    Core
       ↓
    Security module
       ↓
    Core

Core must not require optional modules to function.

---

# 31. Optional Modules

Core is the mandatory foundation.

Other Ziggy modules are optional unless explicitly designated otherwise.

Disabled modules must not unnecessarily consume background resources.

---

# 32. Compatibility Is a Release Requirement

A Core release is not complete merely because Core itself works.

A Core release must also demonstrate that supported modules can continue communicating with the new Core version.

The ecosystem is part of the Core test surface.

---

# 33. Architecture Principle

Ziggy Core follows the petrol-pump principle:

The pump provides a stable interface.

Different vehicles can use the pump without the pump knowing how every vehicle is built.

Likewise:

    Core
      ↓
    stable interfaces
      ↓
    Network
    Security
    Sandbox
    Sherlock
    Learning
    Device Guardian
    Isolate
    Vault
    Forensics
    etc.

Core provides the interfaces.

Modules provide the specialized functionality.

---

# 34. Core Development Rule

Never implement a Core feature simply because a current module needs it.

First determine whether the capability is:

1. genuinely shared infrastructure,
2. a stable public API,
3. useful to multiple modules,
4. safe to expose,
5. maintainable long-term.

If it is module-specific, keep it inside the module.

---

# 35. Change Discipline

Every Core change must answer:

- What contract does this change introduce or modify?
- Which modules depend on it?
- Does it break an existing API?
- What compatibility mechanism is required?
- What tests protect it?
- What happens when it fails?
- Can the change be reverted safely?

---

# 36. Final Core Principle

> Ziggy Core must be difficult to break, easy for modules to integrate with, and stable enough that the Ziggy ecosystem can grow around it for years.

Core is the foundation.

Modules are the ecosystem.

The foundation must not depend on the ecosystem to exist.
