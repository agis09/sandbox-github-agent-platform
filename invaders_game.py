"""Pure game logic for a terminal Invaders game.

Standard library only and terminal independent so it can be unit tested
headless: :func:`step_game` advances the game by exactly one frame and
receives the clock explicitly, keeping the whole module deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# Default board
WIDTH = 40
HEIGHT = 18

# Enemy formation
ENEMY_ROWS = 3
ENEMY_COLS = 6
ENEMY_START_ROW = 1

# Rules
START_LIVES = 3
ENEMY_SCORE = 10
PLAYER_FIRE_COOLDOWN = 0.3  # seconds between player shots
MAX_PLAYER_BULLETS = 2
MAX_ENEMY_BULLETS = 3
ENEMY_FIRE_INTERVAL = 12  # frames between enemy shots
TICK = 0.1  # suggested seconds per frame (~10 FPS)

STATUS_RUNNING = "running"
STATUS_GAME_OVER = "game_over"
STATUS_VICTORY = "victory"


@dataclass(frozen=True)
class Bullet:
    """A single projectile; position on the board grid."""

    x: int
    y: int


@dataclass
class GameState:
    """Full game state; every field is plain data so states compare equal."""

    width: int
    height: int
    player_x: int
    lives: int
    score: int
    enemies: tuple[tuple[int, int], ...]
    sweep_dir: int = 1
    player_bullets: tuple[Bullet, ...] = field(default_factory=tuple)
    enemy_bullets: tuple[Bullet, ...] = field(default_factory=tuple)
    last_fire_time: float = -1e18
    frame: int = 0
    status: str = STATUS_RUNNING


def player_row(state: GameState) -> int:
    """The board row the player (and the shields of death) live on."""
    return state.height - 1


def spawn_formation(width: int, height: int) -> tuple[tuple[int, int], ...]:
    """Build the initial enemy block, centered horizontally."""
    start_col = max(0, (width - ENEMY_COLS) // 2)
    return tuple(
        (start_col + col, ENEMY_START_ROW + row)
        for row in range(ENEMY_ROWS)
        for col in range(ENEMY_COLS)
    )


def new_game(width: int = WIDTH, height: int = HEIGHT) -> GameState:
    """Return a fresh, running game state on the given board size."""
    return GameState(
        width=width,
        height=height,
        player_x=width // 2,
        lives=START_LIVES,
        score=0,
        enemies=spawn_formation(width, height),
    )


def _advance_enemies(state: GameState) -> tuple[tuple[tuple[int, int], ...], int]:
    """Sweep the formation one cell; at an edge, reverse and drop one row."""
    direction = state.sweep_dir
    blocked = any(
        x + direction < 0 or x + direction >= state.width for x, _ in state.enemies
    )
    if not blocked:
        return tuple((x + direction, y) for x, y in state.enemies), direction
    direction = -direction
    moved = []
    for x, y in state.enemies:
        next_x = x + direction
        if next_x < 0 or next_x >= state.width:
            next_x = x
        moved.append((next_x, y + 1))
    return tuple(moved), direction


def _enemy_shots(state: GameState) -> tuple[Bullet, ...]:
    """Deterministic enemy fire: every ENEMY_FIRE_INTERVAL frames the
    lowest, left-most surviving enemy drops one bullet."""
    if not state.enemies or state.frame % ENEMY_FIRE_INTERVAL != 0:
        return ()
    if len(state.enemy_bullets) >= MAX_ENEMY_BULLETS:
        return ()
    shooter = min(state.enemies, key=lambda pos: (-pos[1], pos[0]))
    return (Bullet(shooter[0], shooter[1] + 1),)


def _resolve_collisions(state: GameState) -> GameState:
    """Bullets vs enemies, enemy bullets vs player."""
    alive = list(state.enemies)
    surviving = []
    score = state.score
    for bullet in state.player_bullets:
        if (bullet.x, bullet.y) in alive:
            alive.remove((bullet.x, bullet.y))
            score += ENEMY_SCORE
        else:
            surviving.append(bullet)
    state = replace(state, enemies=tuple(alive), player_bullets=tuple(surviving), score=score)

    row = player_row(state)
    hit_player = any(b.x == state.player_x and b.y == row for b in state.enemy_bullets)
    if not hit_player:
        return state
    state = replace(state, lives=state.lives - 1)
    if state.lives <= 0:
        return replace(state, status=STATUS_GAME_OVER)
    return replace(
        state,
        enemies=spawn_formation(state.width, state.height),
        sweep_dir=1,
        player_x=state.width // 2,
        player_bullets=(),
        enemy_bullets=(),
    )


def step_game(
    state: GameState,
    player_move: int = 0,
    fire: bool = False,
    clock: float = 0.0,
) -> GameState:
    """Advance the game by one frame and return the new state.

    ``player_move`` is -1/0/+1, ``fire`` says whether the fire key was
    held, and ``clock`` is a monotonic timestamp in seconds (injected so
    tests can drive time deterministically). Terminal states are final:
    the same state is returned unchanged.
    """
    if state.status != STATUS_RUNNING:
        return state

    state = replace(state, frame=state.frame + 1)

    if player_move:
        state = replace(
            state,
            player_x=max(0, min(state.width - 1, state.player_x + int(player_move))),
        )

    if (
        fire
        and clock - state.last_fire_time >= PLAYER_FIRE_COOLDOWN
        and len(state.player_bullets) < MAX_PLAYER_BULLETS
    ):
        state = replace(
            state,
            player_bullets=state.player_bullets
            + (Bullet(state.player_x, state.height - 2),),
            last_fire_time=clock,
        )

    state = replace(
        state,
        player_bullets=tuple(
            bullet for bullet in (replace(b, y=b.y - 1) for b in state.player_bullets)
            if bullet.y >= 0
        ),
        enemy_bullets=tuple(
            bullet for bullet in (replace(b, y=b.y + 1) for b in state.enemy_bullets)
            if bullet.y < state.height
        ),
    )

    state.enemies, state.sweep_dir = _advance_enemies(state)
    shots = _enemy_shots(state)
    if shots:
        state = replace(state, enemy_bullets=state.enemy_bullets + shots)

    state = _resolve_collisions(state)

    if state.status == STATUS_RUNNING:
        if any(y >= player_row(state) for _, y in state.enemies):
            state = replace(state, status=STATUS_GAME_OVER)
        elif not state.enemies:
            state = replace(state, status=STATUS_VICTORY)
    return state
