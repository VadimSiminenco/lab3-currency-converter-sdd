"""BNM RateProvider adapter conforming to the domain RateProvider protocol."""
from datetime import date
from typing import Optional

from src.api.bnm_client import BnmClient
from src.cache.rate_cache import RateCache
from src.domain.models import RateSnapshot
from src.parsing.xml_parser import parse_bnm_xml


class BnmRateProvider:
    """Exchange rate provider adapter fetching live rates from the BNM XML service.

    Conforms to the RateProvider protocol defined in src.domain.ports.
    """

    def __init__(
        self,
        client: BnmClient | None = None,
        cache: RateCache | None = None,
    ) -> None:
        self.client = client or BnmClient()
        self.cache = cache or RateCache()

    def get_rates(self, target_date: date) -> Optional[RateSnapshot]:
        """Fetch rates for the given date from BNM.

        Args:
            target_date: The date to retrieve exchange rates for.

        Returns:
            RateSnapshot if rates exist for that date, or None if no rates are published.

        Raises:
            BnmClientError: If network request fails.
            XmlParsingError: If XML response is invalid or malformed.
        """
        xml_content = self.client.fetch_rates_xml(target_date)
        snapshot = parse_bnm_xml(xml_content)

        if snapshot is not None:
            # Automatically persist valid snapshot to local cache
            self.cache.save(snapshot)

        return snapshot
