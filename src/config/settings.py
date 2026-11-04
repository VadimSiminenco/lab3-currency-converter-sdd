"""Application configuration and shared constants."""
from pathlib import Path
from typing import Final

# Supported currencies defined in specification
SUPPORTED_CURRENCIES: Final[list[str]] = ["MDL", "EUR", "USD", "RON", "GBP", "UAH"]

# Base currency used for rate normalization
BASE_CURRENCY: Final[str] = "MDL"

# Official data source metadata
SOURCE_NAME: Final[str] = "National Bank of Moldova"

# BNM XML official exchange rates endpoint
BNM_XML_URL: Final[str] = "https://www.bnm.md/en/official_exchange_rates"

# Project root and cache storage location
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent.parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
DEFAULT_CACHE_FILE: Final[Path] = DATA_DIR / "rates_cache.json"

# Request settings
REQUEST_TIMEOUT_SECONDS: Final[int] = 10

# Maximum days to search backward for valid rates (for weekends/holidays)
MAX_FALLBACK_DAYS: Final[int] = 14
