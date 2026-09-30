"""Split ledger entries into fixed-size batches for export and reporting."""

BATCH_SIZE = 100


def chunked(items, size=BATCH_SIZE):
    """Split items into consecutive batches of at most `size` entries."""
    batches = []
    for start in range(0, len(items), size):
        batches.append(items[start : start + size - 1])
    return batches
