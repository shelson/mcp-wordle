import uuid
import json
from datetime import datetime, timezone

from src.wordle_server.game import MAX_GUESSES


def _decode_hash(data: dict) -> dict:
    result = {}
    for k, v in data.items():
        key = k.decode() if isinstance(k, bytes) else k
        val = v.decode() if isinstance(v, bytes) else v
        result[key] = val
    return result


# --- Game operations ---


async def create_game(redis, word: str, admin_token: str) -> dict:
    game_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await redis.hset(
        f"games:{game_id}",
        mapping={
            "game_id": game_id,
            "word": word.upper(),
            "created_at": now,
            "status": "active",
            "created_by": admin_token,
            "play_count": "0",
            "win_count": "0",
            "total_guesses": "0",
        },
    )
    return await get_game(redis, game_id)


async def get_game(redis, game_id: str) -> dict | None:
    data = await redis.hgetall(f"games:{game_id}")
    if not data:
        return None
    result = _decode_hash(data)
    result["play_count"] = int(result.get("play_count", 0))
    result["win_count"] = int(result.get("win_count", 0))
    result["total_guesses"] = int(result.get("total_guesses", 0))
    return result


async def archive_game(redis, game_id: str, archived: bool) -> bool:
    exists = await redis.exists(f"games:{game_id}")
    if not exists:
        return False
    await redis.hset(f"games:{game_id}", "status", "archived" if archived else "active")
    return True


async def list_games(redis, include_archived: bool = False) -> list[dict]:
    games = []
    async for key in redis.scan_iter("games:*"):
        data = await redis.hgetall(key)
        if data:
            game = _decode_hash(data)
            game["play_count"] = int(game.get("play_count", 0))
            game["win_count"] = int(game.get("win_count", 0))
            game["total_guesses"] = int(game.get("total_guesses", 0))
            if include_archived or game.get("status") == "active":
                games.append(game)
    return games


# --- Session operations ---


async def get_active_session(redis, game_id: str, player_token: str) -> dict | None:
    sid = await redis.get(f"active_session:{game_id}:{player_token}")
    if sid:
        if isinstance(sid, bytes):
            sid = sid.decode()
        return await get_session(redis, sid)
    return None


async def create_session(redis, game_id: str, player_token: str) -> dict:
    existing = await get_active_session(redis, game_id, player_token)
    if existing:
        return existing

    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await redis.hset(
        f"sessions:{session_id}",
        mapping={
            "session_id": session_id,
            "game_id": game_id,
            "player_token": player_token,
            "started_at": now,
            "completed_at": "",
            "guesses": "[]",
            "is_complete": "0",
            "is_won": "0",
            "guess_count": "0",
            "elapsed_seconds": "0.0",
        },
    )
    await redis.set(f"active_session:{game_id}:{player_token}", session_id)
    await redis.sadd(f"player_sessions:{player_token}", session_id)
    return await get_session(redis, session_id)


async def get_session(redis, session_id: str) -> dict | None:
    data = await redis.hgetall(f"sessions:{session_id}")
    if not data:
        return None
    session = _decode_hash(data)
    session["guesses"] = json.loads(session.get("guesses", "[]"))
    session["is_complete"] = session.get("is_complete") == "1"
    session["is_won"] = session.get("is_won") == "1"
    session["guess_count"] = int(session.get("guess_count", 0))
    session["elapsed_seconds"] = float(session.get("elapsed_seconds", 0.0))
    return session


async def add_guess(redis, session_id: str, guess: str, target: str) -> tuple[dict, bool]:
    session = await get_session(redis, session_id)
    if session is None:
        raise ValueError("Session not found")
    if session["is_complete"]:
        raise ValueError("Game already complete")

    guesses: list = session["guesses"]
    guesses.append(guess.upper())
    is_correct = guess.upper() == target.upper()
    is_last = len(guesses) >= MAX_GUESSES

    updates = {
        "guesses": json.dumps(guesses),
        "guess_count": str(len(guesses)),
    }

    now = None
    if is_correct or is_last:
        now = datetime.now(timezone.utc).isoformat()
        updates["is_complete"] = "1"
        updates["is_won"] = "1" if is_correct else "0"
        updates["completed_at"] = now

    await redis.hset(f"sessions:{session_id}", mapping=updates)

    if is_correct or is_last:
        elapsed = _compute_elapsed(session["started_at"], now)
        updates_elapsed = {"elapsed_seconds": str(elapsed)}
        await redis.hset(f"sessions:{session_id}", mapping=updates_elapsed)

        await redis.hincrby(f"games:{session['game_id']}", "play_count", 1)
        await redis.hincrby(f"games:{session['game_id']}", "total_guesses", len(guesses))
        if is_correct:
            await redis.hincrby(f"games:{session['game_id']}", "win_count", 1)

        await _update_player_stats(redis, session["player_token"], is_correct, len(guesses), elapsed)
        await redis.delete(f"active_session:{session['game_id']}:{session['player_token']}")

    session = await get_session(redis, session_id)
    return session, is_correct


