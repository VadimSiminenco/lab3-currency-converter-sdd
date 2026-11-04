# Educational Currency Converter Constitution

<!--
Sync Impact Report
Version change: 0.0.0 -> 1.0.0
Modified principles: N/A -> I. Specification-First Delivery, N/A -> II. Review Before Implementation, N/A -> III. Simple, Maintainable Architecture, N/A -> IV. Financial Correctness and Data Integrity, N/A -> V. Reliability, Offline Resilience, and Quality
Added sections: Additional Constraints, Development Workflow
Removed sections: none
Follow-up TODOs: none
-->

## Core Principles

### I. Specification-First Delivery
All work on the educational currency converter begins with a reviewed, approved specification. Product requirements, acceptance criteria, edge cases, and failure modes MUST be captured before any implementation begins. The specification is the source of truth for scope, and no feature may be implemented, refactored, or merged without traceable alignment to it.

### II. Review Before Implementation
No code, screen mockup, or integration change may be accepted unless it has passed review against the specification, technical constraints, and this constitution. Review is mandatory for architecture choices, risk areas, and validation strategy. Implementation MUST stop when requirements are unclear and must resume only after explicit clarification.

### III. Simple, Maintainable Architecture
The application MUST favor a straightforward architecture with clear separation of concerns: UI concerns, business logic, and data access are distinct and independently understandable. Reuse common patterns only when they reduce complexity; unnecessary abstraction, hidden coupling, and duplicate logic are forbidden. Prefer maintainable code over cleverness.

### IV. Financial Correctness and Data Integrity
All currency conversions MUST use official exchange-rate data from a trusted provider and treat monetary values as precise decimal quantities rather than binary floating-point approximations. Input validation MUST reject missing, malformed, or out-of-range values. Network and API failures MUST be surfaced clearly, and malformed responses MUST be handled without crashing the app.

### V. Reliability, Offline Resilience, and Quality
The solution MUST provide graceful error handling for network failures, timeouts, empty responses, and invalid payloads. It MUST support persistent offline caching of exchange-rate data to preserve functionality when connectivity is limited. Automated unit tests MUST exist for conversion logic, validation rules, and failure scenarios. Any test that exercises network or parsing behavior MUST verify both success and failure paths.

## Additional Constraints
The application is an educational web project intended to demonstrate Spec-Driven Development and disciplined engineering. All implementation work for this project must be assigned to Google Antigravity as the executing team; GitHub Copilot is not the implementation owner for this build. Source code must not be created in this session, and any coding work must occur only in the appropriate implementation workflow after this constitution is approved.

The application MUST avoid hidden business rules, undocumented assumptions, and dependency on ad-hoc data sources. Data access is limited to validated currency-rate feeds and local cache storage. The project MUST preserve clear auditability through meaningful commit messages and pull requests that explain intent, rationale, and verification.

## Development Workflow
The project MUST follow a disciplined workflow: specification review, task planning, implementation, validation, and final review. Each change MUST be related to a specific requirement or defect. Implementation decisions MUST be justified in terms of maintainability, correctness, and testability. Pull requests MUST be meaningful, focused, and accompanied by evidence that relevant tests pass. Commit history MUST communicate intent clearly and remain reviewable by future contributors.

## Governance
This constitution supersedes informal practices that conflict with it. Amendments require a documented rationale, a version bump, and a review of the changed principles and workflow constraints. Any material change to the architecture, validation model, or data-handling rules MUST be reviewed before adoption.

All contributors and reviewers MUST verify compliance with the specification and this constitution before accepting work. Non-compliance is a defect in process and must be corrected before merge. When the project evolves, this document MUST be amended in a way that preserves the original intent of the educational, reliable, and maintainable design.

**Version**: 1.0.0 | **Ratified**: 2026-11-04 | **Last Amended**: 2026-11-04
