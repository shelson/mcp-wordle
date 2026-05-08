import random
from english_words import get_english_words_set

_word_cache: set[str] | None = None


def _get_word_set() -> set[str]:
    global _word_cache
    if _word_cache is None:
        all_words = get_english_words_set(["web2"])
        _word_cache = {w.upper() for w in all_words if len(w) == 5 and w.isalpha()}
    return _word_cache


def is_valid_word(word: str, word_set: set[str] | None = None) -> bool:
    if word_set is None:
        word_set = _get_word_set()
    return len(word) == 5 and word.isalpha() and word.upper() in word_set


def pick_random_word(word_set: set[str] | None = None) -> str:
    if word_set is None:
        word_set = _get_word_set()
    return random.choice(list(word_set))
