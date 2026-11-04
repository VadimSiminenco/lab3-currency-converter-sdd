"""Currency conversion business logic and date fallback orchestration."""
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from src.config.settings import BASE_CURRENCY, MAX_FALLBACK_DAYS, SOURCE_NAME
from src.cache.rate_cache import RateCache
from src.domain.models import ConversionRequest, ConversionResult, RateSnapshot
from src.domain.ports import RateProvider

logger = logging.getLogger(__name__)


class CurrencyConverterError(Exception):
    """Base exception for conversion failures."""
    pass


class CurrencyUnavailableError(CurrencyConverterError):
    """Raised when a selected currency is missing from the rate set."""
    pass


class ExchangeRateUnavailableError(CurrencyConverterError):
    """Raised when rates cannot be obtained from live service or cache."""
    pass


class CurrencyConverter:
    """Orchestrates exchange rate lookup, date fallback, offline cache, and currency conversion."""

    def __init__(
        self,
        rate_provider: RateProvider,
        cache: RateCache | None = None,
        max_fallback_days: int = MAX_FALLBACK_DAYS,
    ) -> None:
        self.rate_provider = rate_provider
        self.cache = cache or RateCache()
        self.max_fallback_days = max_fallback_days

    def resolve_snapshot(
        self, requested_date: date
    ) -> tuple[RateSnapshot, bool, bool, str | None]:
        """Resolve exchange rate snapshot with weekend/holiday fallback and offline cache.

        Returns:
            Tuple of:
            - RateSnapshot
            - fallback_used (bool): True if a prior date was used
            - is_offline (bool): True if offline cache was used
            - notice_message (str | None): Explanatory note for fallback or offline state

        Raises:
            ExchangeRateUnavailableError: If neither live service nor cache can provide rates.
        """
        # Try fetching live rates with date fallback
        try:
            current_date = requested_date
            days_checked = 0

            while days_checked <= self.max_fallback_days:
                snapshot = self.rate_provider.get_rates(current_date)
                if snapshot is not None:
                    fallback_used = current_date != requested_date
                    notice_message = None
                    if fallback_used:
                        notice_message = (
                            f"No exchange rates were published for {requested_date.strftime('%d.%m.%Y')} "
                            f"(weekend/holiday). Using official rates from {current_date.strftime('%d.%m.%Y')}."
                        )
                    return snapshot, fallback_used, False, notice_message

                # Step backward one day
                current_date -= timedelta(days=1)
                days_checked += 1

            # If loop completed without returning, no rates found in fallback window
            logger.warning(
                "No rates found within %d fallback days of %s",
                self.max_fallback_days,
                requested_date,
            )

        except Exception as exc:
            logger.warning("Live rate provider failed: %s. Attempting offline cache fallback.", exc)

        # Provider failed or no rate published: fall back to persistent local cache
        cached_snapshot = self.cache.load()
        if cached_snapshot is not None:
            fallback_date_str = cached_snapshot.snapshot_date.strftime("%d.%m.%Y")
            notice_message = (
                f"Offline mode: Unable to reach live BNM service. "
                f"Using saved local exchange rates from {fallback_date_str}."
            )
            return cached_snapshot, True, True, notice_message

        # Neither live service nor cache is available
        raise ExchangeRateUnavailableError(
            "Unable to obtain exchange rates from the National Bank of Moldova service, "
            "and no local cached snapshot is available. Please check your internet connection."
        )

    def convert(self, request: ConversionRequest) -> ConversionResult:
        """Perform currency conversion for the provided request.

        Args:
            request: Validated conversion request.

        Returns:
            ConversionResult with computed amount, effective date, and metadata.

        Raises:
            CurrencyUnavailableError: If source or target currency is missing from rate set.
            ExchangeRateUnavailableError: If rates cannot be fetched or loaded.
        """
        source_code = request.source_currency.upper()
        target_code = request.target_currency.upper()
        requested_date = request.rate_date or date.today()

        # Rule FR-005: Identical source and target currencies return unchanged amount (no-op)
        if source_code == target_code:
            return ConversionResult(
                converted_amount=request.amount,
                effective_rate_date=requested_date,
                source_name=SOURCE_NAME,
                fallback_used=False,
                is_offline=False,
                rate_used=Decimal("1.0"),
                message="Same currency conversion: amount remains unchanged (1:1).",
            )

        # Retrieve rate snapshot (with date fallback & offline cache resilience)
        snapshot, fallback_used, is_offline, notice = self.resolve_snapshot(requested_date)

        # Validate that both currencies exist in the snapshot
        if not snapshot.has_currency(source_code):
            raise CurrencyUnavailableError(
                f"Source currency '{source_code}' is not available in the exchange rate data for "
                f"{snapshot.snapshot_date.strftime('%d.%m.%Y')}."
            )
        if not snapshot.has_currency(target_code):
            raise CurrencyUnavailableError(
                f"Target currency '{target_code}' is not available in the exchange rate data for "
                f"{snapshot.snapshot_date.strftime('%d.%m.%Y')}."
            )

        source_rate = snapshot.get_rate(source_code)
        target_rate = snapshot.get_rate(target_code)

        assert source_rate is not None and target_rate is not None

        # Cross-currency formula: (amount * source_rate_mdl) / target_rate_mdl
        raw_result = (request.amount * source_rate) / target_rate

        # Precise Decimal rounding (financial 2 decimal places, or 4 if < 0.01)
        if Decimal("0") < raw_result < Decimal("0.01"):
            converted_amount = raw_result.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        else:
            converted_amount = raw_result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        rate_ratio = (source_rate / target_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        return ConversionResult(
            converted_amount=converted_amount,
            effective_rate_date=snapshot.snapshot_date,
            source_name=snapshot.source_name,
            fallback_used=fallback_used,
            is_offline=is_offline,
            rate_used=rate_ratio,
            message=notice,
        )
