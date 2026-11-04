"""Persistent local JSON cache for exchange rates."""
import json
import logging
from pathlib import Path
from typing import Optional

from src.config.settings import DEFAULT_CACHE_FILE, SUPPORTED_CURRENCIES
from src.domain.models import RateSnapshot

logger = logging.getLogger(__name__)


class RateCache:
    """Manages persistent caching of exchange rate snapshots in local JSON storage."""

    def __init__(self, cache_file_path: Path = DEFAULT_CACHE_FILE) -> None:
        self.cache_file_path = Path(cache_file_path)

    def load(self) -> Optional[RateSnapshot]:
        """Load and validate the cached exchange rate snapshot.

        Returns:
            The cached RateSnapshot if valid, or None if the cache does not exist,
            is corrupted, or does not meet validation criteria.
        """
        if not self.cache_file_path.exists():
            return None

        try:
            with open(self.cache_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.warning("Cache file did not contain a valid JSON object.")
                return None

            snapshot = RateSnapshot.from_dict(data)

            # Ensure all supported currencies are present in the cached snapshot
            for code in SUPPORTED_CURRENCIES:
                if not snapshot.has_currency(code):
                    logger.warning("Cached snapshot is missing required currency '%s'.", code)
                    return None

            return snapshot
        except Exception as exc:
            logger.warning("Failed to load or parse rate cache: %s", exc)
            return None

    def save(self, snapshot: RateSnapshot) -> bool:
        """Persist a valid RateSnapshot to disk.

        Ensures that invalid or incomplete snapshots never overwrite a valid cache.

        Args:
            snapshot: The RateSnapshot to persist.

        Returns:
            True if the snapshot was successfully written, False otherwise.
        """
        if not snapshot or not snapshot.rates:
            logger.warning("Refusing to save empty or invalid rate snapshot to cache.")
            return False

        # Verify that all supported currencies exist with valid positive values
        for code in SUPPORTED_CURRENCIES:
            rate = snapshot.get_rate(code)
            if rate is None or not rate.is_finite() or rate <= 0:
                logger.warning(
                    "Refusing to save snapshot missing valid rate for required currency '%s'.", code
                )
                return False

        try:
            self.cache_file_path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = self.cache_file_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, indent=2, ensure_ascii=False)

            temp_path.replace(self.cache_file_path)
            return True
        except Exception as exc:
            logger.error("Failed to write rate cache to '%s': %s", self.cache_file_path, exc)
            return False
