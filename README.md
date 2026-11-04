# Currency Converter (Lab 3)

A modern, educational web application for accurate currency conversion built with **Python**, **Streamlit**, and **Spec-Driven Development (SDD)**.

The application retrieves official daily exchange rates from the **National Bank of Moldova (BNM)** XML feed, supports cross-currency conversion between supported currencies with exact decimal arithmetic, falls back to the latest valid rates on weekends and public holidays, and provides persistent offline cache resilience.

---

## Supported Currencies

- **MDL** — Moldovan Leu (Base Currency)
- **EUR** — Euro
- **USD** — US Dollar
- **RON** — Romanian Leu
- **GBP** — British Pound Sterling
- **UAH** — Ukrainian Hryvnia

---

## Architectural Design & SOLID Principles

The system separates responsibilities and applies SOLID proportionately. `RateProvider` is a narrow extension seam (OCP/ISP), and conversion depends on it rather than HTTP (DIP). DIP is partial because conversion still depends on concrete `RateCache`. Provider substitutability (LSP) requires contract tests; a protocol alone is not proof. Cache writes currently belong to `BnmRateProvider`, so alternate providers must account for persistence behavior.

- **Streamlit UI** (`src/app/ui/streamlit_app.py`, `app.py`): Presentation layer with clean modern light design, real-time input validation, accessible controls, and test IDs.
- **Input Validation** (`src/domain/validation.py`): Enforces positive decimal amounts; rejects empty, zero, negative, alphabetic, or malformed inputs.
- **Conversion Logic** (`src/domain/conversion.py`): Pure calculation with `decimal.Decimal`, rounding, same-currency no-op handling, cross-currency routing, and date fallback orchestration.
- **Rate Provider Port** (`src/domain/ports.py`): `RateProvider` protocol enabling dependency inversion (DIP) and interchangeable rate sources (LSP/OCP).
- **BNM HTTP Client** (`src/api/bnm_client.py`): Dedicated HTTPS client communicating with the BNM XML endpoint with timeout protection.
- **XML Parser** (`src/parsing/xml_parser.py`): Parses official `ValCurs` XML and normalizes rates per unit using `Value / Nominal`.
- **Persistent Cache** (`src/cache/rate_cache.py`): Manages local JSON snapshot storage (`data/rates_cache.json`) that survives app restarts and prevents invalid overwrites.

---

## Project Structure

```text
lab3-currency-converter-sdd/
├── app.py                      # Main application entry point
├── requirements.txt            # Core dependencies
├── requirements-dev.txt        # Development and testing dependencies
├── .gitignore                  # Git ignore definitions
├── README.md                   # Documentation and instructions
├── data/
│   └── rates_cache.json        # Persistent exchange rates JSON cache
├── src/
│   ├── api/
│   │   ├── bnm_client.py       # BNM HTTPS client
│   │   └── bnm_provider.py     # BNM RateProvider adapter
│   ├── app/
│   │   └── ui/
│   │       └── streamlit_app.py# Streamlit user interface
│   ├── cache/
│   │   └── rate_cache.py       # JSON cache management
│   ├── config/
│   │   └── settings.py         # Application configuration & constants
│   ├── domain/
│   │   ├── conversion.py       # Currency conversion & date fallback
│   │   ├── models.py           # Domain models & entities
│   │   ├── ports.py            # RateProvider protocol
│   │   └── validation.py       # Input validation rules
│   └── parsing/
│       └── xml_parser.py       # BNM XML feed parser
└── tests/
    ├── fixtures/               # Sample XML and JSON test fixtures
    ├── unit/                   # Pytest unit tests
    ├── integration/            # Pytest integration tests
    └── e2e/                    # Selenium WebDriver E2E tests (testing branch)
```

---

## Installation & Setup (Windows PowerShell)

### Prerequisites

- Python 3.11 or newer installed and accessible in `PATH`.
- Windows PowerShell.

### 1. Clone the repository and navigate to the project directory

```powershell
cd C:\path\to\lab3-currency-converter-sdd
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade pip and install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

To install development and testing dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

---

## Running the Application

To start the Currency Converter web application:

```powershell
streamlit run app.py
```

Streamlit will launch a local web server (typically at `http://localhost:8501`) and automatically open the application in your default browser.

---

## Key Features & Behavior

1. **Amount Input & Validation**:
   - Accepts any positive numeric value.
   - The **Convert Currency** button is automatically disabled when the amount is blank, zero, negative, or contains non-numeric characters.
   - Clear inline feedback explains why the input is invalid.

2. **Accurate Conversions**:
   - Supports conversions from MDL to foreign currencies, foreign currencies to MDL, and cross-currency conversions (e.g. USD to EUR).
   - Handles identical source and target currencies (e.g. EUR to EUR) with a 1:1 no-op return.
   - Respects the currency `Nominal` attribute (e.g. UAH where Nominal is 10) by normalizing rate to `Value / Nominal`.
   - Uses `decimal.Decimal` with financial `ROUND_HALF_UP` rounding.

3. **Weekend & Holiday Handling**:
   - If official rates were not published for the requested date (weekends or public holidays), the application automatically steps backward day by day to locate the latest published official rate.
   - An informational notice explains which fallback date was applied.

4. **Offline Resilience & Cache Persistence**:
   - Whenever fresh rates are fetched, the application updates `data/rates_cache.json`.
   - If the network is unavailable or BNM fails, the application automatically loads the last valid local cache and displays an offline warning with the snapshot date.
   - Corrupted or invalid payloads never overwrite a valid cache.

---

## Test Execution

The `testing` branch contains pytest unit/integration tests and four Selenium browser tests using deterministic XML data. On 2026-11-04, 110 unit/integration tests and 4 Selenium tests passed in separate runs. Browser tests require Chrome and a compatible driver; Selenium Manager may need network access to provision the driver, while exchange-rate data comes from fixtures rather than live BNM.

Run with the project's virtual environment: `.\.venv\Scripts\python.exe -m pytest -q`. For separate runs, use `-m pytest tests/unit tests/integration -q` and `-m pytest tests/e2e -q`. The current four browser tests cover invalid amounts/disabled Convert, valid conversion and metadata, clearing stale results, and swapping currencies. Browser-level offline/fallback scenarios are not yet covered by these four tests.

The UI refresh uses a responsive light theme, a separate result panel, requested/effective dates, explicit offline/fallback/no-lookup states, and a calculation explanation. Input changes clear the previous result. Widget keys and result/error test IDs are retained for future Selenium tests. CSS lives in `src/app/ui/styles.css`.

### Running Unit Tests

```powershell
pytest tests/unit/
```

### Running Integration Tests

```powershell
pytest tests/integration/
```

### Running Full Pytest Test Suite

```powershell
pytest
```

### Running Selenium E2E Tests (testing branch)

Selenium WebDriver browser tests are implemented on the dedicated `testing` branch:

```powershell
pytest tests/e2e/
```
