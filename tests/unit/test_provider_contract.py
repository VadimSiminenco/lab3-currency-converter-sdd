"""Contract tests for RateProvider protocol implementations (Liskov Substitution Principle)."""
from datetime import date
from decimal import Decimal
from typing import Optional
import pytest

from src.api.bnm_client import BnmClient, BnmNetworkError
from src.api.bnm_provider import BnmRateProvider
from src.cache.rate_cache import RateCache
from src.config.settings import BASE_CURRENCY, SUPPORTED_CURRENCIES
from src.domain.models import RateSnapshot
from src.domain.ports import RateProvider


class DummyMockClient:
    """Mock client returning canned XML responses without making real HTTP calls."""

    def __init__(self, xml_payload: str = "", should_raise: bool = False):
        self.xml_payload = xml_payload
        self.should_raise = should_raise

    def fetch_rates_xml(self, target_date: date) -> str:
        if self.should_raise:
            raise BnmNetworkError("Simulated network timeout")
        return self.xml_payload


class ContractTestRateProviderBase:
    """Base test suite verifying that any RateProvider implementation adheres to the contract."""

    def create_provider(self, *args, **kwargs) -> RateProvider:
        raise NotImplementedError

    def test_implements_protocol(self):
        provider = self.create_provider()
        assert isinstance(provider, RateProvider)
        assert hasattr(provider, "get_rates")
        assert callable(provider.get_rates)


class TestBnmRateProviderContract(ContractTestRateProviderBase):
    """Verifies that BnmRateProvider conforms strictly to the RateProvider contract."""

    VALID_XML = '''<?xml version="1.0" encoding="utf-8"?>
    <ValCurs Date="04.11.2026" name="National Bank of Moldova">
      <Valute><CharCode>EUR</CharCode><Nominal>1</Nominal><Value>19.50</Value></Valute>
      <Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>18.10</Value></Valute>
      <Valute><CharCode>RON</CharCode><Nominal>1</Nominal><Value>3.90</Value></Valute>
      <Valute><CharCode>GBP</CharCode><Nominal>1</Nominal><Value>23.40</Value></Valute>
      <Valute><CharCode>UAH</CharCode><Nominal>10</Nominal><Value>4.30</Value></Valute>
    </ValCurs>'''

    EMPTY_XML = '''<?xml version="1.0" encoding="utf-8"?>
    <ValCurs Date="08.11.2026" name="National Bank of Moldova">
    </ValCurs>'''

    def create_provider(self, xml: str = VALID_XML, should_raise: bool = False, tmp_path=None) -> RateProvider:
        client = DummyMockClient(xml_payload=xml, should_raise=should_raise)
        cache = RateCache(tmp_path / "cache.json") if tmp_path else RateCache()
        return BnmRateProvider(client=client, cache=cache)

    def test_returns_valid_snapshot(self, tmp_path):
        provider = self.create_provider(xml=self.VALID_XML, tmp_path=tmp_path)
        snapshot = provider.get_rates(date(2026, 11, 4))

        assert isinstance(snapshot, RateSnapshot)
        assert snapshot.snapshot_date == date(2026, 11, 4)
        assert isinstance(snapshot.source_name, str) and snapshot.source_name

        # Verify all supported currencies exist with finite positive Decimal rates
        for code in SUPPORTED_CURRENCIES:
            assert snapshot.has_currency(code)
            rate = snapshot.get_rate(code)
            assert isinstance(rate, Decimal)
            assert rate.is_finite()
            assert rate > Decimal("0")

        # Base currency rate must be 1.0
        assert snapshot.get_rate(BASE_CURRENCY) == Decimal("1.0")

    def test_returns_none_when_unpublished(self, tmp_path):
        provider = self.create_provider(xml=self.EMPTY_XML, tmp_path=tmp_path)
        snapshot = provider.get_rates(date(2026, 11, 8))
        assert snapshot is None

    def test_raises_exception_on_network_failure(self, tmp_path):
        provider = self.create_provider(should_raise=True, tmp_path=tmp_path)
        with pytest.raises(Exception):
            provider.get_rates(date(2026, 11, 4))

    def test_caching_behavior_on_valid_fetch(self, tmp_path):
        cache_file = tmp_path / "contract_cache.json"
        cache = RateCache(cache_file)
        client = DummyMockClient(xml_payload=self.VALID_XML)
        provider = BnmRateProvider(client=client, cache=cache)

        assert not cache_file.exists()
        snapshot = provider.get_rates(date(2026, 11, 4))
        assert snapshot is not None

        # Verify snapshot was persisted to cache
        cached = cache.load()
        assert cached is not None
        assert cached.snapshot_date == date(2026, 11, 4)
