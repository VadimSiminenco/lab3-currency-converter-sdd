# Data Model: Currency Converter

## Overview

The application will handle a small set of core entities: the user conversion request, normalized exchange-rate data, the cached snapshot, and the conversion result shown in the interface.

## Entities

### CurrencyCode

Represents a supported currency identifier.

**Allowed values**:
- MDL
- EUR
- USD
- RON
- GBP
- UAH

**Rules**:
- The value must be one of the supported codes.
- The app must validate both source and target selection before conversion.

### ConversionRequest

Represents the user input for a single conversion attempt.

**Fields**:
- `amount`: positive decimal value greater than zero
- `source_currency`: supported currency code
- `target_currency`: supported currency code
- `rate_date`: optional date; defaults to today if omitted

**Validation rules**:
- `amount` must be present and parse as a decimal value.
- `amount` must be greater than zero.
- `source_currency` and `target_currency` must both be selected.
- `source_currency` and `target_currency` cannot be empty.

### ExchangeRateEntry

Represents one normalized official rate entry for a date.

**Fields**:
- `currency_code`: three-letter code from the BNM feed
- `nominal`: official nominal quantity used by the provider
- `value`: official exchange value from the provider
- `rate_per_unit_mdl`: calculated as `value / nominal`

**Validation rules**:
- `currency_code` must be in the supported set or recognized by the feed.
- `nominal` and `value` must both be valid positive decimals.
- `rate_per_unit_mdl` must be positive.

### RateSnapshot

Represents the latest valid locally persisted exchange-rate snapshot.

**Fields**:
- `snapshot_date`: date corresponding to the official feed data
- `source_name`: official source identifier
- `rates`: map of `currency_code` to `rate_per_unit_mdl`
- `generated_at`: timestamp for record creation or refresh

**Validation rules**:
- Snapshot must contain valid normalized rates for all required currencies in use.
- Snapshot must be saved only after validation.
- Invalid feed content must never replace an existing valid snapshot.

### ConversionResult

Represents the result presented to the user.

**Fields**:
- `converted_amount`: final amount after conversion
- `effective_rate_date`: date actually used for the rate
- `source_name`: provider name shown to the user
- `fallback_used`: boolean flag indicating a prior-date fallback
- `message`: optional user-facing explanatory note

**Validation rules**:
- `converted_amount` must be a valid decimal or string representation.
- `effective_rate_date` must be a date.
- `source_name` must be populated for a successful conversion.

### ValidationError

Represents a user-facing validation or runtime failure condition.

**Fields**:
- `type`: validation, unavailable-rate, network-error, invalid-cache, malformed-feed
- `message`: clear user-facing explanation
- `recoverable`: boolean indicating whether retry or fallback is possible

**Validation rules**:
- Errors must be human-readable and actionable.
- Recoverable errors must guide the user to retry or use cached data when available.

## Relationships

- A `ConversionRequest` is evaluated against one or more `ExchangeRateEntry` records from a `RateSnapshot`.
- A `RateSnapshot` is the persisted source of truth used when the live feed is unavailable or invalid.
- Each successful conversion produces one `ConversionResult`.
- Validation failures produce one or more `ValidationError` objects rather than a conversion result.

## State transitions

### Request validation
1. User provides amount, source, target, and optional date.
2. System validates presence and numeric rules.
3. If invalid, request fails and a validation error is returned.

### Rate retrieval flow
1. Request specified date.
2. Attempt official XML fetch.
3. If valid, parse and normalize rates.
4. If invalid or missing, search prior dates for last valid rate.
5. If no valid live rate, use a valid cached snapshot.
6. If neither exists, return an error state without crashing.

### Conversion outcome
1. If source equals target, return unchanged amount.
2. Otherwise compute `amount * source_rate / target_rate` using decimal arithmetic.
3. Display converted amount and effective rate date with source name.
