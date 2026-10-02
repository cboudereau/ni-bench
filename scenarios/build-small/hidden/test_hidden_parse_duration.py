"""Hidden edge-case tests — never shipped to the arm workspace.

Every case follows from the specification in the prompt; nothing here goes
beyond the stated grammar.
"""

import pytest

from timefmt import parse_duration


def test_single_hour_unit():
    assert parse_duration("2h") == 7200


def test_single_minute_unit():
    assert parse_duration("45m") == 2700


def test_all_three_units():
    assert parse_duration("1h2m3s") == 3723


def test_zero_count_is_valid():
    assert parse_duration("0s") == 0


def test_empty_string_rejected():
    with pytest.raises(ValueError):
        parse_duration("")


def test_number_without_unit_rejected():
    with pytest.raises(ValueError):
        parse_duration("90")


def test_repeated_unit_rejected():
    with pytest.raises(ValueError):
        parse_duration("1h2h")


def test_out_of_order_units_rejected():
    with pytest.raises(ValueError):
        parse_duration("30m1h")


def test_result_is_int():
    assert isinstance(parse_duration("90s"), int)
