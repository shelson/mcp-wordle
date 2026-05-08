# Wordle MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Wordle MCP server with admin and player tools, Redis persistence, and Docker Compose deployment.

**Architecture:** Single FastMCP HTTP/SSE server with five focused modules (game, auth, storage, words, server). Token-based auth with admin/player roles. Redis for all persistent state.

**Tech Stack:** Python 3.12+, FastMCP, redis-py (async), english-words, pytest, pytest-asyncio, fakeredis

---

### Task 1: Project bootstrap

**Files:**
- Create: `.gitignore`
- Create: `pyproject.toml`
- Run: `uv sync` to generate `uv.lock`

- [ ] **Step 1: Create .gitignore**

```bash
cat > .gitignore << 'GITEOF'
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
data/
.venv/
.env
*.egg-info/
dist/
build/
GITEOF
```

- [ ] **Step 2: Create pyproject.toml**

```bash
cat > pyproject.toml << 'TOML'
[project]
name = "mcp-wordle"
version = "0.1.0"
description = "Wordle gameplay via MCP"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.0.0",
    "redis[hiredis]>=5.0.0",
    "english-words>=2.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.25.0",
    "fakeredis[lua]>=2.26.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
TOML
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```
Expected: `uv.lock` created, `.venv/` populated.

- [ ] **Step 4: Verify installation**

```bash
uv run python -c "import fastmcp; import redis.asyncio; import english_words; print('OK')"
```
Expected: prints `OK`

- [ ] **Step 5: Commit**

```bash
git add .gitignore pyproject.toml uv.lock
git commit -m "feat: bootstrap project with uv and dependencies"
```

---

### Task 2: Words module

**Files:**
- Create: `src/wordle_server/__init__.py`
- Create: `src/wordle_server/words.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_words.py`

- [ ] **Step 1: Create package init**

```python
# src/wordle_server/__init__.py — empty
```

- [ ] **Step 2: Create tests init**

```python
# tests/__init__.py — empty
```

- [ ] **Step 3: Create conftest with common word set for tests**

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_words():
    """Small controlled word set for testing."""
    return {"SLATE", "CRANE", "ADIEU", "STARE", "AUDIO", "RAISE", "SPLIT", "WORLD"}
```

- [ ] **Step 4: Write tests for words module**

```python
# tests/test_words.py
import pytest
from src.wordle_server.words import (
    _get_word_set,
    is_valid_word,
    pick_random_word,
)

def test_get_word_set_returns_five_letter_uppercase():
    words = _get_word_set()
    assert len(words) > 100
    for w in words:
        assert len(w) == 5
        assert w.isalpha()
        assert w == w.upper()

def test_is_valid_word_accepts_valid_word(sample_words):
    assert is_valid_word("SLATE", sample_words)
    assert is_valid_word("slate", sample_words)
    assert is_valid_word("SlAtE", sample_words)

def test_is_valid_word_rejects_wrong_length(sample_words):
    assert not is_valid_word("SLAT", sample_words)
    assert not is_valid_word("SLATER", sample_words)

def test_is_valid_word_rejects_non_alpha(sample_words):
    assert not is_valid_word("SL4TE", sample_words)
    assert not is_valid_word("SL TE", sample_words)

def test_is_valid_word_rejects_not_in_set(sample_words):
    assert not is_valid_word("ZZZZZ", sample_words)

def test_pick_random_word_returns_from_set():
    word_set = {"SLATE", "CRANE", "ADIEU"}
    for _ in range(20):
        word = pick_random_word(word_set)
        assert word in word_set

def test_pick_random_word_handles_single_word_set():
    word_set = {"SLATE"}
    word = pick_random_word(word_set)
    assert word == "SLATE"
```

- [ ] **Step 5: Run tests to verify they fail**

```bash
uv run pytest tests/test_words.py -v
```
Expected: all tests FAIL (module not found)

- [ ] **Step 6: Implement words module**

```python
# src/wordle_server/words.py
import random
from english_words import get_english_words_set

_word_cache: set[str] | None = None


def _get_word_set() -> set[str]:
    global _word_cache
    if _word_cache is None:
        all_words = get_english_words_set(["web2"])
        _word_cache = {w.upper() for w in all_words if len(w) == 5 and w.isalpha()}
    return _word_cache


