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
