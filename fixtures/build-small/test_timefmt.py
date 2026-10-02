import pytest

from timefmt import format_duration


def test_zero_seconds():
    assert format_duration(0) == "0s"


def test_full_mix():
    assert format_duration(3723) == "1h2m3s"


def test_zero_parts_omitted():
    assert format_duration(3600) == "1h"


def test_negative_rejected():
    with pytest.raises(ValueError):
        format_duration(-1)
