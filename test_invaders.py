"""Unit tests for the invaders game logic (no TTY required).

Run from the repo root with::

    python -m unittest test_invaders -v
"""

import unittest

from invaders import BULLET_SCORE, Game


class GameSetupTests(unittest.TestCase):
    def test_new_game_has_fleet_and_no_game_over(self):
        game = Game()
        self.assertFalse(game.game_over)
        self.assertEqual(game.score, 0)
        self.assertEqual(len(game.enemies), 15)
        self.assertEqual(game.player_row, game.height - 1)
        self.assertEqual(game.player_x, game.width // 2)

    def test_reset_restores_fresh_state(self):
        game = Game()
        game.move_player(3)
        game.fire()
        game.score = 7 * BULLET_SCORE
        game.game_over = True
        game.reset()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.bullets, [])
        self.assertEqual(game.player_x, game.width // 2)
        self.assertFalse(game.game_over)
        self.assertEqual(len(game.enemies), 15)


class PlayerMovementTests(unittest.TestCase):
    def test_moves_left_and_right(self):
        game = Game()
        start = game.player_x
        game.move_player(1)
        self.assertEqual(game.player_x, start + 1)
        game.move_player(-1)
        self.assertEqual(game.player_x, start)

    def test_clamped_at_left_and_right_edges(self):
        game = Game()
        for _ in range(game.width * 2):
            game.move_player(-1)
        self.assertEqual(game.player_x, 0)
        for _ in range(game.width * 2):
            game.move_player(1)
        self.assertEqual(game.player_x, game.width - 1)

    def test_movement_ignored_after_game_over(self):
        game = Game()
        game.game_over = True
        start = game.player_x
        game.move_player(1)
        game.move_player(-1)
        self.assertEqual(game.player_x, start)


class FiringTests(unittest.TestCase):
    def test_fire_spawns_bullet_above_player(self):
        game = Game()
        game.fire()
        self.assertEqual(game.bullets, [(game.player_x, game.player_row - 1)])

    def test_bullet_removed_after_leaving_the_top(self):
        game = Game()
        game.enemies = set()
        game.bullets = [(5, 0)]
        game.step()
        self.assertEqual(game.bullets, [])

    def test_fire_ignored_after_game_over(self):
        game = Game()
        game.game_over = True
        game.fire()
        self.assertEqual(game.bullets, [])


class CollisionTests(unittest.TestCase):
    def test_hit_removes_enemy_and_increases_score(self):
        game = Game()
        game.enemies = {(5, 3)}
        game.bullets = [(5, 5)]
        game.step()
        self.assertEqual(game.enemies, set())
        self.assertEqual(game.bullets, [])
        self.assertEqual(game.score, BULLET_SCORE)

    def test_hit_when_bullet_and_enemy_swap_rows(self):
        game = Game()
        game.enemies = {(5, 3)}
        game.bullets = [(5, 4)]
        game.step()
        self.assertEqual(game.enemies, set())
        self.assertEqual(game.bullets, [])
        self.assertEqual(game.score, BULLET_SCORE)

    def test_miss_leaves_enemy_and_bullet_intact(self):
        game = Game()
        game.enemies = {(5, 3)}
        game.bullets = [(9, 5)]
        game.step()
        self.assertEqual(game.enemies, {(5, 4)})
        self.assertEqual(game.bullets, [(9, 4)])
        self.assertEqual(game.score, 0)


class DescentTests(unittest.TestCase):
    def test_enemies_descend_one_row_per_tick(self):
        game = Game()
        before = set(game.enemies)
        game.step()
        self.assertEqual(game.enemies, {(x, y + 1) for (x, y) in before})

    def test_game_over_when_enemy_reaches_player_row(self):
        game = Game()
        game.enemies = {(5, game.player_row - 1)}
        game.step()
        self.assertEqual(game.enemies, {(5, game.player_row)})
        self.assertTrue(game.game_over)

    def test_game_over_freezes_the_world(self):
        game = Game()
        game.enemies = {(5, game.player_row)}
        game.game_over = True
        game.step()
        game.step()
        self.assertEqual(game.enemies, {(5, game.player_row)})
        self.assertEqual(game.score, 0)


if __name__ == "__main__":
    unittest.main()