def _compute_elapsed(started_at: str, completed_at: str) -> float:
    started = datetime.fromisoformat(started_at)
    ended = datetime.fromisoformat(completed_at)
    return round((ended - started).total_seconds(), 2)


async def _update_player_stats(
    redis, player_token: str, is_won: bool, guess_count: int, elapsed: float
) -> None:
    key = f"players:{player_token}"
    data = await redis.hgetall(key)
    if not data:
        return

    player = _decode_hash(data)
    games_played = int(player.get("games_played", 0)) + 1
    updates = {"games_played": str(games_played)}

    if is_won:
        games_won = int(player.get("games_won", 0)) + 1
        total_guesses = int(player.get("total_guesses", 0)) + guess_count
        current_streak = int(player.get("current_streak", 0)) + 1
        max_streak = max(current_streak, int(player.get("max_streak", 0)))
        total_time = round(float(player.get("total_solve_time", 0)) + elapsed, 2)
        avg_time = round(total_time / games_won, 2)

        guess_dist = json.loads(player.get("guess_dist", "{}"))
        gk = str(guess_count)
        guess_dist[gk] = guess_dist.get(gk, 0) + 1

        updates.update(
            {
                "games_won": str(games_won),
                "total_guesses": str(total_guesses),
                "current_streak": str(current_streak),
                "max_streak": str(max_streak),
                "total_solve_time": str(total_time),
                "avg_solve_time": str(avg_time),
                "guess_dist": json.dumps(guess_dist),
            }
        )
    else:
        updates["current_streak"] = "0"

    await redis.hset(key, mapping=updates)


# --- Stats queries ---


async def get_player_stats(redis, player_token: str) -> dict | None:
    data = await redis.hgetall(f"players:{player_token}")
    if not data:
        return None

    player = _decode_hash(data)
    games_played = int(player.get("games_played", 0))
    games_won = int(player.get("games_won", 0))
    win_rate = round((games_won / games_played * 100), 1) if games_played > 0 else 0.0

    return {
        "token": player.get("token"),
        "created_at": player.get("created_at"),
        "games_played": games_played,
        "games_won": games_won,
        "win_rate": win_rate,
        "current_streak": int(player.get("current_streak", 0)),
        "max_streak": int(player.get("max_streak", 0)),
        "total_solve_time": float(player.get("total_solve_time", 0)),
        "avg_solve_time": float(player.get("avg_solve_time", 0)),
        "guess_distribution": json.loads(player.get("guess_dist", "{}")),
    }


async def get_game_stats(redis, game_id: str) -> dict | None:
    game = await get_game(redis, game_id)
    if game is None:
        return None

    win_count = game["win_count"]
    total_guesses = game["total_guesses"]
    avg_guesses = round((total_guesses / win_count), 1) if win_count > 0 else 0.0

    return {
        "game_id": game["game_id"],
        "word": game["word"],
        "play_count": game["play_count"],
        "win_count": win_count,
        "avg_guesses": avg_guesses,
        "guess_distribution": {},
    }


async def get_global_stats(redis) -> dict:
    total_games = 0
    total_players = 0
    total_plays = 0
    total_wins = 0

    async for key in redis.scan_iter("games:*"):
        total_games += 1
        data = await redis.hgetall(key)
        if data:
            decoded = _decode_hash(data)
            total_plays += int(decoded.get("play_count", 0))
            total_wins += int(decoded.get("win_count", 0))

    async for _key in redis.scan_iter("players:*"):
        total_players += 1

    overall_win_rate = round((total_wins / total_plays * 100), 1) if total_plays > 0 else 0.0

    return {
        "total_games": total_games,
        "total_players": total_players,
        "total_plays": total_plays,
        "overall_win_rate": overall_win_rate,
    }
