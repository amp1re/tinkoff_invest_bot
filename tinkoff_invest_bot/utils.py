from decimal import Decimal


def cast_money(v):
    """
    Converts a money value from the Tinkoff Invest API format to a Decimal.
    The Tinkoff Invest API represents money values with separate fields for units and nanos,
    where 'units' is the integer part and 'nanos' is the fractional part in nanoseconds.

    Parameters
    ----------
    v : object
        An object with 'units' and 'nano' attributes representing a money value.

    Returns
    -------
    Decimal
        The combined value of 'units' and 'nano' as a Decimal.

    Raises
    ------
    ValueError
        If the input money format is invalid or cannot be converted to Decimal.

    Examples
    --------
    >>> money_value = MoneyValue(units=1, nano=500000000)  # Example object similar to API response
    >>> cast_money(money_value)
    Decimal('1.5')

    Note: The actual MoneyValue object structure may vary based on the Tinkoff Invest API.
    """
    try:
        units = Decimal(v.units)
        nano = Decimal(v.nano)
    except (TypeError, ValueError) as exc:
        # Re-raise the exception with a custom message, linking the cause.
        raise ValueError("Invalid money format") from exc
    return units + nano / Decimal(1e9)
