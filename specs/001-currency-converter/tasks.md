# Tasks: Currency Converter

**Input**: Design documents from `/specs/001-currency-converter/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Pytest test tasks are included because the feature specification explicitly requires automated validation and network-independent fixtures.

**Organization**: Tasks are grouped by story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the project structure and dependency baseline for a Python 3.11+ Streamlit app.

- [ ] T001 Create the repository structure for `src/`, `tests/`, `tests/unit/`, `tests/fixtures/`, and `docs/` per the plan (completion: directories exist and align with the implementation layout)
- [ ] T002 Initialize the Python 3.11 environment and install `streamlit`, `requests`, and `pytest` with PowerShell setup instructions in `quickstart.md` (completion: dependency installation commands are documented and the environment is ready for local setup)
- [ ] T003 [P] Create the initial package layout for `src/app`, `src/api`, `src/parsing`, `src/domain`, `src/cache`, and `src/config` (completion: the module structure matches the technical design and all folders exist)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define shared contracts, configuration, and base validation logic required before any story-specific work begins.

- [ ] T004 Create shared configuration/constants for supported currencies, source metadata, and cache file path in `src/config/settings.py` (completion: `MDL`, `EUR`, `USD`, `RON`, `GBP`, and `UAH` are defined as valid codes and the cache location is centralized)
- [ ] T005 [P] Define the shared data model for conversion requests, rate snapshots, conversion results, and validation errors in `src/domain/models.py` (completion: all required fields and validation constraints are represented in the model layer)
- [ ] T006 Create the decimal-safe validation helpers for positive amounts and required field checks in `src/domain/validation.py` (completion: empty, zero, negative, alphabetic, and malformed inputs are rejected with clear validation errors)
- [ ] T007 [P] Define the cache JSON contract and persistence helpers in `src/cache/rate_cache.py` (completion: valid snapshots are serialized without overwriting with invalid data and the cache survives a restart boundary in design)
- [ ] T008 Configure the app-level error boundary and user-facing messaging pattern for conversion failures in `src/app/ui/streamlit_app.py` and supporting utilities (completion: failures are surfaced as clear messages without crashing the app)
- [ ] T009 Create a small shared test fixture helper for CSV/XML-like sample inputs in `tests/fixtures/` and `tests/unit/` (completion: fixtures are reusable for parser, caching, and validation test cases without network dependency)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Convert valid amounts with a graphical UI (Priority: P1) 🎯 MVP

**Goal**: Deliver the basic web conversion workflow with a working UI and currency selection for valid user input.

**Independent Test**: A user can open the app, enter a valid amount, choose source and target currencies, and receive a converted result with the effective date and source name.

### Pytest Tests for User Story 1

- [ ] T010 [P] [US1] Add pytest tests for valid conversion input and same-currency behavior in `tests/unit/test_conversion.py` (completion: valid conversions and identical source/target behavior are covered and pass)
- [ ] T011 [P] [US1] Add pytest tests for UI validation rules in `tests/unit/test_validation.py` (completion: empty, zero, negative, alphabetic, and malformed amounts are rejected with explicit error states)

### Application Implementation for User Story 1

- [ ] T012 [P] [US1] Build the Streamlit form and currency selectors in `src/app/ui/streamlit_app.py` (completion: the UI exposes amount, source currency, target currency, date, and Convert controls with default date behavior)
- [ ] T013 [P] [US1] Implement the conversion calculation flow in `src/domain/conversion.py` (completion: conversion uses Decimal arithmetic and returns the unchanged amount when source equals target)
- [ ] T014 [US1] Wire the form state to validation and conversion logic in `src/app/ui/streamlit_app.py` (completion: the Convert button remains disabled until required fields are valid and the result displays converted amount, effective date, and source name)
- [ ] T015 [US1] Add the standard success message and result rendering in `src/app/ui/streamlit_app.py` (completion: successful conversions show value, effective rate date, and official source name without hidden assumptions)

**Checkpoint**: At this point, User Story 1 should be fully functional and independently testable.

---

## Phase 4: User Story 2 - Parse BNM XML and normalize rates (Priority: P1)

**Goal**: Implement the official exchange-rate retrieval and XML parsing flow, including rate normalization and data validation.

**Independent Test**: Given a valid BNM XML sample, the parser returns the expected normalized MDL-per-unit rates and rejects malformed payloads without crashing.

### Pytest Tests for User Story 2

- [ ] T016 [P] [US2] Add pytest parser tests for valid XML payloads in `tests/unit/test_parser.py` (completion: the parser reads `ValCurs`, `Date`, and `Valute` elements and produces normalized rates)
- [ ] T017 [P] [US2] Add pytest tests for invalid XML and missing field handling in `tests/unit/test_parser.py` (completion: malformed XML or missing required elements produce a clear error and do not overwrite cache data)

### Application Implementation for User Story 2

- [ ] T018 [P] [US2] Implement the BNM HTTP request logic in `src/api/bnm_client.py` (completion: the client requests the official XML endpoint with `get_xml=1` and the selected date format `DD.MM.YYYY` and honors timeouts)
- [ ] T019 [P] [US2] Implement XML parsing and rate normalization in `src/parsing/xml_parser.py` (completion: `CharCode`, `Nominal`, and `Value` are parsed, normalized to MDL-per-unit, and malformed payloads fail safely)
- [ ] T020 [US2] Add live rate retrieval orchestration in `src/api/bnm_client.py` and `src/parsing/xml_parser.py` (completion: a valid response yields a usable normalized rate map for the supported currencies, while invalid responses are surfaced as errors)
- [ ] T021 [US2] Add source metadata handling for the official source name and effective date in `src/parsing/xml_parser.py` and `src/domain/models.py` (completion: the result retains the actual official source name and the effective rate date used)

**Checkpoint**: At this point, the app can fetch and parse official BNM data without leaking invalid XML to downstream conversion logic.

---

## Phase 5: User Story 3 - Handle date fallback, offline cache, and failure recovery (Priority: P1)

**Goal**: Provide resilient fallback behavior for unavailable rates, offline operation, and invalid remote data without crashing the app.

**Independent Test**: A user can request a date with no published rate, a weekend/holiday rate gap, or a failed network request and see either a valid fallback rate or a clear safe error message.

### Pytest Tests for User Story 3

- [ ] T022 [P] [US3] Add pytest tests for prior-date fallback and weekend/holiday logic in `tests/unit/test_conversion.py` (completion: the latest valid prior business date is chosen and the user is informed of the fallback)
- [ ] T023 [P] [US3] Add pytest tests for offline cache use and invalid-cache preservation in `tests/unit/test_cache.py` (completion: a valid snapshot is used when the live feed fails and invalid payloads do not replace a valid cache entry)
- [ ] T024 [P] [US3] Add pytest tests for missing-currency and invalid-XML scenarios in `tests/unit/test_parser.py` and `tests/unit/test_conversion.py` (completion: the app reports missing rates clearly and fails without crashing)

### Application Implementation for User Story 3

- [ ] T025 [US3] Implement date fallback search logic across prior calendar dates in `src/domain/conversion.py` or a date-lookup helper (completion: if no rate exists for the selected date, the app searches backward for the closest valid rate and records the fallback date)
- [ ] T026 [US3] Implement missing-currency detection and the clear user-facing error path in `src/domain/conversion.py` and `src/app/ui/streamlit_app.py` (completion: selected currency absence from the effective date results in a clear message and no silent substitution)
- [ ] T027 [US3] Implement the cache-read and cache-write workflow in `src/cache/rate_cache.py` (completion: valid snapshots persist to local JSON and are reused across restarts; invalid payloads are ignored without overwriting a valid cache)
- [ ] T028 [US3] Implement offline and service-failure fallback handling in `src/api/bnm_client.py` and `src/app/ui/streamlit_app.py` (completion: when the service is unavailable or malformed, the app uses the last valid snapshot if present; otherwise it shows a clear, non-crashing error)
- [ ] T029 [US3] Add clear result messaging for fallback dates and offline use in `src/app/ui/streamlit_app.py` (completion: the interface communicates whether a prior-date fallback or cached snapshot was used, with the actual real date shown)

**Checkpoint**: At this point, the feature handles fallback, offline, and invalid data conditions safely and predictably.

---

## Phase 6: User Story 4 - Documentation, polish, and release readiness (Priority: P2)

**Goal**: Finalize the user-facing documentation, validation guide, and supporting artifacts needed for review and maintenance.

**Independent Test**: Reviewers can follow the project guidance and validate the happy path, fallback path, and offline path without implementation-level ambiguity.

### Pytest Tests for User Story 4

- [ ] T030 [P] [US4] Add a small integration-style pytest flow covering conversion, fallback, and cache persistence in `tests/integration/test_conversion_flow.py` (completion: the end-to-end fixture path validates the main scenarios without live network access)

### Application Implementation for User Story 4

- [ ] T031 [P] [US4] Update `quickstart.md` with setup and validation steps for Windows PowerShell and local test execution (completion: the document includes prerequisites, installation commands, and validation scenarios)
- [ ] T032 [P] [US4] Review and align `research.md`, `data-model.md`, `contracts/official-rate-feed.md`, and `spec.md` with the implementation plan (completion: all artifacts agree on currency codes, rate normalization, and fallback rules)
- [ ] T033 [US4] Document the supported error states and recovery paths in the project docs or README (completion: the user can understand recovery flows and no hidden assumptions remain)

**Checkpoint**: The project is ready for review, with clear documentation and validation coverage for all critical user stories.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup across implementation and test surfaces.

- [ ] T034 [P] Review and refactor shared validation and conversion paths to remove duplication across the app and test layers (completion: common logic is centralized without changing requirement semantics)
- [ ] T035 [P] Run the focused pytest suite for conversion, parser, validation, cache, and integration tests (completion: key unit and integration tests pass with no live network dependency)
- [ ] T036 [P] Validate the end-to-end quickstart flow from `quickstart.md` against the design requirements (completion: the documented steps cover successful conversion, invalid input, fallback, and offline cache behavior)
- [ ] T037 Review Git branch and PR readiness for separate application implementation and pytest workstreams (completion: the app work and test work are clearly separable for different review tracks)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - blocks all user stories
- **User Stories (Phase 3+)**: Depend on the Foundational phase completion
  - User Story 1 (P1) can begin after Phase 2
  - User Story 2 (P1) can begin after Phase 2 and may run in parallel with US1
  - User Story 3 (P1) can begin after Phase 2 and may run in parallel with US1/US2
  - User Story 4 (P2) can begin after Phase 2 and may run in parallel once core functionality is stable
- **Polish (Final Phase)**: Depends on all story work being complete

### User Story Dependencies

- **User Story 1**: No dependency on other stories; MVP path
- **User Story 2**: Depends on shared configuration and model definitions; should be independently testable
- **User Story 3**: Depends on rate parsing and validation logic; must be testable without web access
- **User Story 4**: Depends on the validated features and documentation set; ensures release readiness

### Parallel Opportunities

- T001/T002/T003 can run in parallel
- T004/T005/T006/T007/T009 can run in parallel after setup
- US1 tests and US1 app tasks can run in parallel once the foundation is ready
- US2 tests and US2 app tasks can run in parallel once the parser and API contracts are defined
- US3 tests and US3 app tasks can run in parallel once conversion and cache logic are in place
- Final polish tasks can be run in parallel across docs and test validation once all stories are complete

---

## Parallel Example: Story Workstreams

```bash
# Application implementation workstream
Task: "Build the Streamlit form and currency selectors in src/app/ui/streamlit_app.py"
Task: "Implement the data model and validation helpers in src/domain/"
Task: "Implement BNM XML parsing and rate normalization in src/parsing/xml_parser.py"
Task: "Implement persistent cache handling in src/cache/rate_cache.py"

