"""Unit tests for amount and request validation logic."""
from decimal import Decimal
import pytest

from src.domain.validation import is_amount_valid, validate_amount, validate_request


class TestAmountValidation:
    """Tests for validate_amount function."""

    @pytest.mark.parametrize("empty_input", ["", "   ", None])
    def test_reject_empty_amount(self, empty_input):
        val, err = validate_amount(empty_input)
        assert val is None
        assert err is not None
        assert "required" in err.lower()
        assert is_amount_valid(empty_input) is False

    @pytest.mark.parametrize("zero_input", ["0", "0.0", "0,00", "0.000", 0, Decimal("0")])
    def test_reject_zero_amount(self, zero_input):
        val, err = validate_amount(zero_input)
        assert val is None
        assert err is not None
        assert "greater than zero" in err.lower()
        assert is_amount_valid(zero_input) is False

    @pytest.mark.parametrize("neg_input", ["-1", "-0.01", "-100,50", -5, Decimal("-10")])
    def test_reject_negative_amount(self, neg_input):
        val, err = validate_amount(neg_input)
        assert val is None
        assert err is not None
        assert "greater than zero" in err.lower() or "negative" in err.lower()
        assert is_amount_valid(neg_input) is False

    @pytest.mark.parametrize("malformed", [
        "abc", "12,3x", "12..34", "12.3.4", "$100", "10 000", "12a", "one hundred"
    ])
    def test_reject_alphabetic_and_malformed(self, malformed):
        val, err = validate_amount(malformed)
        assert val is None
        assert err is not None
        assert "invalid amount format" in err.lower()
        assert is_amount_valid(malformed) is False

    @pytest.mark.parametrize("non_finite", [
        "NaN", "nan", "NAN", "Infinity", "-Infinity", "+Infinity", "inf", "-inf"
    ])
    def test_reject_nan_and_infinity(self, non_finite):
        val, err = validate_amount(non_finite)
        assert val is None
        assert err is not None
        assert "finite" in err.lower() or "invalid" in err.lower()
        assert is_amount_valid(non_finite) is False

    @pytest.mark.parametrize("valid_input, expected", [
        ("100", Decimal("100")),
        ("1", Decimal("1")),
        ("100.50", Decimal("100.50")),
        ("0.01", Decimal("0.01")),
        ("25,50", Decimal("25.50")),
        ("1234.5678", Decimal("1234.5678")),
        (50, Decimal("50")),
        (Decimal("75.25"), Decimal("75.25")),
    ])
    def test_accept_valid_amounts(self, valid_input, expected):
        val, err = validate_amount(valid_input)
        assert err is None
        assert val == expected
        assert is_amount_valid(valid_input) is True


class TestRequestValidation:
    """Tests for validate_request function."""

    def test_valid_request(self):
        errors = validate_request("100", "USD", "MDL")
        assert errors == []

    def test_missing_currencies(self):
        errors_source = validate_request("100", "", "MDL")
        assert any("source" in err.lower() for err in errors_source)

        errors_target = validate_request("100", "USD", None)
        assert any("target" in err.lower() for err in errors_target)

    def test_unsupported_currency(self):
        errors = validate_request("100", "JPY", "CAD")
        assert any("JPY" in err for err in errors)
        assert any("CAD" in err for err in errors)

    def test_combined_errors(self):
        errors = validate_request("-50", "INVALID", "")
        assert len(errors) == 3
