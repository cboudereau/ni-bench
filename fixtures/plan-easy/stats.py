"""Text statistics for the wordstats CLI."""

import re
from collections import Counter

WORD_RE = re.compile(r"[A-Za-z']+")


def tokenize(text):
    """Lower-cased word tokens, apostrophes kept."""
    return [word.lower() for word in WORD_RE.findall(text)]


def count_lines(text):
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def count_words(text):
    return len(tokenize(text))


def count_chars(text):
    return len(text)


def top_words(text, n):
    """The n most frequent words, ties broken alphabetically."""
    counts = Counter(tokenize(text))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:n]


def summarize(text):
    return {
        "lines": count_lines(text),
        "words": count_words(text),
        "chars": count_chars(text),
    }
