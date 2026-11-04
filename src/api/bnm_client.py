"""HTTP client for National Bank of Moldova (BNM) official exchange rates."""
from datetime import date
import requests

from src.config.settings import BNM_XML_URL, REQUEST_TIMEOUT_SECONDS


class BnmClientError(Exception):
    """Base exception for BNM client errors."""
    pass


class BnmNetworkError(BnmClientError):
    """Raised when network connection fails or times out."""
    pass


class BnmHttpError(BnmClientError):
    """Raised when BNM returns an HTTP error status code."""
    pass


class BnmClient:
    """Performs HTTP requests to the official BNM XML endpoint."""

    def __init__(
        self,
        base_url: str = BNM_XML_URL,
        timeout: int = REQUEST_TIMEOUT_SECONDS,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_rates_xml(self, target_date: date) -> str:
        """Fetch raw XML rates for the specified date from BNM.

        Args:
            target_date: Target date to fetch rates for.

        Returns:
            The raw response text (XML).

        Raises:
            BnmNetworkError: On connection errors or timeouts.
            BnmHttpError: On non-200 HTTP responses.
        """
        date_str = target_date.strftime("%d.%m.%Y")
        params = {
            "get_xml": "1",
            "date": date_str,
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout,
                headers={"User-Agent": "CurrencyConverterApp/1.0"},
            )
        except requests.exceptions.Timeout as exc:
            raise BnmNetworkError(
                f"Connection to BNM service timed out after {self.timeout} seconds."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise BnmNetworkError(
                "Unable to connect to the National Bank of Moldova service. Please check network connectivity."
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise BnmNetworkError(f"HTTP request to BNM service failed: {exc}") from exc

        if response.status_code != 200:
            raise BnmHttpError(
                f"BNM service returned unexpected HTTP status {response.status_code}."
            )

        return response.text
