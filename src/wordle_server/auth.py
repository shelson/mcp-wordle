import uuid
from datetime import datetime, timezone


async def init_admin_token(redis, token: str) -> None:
    await redis.sadd("admin_tokens", token)


async def validate_admin_token(redis, token: str) -> bool:
    return bool(await redis.sismember("admin_tokens", token))


async def validate_player_token(redis, token: str) -> bool:
    return bool(await redis.exists(f"players:{token}"))


async def register_player(redis) -> str:
    token = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    await redis.hset(
        f"players:{token}",
        mapping={
            "token": token,
            "created_at": now,
            "games_played": "0",
            "games_won": "0",
            "total_guesses": "0",
            "current_streak": "0",
            "max_streak": "0",
            "total_solve_time": "0.0",
            "avg_solve_time": "0.0",
            "guess_dist": "{}",
        },
    )
    return token


async def create_admin_token(redis) -> str:
    token = str(uuid.uuid4())
    await redis.sadd("admin_tokens", token)
    return token
