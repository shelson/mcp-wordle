import redis.asyncio as redis
from fastmcp import FastMCP

from src.wordle_server import auth, storage, words, game


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

    return mcp
