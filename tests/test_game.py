from wordle_server.game import get_feedback, render_board, MAX_GUESSES


# --- get_feedback ---

def test_get_feedback_all_correct():
    result = get_feedback("SLATE", "SLATE")
    assert result == ["green", "green", "green", "green", "green"]


def test_get_feedback_all_wrong():
    result = get_feedback("ABCDE", "FGHIJ")
    assert result == ["white", "white", "white", "white", "white"]


def test_get_feedback_partial_match():
    result = get_feedback("SLATE", "STALE")
    # S=green, L=yellow (L at pos3 in target), A=green, T=yellow (T at pos1), E=green
    assert result == ["green", "yellow", "green", "yellow", "green"]


def test_get_feedback_duplicate_letters_in_guess():
    result = get_feedback("SLEEP", "SLATE")
    # S=green, L=green (exact match at pos1), E=yellow, E=white (only one E in target), P=white
    assert result == ["green", "green", "yellow", "white", "white"]


def test_get_feedback_duplicate_letters_in_target():
    result = get_feedback("SLATE", "SHEEP")
    # S=green, L=white, A=white, T=white, E=yellow
    assert result == ["green", "white", "white", "white", "yellow"]


def test_get_feedback_duplicate_match_priority():
    # When guess has duplicate letter and target has one:
    # First occurrence gets priority for duplicates, but L also matches
    result = get_feedback("BANAL", "APPLE")
    # B=white, A=yellow (first A matched), N=white, A=white (no more A), L=yellow (L exists in target)
    assert result == ["white", "yellow", "white", "white", "yellow"]


def test_get_feedback_case_insensitive():
    result = get_feedback("slate", "SLATE")
    assert result == ["green", "green", "green", "green", "green"]


# --- render_board ---

def test_render_board_all_green():
    board = render_board(["SLATE"], "SLATE")
    expected = "\033[32mS\033[0m \033[32mL\033[0m \033[32mA\033[0m \033[32mT\033[0m \033[32mE\033[0m 🟩 🟩 🟩 🟩 🟩"
    assert board.strip() == expected


def test_render_board_all_white():
    board = render_board(["ABCDE"], "FGHIJ")
    expected = "A B C D E ⬜ ⬜ ⬜ ⬜ ⬜"
    assert board.strip() == expected


def test_render_board_mixed():
    board = render_board(["SLATE"], "STALE")
    # greens at 0,2,4 (S,A,E); yellows at 1,3 (L,T)
    assert "\033[32mS\033[0m" in board
    assert "\033[32mA\033[0m" in board
    assert "\033[32mE\033[0m" in board
    assert "\033[33mL\033[0m" in board
    assert "\033[33mT\033[0m" in board


def test_render_board_empty_guesses():
    board = render_board([], "SLATE")
    assert board == ""


def test_render_board_multiple_guesses():
    board = render_board(["ABCDE", "FGHIJ", "SLATE"], "SLATE")
    lines = board.strip().split("\n")
    assert len(lines) == 3


# --- MAX_GUESSES ---

def test_max_guesses_is_six():
    assert MAX_GUESSES == 6
