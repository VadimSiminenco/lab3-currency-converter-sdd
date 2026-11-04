# Research: Currency Converter

## Decision: Official data source and rate normalization

**Decision**: Use the official National Bank of Moldova XML feed at https://www.bnm.md/en/official_exchange_rates with query parameters `get_xml=1` and `date=DD.MM.YYYY`.

**Rationale**: The requirement explicitly names the official source and requires use of `ValCurs Date` and `Valute` elements, including `CharCode`, `Nominal`, and `Value`. This is the authoritative source for all currency conversion logic.

**Alternatives considered**:
- Use a third-party API or a static local rate table.
- Ignore the designated date and always fetch the latest available rate.

**Why rejected**: Both alternatives conflict with the requirement to use the official NBM feed and to honor selected or fallback dates transparently.

## Decision: Rate normalization model

**Decision**: Normalize each currency to MDL per one unit using `Value / Nominal`, and treat MDL as `1`.

**Rationale**: This ensures coherent cross-currency math regardless of source or target currencies and makes identical-currency conversions predictable.

**Alternatives considered**:
- Store raw `Value` directly without dividing by `Nominal`.
- Use floating-point math for conversion.

**Why rejected**: Raw values would be inaccurate when the official feed uses a nominal factor, and floating-point arithmetic is incompatible with the precision and financial correctness requirement.

## Decision: Fallback and availability logic

**Decision**: When no rate exists for a requested date, the system must check prior calendar dates in descending order until a valid daily rate is found. If the feed is unavailable or malformed, use the latest valid cached snapshot only if it exists; otherwise show a clear user-facing error.

**Rationale**: This matches the business requirement for transparency, offline resilience, and user confidence in the rate date actually applied.

**Alternatives considered**:
- Automatically use the latest available rate without a warning.
- Fail outright on the first missing day without checking prior dates.

**Why rejected**: Both choices would reduce trust and violate the requirement to use the latest prior valid rate when available and to inform the user of the fallback date.

## Decision: Cache format and persistence

**Decision**: Store the most recent valid snapshot in a local JSON file that persists across application restarts and records the snapshot date, source name, and normalized rates keyed by currency code.

**Rationale**: This supports offline operation, survivability across restarts, and easy validation without a database server.

**Alternatives considered**:
- In-memory-only state.
- SQLite or another database service.

**Why rejected**: In-memory state fails the restart requirement, and a database server is explicitly out of scope.

## Decision: Validation and failure handling

**Decision**: Validate input before conversion and reject blank, zero, negative, alphabetic, and malformed amounts with explicit error messaging. Network failures, empty XML, missing fields, and invalid `Valute` entries must not overwrite the valid cache and must not crash the UI.

**Rationale**: These are explicit acceptance criteria and security/safety expectations for a financial conversion tool.

**Alternatives considered**:
- Allow partial or coerced values to be converted.
- Overwrite cache even when response data is invalid.

**Why rejected**: Both would create silent data corruption and violate the requirement to prevent invalid data from overwriting the cache.

## Decision: Testing strategy

**Decision**: Use pytest and define fixtures that provide sample XML payloads, cached snapshots, and offline scenarios without external network dependency.

**Rationale**: This keeps the unit tests deterministic and aligned with the requirement to avoid network-dependent tests.

**Alternatives considered**:
- Direct live-network tests in CI.
- No dedicated fixtures for parser and cache validation.

**Why rejected**: Live-network tests are unreliable and contradict the requirement for offline-safe, deterministic validation.

## Open questions resolved

- Weekend and holiday behavior: use the latest previous valid business date.
- Missing currencies: show a clear unavailable message instead of silently substituting another rate.
- Malformed XML: reject invalid feed and fall back to cache if present.
- Input rules: accept only positive decimal amounts greater than zero.
- Cache persistence: local JSON file remains available after restart.
