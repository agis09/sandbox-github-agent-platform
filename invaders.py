"""A tiny terminal Space Invaders clone (Python standard library only).

The game logic lives in :class:`Game`, a pure class with no terminal or
I/O dependencies, so it can be unit-tested without a TTY (see
``test_invaders.py``). Rendering and key handling are thin layers around
it: frames are redrawn with ANSI cursor-home after every keypress, and
each keypress advances the world by one tick (:meth:`Game.step`).

Controls
--------
left arrow / h     move left
right arrow / l    move right
space / j          fire
q                  quit
r                  restart (on the game-over screen)

Run with ``python invaders.py``. Importing this module has no side
effects; the terminal is only touched when it is executed as a script.
"""

from __future__ import annotations

import select
import sys

WIDTH = 20
HEIGHT = 10
ENEMY_ROWS = 3
ENEMY_COLS = 5
ENEMY_FIRST_X = 2
ENEMY_SPACING = 2
BULLET_SCORE = 10

ENEMY_CHAR = "M"
PLAYER_CHAR = "^"
BULLET_CHAR = "|"

ANSI_HOME = "\x1b[H"
ANSI_CLEAR = "\x1b[2J"

_ARROW_KEYS = {"A": "up", "B": "down", "C": "right", "D": "left"}
_KEY_MAP = {
    "h": "left",
    "l": "right",
    " ": "fire",
    "j": "fire",
    "left": "left",
    "right": "right",
    "fire": "fire",
    "restart": "restart",
    "q": "quit",
    "quit": "quit",
    "r": "restart",
}


class Game:
    """Pure Space Invaders game state (no I/O)."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Start a new game: fresh fleet, centered player, zero score."""
        self.width = WIDTH
        self.height = HEIGHT
        self.score = 0
        self.game_over = False
        self.player_x = self.width // 2
        self.player_row = self.height - 1
        self.bullets: list[tuple[int, int]] = []
        self.enemies: set[tuple[int, int]] = set()
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = ENEMY_FIRST_X + col * ENEMY_SPACING
                if x < self.width:
                    self.enemies.add((x, row))

    def move_player(self, dx: int) -> None:
        """Move the player ``dx`` columns, clamped to the board edges."""
        if not self.game_over:
            self.player_x = max(0, min(self.width - 1, self.player_x + dx))

    def fire(self) -> None:
        """Spawn a bullet just above the player."""
        if not self.game_over:
            self.bullets.append((self.player_x, self.player_row - 1))

    def step(self) -> None:
        """Advance the world one tick.

        Bullets rise (and vanish past the top edge), the enemy fleet
        descends one row, hits are resolved, and the game ends when an
        enemy reaches the player row.
        """
        if self.game_over:
            return

        moved_bullets = [(x, y - 1) for (x, y) in self.bullets if y > 0]
        moved_enemies = {(x, y + 1) for (x, y) in self.enemies}

        # A bullet hits when it lands on an enemy's new cell, or when it
        # and the enemy swap rows this tick (bullet's new cell equals the
        # enemy's old cell).
        hit_positions = [
            bullet
            for bullet in moved_bullets
            if bullet in moved_enemies or bullet in self.enemies
        ]
        destroyed = set()
        for (x, y) in hit_positions:
            if (x, y) in moved_enemies:
                destroyed.add((x, y))
            if (x, y) in self.enemies:
                destroyed.add((x, y + 1))

        self.bullets = [b for b in moved_bullets if b not in hit_positions]
        self.enemies = moved_enemies - destroyed
        self.score += BULLET_SCORE * len(destroyed)

        if any(y >= self.player_row for (_, y) in self.enemies):
            self.game_over = True


def render_frame(game: Game) -> str:
    """Return the board as plain text with a fixed score header line."""
    grid = [[" "] * game.width for _ in range(game.height)]
    for (x, y) in game.enemies:
        if 0 <= x < game.width and 0 <= y < game.height:
            grid[y][x] = ENEMY_CHAR
    for (x, y) in game.bullets:
        if 0 <= x < game.width and 0 <= y < game.height:
            grid[y][x] = BULLET_CHAR
    grid[game.player_row][game.player_x] = PLAYER_CHAR
    lines = [f"INVADERS   score: {game.score}"]
    lines.extend("  " + "".join(row) for row in grid)
    return "\n".join(lines)


def _use_tty() -> bool:
    """True on POSIX when stdin is a terminal (single-char reads usable)."""
    try:
        import termios  # noqa: F401  (POSIX only)
    except ImportError:
        return False
    return sys.stdin.isatty()


def _read_char_tty() -> str:
    """Read one raw character in cbreak mode, decoding arrow keys."""
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd, termios.TCSANOW)
        char = sys.stdin.read(1)
        if char != "\x1b":
            return char
        if select.select([sys.stdin], [], [], 0.05):
            if sys.stdin.read(1) == "[":
                return _ARROW_KEYS.get(sys.stdin.read(1), "none")
        return "none"
    finally:
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)


def _read_key_line() -> str:
    """Non-TTY fallback: read a whole line and map it to a logical key."""
    try:
        line = input().strip().lower()
    except EOFError:
        return "quit"
    return _KEY_MAP.get(line, "none")


def read_key() -> str:
    """Read one keypress and return its logical name.

    Returns one of ``left``, ``right``, ``fire``, ``restart``, ``quit``
    or ``none``.
    """
    if _use_tty():
        return _KEY_MAP.get(_read_char_tty(), "none")
    return _read_key_line()


def _draw(game: Game, use_tty: bool) -> None:
    frame = render_frame(game)
    if game.game_over:
        frame += (
            f"\n\n  GAME OVER - final score: {game.score}"
            "\n  (r)estart or (q)uit"
        )
    sys.stdout.write((ANSI_HOME if use_tty else "\n\n") + frame)
    sys.stdout.flush()


def play_session() -> int:
    """Run one play session (with restart) until the player quits."""
    game = Game()
    use_tty = _use_tty()
    if use_tty:
        sys.stdout.write(ANSI_CLEAR)
    while True:
        _draw(game, use_tty)
        key = read_key()
        if key == "quit":
            break
        if game.game_over:
            if key == "restart":
                game.reset()
            continue
        if key == "left":
            game.move_player(-1)
        elif key == "right":
            game.move_player(1)
        elif key == "fire":
            game.fire()
        game.step()
    if use_tty:
        sys.stdout.write(ANSI_CLEAR)
    print(f"Final score: {game.score} - thanks for playing!")
    return 0


def main() -> int:
    try:
        return play_session()
    except KeyboardInterrupt:
        print("\nInterrupted - thanks for playing!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
