import redis.asyncio as redis
from fastmcp import FastMCP

from wordle_server import auth, storage, words, game


def create_server(r: redis.Redis) -> FastMCP:
    mcp = FastMCP("Wordle MCP Server")

    # --- Admin Tools ---

    @mcp.tool()
    async def create_game(
        admin_token: str, word: str | None = None
    ) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        if word is not None:
            word = word.upper()
            if not words.is_valid_word(word):
                raise ValueError(f"'{word}' is not a valid 5-letter word")

        chosen = word if word else words.pick_random_word()
        game_data = await storage.create_game(r, chosen, admin_token)
        return {
            "game_id": game_data["game_id"],
            "word": game_data["word"],
            "status": game_data["status"],
            "created_at": game_data["created_at"],
        }

    @mcp.tool()
    async def archive_game(
        admin_token: str, game_id: str, archived: bool = True
    ) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        ok = await storage.archive_game(r, game_id, archived)
        if not ok:
            raise ValueError(f"Game '{game_id}' not found")
        g = await storage.get_game(r, game_id)
        return {"game_id": game_id, "status": g["status"]}

    @mcp.tool()
    async def create_admin_token(admin_token: str) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        token = await auth.create_admin_token(r)
        return {"token": token}

    @mcp.tool()
    async def get_game_stats(admin_token: str, game_id: str) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        stats = await storage.get_game_stats(r, game_id)
        if stats is None:
            raise ValueError(f"Game '{game_id}' not found")
        return stats

    @mcp.tool()
    async def get_global_stats(admin_token: str) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        return await storage.get_global_stats(r)

    @mcp.tool()
    async def list_games(
        admin_token: str, include_archived: bool = False
    ) -> dict:
        if not await auth.validate_admin_token(r, admin_token):
            raise ValueError("Invalid admin token")

        games_list = await storage.list_games(r, include_archived)
        return {"games": games_list}

    # --- Player Tools ---

    @mcp.tool()
    async def register_player() -> dict:
        token = await auth.register_player(r)
        return {"player_token": token}

    @mcp.tool()
    async def list_active_games(player_token: str) -> dict:
        if not await auth.validate_player_token(r, player_token):
            raise ValueError("Invalid player token")
        active = await storage.list_games(r, include_archived=False)
        return {"games": active}

    @mcp.tool()
    async def start_game(game_id: str, player_token: str) -> dict:
        if not await auth.validate_player_token(r, player_token):
            raise ValueError("Invalid player token")
        game_data = await storage.get_game(r, game_id)
        if game_data is None:
            raise ValueError(f"Game '{game_id}' not found")
        if game_data["status"] != "active":
            raise ValueError(f"Game '{game_id}' is not active")
        session = await storage.create_session(r, game_id, player_token)
        return {"session_id": session["session_id"], "game_id": game_id}

    @mcp.tool()
    async def make_guess(
        session_id: str, guess: str, player_token: str
    ) -> dict:
        if not await auth.validate_player_token(r, player_token):
            raise ValueError("Invalid player token")
        guess = guess.upper()
        if not words.is_valid_word(guess):
            raise ValueError(f"'{guess}' is not a valid 5-letter word")
        session = await storage.get_session(r, session_id)
        if session is None:
            raise ValueError("Session not found")
        if session["player_token"] != player_token:
            raise ValueError("Session does not belong to this player")
        game_data = await storage.get_game(r, session["game_id"])
        updated, is_correct = await storage.add_guess(
            r, session_id, guess, game_data["word"]
        )
        board = game.render_board(updated["guesses"], game_data["word"])
        return {
            "session_id": session_id,
            "guess_num": updated["guess_count"],
            "board": board,
            "is_complete": updated["is_complete"],
            "is_won": updated["is_won"],
            "message": "Correct!" if is_correct else "Keep going...",
        }

    @mcp.tool()
    async def get_my_stats(player_token: str) -> dict:
        if not await auth.validate_player_token(r, player_token):
            raise ValueError("Invalid player token")
        stats = await storage.get_player_stats(r, player_token)
        if stats is None:
            raise ValueError("Player not found")
        return stats

    @mcp.tool()
    async def get_game_result(session_id: str, player_token: str) -> dict:
        if not await auth.validate_player_token(r, player_token):
            raise ValueError("Invalid player token")
        session = await storage.get_session(r, session_id)
        if session is None:
            raise ValueError("Session not found")
        if session["player_token"] != player_token:
            raise ValueError("Session does not belong to this player")
        game_data = await storage.get_game(r, session["game_id"])
        return {
            "game_id": session["game_id"],
            "word": game_data["word"] if session["is_complete"] else "hidden",
            "guesses": session["guesses"],
            "is_won": session["is_won"],
            "guess_count": session["guess_count"],
            "elapsed_seconds": session["elapsed_seconds"],
        }

    return mcp


async def main():
    import os

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    port = int(os.environ.get("MCP_PORT", "8000"))
    admin_token = os.environ.get("ADMIN_TOKEN", "")

    r = redis.from_url(redis_url, decode_responses=True)
    if admin_token:
        await auth.init_admin_token(r, admin_token)

    mcp = create_server(r)
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
