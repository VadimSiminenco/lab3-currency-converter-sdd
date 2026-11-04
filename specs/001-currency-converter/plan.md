# Implementation Plan: Currency Converter

**Branch**: `001-currency-converter` | **Date**: 2026-11-04 | **Spec**: /specs/001-currency-converter/spec.md

**Input**: Feature specification from `/specs/001-currency-converter/spec.md`

## Summary

Build a lightweight web-based currency conversion application using Python 3.11+, Streamlit, requests, and Decimal arithmetic. The system will fetch official National Bank of Moldova exchange rates from the XML endpoint, normalize values to MDL-per-unit, validate user input, resolve date gaps by checking prior dates, and fall back to a locally stored JSON snapshot when the remote source is unavailable, invalid, or offline. The design keeps UI, validation, conversion, XML parsing, API access, and cache logic deliberately separated to support testability and maintainability.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Streamlit, requests, xml.etree.ElementTree, Decimal, pytest

**Storage**: Local JSON file for persistent exchange-rate cache; no database server or user auth state required

**Testing**: pytest with fixtures for sample XML, cached snapshots, and offline fallback states

**Target Platform**: Windows desktop browser running a local Streamlit application

**Project Type**: Web application

**Performance Goals**: Typical conversion requests complete in under 1 second for a single user session in normal conditions

**Constraints**: Offline-capable, precise financial calculation with Decimal, clear error handling for invalid XML, invalid input, and missing rates, no payment or authentication workflows

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

## Complexity Tracking

No constitution violations or unresolved design gates were identified. The design remains within the project’s constraints for a simple educational web app and avoids unnecessary complexity.