def is_valid_word(word: str, word_set: set[str] | None = None) -> bool:
    if word_set is None:
        word_set = _get_word_set()
    return len(word) == 5 and word.isalpha() and word.upper() in word_set


def pick_random_word(word_set: set[str] | None = None) -> str:
    if word_set is None:
        word_set = _get_word_set()
    return random.choice(list(word_set))
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
uv run pytest tests/test_words.py -v
```
Expected: all PASS

- [ ] **Step 8: Commit**

```bash
git add src/ tests/__init__.py tests/conftest.py tests/test_words.py
git commit -m "feat: add words module with validation and random pick"
```

---

### Task 3: Game module (feedback engine + board rendering)

**Files:**
- Create: `src/wordle_server/game.py`
- Create: `tests/test_game.py`

- [ ] **Step 1: Write tests for game module**

```python
# tests/test_game.py
from src.wordle_server.game import get_feedback, render_board, MAX_GUESSES

# --- get_feedback ---

def test_get_feedback_all_correct():
    result = get_feedback("SLATE", "SLATE")
    assert result == ["green", "green", "green", "green", "green"]

def test_get_feedback_all_wrong():
    result = get_feedback("ABCDE", "FGHIJ")
    assert result == ["white", "white", "white", "white", "white"]

def test_get_feedback_partial_match():
    result = get_feedback("SLATE", "STALE")
    # S correct pos, L correct pos, A wrong pos, T wrong pos, E correct pos
    assert result == ["green", "green", "yellow", "yellow", "green"]

def test_get_feedback_duplicate_letters_in_guess():
    result = get_feedback("SLEEP", "SLATE")
    # S=green, L=white (L is in pos1 not pos2), E=yellow, E=white (only one E in target), P=white
    assert result == ["green", "white", "yellow", "white", "white"]

def test_get_feedback_duplicate_letters_in_target():
    result = get_feedback("SLATE", "SHEEP")
    # S=green, L=white, A=white, T=white, E=yellow
    assert result == ["green", "white", "white", "white", "yellow"]

def test_get_feedback_duplicate_match_priority():
    # When guess has duplicate letter and target has one:
    # First occurrence gets priority
    result = get_feedback("BANAL", "APPLE")
    # B=white, A=yellow (first A matched), N=white, A=white (no more A), L=white
    assert result == ["white", "yellow", "white", "white", "white"]

def test_get_feedback_case_insensitive():
    result = get_feedback("slate", "SLATE")
    assert result == ["green", "green", "green", "green", "green"]

# --- render_board ---

def test_render_board_single_guess():
    board = render_board(["SLATE"], "SLATE")
    assert "\033[32m" in board  # green ANSI
    assert "S" in board
    assert "L" in board
    assert "\033[0m" in board  # reset

def test_render_board_mixed_feedback():
    board = render_board(["SLATE"], "STARE")
    lines = board.strip().split("\n")
    assert len(lines) == 1

def test_render_board_multiple_guesses():
    board = render_board(["ABCDE", "FGHIJ", "SLATE"], "SLATE")
    lines = board.strip().split("\n")
    assert len(lines) == 3

# --- MAX_GUESSES ---

def test_max_guesses_is_six():
    assert MAX_GUESSES == 6
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_game.py -v
```
Expected: all FAIL (module not found)

- [ ] **Step 3: Implement game module**

```python
# src/wordle_server/game.py
from typing import Literal

FeedbackColor = Literal["green", "yellow", "white"]

MAX_GUESSES = 6

GREEN_ANSI = "\033[32m"
YELLOW_ANSI = "\033[33m"
RESET_ANSI = "\033[0m"

COLOR_ANSI = {
    "green": GREEN_ANSI,
    "yellow": YELLOW_ANSI,
    "white": "",
}

COLOR_EMOJI = {
    "green": "\U0001f7e9",
    "yellow": "\U0001f7e8",
    "white": "\u2b1c",
}


def get_feedback(guess: str, target: str) -> list[FeedbackColor]:
    guess = guess.upper()
    target = target.upper()
    result: list[FeedbackColor] = ["white"] * 5

    target_chars: list[str | None] = list(target)

    for i in range(5):
        if guess[i] == target[i]:
            result[i] = "green"
            target_chars[i] = None

    for i in range(5):
        if result[i] == "white" and guess[i] in target_chars:
            result[i] = "yellow"
            target_chars[target_chars.index(guess[i])] = None

    return result


