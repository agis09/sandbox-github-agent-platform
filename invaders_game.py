"""Terminal Space Invaders.

Pure, unit-testable game logic (board, state, movement, shooting, ticking)
plus a thin ``curses`` terminal UI. Stdlib only; importing this module does
not start the game loop.

Run with: python invaders_game.py
Controls: <- / -> (or a / d) to move, space to shoot, q to quit.
"""

from __future__ import annotations

import curses
import sys
from dataclasses import dataclass, field

BOARD_WIDTH = 40
BOARD_HEIGHT = 20
PLAYER_ROW = BOARD_HEIGHT - 1

ENEMY_ROWS = 3
ENEMY_COLS = 6
ENEMY_START_ROW = 1
ENEMY_START_COL = BOARD_WIDTH // 2 - ENEMY_COLS // 2

SCORE_PER_ENEMY = 10
DESCEND_EVERY = 4
TICK_MS = 100

PLAYER_SYMBOL = "M"
ENEMY_SYMBOL = "X"
BULLET_SYMBOL = "|"
EMPTY_SYMBOL = "."

CONTROL_HINT = "arrows/a d: move   space: shoot   q: quit"


@dataclass
class GameState:
    """Mutable state of a single game."""

    player_x: int
    enemies: list[tuple[int, int]] = field(default_factory=list)
    bullets: list[tuple[int, int]] = field(default_factory=list)
    score: int = 0
    ticks: int = 0
    game_over: bool = False
    victory: bool = False

    @property
    def finished(self) -> bool:
        return self.game_over or self.victory


def _initial_enemies() -> list[tuple[int, int]]:
    enemies: list[tuple[int, int]] = []
    for row in range(ENEMY_START_ROW, ENEMY_START_ROW + ENEMY_ROWS):
        for col in range(ENEMY_START_COL, ENEMY_START_COL + ENEMY_COLS):
            enemies.append((col, row))
    return enemies


def new_game() -> GameState:
    """Create a fresh game with the player centered and a full enemy formation."""
    return GameState(player_x=BOARD_WIDTH // 2, enemies=_initial_enemies())


def move_player(state: GameState, dx: int) -> GameState:
    """Move the player left/right, clamped to the board. No-op once finished."""
    if state.finished:
        return state
    state.player_x = max(0, min(BOARD_WIDTH - 1, state.player_x + dx))
    return state


def shoot(state: GameState) -> GameState:
    """Fire one bullet above the player. Only one active bullet at a time."""
    if state.finished or state.bullets:
        return state
    state.bullets.append((state.player_x, PLAYER_ROW - 1))
    return state


def tick(state: GameState) -> GameState:
    """Advance the game by one step.

    Bullets fly up and off the board, a bullet on an enemy destroys both and
    adds to the score, enemies descend one row every ``DESCEND_EVERY`` ticks,
    and the game ends when an invader reaches the player row (or when the
    formation is wiped out, a victory).
    """
    if state.finished:
        return state
    state.ticks += 1

    survivors: list[tuple[int, int]] = []
    for x, y in state.bullets:
        moved = (x, y - 1)
        if moved in state.enemies:
            state.enemies.remove(moved)
            state.score += SCORE_PER_ENEMY
        elif moved[1] >= 0:
            survivors.append(moved)
    state.bullets = survivors

    if state.ticks % DESCEND_EVERY == 0:
        state.enemies = [(x, y + 1) for x, y in state.enemies]

    if any(y >= PLAYER_ROW for _, y in state.enemies):
        state.game_over = True
        state.bullets = []
    elif not state.enemies:
        state.victory = True

    return state


def render(state: GameState) -> str:
    """Render the board as plain text (``BOARD_HEIGHT`` lines of ``BOARD_WIDTH``)."""
    grid = [[EMPTY_SYMBOL] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
    for x, y in state.enemies:
        grid[y][x] = ENEMY_SYMBOL
    for x, y in state.bullets:
        grid[y][x] = BULLET_SYMBOL
    grid[PLAYER_ROW][state.player_x] = PLAYER_SYMBOL
    return "\n".join("".join(row) for row in grid)


def _draw(stdscr: "curses._CursesWindow", state: GameState) -> None:
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()
    lines = [f"Space Invaders   Score: {state.score}"]
    lines += render(state).splitlines()
    lines += ["", CONTROL_HINT]
    for y, line in enumerate(lines):
        if y + 1 >= max_y:
            break
        stdscr.addstr(y, 0, line[: max_x - 1])
    stdscr.refresh()


def _run(stdscr: "curses._CursesWindow") -> None:
    try:
        curses.curs_set(0)
    except curses.error:
        pass  # terminal without cursor-hiding support (e.g. TERM=dumb)
    stdscr.keypad(True)
    stdscr.timeout(TICK_MS)
    state = new_game()

    while True:
        key = stdscr.getch()
        if key == ord("q"):
            break
        if key in (curses.KEY_LEFT, ord("a")):
            move_player(state, -1)
        elif key in (curses.KEY_RIGHT, ord("d")):
            move_player(state, +1)
        elif key == ord(" "):
            shoot(state)
        tick(state)
        _draw(stdscr, state)
        if state.finished:
            break

    message = "YOU WIN!" if state.victory else "GAME OVER"
    stdscr.nodelay(False)
    stdscr.addstr(0, 0, f"{message}   Final score: {state.score}")
    stdscr.addstr(1, 0, "Press any key to quit.")
    stdscr.refresh()
    stdscr.getch()


def main() -> int:
    try:
        curses.wrapper(_run)
    except curses.error as exc:
        print(f"terminal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
