from report import average, batch_totals, grand_total


def test_grand_total_small_ledger():
    amounts = list(range(1, 51))
    assert grand_total(amounts) == sum(amounts)


def test_batch_totals_small_ledger():
    assert batch_totals([10, 20, 30]) == [60]


def test_average_small_ledger():
    assert average([10, 20, 30]) == 20


def test_average_empty_ledger():
    assert average([]) == 0
