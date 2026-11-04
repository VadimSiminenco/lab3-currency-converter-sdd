# Feature Specification: Currency Converter

**Feature Branch**: `001-currency-converter`

**Created**: 2026-11-04

**Status**: Draft

**Input**: User description: "Build a web-based currency converter with a graphical user interface. The exchange-rate source is the official National Bank of Moldova XML service. The application must support MDL, EUR, USD, RON, GBP and UAH. Users can enter an amount, select source and target currencies, optionally choose a rate date (default today), and click Convert. The interface must display the converted amount, the effective exchange-rate date and the source name. The Convert button must remain disabled until required fields are filled. Zero, negative, empty, alphabetic and malformed amounts must be rejected with clear messages. Identical source and target currencies must return the unchanged amount. When no rate exists for the requested date, find the latest available prior rate and inform the user. When offline or the service fails, use the last valid locally saved exchange-rate snapshot if available and show its real date; otherwise show a clear error without crashing. The cache must survive application restart. Include clear acceptance scenarios for all edge cases, including both conversion directions. No registration, login, database server or payment processing. Generate specification artifacts only; do not write application code."

## Clarifications

### Session 2026-11-04

- Q: How should the system behave when the requested date falls on a weekend or public holiday? → A: Use the latest prior published business date with a valid rate and clearly state that the displayed result uses the fallback date.
- Q: What happens when a selected currency is missing from the official data set for the chosen date? → A: Show a clear error stating that the selected currency is unavailable for that date, and do not silently substitute a different rate.
- Q: How should invalid or malformed XML and cache failures be handled? → A: If the XML feed cannot be parsed, the system must reject the invalid response, use the last valid cached snapshot if available, and otherwise present a clear error without crashing.
- Q: What exact amount validation rule is required? → A: Amounts must be positive decimal values greater than zero; empty, zero, negative, alphabetic, and malformed values are rejected before conversion.
- Q: What is the required cache behavior across restarts? → A: Save the most recent valid official snapshot locally and retain it across application restarts for offline use.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Convert a valid amount between supported currencies (Priority: P1)

A user opens the application, enters an amount, selects a source currency and a target currency, and confirms the conversion. The system calculates the converted value and presents the result, the exchange-rate date actually used, and the official source name.

**Why this priority**: This is the primary user journey and the core value of the product. The feature cannot be considered successful unless users can convert amounts accurately using the supported currencies.

**Independent Test**: Can be fully tested by entering a valid amount, selecting a source and target currency, and confirming that the resulting converted value and rate metadata are displayed correctly.

**Acceptance Scenarios**:

1. **Given** the user has filled in a valid amount and selected USD as the source and MDL as the target, **When** they click Convert, **Then** the system displays the converted amount, the effective exchange-rate date, and the official source name.
2. **Given** the user has filled in a valid amount and selected MDL as the source and USD as the target, **When** they click Convert, **Then** the system calculates the reverse conversion and shows the result using the same valuation logic as the forward direction.
3. **Given** a valid conversion request with a selected date, **When** the service provides a matching rate for that date, **Then** the displayed effective rate date matches the selected date and the result is derived from that rate.

---

### User Story 2 - Validate and reject invalid input before calculation (Priority: P1)

A user tries to submit an amount that is incomplete, zero, negative, alphabetic, or malformed. The system blocks the conversion and provides a clear message explaining why the input is invalid.

**Why this priority**: Strong validation is a prerequisite for trustworthy financial calculations and prevents user confusion or incorrect conversions.

**Independent Test**: Can be fully tested by entering invalid numeric inputs and verifying that the Convert action remains unavailable or fails with a clear validation message.

**Acceptance Scenarios**:

1. **Given** the amount field is empty, **When** the user attempts to continue, **Then** the system prevents conversion and shows a clear required-field message.
2. **Given** the user enters 0 or a negative number, **When** they try to convert, **Then** the system rejects the request and explains that the amount must be greater than zero.
3. **Given** the user enters alphabetic or malformed text such as "abc" or "12,3x", **When** they submit the form, **Then** the system rejects the input and shows a clear formatting error.
4. **Given** the user has not filled in the required fields, **When** they view the form, **Then** the Convert button remains disabled until all required inputs are present and valid.

---

### User Story 3 - Handle date, source, and cache fallback scenarios (Priority: P1)

A user requests a conversion for a date when no direct rate is available, or the service is unavailable. The system must identify the latest previous valid rate when possible, inform the user, and fall back to the latest locally saved snapshot if network or service access is unavailable.

**Why this priority**: Currency data is often incomplete or temporarily unavailable, so the product must be resilient and transparent about the date used and the source of the data.