def render_board(guesses: list[str], target: str) -> str:
    lines: list[str] = []
    for guess in guesses:
        feedback = get_feedback(guess, target)
        colored_chars: list[str] = []
        for i, ch in enumerate(guess.upper()):
            ansi = COLOR_ANSI[feedback[i]]
            if ansi:
                colored_chars.append(f"{ansi}{ch}{RESET_ANSI}")
            else:
                colored_chars.append(ch)
        colored = " ".join(colored_chars)
        emoji = " ".join(COLOR_EMOJI[f] for f in feedback)
        lines.append(f"{colored} {emoji}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_game.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/wordle_server/game.py tests/test_game.py
git commit -m "feat: add game logic with feedback engine and ANSI board rendering"
```

---

### Task 4: Auth module

**Files:**
- Create: `src/wordle_server/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write tests for auth module**

```python
# tests/test_auth.py
import pytest
from src.wordle_server.auth import (
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_auth.py -v
```
Expected: all FAIL (module not found)

- [ ] **Step 3: Implement auth module**

```python
# src/wordle_server/auth.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_auth.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/wordle_server/auth.py tests/test_auth.py
git commit -m "feat: add auth module with token generation and validation"
```

---

### Task 5: Storage module — games and sessions

**Files:**
- Create: `src/wordle_server/storage.py`
- Create: `tests/test_storage.py`

- [ ] **Step 1: Write tests for storage module (games + sessions)**

```python
# tests/test_storage.py
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
    # Make 5 wrong guesses first
    for word in ["CRANE", "ADIEU", "AUDIO", "STARE", "RAISE"]:
        await add_guess(redis_db, session["session_id"], word, "SLATE")
    # 6th guess — also wrong
    updated, correct = await add_guess(redis_db, session["session_id"], "SPLIT", "SLATE")
    assert correct is False
    assert updated["is_complete"] is True
    assert updated["is_won"] is False
    assert updated["guess_count"] == 6


@pytest.mark.asyncio
async def test_add_guess_updates_game_and_player_stats(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    _, _ = await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")

    # Check game stats updated
    fetched_game = await get_game(redis_db, game["game_id"])
    assert fetched_game["play_count"] == 1
    assert fetched_game["win_count"] == 1

    # Check player stats updated
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_storage.py -v
```
Expected: all FAIL (module not found)

- [ ] **Step 3: Implement storage module**

```python
# src/wordle_server/storage.py
import uuid
import json
from datetime import datetime, timezone


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
            if include_archived or game.get("status") == "active":
                games.append(game)
    return games


# --- Session operations ---


async def get_active_session(redis, game_id: str, player_token: str) -> dict | None:
    sid = await redis.get(f"active_session:{game_id}:{player_token}")
    if sid and isinstance(sid, str):
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
    from src.wordle_server.game import MAX_GUESSES

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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_storage.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/wordle_server/storage.py tests/test_storage.py
git commit -m "feat: add storage module with game/session CRUD and stats"
```

---

### Task 6: Storage module — stats queries

**Files:**
- Modify: `src/wordle_server/storage.py` (append stats functions)
- Modify: `tests/test_storage.py` (append stats tests)

- [ ] **Step 1: Append stats tests to test_storage.py**

Append the following to `tests/test_storage.py`:

```python
# --- Stats queries ---

from src.wordle_server.storage import (
    get_player_stats,
    get_game_stats,
    get_global_stats,
    add_guess as storage_add_guess,
)


@pytest.mark.asyncio
async def test_get_player_stats_nonexistent(redis_db):
    result = await get_player_stats(redis_db, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_get_player_stats_with_games(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")

    stats = await get_player_stats(redis_db, "player-1")
    assert stats is not None
    assert stats["games_played"] == 1
    assert stats["games_won"] == 1
    assert stats["win_rate"] == 100.0
    assert stats["current_streak"] == 1
    assert stats["max_streak"] == 1
    assert "1" in stats["guess_distribution"]


@pytest.mark.asyncio
async def test_get_player_stats_loss_resets_streak(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")
    # Second game — lose
    session2 = await create_session(redis_db, game["game_id"], "player-1")
    for word in ["CRANE", "ADIEU", "AUDIO", "STARE", "RAISE", "SPLIT"]:
        await add_guess(redis_db, session2["session_id"], word, "SLATE")

    stats = await get_player_stats(redis_db, "player-1")
    assert stats["current_streak"] == 0
    assert stats["max_streak"] == 1
    assert stats["games_played"] == 2
    assert stats["games_won"] == 1


@pytest.mark.asyncio
async def test_get_game_stats(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    stats = await get_game_stats(redis_db, game["game_id"])
    assert stats is not None
    assert stats["word"] == "SLATE"
    assert stats["play_count"] == 0
    assert stats["win_count"] == 0


@pytest.mark.asyncio
async def test_get_game_stats_nonexistent(redis_db):
    result = await get_game_stats(redis_db, "nope")
    assert result is None


@pytest.mark.asyncio
async def test_get_global_stats_empty(redis_db):
    stats = await get_global_stats(redis_db)
    assert stats["total_games"] == 0
    assert stats["total_players"] == 0
    assert stats["total_plays"] == 0


@pytest.mark.asyncio
async def test_get_global_stats_with_data(redis_db, admin_token):
    game = await create_game(redis_db, "SLATE", admin_token)
    session = await create_session(redis_db, game["game_id"], "player-1")
    await add_guess(redis_db, session["session_id"], "SLATE", "SLATE")

    stats = await get_global_stats(redis_db)
    assert stats["total_games"] >= 1
    assert stats["total_plays"] == 1
    assert stats["overall_win_rate"] == 100.0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_storage.py::test_get_player_stats_nonexistent tests/test_storage.py::test_get_player_stats_with_games -v
```
Expected: FAIL (function not defined)

- [ ] **Step 3: Append stats functions to storage.py**

Append the following to `src/wordle_server/storage.py`:

```python
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
```

- [ ] **Step 4: Run all storage tests to verify they pass**

```bash
uv run pytest tests/test_storage.py -v
```
Expected: all PASS (old + new)

- [ ] **Step 5: Commit**

```bash
git add src/wordle_server/storage.py tests/test_storage.py
git commit -m "feat: add stats query functions to storage module"
```

---

### Task 7: Server module — admin tools

**Files:**
- Create: `src/wordle_server/server.py`
- Create: `tests/test_server_admin.py`

- [ ] **Step 1: Write integration tests for admin tools**

```python
# tests/test_server_admin.py
import os
import pytest
import uuid


@pytest.fixture(scope="module")
def admin_token():
    return str(uuid.uuid4())


@pytest.fixture(scope="module")
def redis_url():
    return os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="module")
async def _redis(redis_url, admin_token):
    import redis.asyncio as redis

    r = redis.from_url(redis_url, decode_responses=True)
    await r.flushdb()
    await r.sadd("admin_tokens", admin_token)
    yield r
    await r.flushdb()
    await r.close()


@pytest.fixture(scope="module")
async def mcp_server(_redis):
    from src.wordle_server.server import create_server

    return create_server(_redis)


@pytest.fixture
async def client(mcp_server):
    from fastmcp import Client

    async with Client(mcp_server) as c:
        yield c


@pytest.mark.asyncio
async def test_create_game_random_word(client, admin_token):
    result = await client.call_tool("create_game", {"admin_token": admin_token})
    assert result.game_id is not None
    assert len(result.word) == 5
    assert result.status == "active"


@pytest.mark.asyncio
async def test_create_game_specific_word(client, admin_token):
    result = await client.call_tool(
        "create_game", {"word": "SLATE", "admin_token": admin_token}
    )
    assert result.word == "SLATE"


@pytest.mark.asyncio
async def test_create_game_invalid_word(client, admin_token):
    with pytest.raises(Exception):
        await client.call_tool(
            "create_game", {"word": "ZZZZZ", "admin_token": admin_token}
        )


@pytest.mark.asyncio
async def test_create_game_invalid_admin_token(client):
    with pytest.raises(Exception):
        await client.call_tool(
            "create_game", {"word": "SLATE", "admin_token": "bad-token"}
        )


@pytest.mark.asyncio
async def test_archive_game(client, admin_token):
    result = await client.call_tool("create_game", {"admin_token": admin_token})
    r = await client.call_tool(
        "archive_game", {"game_id": result.game_id, "admin_token": admin_token}
    )
    assert r.status == "archived"


@pytest.mark.asyncio
async def test_create_admin_token(client, admin_token):
    result = await client.call_tool("create_admin_token", {"admin_token": admin_token})
    assert result.token is not None
    assert len(result.token) > 0


@pytest.mark.asyncio
async def test_list_games(client, admin_token):
    await client.call_tool("create_game", {"admin_token": admin_token})
    await client.call_tool("create_game", {"admin_token": admin_token})
    result = await client.call_tool(
        "list_games", {"admin_token": admin_token, "include_archived": False}
    )
    assert len(result.games) >= 2


@pytest.mark.asyncio
async def test_get_game_stats(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token})
    result = await client.call_tool(
        "get_game_stats", {"game_id": g.game_id, "admin_token": admin_token}
    )
    assert result.word == g.word
    assert result.play_count == 0


@pytest.mark.asyncio
async def test_get_global_stats(client, admin_token):
    result = await client.call_tool("get_global_stats", {"admin_token": admin_token})
    assert "total_games" in result
    assert "total_players" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_server_admin.py -v
```
Expected: FAIL (create_server not found)

- [ ] **Step 3: Implement server module with admin tools**

```python
# src/wordle_server/server.py
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
```

- [ ] **Step 4: Run admin server tests**

```bash
uv run pytest tests/test_server_admin.py -v
```
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/wordle_server/server.py tests/test_server_admin.py
git commit -m "feat: add server module with admin tools"
```

---

### Task 8: Server module — player tools

**Files:**
- Modify: `src/wordle_server/server.py` (append player tools)
- Create: `tests/test_server_player.py`

- [ ] **Step 1: Write integration tests for player tools**

```python
# tests/test_server_player.py
import os
import uuid
import pytest


@pytest.fixture(scope="module")
def admin_token():
    return str(uuid.uuid4())


@pytest.fixture(scope="module")
def redis_url():
    return os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/1")


@pytest.fixture(scope="module")
async def _redis(redis_url, admin_token):
    import redis.asyncio as redis

    r = redis.from_url(redis_url, decode_responses=True)
    await r.flushdb()
    await r.sadd("admin_tokens", admin_token)
    yield r
    await r.flushdb()
    await r.close()


@pytest.fixture(scope="module")
async def mcp_server(_redis):
    from src.wordle_server.server import create_server

    return create_server(_redis)


@pytest.fixture
async def client(mcp_server):
    from fastmcp import Client

    async with Client(mcp_server) as c:
        yield c


@pytest.mark.asyncio
async def test_register_player(client):
    result = await client.call_tool("register_player", {})
    assert result.player_token is not None
    assert len(result.player_token) > 0


@pytest.mark.asyncio
async def test_list_active_games(client, admin_token):
    # Create a game as admin
    await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    # Register as player
    reg = await client.call_tool("register_player", {})
    result = await client.call_tool(
        "list_active_games", {"player_token": reg.player_token}
    )
    assert len(result.games) >= 1


@pytest.mark.asyncio
async def test_list_active_games_excludes_archived(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token})
    await client.call_tool(
        "archive_game", {"admin_token": admin_token, "game_id": g.game_id}
    )
    reg = await client.call_tool("register_player", {})
    result = await client.call_tool(
        "list_active_games", {"player_token": reg.player_token}
    )
    game_ids = [g.item["game_id"] for g in result.games]
    assert g.game_id not in game_ids


