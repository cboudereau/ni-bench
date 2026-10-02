import stats


def test_tokenize_lowercases_and_keeps_apostrophes():
    assert stats.tokenize("Don't Stop me now") == ["don't", "stop", "me", "now"]


def test_count_lines_without_trailing_newline():
    assert stats.count_lines("a\nb") == 2


def test_count_lines_with_trailing_newline():
    assert stats.count_lines("a\nb\n") == 2


def test_count_lines_empty():
    assert stats.count_lines("") == 0


def test_count_words():
    assert stats.count_words("one two, three!") == 3


def test_top_words_ranks_by_count_then_alphabet():
    assert stats.top_words("b b a a c", 2) == [("a", 2), ("b", 2)]


def test_summarize_keys():
    assert stats.summarize("hi\n") == {"lines": 1, "words": 1, "chars": 3}
