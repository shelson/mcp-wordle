import pytest
from wordle_server.auth import (
    validate_admin_token,
    validate_player_token,
    register_player,
    create_admin_token,
    init_admin_token,
)


@pytest.fixture
async def clean_redis(fake_redis):
    async with fake_redis(mode="redis") as r:
        await r.flushdb()
        yield r


@pytest.mark.asyncio
async def test_init_admin_token(clean_redis):
    await init_admin_token(clean_redis, "admin-token-123")
    assert await clean_redis.sismember("admin_tokens", "admin-token-123")


@pytest.mark.asyncio
async def test_validate_admin_token_valid(clean_redis):
    await clean_redis.sadd("admin_tokens", "admin-token-abc")
    result = await validate_admin_token(clean_redis, "admin-token-abc")
    assert result is True


@pytest.mark.asyncio
async def test_validate_admin_token_invalid(clean_redis):
    result = await validate_admin_token(clean_redis, "nonexistent")
    assert result is False


@pytest.mark.asyncio
async def test_validate_player_token_valid(clean_redis):
    await clean_redis.hset(
        "players:player-xyz",
        mapping={"token": "player-xyz", "games_played": "0"},
    )
    result = await validate_player_token(clean_redis, "player-xyz")
    assert result is True


@pytest.mark.asyncio
async def test_validate_player_token_invalid(clean_redis):
    result = await validate_player_token(clean_redis, "nope")
    assert result is False


@pytest.mark.asyncio
async def test_register_player_creates_token(clean_redis):
    token = await register_player(clean_redis)
    assert token is not None
    assert len(token) > 0
    data = await clean_redis.hgetall(f"players:{token}")
    assert data[b"token"] == token.encode()
    assert data[b"games_played"] == b"0"
    assert data[b"games_won"] == b"0"


@pytest.mark.asyncio
async def test_create_admin_token(clean_redis):
    token = await create_admin_token(clean_redis)
    assert token is not None
    assert await clean_redis.sismember("admin_tokens", token)
