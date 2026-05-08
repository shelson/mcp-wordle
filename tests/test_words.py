import pytest
from src.wordle_server.words import (
    _get_word_set,
    is_valid_word,
    pick_random_word,
)


def test_get_word_set_returns_five_letter_uppercase():
    words = _get_word_set()
    assert len(words) > 100
    for w in words:
        assert len(w) == 5
        assert w.isalpha()
        assert w == w.upper()


def test_is_valid_word_accepts_valid_word(sample_words):
    assert is_valid_word("SLATE", sample_words)
    assert is_valid_word("slate", sample_words)
    assert is_valid_word("SlAtE", sample_words)


def test_is_valid_word_rejects_wrong_length(sample_words):
    assert not is_valid_word("SLAT", sample_words)
    assert not is_valid_word("SLATER", sample_words)


def test_is_valid_word_rejects_non_alpha(sample_words):
    assert not is_valid_word("SL4TE", sample_words)
    assert not is_valid_word("SL TE", sample_words)


def test_is_valid_word_rejects_not_in_set(sample_words):
    assert not is_valid_word("ZZZZZ", sample_words)


def test_pick_random_word_returns_from_set():
    word_set = {"SLATE", "CRANE", "ADIEU"}
    for _ in range(20):
        word = pick_random_word(word_set)
        assert word in word_set


def test_pick_random_word_handles_single_word_set():
    word_set = {"SLATE"}
    word = pick_random_word(word_set)
    assert word == "SLATE"
