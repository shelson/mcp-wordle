import pytest
from wordle_server.server import create_server


@pytest.fixture
async def redis_db(fake_redis):
    import redis.asyncio as redis
    async with fake_redis(mode="redis") as r:
        await r.flushdb()
        await r.sadd("admin_tokens", "admin-test-token")
        yield r


@pytest.fixture
async def client(redis_db):
    from fastmcp.client import Client
    server = create_server(redis_db)
    async with Client(server) as c:
        yield c


ADMIN = "admin-test-token"


@pytest.mark.asyncio
async def test_create_game_random_word(client):
    result = await client.call_tool("create_game", {"admin_token": ADMIN})
    data = result.structured_content
    assert data["game_id"] is not None
    assert len(data["word"]) == 5
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_create_game_specific_word(client):
    result = await client.call_tool(
        "create_game", {"word": "SLATE", "admin_token": ADMIN}
    )
    data = result.structured_content
    assert data["word"] == "SLATE"


@pytest.mark.asyncio
async def test_create_game_invalid_admin_token(client):
    with pytest.raises(Exception):
        await client.call_tool(
            "create_game", {"word": "SLATE", "admin_token": "bad-token"}
        )


@pytest.mark.asyncio
async def test_archive_game(client):
    r1 = await client.call_tool("create_game", {"admin_token": ADMIN})
    gid = r1.structured_content["game_id"]
    r2 = await client.call_tool(
        "archive_game", {"game_id": gid, "admin_token": ADMIN}
    )
    assert r2.structured_content["status"] == "archived"


@pytest.mark.asyncio
async def test_create_admin_token(client):
    result = await client.call_tool("create_admin_token", {"admin_token": ADMIN})
    data = result.structured_content
    assert data["token"] is not None
    assert len(data["token"]) > 0


@pytest.mark.asyncio
async def test_list_games(client):
    await client.call_tool("create_game", {"admin_token": ADMIN})
    await client.call_tool("create_game", {"admin_token": ADMIN})
    result = await client.call_tool(
        "list_games", {"admin_token": ADMIN, "include_archived": False}
    )
    data = result.structured_content
    assert len(data["games"]) >= 2


@pytest.mark.asyncio
async def test_get_game_stats(client):
    r = await client.call_tool("create_game", {"admin_token": ADMIN})
    gid = r.structured_content["game_id"]
    result = await client.call_tool(
        "get_game_stats", {"game_id": gid, "admin_token": ADMIN}
    )
    data = result.structured_content
    assert data["word"] == r.structured_content["word"]
    assert data["play_count"] == 0


@pytest.mark.asyncio
async def test_get_global_stats(client):
    result = await client.call_tool("get_global_stats", {"admin_token": ADMIN})
    data = result.structured_content
    assert "total_games" in data
    assert "total_players" in data
