# Implementation Plan: Currency Converter

**Branch**: `001-currency-converter` | **Date**: 2026-11-04 | **Spec**: /specs/001-currency-converter/spec.md

**Input**: Feature specification from `/specs/001-currency-converter/spec.md`

## Summary

Build a lightweight web-based currency conversion application using Python 3.11+, Streamlit, requests, and Decimal arithmetic. The system will fetch official National Bank of Moldova exchange rates from the XML endpoint, normalize values to MDL-per-unit, validate user input, resolve date gaps by checking prior dates, and fall back to a locally stored JSON snapshot when the remote source is unavailable, invalid, or offline. A focused rate-provider protocol separates conversion logic from the BNM provider and HTTP implementation, allowing interchangeable providers without unnecessary framework or abstraction layers. UI, validation, conversion, XML parsing, API access, and cache logic remain distinct responsibilities.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Streamlit, requests, xml.etree.ElementTree, Decimal

**Testing Dependencies**: pytest, Selenium WebDriver

**Storage**: Local JSON file for persistent exchange-rate cache; no database server or user auth state required

**Testing**: pytest unit tests with fixtures for sample XML, cached snapshots, and offline fallback states; separate Selenium WebDriver E2E tests using headless Chrome, explicit waits, and deterministic fixture-backed or stubbed rates

**Target Platform**: Windows desktop and smaller-screen browsers running a local Streamlit application; Chrome is preferred for headless E2E testing

**Project Type**: Web application

**Performance Goals**: Typical conversion requests complete in under 1 second for a single user session in normal conditions

**Constraints**: Offline-capable, precise financial calculation with Decimal, clear error handling for invalid XML, invalid input, and missing rates, responsive consistent light UI, no payment or authentication workflows; Selenium E2E tests are implemented on the `testing` branch and must not depend on the live rate service

**Scale/Scope**: Single-user educational web app with six supported currencies and date-based rate lookup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Specification-First Delivery**: Pass. The feature is driven by an approved specification and a clarified acceptance set.
- **Review Before Implementation**: Pass. Design and validation decisions are recorded before implementation work begins.
- **Simple, Maintainable Architecture**: Pass. The intended layout separates UI, API client, parsing, validation, conversion, and caching responsibilities.
- **Financial Correctness and Data Integrity**: Pass. The plan uses official exchange-rate data, Decimal arithmetic, and explicit validation for malformed or missing inputs.
- **Reliability, Offline Resilience, and Quality**: Pass. The design includes cache persistence, fallback to prior dates, and testable failure scenarios using fixtures instead of network dependencies.

## Project Structure

### Documentation (this feature)

```text
specs/001-currency-converter/
├── plan.md              # This file
├── research.md          # Phase 0 research output
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 validation guide
├── contracts/           # Phase 1 contracts
├── spec.md              # Approved feature specification
├── checklists/
│   └── requirements.md  # Quality checklist
└── tasks.md             # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── app/
│   └── ui/
│       └── streamlit_app.py
├── api/
│   └── bnm_client.py
├── parsing/
│   └── xml_parser.py
├── domain/
│   ├── validation.py
│   ├── conversion.py
│   └── models.py
├── cache/
│   └── rate_cache.py
└── config/
    └── settings.py

tests/
├── unit/
│   ├── test_validation.py
│   ├── test_conversion.py
│   ├── test_parser.py
│   └── test_cache.py
├── fixtures/
│   ├── valid_rate_feed.xml
│   ├── invalid_rate_feed.xml
│   └── cached_snapshot.json
└── integration/
    └── test_conversion_flow.py
```

**Structure Decision**: Use a single Python project with a small modular layout. UI, API access, XML parsing, validation, conversion logic, and cache management are separated into distinct folders so each module can be tested independently without coupling to the interface.

## Architecture Boundaries

- The Streamlit UI owns presentation and interaction only; validation and conversion rules remain outside UI code.
- Conversion orchestration depends on a focused `RateProvider` protocol in `src/domain/ports.py`, not on `requests` or a concrete HTTP client.
- `src/api/bnm_provider.py` implements the provider contract, delegates HTTP access to `src/api/bnm_client.py`, and uses the separate XML parser. A conforming alternate provider can replace it without changing conversion logic.
- Provider implementations must be substitutable through the same provider contract. Keep contracts narrow and introduce no provider registry or generalized plugin system unless a demonstrated requirement needs one.
- Keep cache persistence in its own module; do not combine it with XML parsing, HTTP access, conversion, or UI rendering.

## UI and Browser Test Requirements

Use Streamlit's supported layout and controls to provide the consistent light visual design, readable typography, rounded controls, prominent result, clear error/offline states, and desktop/small-screen usability required by the spec. Keep unit tests in `tests/unit/` and Selenium browser tests in `tests/e2e/`. E2E tests run with pytest, prefer headless Chrome and explicit waits, use deterministic fixture-backed or stubbed rates, and are implemented on the `testing` branch. README must document the unit, E2E, and full-suite commands.

## Complexity Tracking

No constitution violations or unresolved design gates were identified. The design remains within the project’s constraints for a simple educational web app and avoids unnecessary complexity.
