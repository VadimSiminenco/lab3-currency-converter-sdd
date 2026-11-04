"""Unit tests for BNM XML feed parser."""
from datetime import date
from decimal import Decimal
from pathlib import Path
import pytest

from src.parsing.xml_parser import XmlParsingError, parse_bnm_xml

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


class TestXmlParser:
    """Tests for parse_bnm_xml function."""

    def test_parse_valid_feed_fixture(self):
        fixture_path = FIXTURES_DIR / "valid_rate_feed.xml"
        content = fixture_path.read_text(encoding="utf-8")

        snapshot = parse_bnm_xml(content)
        assert snapshot is not None
        assert snapshot.snapshot_date == date(2026, 11, 4)
        assert snapshot.source_name == "Official exchange rates"

        # Base currency MDL
        assert snapshot.rates["MDL"] == Decimal("1.0")

        # Standard currencies with Nominal 1
        assert snapshot.rates["EUR"] == Decimal("19.5432")
        assert snapshot.rates["USD"] == Decimal("18.1250")
        assert snapshot.rates["RON"] == Decimal("3.9280")
        assert snapshot.rates["GBP"] == Decimal("23.4500")

        # Currency with Nominal 10: Value 4.3500 / 10 = 0.4350
        assert snapshot.rates["UAH"] == Decimal("0.4350")

    def test_parse_iso_date_format(self):
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <ValCurs Date="2026-11-04" name="National Bank of Moldova">
            <Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>18.00</Value></Valute>
        </ValCurs>'''
        snapshot = parse_bnm_xml(xml)
        assert snapshot is not None
        assert snapshot.snapshot_date == date(2026, 11, 4)

    def test_empty_valute_list_returns_none(self):
        """Weekend or holiday feed with no published rates returns None."""
        xml = '''<?xml version="1.0" encoding="utf-8"?>
        <ValCurs Date="08.11.2026" name="Official exchange rates">
        </ValCurs>'''
        snapshot = parse_bnm_xml(xml)
        assert snapshot is None

    @pytest.mark.parametrize("empty_payload", ["", "   ", None])
    def test_empty_xml_raises_error(self, empty_payload):
        with pytest.raises(XmlParsingError, match="Empty XML response"):
            parse_bnm_xml(empty_payload)

    def test_malformed_xml_syntax(self):
        with pytest.raises(XmlParsingError, match="Malformed XML syntax"):
            parse_bnm_xml("<ValCurs><unclosed></ValCurs>")

    def test_invalid_root_tag(self):
        with pytest.raises(XmlParsingError, match="Unexpected root element"):
            parse_bnm_xml("<WrongRoot Date='01.01.2026'></WrongRoot>")

    def test_missing_date_in_root(self):
        with pytest.raises(XmlParsingError, match="Missing 'Date'"):
            parse_bnm_xml("<ValCurs name='Rates'><Valute><CharCode>USD</CharCode></Valute></ValCurs>")

    def test_missing_char_code(self):
        xml = '''<ValCurs Date="01.01.2026"><Valute><Nominal>1</Nominal><Value>18</Value></Valute></ValCurs>'''
        with pytest.raises(XmlParsingError, match="missing CharCode"):
            parse_bnm_xml(xml)

    def test_missing_nominal(self):
        xml = '''<ValCurs Date="01.01.2026"><Valute><CharCode>USD</CharCode><Value>18</Value></Valute></ValCurs>'''
        with pytest.raises(XmlParsingError, match="missing Nominal"):
            parse_bnm_xml(xml)

    def test_missing_value(self):
        xml = '''<ValCurs Date="01.01.2026"><Valute><CharCode>USD</CharCode><Nominal>1</Nominal></Valute></ValCurs>'''
        with pytest.raises(XmlParsingError, match="missing Value"):
            parse_bnm_xml(xml)

    @pytest.mark.parametrize("bad_nominal", ["0", "-1", "abc", "NaN", "Infinity", "-Infinity"])
    def test_invalid_nominal_values(self, bad_nominal):
        xml = f'''<ValCurs Date="01.01.2026"><Valute><CharCode>USD</CharCode><Nominal>{bad_nominal}</Nominal><Value>18.0</Value></Valute></ValCurs>'''
        with pytest.raises(XmlParsingError):
            parse_bnm_xml(xml)

    @pytest.mark.parametrize("bad_val", ["0", "-10", "xyz", "NaN", "Infinity", "-Infinity"])
    def test_invalid_value_entries(self, bad_val):
        xml = f'''<ValCurs Date="01.01.2026"><Valute><CharCode>USD</CharCode><Nominal>1</Nominal><Value>{bad_val}</Value></Valute></ValCurs>'''
        with pytest.raises(XmlParsingError):
            parse_bnm_xml(xml)

    def test_comma_decimal_separator_support(self):
        xml = '''<ValCurs Date="01.01.2026"><Valute><CharCode>EUR</CharCode><Nominal>1</Nominal><Value>19,5432</Value></Valute></ValCurs>'''
        snapshot = parse_bnm_xml(xml)
        assert snapshot is not None
        assert snapshot.rates["EUR"] == Decimal("19.5432")
