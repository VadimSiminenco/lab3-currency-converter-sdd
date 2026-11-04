"""Unit tests for local JSON rate cache persistence and integrity."""
from datetime import date, datetime, timezone
from decimal import Decimal
import json
import pytest

from src.cache.rate_cache import RateCache
from src.config.settings import SUPPORTED_CURRENCIES
from src.domain.models import RateSnapshot


@pytest.fixture
def valid_snapshot():
    return RateSnapshot(
        snapshot_date=date(2026, 11, 4),
        source_name="National Bank of Moldova",
        rates={
            "MDL": Decimal("1.0"),
            "EUR": Decimal("19.5432"),
            "USD": Decimal("18.1250"),
            "RON": Decimal("3.9280"),
            "GBP": Decimal("23.4500"),
            "UAH": Decimal("0.4350"),
        },
        generated_at=datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc),
    )


class TestRateCache:
    """Tests for RateCache class."""

    def test_save_and_load_roundtrip(self, tmp_path, valid_snapshot):
        cache_file = tmp_path / "rates.json"
        cache = RateCache(cache_file)

        assert cache.save(valid_snapshot) is True
        loaded = cache.load()

        assert loaded is not None
        assert loaded.snapshot_date == valid_snapshot.snapshot_date
        assert loaded.source_name == valid_snapshot.source_name
        for code in SUPPORTED_CURRENCIES:
            assert loaded.rates[code] == valid_snapshot.rates[code]
            assert isinstance(loaded.rates[code], Decimal)

    def test_persistence_across_instances(self, tmp_path, valid_snapshot):
        cache_file = tmp_path / "rates.json"
        first_instance = RateCache(cache_file)
        first_instance.save(valid_snapshot)

        # Emulate application restart with new instance
        second_instance = RateCache(cache_file)
        restarted_snapshot = second_instance.load()

        assert restarted_snapshot is not None
        assert restarted_snapshot.snapshot_date == valid_snapshot.snapshot_date
        assert restarted_snapshot.rates["USD"] == Decimal("18.1250")

    def test_missing_cache_file_returns_none(self, tmp_path):
        cache = RateCache(tmp_path / "non_existent.json")
        assert cache.load() is None

    @pytest.mark.parametrize("corrupt_content", [
        "",
        "   ",
        "{malformed-json:",
        "[1, 2, 3]",
        '"just a string"',
        "12345",
    ])
    def test_corrupted_cache_file_returns_none_without_crash(self, tmp_path, corrupt_content):
        cache_file = tmp_path / "corrupt.json"
        cache_file.write_text(corrupt_content, encoding="utf-8")

        cache = RateCache(cache_file)
        assert cache.load() is None

    def test_cache_missing_required_currency_returns_none(self, tmp_path, valid_snapshot):
        cache_file = tmp_path / "partial.json"
        data = valid_snapshot.to_dict()
        del data["rates"]["UAH"]
        cache_file.write_text(json.dumps(data), encoding="utf-8")

        cache = RateCache(cache_file)
        assert cache.load() is None

    def test_refuse_save_missing_required_currency(self, tmp_path, valid_snapshot):
        cache_file = tmp_path / "rates.json"
        cache = RateCache(cache_file)

        partial_rates = {k: v for k, v in valid_snapshot.rates.items() if k != "RON"}
        partial_snapshot = RateSnapshot(
            snapshot_date=valid_snapshot.snapshot_date,
            source_name=valid_snapshot.source_name,
            rates=partial_rates,
        )

        assert cache.save(partial_snapshot) is False
        assert not cache_file.exists()

    @pytest.mark.parametrize("bad_rate", [
        Decimal("0"),
        Decimal("-5.0"),
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ])
    def test_refuse_save_invalid_rate_values(self, tmp_path, valid_snapshot, bad_rate):
        cache_file = tmp_path / "rates.json"
        cache = RateCache(cache_file)

        rates = dict(valid_snapshot.rates)
        rates["EUR"] = bad_rate
        snapshot = RateSnapshot(
            snapshot_date=valid_snapshot.snapshot_date,
            source_name=valid_snapshot.source_name,
            rates=rates,
        )

        assert cache.save(snapshot) is False
        assert not cache_file.exists()

    def test_never_overwrite_valid_cache_with_invalid_data(self, tmp_path, valid_snapshot):
        cache_file = tmp_path / "rates.json"
        cache = RateCache(cache_file)

        # 1. Save valid cache
        assert cache.save(valid_snapshot) is True

        # 2. Attempt to save invalid snapshot
        invalid_snapshot = RateSnapshot(
            snapshot_date=date(2026, 11, 5),
            source_name="Unknown",
            rates={"MDL": Decimal("1.0")},  # missing all other currencies
        )
        assert cache.save(invalid_snapshot) is False

        # 3. Verify original valid snapshot remains untouched
        reloaded = cache.load()
        assert reloaded is not None
        assert reloaded.snapshot_date == valid_snapshot.snapshot_date
        assert reloaded.rates["EUR"] == Decimal("19.5432")
