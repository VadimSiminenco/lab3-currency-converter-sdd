"""Input validation logic for currency conversion requests."""
from decimal import Decimal, InvalidOperation
from typing import Any
from src.config.settings import SUPPORTED_CURRENCIES


def validate_amount(amount_raw: Any) -> tuple[Decimal | None, str | None]:
    """Validate and parse user-entered amount.

    Args:
        amount_raw: The raw input for amount (string, number, or None).

    Returns:
        A tuple of (parsed_decimal, error_message).
        If validation succeeds, error_message is None.
        If validation fails, parsed_decimal is None.
    """
    if amount_raw is None:
        return None, "Amount is required. Please enter an amount."

    amount_str = str(amount_raw).strip()
    if not amount_str:
        return None, "Amount is required. Please enter an amount."

    # Normalize comma to dot if used as decimal separator
    normalized = amount_str.replace(",", ".")

    try:
        val = Decimal(normalized)
    except (InvalidOperation, ValueError):
        return (
            None,
            f"Invalid amount format '{amount_str}'. Please enter a valid number (e.g. 100 or 25.50).",
        )

    if not val.is_finite():
        return None, "Amount must be a finite positive number."

    if val == Decimal("0"):
        return None, "Amount must be greater than zero."

    if val < Decimal("0"):
        return None, "Amount must be greater than zero. Negative amounts are not allowed."

    return val, None


def is_amount_valid(amount_raw: Any) -> bool:
    """Helper to quickly check if an amount is valid without error message."""
    val, err = validate_amount(amount_raw)
    return err is None and val is not None


def validate_request(
    amount_raw: Any,
    source_curr: str | None,
    target_curr: str | None,
) -> list[str]:
    """Validate all fields required for a conversion request.

    Args:
        amount_raw: Raw amount input.
        source_curr: Source currency code.
        target_curr: Target currency code.

    Returns:
        List of validation error messages. Empty list indicates valid inputs.
    """
    errors: list[str] = []

    _, amount_err = validate_amount(amount_raw)
    if amount_err:
        errors.append(amount_err)

    if not source_curr or not str(source_curr).strip():
        errors.append("Source currency must be selected.")
    elif source_curr.upper() not in SUPPORTED_CURRENCIES:
        errors.append(f"Source currency '{source_curr}' is not supported.")

    if not target_curr or not str(target_curr).strip():
        errors.append("Target currency must be selected.")
    elif target_curr.upper() not in SUPPORTED_CURRENCIES:
        errors.append(f"Target currency '{target_curr}' is not supported.")

    return errors
