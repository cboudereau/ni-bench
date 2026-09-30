"""Hidden post-check tests — never shipped to the arm workspace.

They pin the root cause: every entry must survive batching across boundaries,
so a fix that bypasses or compensates in report.py still fails here.
"""

from batching import chunked
from report import grand_total


def test_chunked_preserves_every_item_across_boundaries():
    items = list(range(250))
    flattened = [item for batch in chunked(items) for item in batch]
    assert flattened == items


def test_grand_total_matches_direct_sum_beyond_batch_size():
    amounts = list(range(1, 251))
    assert grand_total(amounts) == sum(amounts)


def test_grand_total_exact_at_batch_boundary():
    amounts = [1] * 100
    assert grand_total(amounts) == 100
