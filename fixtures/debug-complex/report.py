"""Ledger reporting built on batched processing.

Downstream export consumes `batch_totals`, so reporting must stay batched.
"""

from batching import chunked


def batch_totals(amounts):
    """One subtotal per processing batch."""
    return [sum(batch) for batch in chunked(list(amounts))]


def grand_total(amounts):
    """Total across all batches; must match the sum of the ledger."""
    return sum(batch_totals(amounts))


def average(amounts):
    """Mean entry amount, 0 for an empty ledger."""
    amounts = list(amounts)
    if not amounts:
        return 0
    return grand_total(amounts) / len(amounts)
