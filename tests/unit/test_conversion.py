"""Unit tests for currency conversion business logic, date fallback, and offline handling."""
from datetime import date, timedelta
from decimal import Decimal
import pytest

from src.cache.rate_cache import RateCache
from src.config.settings import SOURCE_NAME
from src.domain.conversion import (
    CurrencyConverter,
    CurrencyUnavailableError,
    ExchangeRateUnavailableError,
)
from src.domain.models import ConversionRequest, RateSnapshot


@pytest.fixture
def sample_rates():
    return {
        "MDL": Decimal("1.0"),
        "EUR": Decimal("19.5432"),
        "USD": Decimal("18.1250"),
        "RON": Decimal("3.9280"),
        "GBP": Decimal("23.4500"),
        "UAH": Decimal("0.4350"),  # Normalized (Value 4.3500 / Nominal 10)
    }


@pytest.fixture
def sample_snapshot(sample_rates):
    return RateSnapshot(
        snapshot_date=date(2026, 11, 4),
        source_name="National Bank of Moldova",
        rates=sample_rates,
    )


class SpyRateProvider:
    """Mock provider recording calls and returning preset snapshots."""

    def __init__(self, snapshot: RateSnapshot | None = None, date_map: dict | None = None, should_fail: bool = False):
        self.snapshot = snapshot
        self.date_map = date_map or {}
        self.should_fail = should_fail
        self.call_count = 0
        self.requested_dates: list[date] = []

    def get_rates(self, target_date: date) -> RateSnapshot | None:
        self.call_count += 1
        self.requested_dates.append(target_date)
        if self.should_fail:
            raise ConnectionError("Simulated network outage")
        if target_date in self.date_map:
            return self.date_map[target_date]
        return self.snapshot


class TestSameCurrencyConversion:
    """Tests for identical source and target currencies (FR-005)."""

    @pytest.mark.parametrize("curr", ["MDL", "EUR", "USD", "RON", "GBP", "UAH"])
    def test_same_currency_no_op(self, curr, sample_snapshot):
        provider = SpyRateProvider(sample_snapshot)
        converter = CurrencyConverter(rate_provider=provider)

        req = ConversionRequest(amount=Decimal("123.45"), source_currency=curr, target_currency=curr)
        res = converter.convert(req)

        assert res.converted_amount == Decimal("123.45")
        assert res.rate_used == Decimal("1.0")
        assert res.fallback_used is False
        assert res.is_offline is False
        # Crucial check: provider was NEVER queried
        assert provider.call_count == 0


class TestConversionCalculations:
    """Tests for calculation accuracy, both directions, cross-currency, and nominal."""

    def test_foreign_to_base_usd_to_mdl(self, sample_snapshot):
        # 100 USD * 18.1250 / 1.0 = 1812.50 MDL
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res = converter.convert(ConversionRequest(Decimal("100"), "USD", "MDL"))
        assert res.converted_amount == Decimal("1812.50")

    def test_base_to_foreign_mdl_to_usd(self, sample_snapshot):
        # 1812.50 MDL * 1.0 / 18.1250 = 100.00 USD
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res = converter.convert(ConversionRequest(Decimal("1812.50"), "MDL", "USD"))
        assert res.converted_amount == Decimal("100.00")

    def test_cross_currency_usd_to_eur(self, sample_snapshot):
        # 100 USD * 18.1250 / 19.5432 = 92.743767... => 92.74 EUR
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res = converter.convert(ConversionRequest(Decimal("100"), "USD", "EUR"))
        assert res.converted_amount == Decimal("92.74")
        assert res.rate_used == Decimal("0.9274")

    def test_cross_currency_eur_to_ron(self, sample_snapshot):
        # 100 EUR * 19.5432 / 3.9280 = 497.53564... => 497.54 RON
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res = converter.convert(ConversionRequest(Decimal("100"), "EUR", "RON"))
        assert res.converted_amount == Decimal("497.54")

    def test_nominal_multiplier_currency_uah(self, sample_snapshot):
        # 100 UAH (rate 0.4350) -> 43.50 MDL
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res_uah_to_mdl = converter.convert(ConversionRequest(Decimal("100"), "UAH", "MDL"))
        assert res_uah_to_mdl.converted_amount == Decimal("43.50")

        # Reverse: 43.50 MDL / 0.4350 -> 100.00 UAH
        res_mdl_to_uah = converter.convert(ConversionRequest(Decimal("43.50"), "MDL", "UAH"))
        assert res_mdl_to_uah.converted_amount == Decimal("100.00")

    def test_rounding_half_up(self):
        # Verify ROUND_HALF_UP on boundary cases: .005 rounds up, .004 rounds down
        snap_up = RateSnapshot(
            snapshot_date=date(2026, 11, 4),
            source_name="National Bank of Moldova",
            rates={"MDL": Decimal("1.0"), "USD": Decimal("10.005"), "EUR": Decimal("10.004"), "RON": Decimal("1.0"), "GBP": Decimal("1.0"), "UAH": Decimal("1.0")},
        )
        converter = CurrencyConverter(rate_provider=SpyRateProvider(snap_up))

        # 1 USD -> 10.005 MDL -> rounds up to 10.01
        res_up = converter.convert(ConversionRequest(Decimal("1"), "USD", "MDL"))
        assert res_up.converted_amount == Decimal("10.01")

        # 1 EUR -> 10.004 MDL -> rounds down to 10.00
        res_down = converter.convert(ConversionRequest(Decimal("1"), "EUR", "MDL"))
        assert res_down.converted_amount == Decimal("10.00")

    def test_small_amount_preserves_four_decimal_places(self, sample_snapshot):
        # 1 UAH to GBP: 1 * 0.4350 / 23.4500 = 0.018549... => 0.02 GBP
        # 0.1 UAH to GBP: 0.1 * 0.4350 / 23.4500 = 0.001855... => 0.0019 GBP (positive < 0.01)
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        res = converter.convert(ConversionRequest(Decimal("0.1"), "UAH", "GBP"))
        assert Decimal("0") < res.converted_amount < Decimal("0.01")
        assert res.converted_amount == Decimal("0.0019")


