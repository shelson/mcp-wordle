import json
import pytest
from src.wordle_server.storage import (
    create_game,
    get_game,
    archive_game,
    list_games,
    create_session,
    get_session,
    get_active_session,
    add_guess,
    _decode_hash,
)


@pytest.fixture
async def redis_db(fake_redis):
    async with fake_redis(mode="redis") as r:
        await r.flushdb()
        yield r


@pytest.fixture
def admin_token():
    return "admin-123"


# --- Game CRUD ---


@pytest.mark.asyncio
async def test_create_game(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    assert game["game_id"] is not None
    assert game["word"] == "SLATE"
    assert game["status"] == "active"
    assert game["created_by"] == admin_token
    assert game["play_count"] == 0


@pytest.mark.asyncio
async def test_get_game_exists(redis_db, admin_token):
    game = await create_game(redis_db, "CRANE", admin_token)
    fetched = await get_game(redis_db, game["game_id"])
    assert fetched is not None
    assert fetched["word"] == "CRANE"


@pytest.mark.asyncio
async def test_get_game_nonexistent(redis_db):
    result = await get_game(redis_db, "nonexistent-id")
    assert result is None


@pytest.mark.asyncio
async def test_archive_game(redis_db, admin_token):
    game = await create_game(redis_db, "ADIEU", admin_token)
    result = await archive_game(redis_db, game["game_id"], True)
    assert result is True
    fetched = await get_game(redis_db, game["game_id"])
    assert fetched["status"] == "archived"


@pytest.mark.asyncio
async def test_archive_game_unarchive(redis_db, admin_token):
    game = await create_game(redis_db, "ADIEU", admin_token)
    await archive_game(redis_db, game["game_id"], True)
    await archive_game(redis_db, game["game_id"], False)
    fetched = await get_game(redis_db, game["game_id"])
    assert fetched["status"] == "active"


@pytest.mark.asyncio
async def test_archive_game_nonexistent(redis_db):
    result = await archive_game(redis_db, "nope", True)
    assert result is False


@pytest.mark.asyncio
async def test_list_games_active_only(redis_db, admin_token):
    g1 = await create_game(redis_db, "SLATE", admin_token)
    g2 = await create_game(redis_db, "CRANE", admin_token)
    await archive_game(redis_db, g2["game_id"], True)
    games = await list_games(redis_db, include_archived=False)
    assert len(games) == 1
    assert games[0]["game_id"] == g1["game_id"]


@pytest.mark.asyncio
async def test_list_games_include_archived(redis_db, admin_token):
    await create_game(redis_db, "SLATE", admin_token)
    g2 = await create_game(redis_db, "CRANE", admin_token)
    await archive_game(redis_db, g2["game_id"], True)
    games = await list_games(redis_db, include_archived=True)
    assert len(games) == 2


# --- Session CRUD ---


@pytest.mark.asyncio
async def test_create_session(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    assert session["session_id"] is not None
    assert session["game_id"] == game["game_id"]
    assert session["player_token"] == "player-1"
    assert session["is_complete"] is False
    assert session["guesses"] == []


@pytest.mark.asyncio
async def test_create_session_duplicate_returns_existing(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    s1 = await create_session(redis_db, game["game_id"], "player-1")
    s2 = await create_session(redis_db, game["game_id"], "player-1")
    assert s2["session_id"] == s1["session_id"]


@pytest.mark.asyncio
async def test_get_active_session(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    active = await get_active_session(redis_db, game["game_id"], "player-1")
    assert active is not None
    assert active["session_id"] == session["session_id"]


@pytest.mark.asyncio
async def test_get_active_session_none(redis_db):
    active = await get_active_session(redis_db, "game-x", "player-x")
    assert active is None


@pytest.mark.asyncio
async def test_add_guess_correct(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    updated, correct = await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")
    assert correct is True
    assert updated["is_complete"] is True
    assert updated["is_won"] is True
    assert len(updated["guesses"]) == 1
    assert updated["guess_count"] == 1


@pytest.mark.asyncio
async def test_add_guess_incorrect(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    updated, correct = await add_guess(redis_db, session["session_id"], "CRANE", "SLATE")
    assert correct is False
    assert updated["is_complete"] is False
    assert len(updated["guesses"]) == 1


@pytest.mark.asyncio
async def test_add_guess_sixth_guess_wrong_ends_game(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    for word in ["CRANE", "ADIEU", "AUDIO", "STARE", "RAISE"]:
        await add_guess(redis_db, session["session_id"], word, "SLATE")
    updated, correct = await add_guess(redis_db, session["session_id"], "SPLIT", "SLATE")
    assert correct is False
    assert updated["is_complete"] is True
    assert updated["is_won"] is False
    assert updated["guess_count"] == 6


@pytest.mark.asyncio
async def test_add_guess_updates_game_and_player_stats(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    await redis_db.hset(
        "players:player-1",
        mapping={
            "token": "player-1",
            "games_played": "0",
            "games_won": "0",
            "current_streak": "0",
            "max_streak": "0",
            "total_guesses": "0",
            "total_solve_time": "0.0",
            "avg_solve_time": "0.0",
            "guess_dist": "{}",
        },
    )
    _, _ = await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")

    fetched_game = await get_game(redis_db, game["game_id"])
    assert fetched_game["play_count"] == 1
    assert fetched_game["win_count"] == 1

    player = await redis_db.hgetall("players:player-1")
    assert player[b"games_played"] == b"1"
    assert player[b"games_won"] == b"1"
    assert player[b"current_streak"] == b"1"
    assert player[b"max_streak"] == b"1"


@pytest.mark.asyncio
async def test_add_guess_on_completed_session_raises(redis_db, admin_token):
    import pytest
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")
    with pytest.raises(ValueError, match="already complete"):
        await add_guess(redis_db, session["session_id"], "CRANE", "SLATE")


@pytest.mark.asyncio
async def test_decode_hash():
    raw = {b"key1": b"value1", b"num": b"5"}
    result = _decode_hash(raw)
    assert result == {"key1": "value1", "num": "5"}


@pytest.mark.asyncio
async def test_add_guess_nonexistent_session(redis_db):
    with pytest.raises(ValueError, match="Session not found"):
        await add_guess(redis_db, "fake-session-id", "SLATE", "SLATE")


@pytest.mark.asyncio
async def test_get_session_nonexistent(redis_db):
    result = await get_session(redis_db, "fake-session-id")
    assert result is None


@pytest.mark.asyncio
async def test_list_games_includes_total_guesses_as_int(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    games = await list_games(redis_db, include_archived=True)
    assert isinstance(games[0]["total_guesses"], int)
    assert games[0]["total_guesses"] == 0
