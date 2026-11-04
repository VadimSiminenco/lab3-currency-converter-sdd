# Quickstart: Currency Converter Validation Guide

## Prerequisites

- Python 3.11+
- Windows PowerShell
- Access to the official NBM rate source for live validation

## Setup

```powershell
cd C:\path\to\lab3-currency-converter-sdd
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install streamlit requests pytest
```

## Validation scenarios

### 1. Successful conversion
- Open the app in the browser.
- Enter a positive amount such as `100`.
- Select `USD` as source and `MDL` as target.
- Leave the date blank to use today.
- Click Convert.
- Confirm that the output shows the converted amount, effective date, and source name.

### 2. Invalid amount rejection
- Enter `0`, `-5`, `abc`, or an empty value.
- Confirm the Convert button stays disabled or the submission is rejected with a clear message.

### 3. Weekend and holiday fallback
- Choose a date on a weekend or holiday when the official feed has no rate.
- Confirm the app selects the latest prior valid business date and informs the user of the fallback date.

### 4. Same-currency conversion
- Select the same currency in both dropdowns, such as `EUR` to `EUR`.
- Enter a valid positive amount.
- Confirm the result equals the original amount unchanged.

### 5. Missing currency in feed
- Request a date where a chosen currency is absent from the official feed.
- Confirm the app shows a currency-unavailable message and does not substitute another rate silently.

### 6. Offline or service failure fallback
- Simulate a network outage or invalid feed.
- Confirm the app uses the most recent valid JSON cache if available and shows the real snapshot date.
- Confirm the app remains responsive and does not crash.

### 7. No cache available
- Remove or invalidate the cache file.
- Simulate a failed feed request.
- Confirm the app shows a clear error without crashing.

### 8. Restart persistence
- Perform a successful fetch or conversion.
- Close and reopen the application.
- Confirm the saved snapshot remains available for offline conversion.

## Expected outcome

The feature is considered ready when each validation scenario above produces the expected error, fallback behavior, or conversion result without crashing the application.
