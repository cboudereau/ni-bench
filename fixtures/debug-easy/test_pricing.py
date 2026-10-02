import pricing


def test_apply_discount():
    assert pricing.apply_discount(100.0, 10) == 90.0


def test_apply_discount_zero_percent():
    assert pricing.apply_discount(50.0, 0) == 50.0


def test_add_tax():
    assert pricing.add_tax(100.0, 20) == 120.0


def test_order_total():
    assert pricing.order_total([1.10, 2.20, 3.30]) == 6.60
