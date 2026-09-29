"""A tiny terminal Space Invaders game built on the standard library only.

The game logic (class :class:`Game`) is kept completely separate from
I/O so it can be unit tested without a terminal (see
``test_invader_game.py``).  Run ``python invader_game.py`` in an
interactive terminal to play; the README documents the controls.
"""

from __future__ import annotations

import random
import sys

WIDTH = 40
HEIGHT = 14
ENEMY_ROWS = 3
ENEMY_COLS = 8
PLAYER_LIVES = 3
ENEMY_TOP = 1
KILL_SCORE = 10

ENEMY_CHAR = "M"
PLAYER_CHAR = "@"
BULLET_CHAR = "|"
ENEMY_BULLET_CHAR = "o"


class Game:
    """Pure game logic for a small Space Invaders variant.

    The board is ``width`` columns by ``height`` rows.  Row 0 and row
    ``height - 1`` are walls.  The player stands on row ``player_row``
    (``height - 2``) and can move within columns ``1 .. width - 2``.
    The enemy formation starts near the top and drifts horizontally;
    whenever it reaches an edge it descends by one row.  The game ends
    when the player runs out of lives, the formation reaches the
    player's row, or every enemy is destroyed.
    """

    def __init__(
        self,
        width: int = WIDTH,
        height: int = HEIGHT,
        formation_interval: int = 3,
        enemy_fire_chance: float = 0.05,
        rng: random.Random | None = None,
    ) -> None:
        if width < 8 or height < 6:
            raise ValueError("board must be at least 8x6")
        if not 0.0 <= enemy_fire_chance <= 1.0:
            raise ValueError("enemy_fire_chance must be within [0, 1]")
        self.width = width
        self.height = height
        self.formation_interval = formation_interval
        self.enemy_fire_chance = enemy_fire_chance
        self.rng = rng if rng is not None else random.Random()
        self.reset()

    # ------------------------------------------------------------------ #
    # state
    # ------------------------------------------------------------------ #

    def reset(self) -> None:
        """(Re)initialise the board to its starting state."""
        self.player_x = self.width // 2
        self.lives = PLAYER_LIVES
        self.score = 0
        self.tick = 0
        self.direction = 1
        self.running = True
        self.won = False
        self.lost = False
        self.player_bullets: list[tuple[int, int]] = []
        self.enemy_bullets: list[tuple[int, int]] = []
        left = (self.width - ENEMY_COLS) // 2
        self.enemies: list[tuple[int, int]] = [
            (left + x, ENEMY_TOP + y)
            for y in range(ENEMY_ROWS)
            for x in range(ENEMY_COLS)
        ]

    def restart(self) -> None:
        self.reset()

    @property
    def player_row(self) -> int:
        return self.height - 2

    @property
    def finished(self) -> bool:
        return not self.running

    @property
    def game_over(self) -> bool:
        return self.won or self.lost

    # ------------------------------------------------------------------ #
    # player actions
    # ------------------------------------------------------------------ #

    def move_player(self, dx: int) -> None:
        """Move the player ``dx`` columns, clamped to the play field."""
        if not self.running:
            return
        self.player_x = max(1, min(self.width - 2, self.player_x + dx))

    def fire(self) -> bool:
        """Fire one bullet straight up.  Only one may be in flight.

        Returns True if a bullet was actually fired.
        """
        if not self.running or self.player_bullets:
            return False
        self.player_bullets.append((self.player_x, self.player_row - 1))
        return True

    # ------------------------------------------------------------------ #
    # simulation
    # ------------------------------------------------------------------ #

    def step(self) -> None:
        """Advance the game by one tick."""
        if not self.running:
            return
        self.tick += 1
        self._move_player_bullets()
        self._move_formation()
        self._maybe_enemies_fire()
        self._move_enemy_bullets()
        self._resolve_collisions()
        self._evaluate()

    def _move_player_bullets(self) -> None:
        self.player_bullets = [
            (x, y - 1) for x, y in self.player_bullets if y - 1 >= 1
        ]

    def _move_formation(self) -> None:
        if not self.enemies or self.tick % self.formation_interval != 0:
            return
        xs = [x for x, _ in self.enemies]
        if self.direction > 0 and max(xs) + 1 > self.width - 2:
            self.direction = -1
            self._descend_formation()
            return
        if self.direction < 0 and min(xs) - 1 < 1:
            self.direction = 1
            self._descend_formation()
            return
        self.enemies = [(x + self.direction, y) for x, y in self.enemies]

    def _descend_formation(self) -> None:
        self.enemies = [(x, y + 1) for x, y in self.enemies]

    def _maybe_enemies_fire(self) -> None:
        if not self.enemies or self.rng.random() >= self.enemy_fire_chance:
            return
        x, y = self.enemies[self.rng.randrange(len(self.enemies))]
        if y + 1 > self.player_row:
            return
        if (x, y + 1) in self.enemy_bullets:
            return
        self.enemy_bullets.append((x, y + 1))

    def _move_enemy_bullets(self) -> None:
        kept: list[tuple[int, int]] = []
        for x, y in self.enemy_bullets:
            y += 1
            if y >= self.height - 1:
                continue
            kept.append((x, y))
        self.enemy_bullets = kept

    def _resolve_collisions(self) -> None:
        enemy_cells = set(self.enemies)
        remaining: list[tuple[int, int]] = []
        killed = False
        for x, y in self.player_bullets:
            if (x, y) in enemy_cells:
                enemy_cells.discard((x, y))
                self.score += KILL_SCORE
                killed = True
            else:
                remaining.append((x, y))
        if killed:
            self.enemies = sorted(enemy_cells)
        self.player_bullets = remaining
        self._check_player_hit()

    def _check_player_hit(self) -> None:
        target = (self.player_x, self.player_row)
        hit = target in self.enemy_bullets or target in set(self.enemies)
        if not hit:
            return
        self.lives -= 1
        self.enemy_bullets = []
        self.player_x = self.width // 2
        if self.lives <= 0:
            self.running = False
            self.lost = True

    def _evaluate(self) -> None:
        if not self.running:
            return
        if not self.enemies:
            self.running = False
            self.won = True
            return
        if any(y >= self.player_row for _, y in self.enemies):
            self.running = False
            self.lost = True


