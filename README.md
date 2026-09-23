# Ziggy

**Linux, without the guesswork.**

Ziggy is an open-source Linux system intelligence and control platform designed to make Linux more understandable, manageable, observable, and secure without hiding Linux itself.

> **Ziggy never makes Linux complicated. Ziggy makes Linux understandable.**

## Status

🚧 **Active development — architecture rebuild**

This repository contains the new Ziggy architecture, being built from the ground up with a modular Core designed to support independent Ziggy modules.

The project is intentionally being developed piece by piece rather than as a single large implementation.

## Vision

Linux is powerful, but powerful systems can sometimes be difficult to understand.

Ziggy aims to provide a human-friendly layer over Linux that helps users:

* understand what their system is doing
* investigate what happened
* manage common system operations
* monitor applications and system activity
* improve security
* control network access
* isolate applications
* learn Linux through real usage
* automate repetitive workflows
* investigate security incidents
* extend Ziggy through independently managed modules

Ziggy is not intended to replace Linux.

It is intended to make Linux easier to understand and control.

## Architecture

Ziggy is built around a stable Core.

```text
                         ZIGGY
                           │
                         CORE
                           │
          ┌────────────────┼────────────────┐
          │                │                │
       Security         Network          Sandbox
          │                │                │
       Learning         Sherlock        Device Guardian
          │                │                │
          └────────────────┼────────────────┘
                           │
                     Future Modules
```

The Core provides shared infrastructure and stable APIs.

Modules depend on Core.

Core does not depend on optional modules.

This allows Ziggy to grow without turning the Core into one giant collection of unrelated features.

## Core

The Ziggy Core is responsible for platform-level functionality such as:

* module lifecycle
* module compatibility
* module discovery and management
* permissions and capabilities
* event infrastructure
* configuration
* storage
* logging
* cryptographic services
* policy enforcement
* command registration
* module trust and verification
* shared APIs
* health monitoring
* lifecycle management

The Core is being designed as a stable platform for future Ziggy modules.

## Development Philosophy

Ziggy is being built using a deliberate engineering process:

```text
Design
  ↓
Contract
  ↓
Implement
  ↓
Test
  ↓
Integrate
  ↓
Break
  ↓
Fix
  ↓
Document
  ↓
Commit
```

The goal is not to build Ziggy as quickly as possible.

The goal is to build a Core that is difficult to break, easy for modules to integrate with, and stable enough to support Ziggy for years.

## Current Development

Current Core foundation:

* [x] Core API versioning
* [x] Module manifest
* [x] Compatibility checker
* [x] Module registry
* [ ] Module manager
* [ ] Module lifecycle
* [ ] Permission system
* [ ] Event system
* [ ] Storage API
* [ ] Configuration API
* [ ] Logging API
* [ ] Policy API
* [ ] Crypto API
* [ ] Module verification
* [ ] Module installation system
* [ ] Module health monitoring

More components will be added as the architecture develops.

## Project Structure

```text
ziggy/
├── core/
│   ├── api/
│   ├── modules/
│   └── compatibility/
│
├── tests/
│   └── core/
│
├── CORE_SKILL.md
├── LICENSE
├── README.md
└── .gitignore
```

The structure will evolve as the Core architecture develops.

## Testing

Core components are developed with automated tests.

Run the Core test suite:

```bash
python3 -m pytest tests/core/
```

The project aims to keep the Core continuously testable as new components are introduced.

## Open Source

Ziggy is open source and licensed under the MIT License.

Contributions, ideas, experiments, modules, documentation, testing, and constructive criticism are welcome.

However, inclusion in the official Ziggy ecosystem is subject to review.

**Contribution is appreciated; inclusion is not guaranteed.**

## Author

**Dipak Yadav**
Creator & Developer

Email: `dipak.cybersec@gmail.com`

Ziggy is an independent open-source project created and developed by Dipak Yadav.

## Project Principle

> **Linux, without the guesswork.**

Ziggy exists to make Linux more understandable — not to make users dependent on Ziggy.
