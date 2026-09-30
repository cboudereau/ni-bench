"""Order pricing helpers."""


def apply_discount(price, percent):
    """Return the price reduced by the given percentage."""
    return round(price * (1 + percent / 100), 2)


def add_tax(price, rate):
    """Return the price increased by the given tax rate percentage."""
    return round(price * (1 + rate / 100), 2)


def order_total(prices):
    """Return the rounded sum of line prices."""
    return round(sum(prices), 2)
