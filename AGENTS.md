# AGENTS.md

## Overview
MCP server that provides Wordle gameplay via the Model Context Protocol. Built with FastMCP (HTTP/SSE transport), Redis persistence, and Docker Compose deployment.

## Project status
Implementation complete. 75 tests passing. Two roles: admin (create/manage games) and player (play, view stats). Token-based auth.

## How to run

```bash
# Generate admin token
uuidgen

# Docker Compose (recommended)
ADMIN_TOKEN=<guid> docker compose up --build -d

# Local dev
REDIS_URL=redis://localhost:6379 ADMIN_TOKEN=<guid> uv run wordle-server
```

Server runs at `http://0.0.0.0:8000/mcp`. Connect as player: call `register_player` to get a token, then `list_active_games` → `start_game` → `make_guess`.

## Architecture

| Module | File | Responsibility |
|--------|------|----------------|
| Server | `src/wordle_server/server.py` | FastMCP setup, 6 admin + 6 player tool registrations |
| Game Logic | `src/wordle_server/game.py` | Feedback engine, ANSI board rendering |
| Auth | `src/wordle_server/auth.py` | GUID token generation/validation |
| Storage | `src/wordle_server/storage.py` | Redis CRUD for games, sessions, stats |
| Words | `src/wordle_server/words.py` | Word list loading from english-words |

## Workflow

### Python toolchain
All Python is managed via `uv`. Dependencies in `pyproject.toml`. Run `uv sync` to install. Use `uv run pytest tests/` to test.

### Branching
Never commit to `main`. All work must happen in branches.

### Testing
75 tests across 6 test files. `uv run pytest tests/ -v` runs everything. Tests use `fakeredis` — no external dependencies needed.

### graphify indexing
This project has a graphify knowledge graph at graphify-out/.

Rules:

Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
After every git commit, update the graphify index. The `graphify` Python package is already installed and available on `PATH`.

## License
MIT — see [LICENSE](./LICENSE)