**Independent Test**: Can be tested by requesting a conversion for a date without a rate, requesting a conversion on a weekend or holiday, testing a missing currency in the feed, and verifying offline fallback behavior with the correct date messaging.

**Acceptance Scenarios**:

1. **Given** the requested date is a weekend or public holiday and no rate is published for that date, **When** the user clicks Convert, **Then** the system selects the latest prior published business date with a valid rate, displays the converted result, and clearly states that the fallback rate date was used.
2. **Given** the requested date has no published rate for any prior valid date, **When** the user clicks Convert, **Then** the system shows a clear warning that no valid rate is available and does not produce a misleading conversion result.
3. **Given** the source or target currency is absent from the official rate set for the selected date, **When** the user clicks Convert, **Then** the system shows a clear currency-unavailable message and does not substitute a different rate silently.
4. **Given** the source and target currencies are identical, **When** the user converts, **Then** the system returns the unchanged amount without any rate lookup or monetary transformation.
5. **Given** the official XML response is malformed, incomplete, or invalid, **When** the user requests a conversion, **Then** the system rejects the invalid feed, uses the last valid cached snapshot if available, and otherwise shows a clear error without crashing.
6. **Given** the service is offline or unavailable, **When** a valid cached snapshot exists, **Then** the system uses that local snapshot, shows the real snapshot date, and keeps the app running without crashing.
7. **Given** the service is offline and no valid cached snapshot exists, **When** the user attempts a conversion, **Then** the system shows a clear error and does not crash or leave the application in an unusable state.
8. **Given** the application is restarted after a successful conversion or exchange-rate fetch, **When** the user requests conversion offline, **Then** the previously saved cache remains available and is used as the last valid local snapshot.

---

### User Story 4 - View the required currency metadata and official data source (Priority: P2)

A user needs confidence that the displayed result is based on the correct official data source and the correct effective date. The application presents this metadata consistently for every conversion result.

**Why this priority**: Transparency is essential for trust, especially in financial conversions based on official rate feeds.

**Independent Test**: Can be fully tested by verifying that each conversion result includes the converted amount, the effective exchange-rate date, and the source name shown directly in the interface.

**Acceptance Scenarios**:

1. **Given** a completed conversion, **When** the result is displayed, **Then** the interface shows the converted amount, the actual effective exchange-rate date used, and the official source name.
2. **Given** a fallback rate is selected due to missing data for a requested date, **When** the result is displayed, **Then** the interface identifies the fallback rate date and the source name clearly.

---

### Edge Cases

- What happens when the selected date falls on a weekend or a public holiday and the official service has no published rate for that date?
- How does the system behave when the official source returns malformed, incomplete, or unexpectedly empty XML data?
- What happens when the selected source or target currency is missing from the rate set for the requested date?
- How does the system handle a stale cached snapshot when no network access is available?
- What happens when the user selects the same currency in both fields and enters a valid amount?
- What happens when a cached snapshot exists but the requested date is newer than the last published rate?
- What happens when the user changes the amount or currency selection after a previous conversion result?
- What happens when the user tries to convert before entering all required values or after entering an invalid amount?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a graphical web interface for currency conversion using supported currencies: MDL, EUR, USD, RON, GBP, and UAH.
- **FR-002**: The system MUST allow users to enter an amount, choose a source currency, choose a target currency, and optionally choose a rate date with today as the default value.
- **FR-003**: The system MUST prevent conversion until all required fields are present and valid, and the Convert button MUST remain disabled until that condition is satisfied.
- **FR-004**: The system MUST reject zero, negative, empty, alphabetic, and malformed amount values with clear and user-friendly error messages.
- **FR-005**: The system MUST treat identical source and target currencies as a no-op conversion and return the unchanged amount without altering the value.
- **FR-006**: The system MUST use the official National Bank of Moldova XML exchange-rate service as the primary source of exchange-rate data when available.
- **FR-007**: The system MUST display the converted amount, the effective exchange-rate date used, and the source name for each successful result.
- **FR-008**: When the requested rate date is a weekend, a public holiday, or any other date with no published rate, the system MUST find the latest prior published business date with a valid rate and clearly inform the user that the fallback date was used.
- **FR-009**: When the selected source or target currency does not exist in the official rate set for the chosen effective date, the system MUST show a clear currency-unavailable message and MUST NOT silently substitute an alternative rate.
- **FR-010**: When the service is unavailable or the exchange-rate request fails, the system MUST use the most recent valid locally saved snapshot if one exists and show its real date.
- **FR-011**: When no valid local snapshot exists and the service fails, the system MUST show a clear error message without crashing the application.
- **FR-012**: The system MUST persist the latest valid exchange-rate snapshot so it remains available after application restart.
- **FR-013**: The system MUST handle malformed, incomplete, or invalid exchange-rate responses gracefully and avoid crashing or exposing unhandled errors to the user.
- **FR-014**: The system MUST support conversion in both directions, including from MDL to another supported currency and from another supported currency to MDL.
- **FR-015**: The application MUST not require registration, login, a database server, or payment processing to perform the requested currency conversion use case.
- **FR-016**: The system MUST keep error states understandable and actionable so users know what went wrong and what to do next.
- **FR-017**: The system MUST preserve the last valid cached exchange-rate snapshot, even after an invalid or failed refresh attempt, unless a newer valid snapshot replaces it.
- **FR-018**: The application MUST be implemented in Python using Streamlit.
- **FR-019**: The interface MUST use a consistent light theme, readable typography, rounded controls, and visually prominent conversion results.
- **FR-020**: The interface MUST clearly distinguish validation errors, rate errors, and offline warnings, and remain usable on desktop and smaller screens.

