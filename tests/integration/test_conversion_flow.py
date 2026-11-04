"""Integration tests for currency conversion flows without live network access."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from src.api.bnm_provider import BnmRateProvider
from src.cache.rate_cache import RateCache
from src.domain.conversion import CurrencyConverter
from src.domain.models import ConversionRequest

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class FakeHttpClient:
    """Simulates HTTP client using fixture files."""

    def __init__(self, fixture_xml: str, fail: bool = False):
        self.fixture_xml = fixture_xml
        self.fail = fail

    def fetch_rates_xml(self, target_date: date) -> str:
        if self.fail:
            raise ConnectionError("Simulated BNM connection failure")
        return self.fixture_xml


class TestConversionFlowIntegration:
    """End-to-end integration flows across API adapter, XML parser, cache, and conversion logic."""

    def test_full_live_conversion_and_cache_population(self, tmp_path):
        valid_xml = (FIXTURES_DIR / "valid_rate_feed.xml").read_text(encoding="utf-8")
        cache_path = tmp_path / "integration_cache.json"
        cache = RateCache(cache_path)

        client = FakeHttpClient(fixture_xml=valid_xml)
        provider = BnmRateProvider(client=client, cache=cache)
        converter = CurrencyConverter(rate_provider=provider, cache=cache)

        # 1. First conversion request: 100 USD to MDL
        req = ConversionRequest(
            amount=Decimal("100"),
            source_currency="USD",
            target_currency="MDL",
            rate_date=date(2026, 11, 4),
        )
        res = converter.convert(req)

        assert res.converted_amount == Decimal("1812.50")
        assert res.effective_rate_date == date(2026, 11, 4)
        assert res.source_name == "Official exchange rates"
        assert res.fallback_used is False
        assert res.is_offline is False

        # Verify that cache was populated on disk
        assert cache_path.exists()
        cached = cache.load()
        assert cached is not None
        assert cached.rates["USD"] == Decimal("18.1250")

    def test_offline_resilience_after_service_failure(self, tmp_path):
        valid_xml = (FIXTURES_DIR / "valid_rate_feed.xml").read_text(encoding="utf-8")
        cache_path = tmp_path / "integration_cache.json"
        cache = RateCache(cache_path)

        # Pre-seed cache as if from a prior successful session
        provider_init = BnmRateProvider(client=FakeHttpClient(fixture_xml=valid_xml), cache=cache)
        provider_init.get_rates(date(2026, 11, 4))
        assert cache_path.exists()

        # Now simulate network failure
        offline_client = FakeHttpClient(fixture_xml="", fail=True)
        offline_provider = BnmRateProvider(client=offline_client, cache=cache)
        offline_converter = CurrencyConverter(rate_provider=offline_provider, cache=cache)

        req = ConversionRequest(
            amount=Decimal("50"),
            source_currency="EUR",
            target_currency="RON",
            rate_date=date(2026, 11, 4),
        )
        res = offline_converter.convert(req)

        # 50 EUR * 19.5432 / 3.9280 = 248.7678... => 248.77 RON
        assert res.converted_amount == Decimal("248.77")
        assert res.is_offline is True
        assert res.effective_rate_date == date(2026, 11, 4)
        assert res.message is not None
        assert "Offline mode" in res.message
