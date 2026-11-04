"""Domain models, ports, validation, and conversion business logic."""
from src.domain.models import (
    ConversionRequest,
    ConversionResult,
    ExchangeRateEntry,
    RateSnapshot,
    ValidationError,
)
from src.domain.ports import RateProvider
from src.domain.validation import validate_amount, validate_request


def __getattr__(name: str):
    """Keep the public converter export without a cache/domain import cycle."""
    if name == "CurrencyConverter":
        from src.domain.conversion import CurrencyConverter
        return CurrencyConverter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "ConversionRequest",
    "ConversionResult",
    "ExchangeRateEntry",
    "RateSnapshot",
    "ValidationError",
    "RateProvider",
    "validate_amount",
    "validate_request",
    "CurrencyConverter",
]
