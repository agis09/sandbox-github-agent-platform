"""Tests for invaders_game (pure game logic; the curses UI is not exercised)."""

import unittest

from invaders_game import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    BULLET_SYMBOL,
    DESCEND_EVERY,
    EMPTY_SYMBOL,
    ENEMY_COLS,
    ENEMY_ROWS,
    ENEMY_SYMBOL,
    PLAYER_ROW,
    PLAYER_SYMBOL,
    SCORE_PER_ENEMY,
    move_player,
    new_game,
    render,
    shoot,
    tick,
)


class NewGameTest(unittest.TestCase):
    def test_initial_state(self):
        state = new_game()
        self.assertEqual(state.player_x, BOARD_WIDTH // 2)
        self.assertEqual(len(state.enemies), ENEMY_ROWS * ENEMY_COLS)
        self.assertEqual(state.bullets, [])
        self.assertEqual(state.score, 0)
        self.assertEqual(state.ticks, 0)
        self.assertFalse(state.game_over)
        self.assertFalse(state.victory)

    def test_initial_enemies_are_on_board_and_above_player(self):
        state = new_game()
        for x, y in state.enemies:
            self.assertTrue(0 <= x < BOARD_WIDTH)
            self.assertTrue(0 <= y < PLAYER_ROW)


class MovePlayerTest(unittest.TestCase):
    def test_clamps_left_edge(self):
        state = new_game()
        move_player(state, -BOARD_WIDTH * 2)
        self.assertEqual(state.player_x, 0)

    def test_clamps_right_edge(self):
        state = new_game()
        move_player(state, BOARD_WIDTH * 2)
        self.assertEqual(state.player_x, BOARD_WIDTH - 1)

    def test_small_moves_accumulate(self):
        state = new_game()
        start = state.player_x
        move_player(state, -2)
        self.assertEqual(state.player_x, start - 2)
        move_player(state, +3)
        self.assertEqual(state.player_x, start + 1)

    def test_no_move_after_game_over(self):
        state = new_game()
        state.game_over = True
        move_player(state, 1)
        self.assertEqual(state.player_x, BOARD_WIDTH // 2)


class ShootTest(unittest.TestCase):
    def test_bullet_starts_above_player(self):
        state = new_game()
        shoot(state)
        self.assertEqual(state.bullets, [(state.player_x, PLAYER_ROW - 1)])

    def test_only_one_bullet_at_a_time(self):
        state = new_game()
        shoot(state)
        shoot(state)
        self.assertEqual(len(state.bullets), 1)

    def test_cannot_shoot_when_finished(self):
        state = new_game()
        state.game_over = True
        shoot(state)
        self.assertEqual(state.bullets, [])


class BulletTest(unittest.TestCase):
    def test_bullet_moves_up_each_tick(self):
        state = new_game()
        state.enemies = [(0, 1)]  # off to the side, never hit
        shoot(state)
        tick(state)
        self.assertEqual(state.bullets, [(state.player_x, PLAYER_ROW - 2)])

    def test_bullet_leaves_the_board(self):
        state = new_game()
        state.enemies = [(0, 1)]
        shoot(state)
        for _ in range(PLAYER_ROW + 1):
            tick(state)
        self.assertEqual(state.bullets, [])


class CollisionTest(unittest.TestCase):
    def test_hit_removes_enemy_and_adds_score(self):
        state = new_game()
        state.enemies = [(state.player_x, PLAYER_ROW - 3), (0, 1)]
        shoot(state)
        tick(state)  # bullet moves from PLAYER_ROW - 1 to PLAYER_ROW - 2
        tick(state)  # bullet reaches the invader at PLAYER_ROW - 3
        self.assertEqual(state.score, SCORE_PER_ENEMY)
        self.assertEqual(state.enemies, [(0, 1)])
        self.assertEqual(state.bullets, [])

    def test_victory_when_all_enemies_defeated(self):
        state = new_game()
        state.enemies = [(state.player_x, PLAYER_ROW - 3)]
        shoot(state)
        tick(state)
        tick(state)
        self.assertTrue(state.victory)
        self.assertFalse(state.game_over)
        self.assertEqual(state.score, SCORE_PER_ENEMY)


class DescentTest(unittest.TestCase):
    def test_enemies_hold_position_before_interval(self):
        state = new_game()
        initial = set(state.enemies)
        for _ in range(DESCEND_EVERY - 1):
            tick(state)
        self.assertEqual(set(state.enemies), initial)

    def test_enemies_descend_one_row_every_interval(self):
        state = new_game()
        initial = new_game().enemies
        for _ in range(DESCEND_EVERY):
            tick(state)
        self.assertEqual(set(state.enemies), {(x, y + 1) for x, y in initial})


class GameOverTest(unittest.TestCase):
    def test_game_over_when_enemies_reach_player_row(self):
        state = new_game()
        state.enemies = [(0, 1), (state.player_x, PLAYER_ROW - 1)]
        for _ in range(DESCEND_EVERY):
            tick(state)
        self.assertTrue(state.game_over)
        self.assertFalse(state.victory)

    def test_state_frozen_after_game_over(self):
        state = new_game()
        state.enemies = [(0, PLAYER_ROW - 1)]
        for _ in range(DESCEND_EVERY):
            tick(state)
        self.assertTrue(state.game_over)
        snapshot = (state.score, list(state.enemies), list(state.bullets), state.player_x)
        tick(state)
        tick(state)
        move_player(state, 1)
        shoot(state)
        self.assertEqual((state.score, list(state.enemies), list(state.bullets), state.player_x), snapshot)


class RenderTest(unittest.TestCase):
    def test_render_bounds(self):
        lines = render(new_game()).splitlines()
        self.assertEqual(len(lines), BOARD_HEIGHT)
        self.assertTrue(all(len(line) == BOARD_WIDTH for line in lines))

    def test_render_symbols(self):
        state = new_game()
        state.enemies = [(3, 2)]
        state.bullets = [(state.player_x, PLAYER_ROW - 1)]
        grid = [list(line) for line in render(state).splitlines()]
        self.assertEqual(grid[PLAYER_ROW][state.player_x], PLAYER_SYMBOL)
        self.assertEqual(grid[2][3], ENEMY_SYMBOL)
        self.assertEqual(grid[PLAYER_ROW - 1][state.player_x], BULLET_SYMBOL)
        self.assertEqual(grid[0][0], EMPTY_SYMBOL)


if __name__ == "__main__":
    unittest.main()
