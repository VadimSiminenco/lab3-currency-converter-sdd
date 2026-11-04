"""Domain models for currency conversion, exchange rates, and validation."""
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class ConversionRequest:
    """Represents a validated currency conversion request."""

    amount: Decimal
    source_currency: str
    target_currency: str
    rate_date: date | None = None

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("Amount must be greater than zero.")
        if not self.source_currency or not self.target_currency:
            raise ValueError("Source and target currencies must be specified.")


@dataclass(frozen=True)
class ExchangeRateEntry:
    """Represents one normalized rate entry for a currency from the provider."""

    currency_code: str
    nominal: Decimal
    value: Decimal
    rate_per_unit_mdl: Decimal

    def __post_init__(self) -> None:
        if not self.nominal.is_finite() or self.nominal <= Decimal("0"):
            raise ValueError("Nominal must be a finite positive number greater than zero.")
        if not self.value.is_finite() or self.value <= Decimal("0"):
            raise ValueError("Value must be a finite positive number greater than zero.")
        if not self.rate_per_unit_mdl.is_finite() or self.rate_per_unit_mdl <= Decimal("0"):
            raise ValueError("Rate per unit must be a finite positive number greater than zero.")


@dataclass(frozen=True)
class RateSnapshot:
    """Represents a set of official exchange rates for a specific date."""

    snapshot_date: date
    source_name: str
    rates: dict[str, Decimal]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def get_rate(self, code: str) -> Decimal | None:
        """Return the rate per unit in MDL for the currency code, or None if not present."""
        return self.rates.get(code.upper())

    def has_currency(self, code: str) -> bool:
        """Check whether the currency is present in the snapshot."""
        return code.upper() in self.rates

    def to_dict(self) -> dict[str, Any]:
        """Serialize the snapshot to a JSON-compatible dictionary."""
        return {
            "snapshot_date": self.snapshot_date.isoformat(),
            "source_name": self.source_name,
            "rates": {code: str(rate) for code, rate in self.rates.items()},
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RateSnapshot":
        """Deserialize a dictionary to a RateSnapshot."""
        snapshot_date = date.fromisoformat(data["snapshot_date"])
        source_name = str(data["source_name"])
        raw_rates = data.get("rates", {})
        rates: dict[str, Decimal] = {}
        for code, rate_val in raw_rates.items():
            rate_dec = Decimal(str(rate_val))
            if not rate_dec.is_finite() or rate_dec <= Decimal("0"):
                raise ValueError(f"Invalid non-positive or non-finite rate for {code}: {rate_val}")
            rates[code.upper()] = rate_dec

        gen_str = data.get("generated_at")
        generated_at = (
            datetime.fromisoformat(gen_str)
            if gen_str
            else datetime.now(timezone.utc)
        )
        return cls(
            snapshot_date=snapshot_date,
            source_name=source_name,
            rates=rates,
            generated_at=generated_at,
        )


@dataclass(frozen=True)
class ConversionResult:
    """Represents the outcome of a currency conversion calculation."""

    converted_amount: Decimal
    effective_rate_date: date
    source_name: str
    fallback_used: bool = False
    is_offline: bool = False
    rate_used: Decimal | None = None
    message: str | None = None


@dataclass(frozen=True)
class ValidationError:
    """Represents a user-facing validation or business rule failure."""

    type: str
    message: str
    recoverable: bool = False
