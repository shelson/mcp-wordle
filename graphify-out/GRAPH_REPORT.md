# Graph Report - mcp-wordle  (2026-05-08)

## Corpus Check
- 14 files · ~10,766 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 128 nodes · 233 edges · 13 communities
- Extraction: 57% EXTRACTED · 43% INFERRED · 0% AMBIGUOUS · INFERRED: 101 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `546db798`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `create_game()` - 22 edges
2. `create_session()` - 15 edges
3. `add_guess()` - 14 edges
4. `get_feedback()` - 9 edges
5. `render_board()` - 9 edges
6. `get_game()` - 9 edges
7. `_decode_hash()` - 8 edges
8. `archive_game()` - 6 edges
9. `get_session()` - 6 edges
10. `is_valid_word()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `test_create_game()` --calls--> `create_game()`  [INFERRED]
  tests/test_storage.py → src/wordle_server/storage.py
- `test_get_session_nonexistent()` --calls--> `get_session()`  [INFERRED]
  tests/test_storage.py → src/wordle_server/storage.py
- `test_is_valid_word_accepts_valid_word()` --calls--> `is_valid_word()`  [INFERRED]
  tests/test_words.py → src/wordle_server/words.py
- `test_is_valid_word_rejects_wrong_length()` --calls--> `is_valid_word()`  [INFERRED]
  tests/test_words.py → src/wordle_server/words.py
- `test_is_valid_word_rejects_non_alpha()` --calls--> `is_valid_word()`  [INFERRED]
  tests/test_words.py → src/wordle_server/words.py

## Communities (13 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.19
Nodes (16): test_get_feedback_all_correct(), test_get_feedback_all_wrong(), test_get_feedback_case_insensitive(), test_get_feedback_duplicate_letters_in_guess(), test_get_feedback_duplicate_letters_in_target(), test_get_feedback_duplicate_match_priority(), test_get_feedback_partial_match(), test_render_board_all_green() (+8 more)

### Community 1 - "Community 1"
Cohesion: 0.21
Nodes (12): test_create_admin_token(), test_init_admin_token(), test_register_player_creates_token(), test_validate_admin_token_invalid(), test_validate_admin_token_valid(), test_validate_player_token_invalid(), test_validate_player_token_valid(), create_admin_token() (+4 more)

### Community 2 - "Community 2"
Cohesion: 0.15
Nodes (4): client(), client(), create_server(), main()

### Community 3 - "Community 3"
Cohesion: 0.24
Nodes (12): test_add_guess_correct(), test_add_guess_incorrect(), test_add_guess_nonexistent_session(), test_decode_hash(), test_get_global_stats_empty(), test_get_global_stats_with_data(), add_guess(), _compute_elapsed() (+4 more)

### Community 4 - "Community 4"
Cohesion: 0.27
Nodes (13): test_add_guess_updates_game_and_player_stats(), test_archive_game(), test_archive_game_nonexistent(), test_archive_game_unarchive(), test_get_game_exists(), test_get_game_nonexistent(), test_list_games_active_only(), test_list_games_include_archived() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (10): test_get_word_set_returns_five_letter_uppercase(), test_is_valid_word_accepts_valid_word(), test_is_valid_word_rejects_non_alpha(), test_is_valid_word_rejects_not_in_set(), test_is_valid_word_rejects_wrong_length(), test_pick_random_word_handles_single_word_set(), test_pick_random_word_returns_from_set(), _get_word_set() (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.22
Nodes (8): fake_redis(), Small controlled word set for testing., Small controlled word set for testing., sample_words(), clean_redis(), redis_db(), redis_db(), redis_db()

### Community 8 - "Community 8"
Cohesion: 0.29
Nodes (8): test_add_guess_on_completed_session_raises(), test_add_guess_sixth_guess_wrong_ends_game(), test_create_session(), test_create_session_duplicate_returns_existing(), test_get_active_session(), test_get_active_session_none(), create_session(), get_active_session()

### Community 9 - "Community 9"
Cohesion: 0.32
Nodes (6): test_create_game(), test_get_game_stats(), test_get_game_stats_avg_guesses(), test_get_game_stats_nonexistent(), test_get_session_nonexistent(), get_game_stats()

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (4): test_get_player_stats_loss_resets_streak(), test_get_player_stats_nonexistent(), test_get_player_stats_with_games(), get_player_stats()

## Knowledge Gaps
- **2 isolated node(s):** `Small controlled word set for testing.`, `Small controlled word set for testing.`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `redis_db()` connect `Community 7` to `Community 9`?**
  _High betweenness centrality (0.276) - this node is a cross-community bridge._
- **Why does `clean_redis()` connect `Community 7` to `Community 1`?**
  _High betweenness centrality (0.140) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `create_game()` (e.g. with `test_create_game()` and `test_get_game_exists()`) actually correct?**
  _`create_game()` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `create_session()` (e.g. with `test_create_session()` and `test_create_session_duplicate_returns_existing()`) actually correct?**
  _`create_session()` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `add_guess()` (e.g. with `test_add_guess_correct()` and `test_add_guess_incorrect()`) actually correct?**
  _`add_guess()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `get_feedback()` (e.g. with `test_get_feedback_all_correct()` and `test_get_feedback_all_wrong()`) actually correct?**
  _`get_feedback()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `render_board()` (e.g. with `test_render_board_all_green()` and `test_render_board_all_white()`) actually correct?**
  _`render_board()` has 7 INFERRED edges - model-reasoned connections that need verification._