# Contract: Official BNM Rate Feed

## Purpose

This document defines the external data contract consumed by the currency converter for live exchange-rate data and the local fallback snapshot used when the live feed is unavailable.

## Live feed endpoint

**Endpoint**: https://www.bnm.md/en/official_exchange_rates

**Required query parameters**:
- `get_xml=1`
- `date=DD.MM.YYYY`

**Expected response**:
- `Content-Type`: XML
- Root element: `ValCurs`
- `Date` element contains the published official date
- `Valute` child elements each contain currency-specific metadata

## XML contract

### Root

- `ValCurs`
  - child: `Date`
  - child: `Valute` repeated elements

### Valute element

Each `Valute` element must include:
- `CharCode`: three-letter currency code
- `Nominal`: integer or numeric multiplier used by the provider
- `Value`: official value in MDL for the nominal quantity

### Normalization rule

For each valid `Valute` item:
- `normalized_rate = Value / Nominal`
- For MDL, the normalized rate is treated as `1`
- Cross-currency conversion: `amount * source_rate / target_rate`

## Failure conditions

The live feed is considered invalid when any of the following occurs:
- HTTP request fails or times out
- Response body is empty
- XML cannot be parsed
- Required elements are missing or malformed
- `Value` or `Nominal` are not valid positive decimals

When such conditions occur, the app must not overwrite a valid existing cache and must show a clear error or use the last valid snapshot if available.

## Local cache contract

The persisted cache is a JSON object with the following shape:

```json
{
  "snapshot_date": "2026-11-04",
  "source_name": "National Bank of Moldova",
  "rates": {
    "MDL": 1,
    "EUR": 22.345,
    "USD": 18.96,
    "RON": 4.82,
    "GBP": 26.15,
    "UAH": 0.67
  },
  "generated_at": "2026-11-04T12:00:00Z"
}
```

**Rules**:
- The cache must remain valid only when all required rate entries are present and parse successfully.
- Invalid or partial snapshots must not be stored.
- The most recent valid snapshot must be retained across application restarts.

## UI contract

The interface must display:
- entered amount
- source currency
- target currency
- selected or default date
- converted amount
- effective rate date used
- source name
- clear validation or fallback messages when needed

The Convert action must remain disabled until required inputs are valid and complete.
