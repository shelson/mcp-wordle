import pytest


@pytest.fixture
def sample_words():
    """Small controlled word set for testing."""
    return {"SLATE", "CRANE", "ADIEU", "STARE", "AUDIO", "RAISE", "SPLIT", "WORLD"}