# Pytest test workstream
Task: "Add pytest conversion tests in tests/unit/test_conversion.py"
Task: "Add pytest parser tests in tests/unit/test_parser.py"
Task: "Add pytest cache tests in tests/unit/test_cache.py"
Task: "Add end-to-end integration tests in tests/integration/test_conversion_flow.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete User Story 1 tasks
4. Validate the happy path and invalid input flow
5. Stop and confirm the MVP is stable before adding date fallback and network resilience

### Incremental Delivery

1. Phase 1 + Phase 2: Foundation ready
2. User Story 1: Valid conversion flow
3. User Story 2: Official BNM parsing and normalization
4. User Story 3: Fallback, cache, and error resilience
5. User Story 4: Documentation and final quality review

### Parallel Team Strategy

With separate implementation teams:

1. Team A handles application implementation tasks in `src/`
2. Team B handles pytest tasks under `tests/`
3. Each workstream is reviewable independently via separate Git branches and pull requests without mixing source code changes and tests

---

## Notes

- [P] tasks indicate different files and no dependency blocking
- Story labels map each task to a specific user story for traceability
- Each task includes a completion criterion to reduce ambiguity before implementation begins
- The `src/` implementation work and `tests/` work are intentionally separated in task design for independent branches and pull requests
- Do not start implementation until all prerequisites and task dependencies are complete
