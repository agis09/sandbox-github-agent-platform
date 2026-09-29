"""Headless unit tests for the pure invaders_game logic."""

import unittest

from invaders_game import (
    ENEMY_COLS,
    ENEMY_ROWS,
    ENEMY_SCORE,
    HEIGHT,
    MAX_PLAYER_BULLETS,
    PLAYER_FIRE_COOLDOWN,
    START_LIVES,
    STATUS_GAME_OVER,
    STATUS_RUNNING,
    STATUS_VICTORY,
    WIDTH,
    Bullet,
    GameState,
    new_game,
    player_row,
    spawn_formation,
    step_game,
)


def run_script(n_frames: int, fire_every: int = 5) -> GameState:
    """Drive a fresh game with a fixed deterministic input sequence."""
    state = new_game()
    for frame in range(1, n_frames + 1):
        move = (frame % 3) - 1
        fire = frame % fire_every == 0
        state = step_game(state, move, fire, frame * 0.1)
        if state.status != STATUS_RUNNING:
            break
    return state


class NewGameTest(unittest.TestCase):
    def test_initial_state_invariants(self) -> None:
        state = new_game()
        self.assertEqual(state.status, STATUS_RUNNING)
        self.assertEqual(state.lives, START_LIVES)
        self.assertEqual(state.score, 0)
        self.assertEqual(state.frame, 0)
        self.assertEqual(state.player_x, WIDTH // 2)
        self.assertEqual(len(state.enemies), ENEMY_ROWS * ENEMY_COLS)
        self.assertEqual(state.sweep_dir, 1)
        self.assertEqual(state.player_bullets, ())
        self.assertEqual(state.enemy_bullets, ())
        xs = {x for x, _ in state.enemies}
        ys = {y for _, y in state.enemies}
        self.assertEqual(len(xs), ENEMY_COLS)
        self.assertEqual(len(ys), ENEMY_ROWS)
        for x, y in state.enemies:
            self.assertGreaterEqual(x, 0)
            self.assertLess(x, WIDTH)
            self.assertGreaterEqual(y, 0)
            self.assertLess(y, player_row(state))

    def test_formation_centered_on_custom_board(self) -> None:
        formation = spawn_formation(24, 12)
        self.assertEqual(len(formation), ENEMY_ROWS * ENEMY_COLS)
        xs = sorted({x for x, _ in formation})
        self.assertEqual(len(xs), ENEMY_COLS)
        self.assertEqual(min(xs) + max(xs), 24 - 1)
        state = new_game(24, 12)
        self.assertEqual(state.player_x, 12)
        self.assertEqual(player_row(state), 11)
        for _, y in state.enemies:
            self.assertLess(y, 11)


class PlayerMovementTest(unittest.TestCase):
    def test_player_moves_and_clamps_at_boundaries(self) -> None:
        state = new_game()
        for i in range(1, 101):
            state = step_game(state, 1, False, i * 0.1)
            self.assertLess(state.player_x, WIDTH)
        self.assertEqual(state.player_x, WIDTH - 1)

        state = new_game()
        for i in range(1, 101):
            state = step_game(state, -1, False, i * 0.1)
            self.assertGreaterEqual(state.player_x, 0)
        self.assertEqual(state.player_x, 0)


class BulletTest(unittest.TestCase):
    def test_fire_spawns_bullet_that_travels_up(self) -> None:
        state = new_game()
        fired = step_game(state, 0, True, 0.0)
        # a bullet spawns one row above the player and moves in the same frame
        self.assertEqual(fired.player_bullets, (Bullet(state.player_x, HEIGHT - 3),))
        self.assertEqual(fired.last_fire_time, 0.0)

        moved = step_game(fired, 0, False, 0.1)
        self.assertEqual(moved.player_bullets, (Bullet(state.player_x, HEIGHT - 4),))

        leaving = moved
        for i in range(1, HEIGHT + 1):
            leaving = step_game(leaving, 0, False, (i + 1) * 0.1)
        self.assertEqual(leaving.player_bullets, ())

    def test_cannot_fire_inside_cooldown(self) -> None:
        state = new_game()
        state = step_game(state, 0, True, 0.0)
        state = step_game(state, 0, True, 0.1)
        self.assertEqual(len(state.player_bullets), 1)
        self.assertEqual(state.last_fire_time, 0.0)

    def test_player_bullet_cap(self) -> None:
        state = new_game()
        state = step_game(state, 0, True, 0.0)
        state = step_game(state, 0, True, PLAYER_FIRE_COOLDOWN)
        self.assertEqual(len(state.player_bullets), MAX_PLAYER_BULLETS)
        state = step_game(state, 0, True, PLAYER_FIRE_COOLDOWN * 2)
        self.assertEqual(len(state.player_bullets), MAX_PLAYER_BULLETS)
        self.assertEqual(state.last_fire_time, PLAYER_FIRE_COOLDOWN)


class EnemyMovementTest(unittest.TestCase):
    def test_enemies_sweep_then_descend_and_reverse(self) -> None:
        prev = new_game()
        descended = False
        for i in range(1, 60):
            cur = step_game(prev, 0, False, i * 0.1)
            if cur.sweep_dir != prev.sweep_dir:
                self.assertEqual(cur.sweep_dir, -1)
                for (px, py), (_, cy) in zip(prev.enemies, cur.enemies):
                    self.assertEqual(cy, py + 1)
                descended = True
                break
            for (px, py), (cx, cy) in zip(prev.enemies, cur.enemies):
                self.assertEqual(cx, px + prev.sweep_dir)
                self.assertEqual(cy, py)
            prev = cur
        self.assertTrue(descended, "enemies never reached an edge within 60 frames")


class CollisionTest(unittest.TestCase):
    def test_bullet_kills_enemy_and_scores(self) -> None:
        state = new_game()
        # Single enemy sweeps right at 1 cell/frame; the bullet fired from
        # x=23 on frame 1 rises 1 cell/frame and meets it exactly on frame 13.
        state.player_x = 23
        state.enemies = ((10, 3),)
        state.sweep_dir = 1
        state = step_game(state, 0, True, 0.0)
        for i in range(1, 20):
            state = step_game(state, 0, False, i * 0.1)
            if state.status != STATUS_RUNNING:
                break
        self.assertEqual(state.status, STATUS_VICTORY)
        self.assertEqual(state.score, ENEMY_SCORE)
        self.assertEqual(state.enemies, ())

    def test_enemy_bullet_hits_player_and_resets_wave(self) -> None:
        state = new_game()
        state.player_x = 5
        state.enemies = ((5, 4),)
        state.sweep_dir = -1
        state.enemy_bullets = (Bullet(5, HEIGHT - 2),)
        state = step_game(state, 0, False, 0.0)
        self.assertEqual(state.lives, START_LIVES - 1)
        self.assertEqual(state.status, STATUS_RUNNING)
        self.assertEqual(len(state.enemies), ENEMY_ROWS * ENEMY_COLS)
        self.assertEqual(state.player_x, WIDTH // 2)
        self.assertEqual(state.player_bullets, ())
        self.assertEqual(state.enemy_bullets, ())

    def test_all_lives_lost_is_game_over(self) -> None:
        state = new_game()
        for _ in range(START_LIVES):
            state.player_x = 5
            state.enemies = ((5, 4),)
            state.sweep_dir = -1
            state.enemy_bullets = (Bullet(5, HEIGHT - 2),)
            state = step_game(state, 0, False, 0.0)
        self.assertEqual(state.status, STATUS_GAME_OVER)
        self.assertEqual(state.lives, 0)

    def test_enemy_reaching_player_row_is_game_over(self) -> None:
        state = new_game()
        state.enemies = ((WIDTH - 1, HEIGHT - 2),)
        state.sweep_dir = 1  # blocked at the right edge, so it drops
        state = step_game(state, 0, False, 0.0)
        self.assertEqual(state.status, STATUS_GAME_OVER)
        self.assertEqual(state.lives, START_LIVES)

    def test_enemy_bullets_removed_off_screen(self) -> None:
        state = new_game()
        state.enemies = ((0, 1),)
        state.sweep_dir = -1
        state.enemy_bullets = (Bullet(5, HEIGHT - 1),)
        state = step_game(state, 0, False, 0.0)
        self.assertEqual(state.enemy_bullets, ())
        self.assertEqual(state.status, STATUS_RUNNING)


class TerminalStateTest(unittest.TestCase):
    def test_terminal_states_are_frozen(self) -> None:
        state = new_game()
        state.enemies = ((WIDTH - 1, HEIGHT - 2),)
        state = step_game(state, 0, False, 0.0)
        self.assertEqual(state.status, STATUS_GAME_OVER)
        self.assertIs(step_game(state, 1, True, 1.0), state)

        victory = new_game()
        victory.player_x = 23
        victory.enemies = ((10, 3),)
        victory = step_game(victory, 0, True, 0.0)
        for i in range(1, 20):
            victory = step_game(victory, 0, False, i * 0.1)
            if victory.status != STATUS_RUNNING:
                break
        self.assertEqual(victory.status, STATUS_VICTORY)
        self.assertIs(step_game(victory, -1, True, 2.0), victory)

    def test_deterministic_replay(self) -> None:
        self.assertEqual(run_script(200), run_script(200))


class InvariantTest(unittest.TestCase):
    def test_invariants_hold_over_many_frames(self) -> None:
        state = new_game()
        for frame in range(1, 301):
            move = (frame % 3) - 1
            fire = frame % 10 == 0
            state = step_game(state, move, fire, frame * 0.1)
            self.assertGreaterEqual(state.player_x, 0)
            self.assertLess(state.player_x, state.width)
            self.assertGreaterEqual(state.score, 0)
            self.assertGreaterEqual(state.lives, 0)
            self.assertLessEqual(state.lives, START_LIVES)
            for x, y in state.enemies:
                self.assertGreaterEqual(x, 0)
                self.assertLess(x, state.width)
                self.assertGreaterEqual(y, 0)
                self.assertLess(y, state.height)
            for bullet in state.player_bullets:
                self.assertGreaterEqual(bullet.y, 0)
                self.assertLess(bullet.y, state.height)
            for bullet in state.enemy_bullets:
                self.assertGreaterEqual(bullet.y, 0)
                self.assertLess(bullet.y, state.height)
            if state.status != STATUS_RUNNING:
                break


if __name__ == "__main__":
    unittest.main()