# ---------------------------------------------------------------------- #
# rendering (pure text, no I/O)
# ---------------------------------------------------------------------- #


def build_frame(game: Game) -> str:
    """Render the play field as a block of plain text."""
    field = [[" "] * game.width for _ in range(game.height)]
    for x, y in game.enemies:
        if 1 <= y < game.height - 1:
            field[y][x] = ENEMY_CHAR
    for x, y in game.enemy_bullets:
        if 1 <= y < game.height - 1:
            field[y][x] = ENEMY_BULLET_CHAR
    for x, y in game.player_bullets:
        if 1 <= y < game.height - 1:
            field[y][x] = BULLET_CHAR
    if not game.lost:
        field[game.player_row][game.player_x] = PLAYER_CHAR
    lines = ["-" * game.width]
    lines.extend("".join(row) for row in field[1 : game.height - 1])
    lines.append("-" * game.width)
    return "\n".join(lines)


def build_hud(game: Game) -> str:
    return f"Score: {game.score}   Lives: {game.lives}"


# ---------------------------------------------------------------------- #
# terminal front-end (only used when run as a script)
# ---------------------------------------------------------------------- #


def read_key(timeout: float) -> str | None:
    """Read one keypress or arrow-key escape sequence; None on timeout."""
    import select

    if not select.select([sys.stdin], [], [], timeout)[0]:
        return None
    ch = sys.stdin.read(1)
    if ch != "\x1b":
        return ch
    seq = ch
    while select.select([sys.stdin], [], [], 0.02)[0]:
        nxt = sys.stdin.read(1)
        seq += nxt
        if len(seq) >= 3 and nxt in "ABCD":
            return seq
    return seq  # bare ESC (no sequence followed)


def _draw(game: Game) -> None:
    help_text = "arrows/a d: move   space: fire   q: quit"
    if game.game_over:
        help_text += "   r: restart"
    lines = [build_hud(game), "", build_frame(game), "", help_text]
    if game.game_over:
        lines.append("GAME OVER" if game.lost else "YOU WIN!")
        lines.append(f"final score: {game.score}")
    text = "\n".join(line.ljust(game.width) for line in lines) + "\n"
    sys.stdout.write("\x1b[H" + text)
    sys.stdout.flush()


def _game_loop(game: Game) -> None:
    frame_delay = 0.1
    sys.stdout.write("\x1b[2J")
    sys.stdout.flush()
    while True:
        game.step()
        _draw(game)
        key = read_key(frame_delay)
        if key is None:
            continue
        if key in ("q", "Q", "\x03"):
            return
        if game.game_over:
            if key in ("r", "R", "\r", "\n"):
                game.restart()
            continue
        if key in ("\x1b[D", "a", "A"):
            game.move_player(-1)
        elif key in ("\x1b[C", "d", "D"):
            game.move_player(1)
        elif key in (" ", "\r", "\n"):
            game.fire()


def run_interactive() -> int:
    """Run the game in the current terminal.  Returns a process exit code."""
    if not sys.stdin.isatty():
        print(
            "invader_game.py needs an interactive terminal (stdin must be a TTY).\n"
            "Run it directly in a terminal:  python invader_game.py"
        )
        return 1
    import termios
    import tty

    game = Game()
    fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        _game_loop(game)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
    print(f"\nThanks for playing!  Final score: {game.score}")
    return 0


def main() -> int:
    try:
        return run_interactive()
    except KeyboardInterrupt:
        print("\nBye!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