@pytest.mark.asyncio
async def test_start_game(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    result = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    assert result.session_id is not None
    assert result.game_id == g.game_id


@pytest.mark.asyncio
async def test_start_game_invalid_player_token(client):
    with pytest.raises(Exception):
        await client.call_tool(
            "start_game", {"game_id": "some-id", "player_token": "bad-token"}
        )


@pytest.mark.asyncio
async def test_make_guess_correct(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    result = await client.call_tool(
        "make_guess",
        {
            "session_id": sess.session_id,
            "guess": "SLATE",
            "player_token": reg.player_token,
        },
    )
    assert result.is_complete is True
    assert result.is_won is True
    assert result.board is not None


@pytest.mark.asyncio
async def test_make_guess_incorrect_continues(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    result = await client.call_tool(
        "make_guess",
        {
            "session_id": sess.session_id,
            "guess": "CRANE",
            "player_token": reg.player_token,
        },
    )
    assert result.is_complete is False
    assert result.is_won is False
    assert result.guess_num == 1


@pytest.mark.asyncio
async def test_make_guess_invalid_word_rejected(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    with pytest.raises(Exception):
        await client.call_tool(
            "make_guess",
            {
                "session_id": sess.session_id,
                "guess": "ZZZZZ",
                "player_token": reg.player_token,
            },
        )


@pytest.mark.asyncio
async def test_make_guess_completed_session_rejected(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    await client.call_tool(
        "make_guess",
        {
            "session_id": sess.session_id,
            "guess": "SLATE",
            "player_token": reg.player_token,
        },
    )
    with pytest.raises(Exception):
        await client.call_tool(
            "make_guess",
            {
                "session_id": sess.session_id,
                "guess": "CRANE",
                "player_token": reg.player_token,
            },
        )


@pytest.mark.asyncio
async def test_get_my_stats(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    await client.call_tool(
        "make_guess",
        {
            "session_id": sess.session_id,
            "guess": "SLATE",
            "player_token": reg.player_token,
        },
    )
    result = await client.call_tool(
        "get_my_stats", {"player_token": reg.player_token}
    )
    assert result.games_played == 1
    assert result.games_won == 1
    assert result.win_rate == 100.0


@pytest.mark.asyncio
async def test_get_game_result(client, admin_token):
    g = await client.call_tool("create_game", {"admin_token": admin_token, "word": "SLATE"})
    reg = await client.call_tool("register_player", {})
    sess = await client.call_tool(
        "start_game", {"game_id": g.game_id, "player_token": reg.player_token}
    )
    await client.call_tool(
        "make_guess",
        {
            "session_id": sess.session_id,
            "guess": "SLATE",
            "player_token": reg.player_token,
        },
    )
    result = await client.call_tool(
        "get_game_result",
        {"session_id": sess.session_id, "player_token": reg.player_token},
    )
    assert result.is_won is True
    assert result.guess_count == 1
    assert result.word == "SLATE"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_server_player.py -v
```
Expected: all or most FAIL (player tools not registered yet)

- [ ] **Step 3: Append player tools to server.py**

Append the following before the final `return mcp` in `src/wordle_server/server.py`:

```python
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
```

- [ ] **Step 4: Add main entry point to server.py**

Append at the end of `src/wordle_server/server.py`:

```python
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
```

And at the very bottom:

```python
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

- [ ] **Step 5: Run player server tests**

```bash
uv run pytest tests/test_server_player.py -v
```
Expected: all PASS

- [ ] **Step 6: Run all server tests**

```bash
uv run pytest tests/test_server_admin.py tests/test_server_player.py -v
```
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add src/wordle_server/server.py tests/test_server_player.py
git commit -m "feat: add player tools and main entry point to server"
```

---

### Task 9: Docker setup

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.12-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ ./src/

ENV MCP_PORT=8000
ENV MCP_TRANSPORT=http

EXPOSE 8000

CMD ["uv", "run", "python", "-m", "src.wordle_server.server"]
```

- [ ] **Step 2: Create docker-compose.yml**

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    volumes:
      - ./data/redis:/data
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"

  wordle-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - ADMIN_TOKEN=${ADMIN_TOKEN:-admin-dev-token}
      - MCP_PORT=8000
      - MCP_TRANSPORT=http
    depends_on:
      - redis
```

- [ ] **Step 3: Create .env.example**

```
ADMIN_TOKEN=your-admin-guid-here
```

- [ ] **Step 4: Commit**

```bash
git add Dockerfile docker-compose.yml .env.example
git commit -m "feat: add Docker and Compose setup"
```

---

### Task 10: Final verification

**Files:**
- Modify: `pyproject.toml` (add script entry point)

- [ ] **Step 1: Add script entry point to pyproject.toml**

Add `[project.scripts]` to `pyproject.toml`:

```toml
[project.scripts]
wordle-server = "src.wordle_server.server:main"
```

- [ ] **Step 2: Run full test suite**

```bash
uv run pytest tests/ -v
```
Expected: all tests PASS

- [ ] **Step 3: Verify Docker builds**

```bash
docker compose build
```
Expected: builds successfully

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add script entry point, finalize"
```

---

### Task 11: Post-implementation — graphify index

- [ ] **Step 1: Update graphify index**

```bash
graphify extract .
```
Expected: successful index update