class TestUnavailableCurrencies:
    """Tests for missing currency handling (FR-009)."""

    def test_missing_source_currency_raises_error(self, sample_snapshot):
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        req = ConversionRequest(Decimal("100"), "CAD", "MDL")
        with pytest.raises(CurrencyUnavailableError, match="Source currency 'CAD' is not available"):
            converter.convert(req)

    def test_missing_target_currency_raises_error(self, sample_snapshot):
        converter = CurrencyConverter(rate_provider=SpyRateProvider(sample_snapshot))
        req = ConversionRequest(Decimal("100"), "USD", "JPY")
        with pytest.raises(CurrencyUnavailableError, match="Target currency 'JPY' is not available"):
            converter.convert(req)


class TestDateFallback:
    """Tests for weekend and holiday historical rate fallback (FR-008)."""

    def test_weekend_fallback_to_previous_friday(self, sample_rates):
        sunday = date(2026, 11, 8)
        saturday = date(2026, 11, 7)
        friday = date(2026, 11, 6)

        friday_snapshot = RateSnapshot(
            snapshot_date=friday,
            source_name="National Bank of Moldova",
            rates=sample_rates,
        )

        # Sunday and Saturday have no published rates; Friday has rates
        date_map = {
            sunday: None,
            saturday: None,
            friday: friday_snapshot,
        }
        provider = SpyRateProvider(date_map=date_map)
        converter = CurrencyConverter(rate_provider=provider)

        res = converter.convert(ConversionRequest(Decimal("100"), "USD", "MDL", rate_date=sunday))

        assert res.fallback_used is True
        assert res.effective_rate_date == friday
        assert res.converted_amount == Decimal("1812.50")
        assert res.message is not None
        assert "08.11.2026" in res.message
        assert "06.11.2026" in res.message
        assert provider.call_count == 3  # Sunday, Saturday, Friday

    def test_fallback_exceeds_max_window_raises_error(self, tmp_path):
        # Empty provider and empty cache
        provider = SpyRateProvider(snapshot=None)
        cache = RateCache(tmp_path / "empty_cache.json")
        converter = CurrencyConverter(rate_provider=provider, cache=cache, max_fallback_days=5)

        with pytest.raises(ExchangeRateUnavailableError, match="Unable to obtain exchange rates"):
            converter.convert(ConversionRequest(Decimal("100"), "USD", "MDL", rate_date=date(2026, 1, 10)))


class TestOfflineFallback:
    """Tests for offline cache fallback and service outage recovery (FR-010, FR-011)."""

    def test_offline_fallback_uses_cached_snapshot(self, tmp_path, sample_snapshot):
        cache_file = tmp_path / "offline_rates.json"
        cache = RateCache(cache_file)
        assert cache.save(sample_snapshot) is True

        failing_provider = SpyRateProvider(should_fail=True)
        converter = CurrencyConverter(rate_provider=failing_provider, cache=cache)

        res = converter.convert(ConversionRequest(Decimal("50"), "USD", "MDL"))

        assert res.is_offline is True
        assert res.fallback_used is True
        assert res.effective_rate_date == sample_snapshot.snapshot_date
        assert res.converted_amount == Decimal("906.25")
        assert res.message is not None
        assert "Offline mode" in res.message

    def test_offline_with_no_cache_raises_error(self, tmp_path):
        cache_file = tmp_path / "non_existent.json"
        cache = RateCache(cache_file)
        failing_provider = SpyRateProvider(should_fail=True)
        converter = CurrencyConverter(rate_provider=failing_provider, cache=cache)

        with pytest.raises(ExchangeRateUnavailableError, match="no local cached snapshot is available"):
            converter.convert(ConversionRequest(Decimal("100"), "USD", "MDL"))
