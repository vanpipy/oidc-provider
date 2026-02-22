<!--
Sync Impact Report
Version change: none → 1.0.0
Modified principles:
- Initial constitution created (no previous titles)
Added sections:
- Core Principles
- Architecture and Technology Constraints
- Development Workflow and Quality Gates
Templates requiring updates:
- .specify/templates/plan-template.md: ✅ aligned
- .specify/templates/spec-template.md: ✅ aligned
- .specify/templates/tasks-template.md: ✅ updated (tests required for all core behavior)
- .specify/templates/commands/*.md: ⚠ not present in this repo
Follow-up TODOs:
- None
-->

# OIDC Identity Provider Constitution

## Core Principles

### I. Low Coupling via Clear Boundaries

- The system is organized into explicit layers and modules (interface, application,
  domain, infrastructure) with well-defined responsibilities.
- Dependencies always point inward: outer layers can depend on inner layers only
  through stable interfaces or protocols, never the other way around.
- Frameworks and infrastructure (FastAPI, SQLAlchemy, Authlib, database, caches)
  are hidden behind clear abstractions so they can be replaced without rewriting
  domain logic.
- Cross-module access, hidden globals, and implicit shared state are not allowed.
- Public contracts between modules change only with deliberate review and clear
  migration plans.

Rationale: Loose coupling makes the OIDC provider easier to evolve, test, and
operate while reducing the blast radius of changes to frameworks, storage, or
deployment environments.

### II. High Cohesion Around OIDC Flows

- Code is grouped by OIDC/OAuth2 responsibilities (e.g., authorization endpoint,
  token issuance, userinfo, client management) rather than by technical layer only.
- Each module encapsulates closely related data, behavior, and rules so that a
  single feature can be understood and modified locally.
- Domain concepts (Client, User, Token, AuthorizationCode, etc.) include their
  own invariants and validation logic instead of scattering rules across services
  and controllers.
- New features must integrate into the existing domain model and OIDC flows
  instead of introducing ad hoc paths or "one-off" endpoints.

Rationale: High cohesion keeps OIDC behavior understandable, reduces duplication,
and localizes change so that features can be implemented and tested independently.

### III. Strict Automated Testing and Coverage (NON-NEGOTIABLE)

- Every piece of non-trivial behavior must have automated tests, with a strong
  focus on unit tests for domain and application logic.
- Tests MUST be written before or alongside implementation and MUST fail at least
  once before the implementation is considered complete.
- Core domain and application modules MUST maintain high coverage; as a baseline,
  new or changed domain logic requires full branch coverage for normal and error
  paths.
- Regressions must be reproduced with a failing test before fixes are merged.
- CI pipelines MUST run the full test suite on every change; merges are blocked
  on failures.

Rationale: The OIDC provider is security-sensitive infrastructure. Strict and
comprehensive testing is required to prevent regressions, ensure spec compliance,
and enable safe refactoring.

### IV. Security, Compliance, and Privacy by Design

- Behavior MUST comply with relevant OpenID Connect and OAuth 2.0 specifications
  for the supported flows.
- Sensitive data (passwords, client secrets, tokens, keys) is never logged and
  is always handled using secure, modern cryptographic practices.
- Defaults are secure by design: least privilege, minimal scopes, and strict
  validation of redirect URIs, audiences, and token lifetimes.
- All changes that affect authentication, authorization, cryptography, or data
  protection MUST include explicit threat and misuse considerations in design
  and tests.

Rationale: As an identity provider, any weakness directly impacts user security
and relying parties. Security is treated as a primary feature, not an afterthought.

### V. Observability and Operational Simplicity

- The system emits structured logs and metrics for key OIDC interactions
  (authorization, token issuance, token failure, userinfo) without leaking
  secrets or personal data.
- Error responses are standards-compliant and informative for clients while
  avoiding internal implementation details.
- Operational tasks (deployment, migrations, configuration) are automated and
  repeatable; manual steps are documented and minimized.
- Designs favor the simplest solution that satisfies the requirements and core
  principles, avoiding unnecessary abstraction or over-engineering.

Rationale: Clear observability and simple operations make it possible to detect
and diagnose issues quickly while keeping the provider maintainable over time.

## Architecture and Technology Constraints

- The service is implemented in Python 3.10+ using FastAPI, SQLAlchemy,
  Pydantic, Authlib, and related libraries as the primary stack.
- The API layer focuses on HTTP protocol concerns and delegates business rules
  to application and domain services.
- Persistence concerns are isolated behind repository patterns or equivalent
  abstractions; domain logic does not depend on specific database technology.
- Time, configuration, and external integrations are abstracted so that behavior
  can be reliably unit-tested without real network or system dependencies.
- All public HTTP contracts (routes, request/response schemas, error formats)
  are treated as stable external interfaces and updated with care.

## Development Workflow and Quality Gates

- Work proceeds in small, independently testable slices corresponding to user
  journeys and OIDC use cases.
- Each change MUST:
  - Include or update automated tests.
  - Keep module boundaries clear and consistent with the core principles.
  - Avoid introducing hidden coupling or duplicating domain rules.
- Code review MUST check:
  - Adherence to low-coupling and high-cohesion principles.
  - Adequate unit test coverage and meaningful assertions.
  - Security implications for authentication, authorization, and data handling.
- CI MUST run linting, type checks (where configured), and the full test suite;
  failures block merging.
- Feature branches are only considered complete when they can be demonstrated
  via tests and, where applicable, through OIDC-compliant flows end to end.

## Governance

- This constitution is the authoritative reference for architectural and process
  decisions for the OIDC Identity Provider.
- Amendments to principles or governance require:
  - A clear description of the change and its rationale.
  - An assessment of impact on existing code, tests, and external contracts.
  - A version bump according to semantic versioning:
    - MAJOR for breaking governance changes or removal/redefinition of principles.
    - MINOR for new or significantly expanded principles or sections.
    - PATCH for clarifications and non-semantic refinements.
- All feature plans, specifications, and task lists must be checked against this
  constitution; deviations must be explicitly justified and, if recurring, lead
  to a proposed amendment.

**Version**: 1.0.0 | **Ratified**: 2026-02-22 | **Last Amended**: 2026-02-22