### Architecture and Quality Requirements

- **QR-001**: UI rendering, conversion calculations, input validation, BNM API access, XML parsing, and cache persistence MUST have distinct responsibilities.
- **QR-002**: Conversion logic MUST depend on a focused rate-provider abstraction so another provider can be added without rewriting conversion logic.
- **QR-003**: Rate providers conforming to the provider contract MUST be interchangeable and honor the same observable behavior and result contract.
- **QR-004**: Interfaces or protocols MUST be small and focused; business logic MUST NOT depend directly on a concrete HTTP client.
- **QR-005**: The architecture MUST apply these principles without introducing abstractions that do not reduce complexity or support a current requirement.
- **QR-006**: Automated unit tests MUST use pytest and remain separate from browser-level end-to-end tests.
- **QR-007**: Browser-level end-to-end tests MUST use Selenium WebDriver with pytest and cover valid conversion, validation, the disabled Convert button, conversion result, effective rate date, and source name.
- **QR-008**: Selenium tests SHOULD use Chrome in headless mode and explicit waits, and MUST use deterministic fixture-backed or stubbed rate data rather than require the live BNM service.
- **QR-009**: Selenium E2E tests MUST be implemented on the `testing` branch.
- **QR-010**: The README MUST document commands for running unit tests, Selenium E2E tests, and the complete test suite.

### Key Entities

- **Currency Conversion Request**: Represents the user's input, including the amount, source currency, target currency, and optional rate date.
- **Exchange Rate Snapshot**: Represents an official rate dataset stored locally, including the effective date, supported rates, and source metadata.
- **Conversion Result**: Represents the computed output, including the converted amount, the effective rate date used, and the source name displayed to the user.
- **Validation Error**: Represents a rejected input state due to an empty, invalid, zero, negative, or malformed amount.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a valid currency conversion in under 2 minutes with no prior training.
- **SC-002**: The application correctly rejects all disallowed amount states and presents clear user-facing validation messages in 100% of tested invalid-input scenarios.
- **SC-003**: The application successfully handles both conversion directions for all supported currencies with the expected result and source metadata in 100% of tested valid scenarios.
- **SC-004**: When a requested date lacks a rate, falls on a weekend or public holiday, or has a missing currency entry, the application uses the latest prior valid rate only when it exists and informs the user in 100% of the tested fallback scenarios.
- **SC-005**: When the network or official service is unavailable, the application uses the last valid cached snapshot when available and shows the real snapshot date without crashing in 100% of offline/failure tests.
- **SC-006**: Cached exchange-rate data remains available across application restarts in 100% of persistence tests.
- **SC-007**: The system provides a clear error and remains usable when no valid cache exists and the service fails.
- **SC-008**: Invalid or malformed XML responses are rejected without crashing the application, and the system falls back to the last valid cached snapshot whenever one exists.
- **SC-009**: The interface remains readable and operable at desktop and smaller-screen sizes, with a consistent light appearance, clearly visible errors/offline warnings, and a prominent result.
- **SC-010**: The Selenium E2E suite passes in headless Chrome using deterministic rate data and verifies valid conversion, validation, disabled-button behavior, result amount, effective date, and source name.

## Assumptions

- Users are acting as individual consumers who need a simple and reliable conversion tool for supported currencies.
- The application is limited to educational use and does not require account creation or user accounts.
- The pricing and rate data are based on official exchange information and should be shown transparently to the user.
- If the requested conversion date is unavailable, using the latest prior valid rate is the preferred fallback behavior for continuity and user trust.
- Local cache storage is available to the application and is expected to persist across restarts as part of the product requirement.
- The feature is scoped to the conversion workflow and does not include broader financial products, payment, or authentication features.
