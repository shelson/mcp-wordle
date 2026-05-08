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
async def test_register_player(client):
    result = await client.call_tool("register_player", {})
    data = result.structured_content
    assert data["player_token"] is not None
    assert len(data["player_token"]) > 0


@pytest.mark.asyncio
async def test_list_active_games(client):
    await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    result = await client.call_tool("list_active_games", {"player_token": pt})
    data = result.structured_content
    assert len(data["games"]) >= 1


@pytest.mark.asyncio
async def test_list_active_games_excludes_archived(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN})
    gid = g.structured_content["game_id"]
    await client.call_tool("archive_game", {"admin_token": ADMIN, "game_id": gid})
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    result = await client.call_tool("list_active_games", {"player_token": pt})
    game_ids = [game["game_id"] for game in result.structured_content["games"]]
    assert gid not in game_ids


@pytest.mark.asyncio
async def test_start_game(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    result = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    data = result.structured_content
    assert data["session_id"] is not None
    assert data["game_id"] == gid


@pytest.mark.asyncio
async def test_start_game_invalid_player_token(client):
    with pytest.raises(Exception):
        await client.call_tool("start_game", {"game_id": "some-id", "player_token": "bad-token"})


@pytest.mark.asyncio
async def test_make_guess_correct(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    result = await client.call_tool(
        "make_guess", {"session_id": sid, "guess": "SLATE", "player_token": pt}
    )
    data = result.structured_content
    assert data["is_complete"] is True
    assert data["is_won"] is True
    assert data["board"] is not None


@pytest.mark.asyncio
async def test_make_guess_incorrect_continues(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    result = await client.call_tool(
        "make_guess", {"session_id": sid, "guess": "CRANE", "player_token": pt}
    )
    data = result.structured_content
    assert data["is_complete"] is False
    assert data["is_won"] is False
    assert data["guess_num"] == 1


@pytest.mark.asyncio
async def test_make_guess_invalid_word_rejected(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    with pytest.raises(Exception):
        await client.call_tool(
            "make_guess", {"session_id": sid, "guess": "ZZZZZ", "player_token": pt}
        )


@pytest.mark.asyncio
async def test_make_guess_completed_session_rejected(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    await client.call_tool(
        "make_guess", {"session_id": sid, "guess": "SLATE", "player_token": pt}
    )
    with pytest.raises(Exception):
        await client.call_tool(
            "make_guess", {"session_id": sid, "guess": "CRANE", "player_token": pt}
        )


@pytest.mark.asyncio
async def test_get_my_stats(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    await client.call_tool(
        "make_guess", {"session_id": sid, "guess": "SLATE", "player_token": pt}
    )
    result = await client.call_tool("get_my_stats", {"player_token": pt})
    data = result.structured_content
    assert data["games_played"] == 1
    assert data["games_won"] == 1
    assert data["win_rate"] == 100.0


@pytest.mark.asyncio
async def test_get_game_result(client):
    g = await client.call_tool("create_game", {"admin_token": ADMIN, "word": "SLATE"})
    gid = g.structured_content["game_id"]
    reg = await client.call_tool("register_player", {})
    pt = reg.structured_content["player_token"]
    sess = await client.call_tool("start_game", {"game_id": gid, "player_token": pt})
    sid = sess.structured_content["session_id"]
    await client.call_tool(
        "make_guess", {"session_id": sid, "guess": "SLATE", "player_token": pt}
    )
    result = await client.call_tool(
        "get_game_result", {"session_id": sid, "player_token": pt}
    )
    data = result.structured_content
    assert data["is_won"] is True
    assert data["guess_count"] == 1
    assert data["word"] == "SLATE"
