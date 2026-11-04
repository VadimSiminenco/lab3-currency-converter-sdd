"""XML parser for the National Bank of Moldova (BNM) official exchange rates feed."""
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.config.settings import BASE_CURRENCY, SOURCE_NAME
from src.domain.models import RateSnapshot


class XmlParsingError(Exception):
    """Raised when the XML feed is malformed, missing required elements, or cannot be parsed."""
    pass


def _parse_date_str(date_str: str) -> date:
    """Parse date from string in either DD.MM.YYYY or YYYY-MM-DD format."""
    date_str = date_str.strip()
    try:
        return datetime.strptime(date_str, "%d.%m.%Y").date()
    except ValueError:
        pass

    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise XmlParsingError(f"Cannot parse rate date from string: '{date_str}'") from exc


def parse_bnm_xml(xml_content: str | bytes) -> Optional[RateSnapshot]:
    """Parse BNM XML content and return a normalized RateSnapshot.

    If the XML is valid but contains no Valute entries (e.g. for an unpublished weekend/holiday),
    returns None.

    Args:
        xml_content: Raw XML response body.

    Returns:
        RateSnapshot if rates are present, None if no rates are published for this date.

    Raises:
        XmlParsingError: If XML is malformed, root element is invalid, or required fields are missing.
    """
    if not xml_content or (isinstance(xml_content, str) and not xml_content.strip()):
        raise XmlParsingError("Empty XML response received.")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as exc:
        raise XmlParsingError(f"Malformed XML syntax: {exc}") from exc

    if root.tag != "ValCurs":
        raise XmlParsingError(f"Unexpected root element '{root.tag}', expected 'ValCurs'.")

    # Extract date from attribute or child element
    raw_date = root.attrib.get("Date")
    if not raw_date:
        date_elem = root.find("Date")
        if date_elem is not None and date_elem.text:
            raw_date = date_elem.text

    if not raw_date:
        raise XmlParsingError("Missing 'Date' in ValCurs root element.")

    snapshot_date = _parse_date_str(raw_date)

    # Source name from attribute or default
    source_name = root.attrib.get("name") or SOURCE_NAME

    valute_elements = root.findall("Valute")
    if not valute_elements:
        # Date has no published rates (e.g. weekend or holiday)
        return None

    rates: dict[str, Decimal] = {
        BASE_CURRENCY: Decimal("1.0"),
    }

    for valute in valute_elements:
        char_code_elem = valute.find("CharCode")
        nominal_elem = valute.find("Nominal")
        value_elem = valute.find("Value")

        if char_code_elem is None or not char_code_elem.text:
            raise XmlParsingError("Valute element missing CharCode.")
        if nominal_elem is None or not nominal_elem.text:
            raise XmlParsingError("Valute element missing Nominal.")
        if value_elem is None or not value_elem.text:
            raise XmlParsingError("Valute element missing Value.")

        currency_code = char_code_elem.text.strip().upper()

        try:
            nominal = Decimal(nominal_elem.text.strip().replace(",", "."))
            if not nominal.is_finite() or nominal <= Decimal("0"):
                raise XmlParsingError(f"Non-positive or non-finite nominal for {currency_code}: {nominal}")
        except (InvalidOperation, ValueError) as exc:
            raise XmlParsingError(f"Invalid Nominal value for {currency_code}: {nominal_elem.text}") from exc

        try:
            value = Decimal(value_elem.text.strip().replace(",", "."))
            if not value.is_finite() or value <= Decimal("0"):
                raise XmlParsingError(f"Non-positive or non-finite rate value for {currency_code}: {value}")
        except (InvalidOperation, ValueError) as exc:
            raise XmlParsingError(f"Invalid Value for {currency_code}: {value_elem.text}") from exc

        # Normalized rate = Value / Nominal (MDL per 1 unit of foreign currency)
        rate_per_unit = value / nominal
        rates[currency_code] = rate_per_unit

    return RateSnapshot(
        snapshot_date=snapshot_date,
        source_name=source_name,
        rates=rates,
    )
