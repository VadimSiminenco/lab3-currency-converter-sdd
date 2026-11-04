"""Domain port interfaces and protocols."""
from datetime import date
from typing import Optional, Protocol
from src.domain.models import RateSnapshot


class RateProvider(Protocol):
    """Protocol for fetching exchange rate snapshots from an exchange rate source.

    Allows interchangeable implementations (e.g. BNM XML provider, offline fixture provider,
    mock test provider) without coupling domain conversion logic to HTTP or XML details.
    """

    def get_rates(self, target_date: date) -> Optional[RateSnapshot]:
        """Fetch rates for a given date.

        Args:
            target_date: The date for which rates should be fetched.

        Returns:
            RateSnapshot if rates exist for that date, or None if no rates are published.

        Raises:
            Exception: If network or provider communication fails.
        """
        ...
