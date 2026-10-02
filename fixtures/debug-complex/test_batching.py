from batching import chunked


def test_small_input_fits_one_batch():
    assert chunked([1, 2, 3, 4, 5]) == [[1, 2, 3, 4, 5]]


def test_empty_input_gives_no_batches():
    assert chunked([]) == []


def test_batch_count_for_two_hundred_entries():
    assert len(chunked(list(range(200)))) == 2
