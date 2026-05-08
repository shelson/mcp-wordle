import pytest
from fakeredis import aioredis


@pytest.fixture
def fake_redis():
    return aioredis.FakeRedis


@pytest.fixture
def sample_words():
    """Small controlled word set for testing."""
    return {"SLATE", "CRANE", "ADIEU", "STARE", "AUDIO", "RAISE", "SPLIT", "WORLD"}
