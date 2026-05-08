# Wordle MCP Server — Design Spec

## Overview

MCP (Model Context Protocol) server that provides Wordle gameplay via FastMCP. Two roles: admins (create/manage games) and players (play games, view personal stats). Single HTTP/SSE server with role-based tool authorization. Redis for persistence. Docker Compose deployment.

## Architecture

### Components

| Module | File | Responsibility |
|--------|------|----------------|
| Server | `src/server.py` | FastMCP instance, tool registrations, transport config |
| Game Logic | `src/game.py` | Feedback engine, word validation, board rendering with ANSI colors |
| Auth | `src/auth.py` | Token generation/validation, role checks |
| Storage | `src/storage.py` | Redis CRUD operations |
| Words | `src/words.py` | Word list loading from Python package, validation |

### Transport

HTTP/SSE via FastMCP's built-in transport. Single port (`8000`) with all tools exposed. Role enforcement happens at the tool level via token validation.

### Auth Model

- **Admin token**: Static GUID, initialized from `ADMIN_TOKEN` env var. Additional admin tokens created via `create_admin_token` tool.
- **Player token**: Auto-issued GUID on first `register_player` call. No expiration. Passed in every subsequent player tool call.
- Tokens are plain GUIDs — validated by Redis set/hash membership check.

## MCP Tools

### Admin Tools

All admin tools require an `admin_token: str` parameter. Reject calls with invalid/non-admin tokens.

| Tool | Signature | Description |
|------|-----------|-------------|
| `create_game` | `word: str \| None = None` → `{game_id, word, status, created_at}` | Create game with specified word or random 5-letter pick |
| `archive_game` | `game_id: str, archived: bool = True` → `{game_id, status}` | Toggle archive status. Archived games hidden from player listing |
| `create_admin_token` | *(none)* → `{token}` | Generate new admin GUID token |
| `get_game_stats` | `game_id: str` → `{game_id, word, play_count, win_count, avg_guesses, guess_distribution}` | Admin view of per-game stats (no session-level detail) |
| `get_global_stats` | *(none)* → `{total_games, total_players, total_plays, overall_win_rate}` | Global aggregate stats |
| `list_games` | `include_archived: bool = False` → `[{game_id, word, status, play_count}]` | List all games |

### Player Tools

| Tool | Signature | Auth | Description |
|------|-----------|------|-------------|
| `register_player` | *(none)* → `{player_token}` | None | Issue persistent GUID token. First/only call for new players |
| `list_active_games` | `player_token: str` → `[{game_id, status, play_count}]` | Token | List playable games (active only) |
| `start_game` | `game_id: str, player_token: str` → `{session_id, game_id}` | Token | Begin new game session. Returns session_id |
| `make_guess` | `session_id: str, guess: str, player_token: str` → `{session_id, guess_num, board: str, is_complete: bool, is_won: bool, message: str}` | Token | Submit 5-letter guess. Returns ANSI-colored board of all guesses so far. Rejects invalid words or already-completed sessions |
| `get_my_stats` | `player_token: str` → `{games_played, games_won, win_rate, current_streak, max_streak, guess_distribution}` | Token | Player's personal stats |
| `get_game_result` | `session_id: str, player_token: str` → `{game_id, word, guesses, is_won, guess_count}` | Token | Result of a specific session |

## Game Rules

Standard Wordle rules:
- 6 guesses maximum
- 5-letter words only
- Feedback per letter: green (correct position), yellow (in word, wrong position), white/gray (not in word)
- Duplicate letters: first occurrence matched first (standard Wordle behavior)
- Win if guess matches target word exactly
- Invalid words (not in word list) are rejected and do NOT count toward the 6-guess limit
- Starting a game the player already has an active session for returns the existing session (no duplicates)

### Board Rendering

Each `make_guess` call returns a multi-line ANSI-colored string showing the full board of all guesses made so far in this session:

```
S L A T E    ⬜ 🟨 ⬜ ⬜ ⬜
C R A N E    ⬜ 🟩 🟩 ⬜ 🟩
...
```

ANSI codes: green `\033[32m`, yellow `\033[33m`, reset `\033[0m`.

## Redis Data Model

Keys are colon-namespaced. Vectors (lists, sets) use JSON serialization within Redis string values where native types are impractical.

```
admin_tokens              → Set<str>                        {"abc-123-admin", ...}

players:{token}           → Hash {
    token, created_at, games_played, games_won,
    total_guesses, current_streak, max_streak,
    guess_dist (JSON: {"1":2,"2":5,"3":3,...})
}

games:{game_id}           → Hash {
    game_id, word, created_at, status ("active"|"archived"),
    created_by, play_count, win_count, total_guesses
}

sessions:{session_id}    → Hash {
    session_id, game_id, player_token, started_at,
    guesses (JSON: ["SLATE","CRANE",...]),
    is_complete, is_won, guess_count
}

player_sessions:{token}  → Set<str>                        session IDs for player

active_session:{game_id}:{player_token} → String           session_id or empty
```

## Deployment

### docker-compose.yml

```yaml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    ports:
      - "6379"

  wordle-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ADMIN_TOKEN=${ADMIN_TOKEN}
      - MCP_PORT=8000
      - MCP_TRANSPORT=http
    depends_on:
      - redis
```

### Dockerfile

Python 3.12+ base. Install via `uv sync`. Copy `src/` and run with `uv run python -m src.server`.

### Configuration

All configuration via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `ADMIN_TOKEN` | *(required)* | Initial admin GUID token |
| `MCP_PORT` | `8000` | HTTP server port |
| `MCP_TRANSPORT` | `http` | Transport mode |

## Project Structure

```
mcp-wordle/
  data/redis/              # Redis AOF data (gitignored)
  src/
    server.py              # FastMCP setup, tool registrations
    game.py                # Wordle logic
    auth.py                # Token management
    storage.py             # Redis operations
    words.py               # Word list
  tests/
    test_game.py
    test_auth.py
    test_storage.py
    test_server.py
  Dockerfile
  docker-compose.yml
  pyproject.toml
  uv.lock
```

## Dependencies

- `fastmcp` — MCP server framework
- `redis[hiredis]` — Redis client with C parser
- A 5-letter word list Python package (TBD during implementation)
- `pytest`, `pytest-asyncio` — Testing

## Testing Strategy

- **Unit tests**: `test_game.py` (feedback logic, board rendering), `test_auth.py` (token validation), `test_storage.py` (Redis ops with fakeredis or real Redis)
- **Integration tests**: `test_server.py` using FastMCP test client against a running server with Redis

## Out of Scope

- Multiple languages / i18n
- Leaderboards
- Web UI
- Notification/streaming of game events
- Rate limiting
