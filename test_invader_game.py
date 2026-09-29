"""Unit tests for the invader_game logic (no terminal required).

Run with:  python -m unittest discover
"""

import random
import unittest

from invader_game import Game, build_frame, build_hud


def make_game(**kwargs) -> Game:
    """Build a deterministic game (seeded RNG, enemies never fire)."""
    kwargs.setdefault("rng", random.Random(42))
    kwargs.setdefault("enemy_fire_chance", 0.0)
    return Game(**kwargs)


class TestInitialState(unittest.TestCase):
    def test_initial_layout(self) -> None:
        game = make_game()
        self.assertTrue(game.running)
        self.assertFalse(game.game_over)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.player_x, game.width // 2)
        self.assertEqual(len(game.enemies), 24)
        self.assertEqual(game.player_bullets, [])
        self.assertEqual(game.enemy_bullets, [])

    def test_rejects_tiny_boards(self) -> None:
        with self.assertRaises(ValueError):
            Game(width=5, height=14)
        with self.assertRaises(ValueError):
            Game(width=40, height=4)
        with self.assertRaises(ValueError):
            Game(enemy_fire_chance=1.5)


class TestPlayerMovement(unittest.TestCase):
    def test_moves_and_clamps_to_bounds(self) -> None:
        game = make_game()
        for _ in range(100):
            game.move_player(-1)
        self.assertEqual(game.player_x, 1)
        for _ in range(100):
            game.move_player(1)
        self.assertEqual(game.player_x, game.width - 2)

    def test_ignored_after_game_over(self) -> None:
        game = make_game()
        game.enemies = [(game.player_x, game.player_row)]
        game.step()
        self.assertFalse(game.running)
        game.move_player(-1)
        self.assertEqual(game.player_x, game.width // 2)


class TestFiring(unittest.TestCase):
    def test_one_bullet_in_flight_at_a_time(self) -> None:
        game = make_game()
        self.assertTrue(game.fire())
        self.assertFalse(game.fire())
        game.step()
        self.assertFalse(game.fire())

    def test_bullet_rises_and_fades_at_top(self) -> None:
        game = make_game()
        game.enemies = [(5, 1), (5, 2), (5, 3)]
        game.fire()
        (x, y0), = game.player_bullets
        self.assertEqual((x, y0), (game.player_x, game.player_row - 1))
        game.step()
        (x, y1), = game.player_bullets
        self.assertEqual(y1, y0 - 1)
        for _ in range(30):
            game.step()
        self.assertEqual(game.player_bullets, [])

    def test_cannot_fire_after_game_over(self) -> None:
        game = make_game()
        game.enemies = []
        game.step()
        self.assertTrue(game.won)
        self.assertFalse(game.fire())
        self.assertEqual(game.player_bullets, [])


class TestEnemyFormation(unittest.TestCase):
    def test_moves_horizontally(self) -> None:
        game = make_game(formation_interval=1)
        start = list(game.enemies)
        game.step()
        self.assertEqual(game.enemies, [(x + 1, y) for x, y in start])
        self.assertEqual(game.direction, 1)

    def test_descends_and_reverses_at_right_edge(self) -> None:
        game = make_game(formation_interval=1)
        game.enemies = [(game.width - 2, 2)]
        game.step()
        self.assertEqual(game.direction, -1)
        self.assertEqual(game.enemies, [(game.width - 2, 3)])

    def test_descends_and_reverses_at_left_edge(self) -> None:
        game = make_game(formation_interval=1)
        game.direction = -1
        game.enemies = [(1, 2)]
        game.step()
        self.assertEqual(game.direction, 1)
        self.assertEqual(game.enemies, [(1, 3)])

    def test_enemies_fire_downwards(self) -> None:
        game = make_game(enemy_fire_chance=1.0)
        game.enemies = [(10, 3)]
        game.step()
        self.assertEqual(game.enemy_bullets, [(10, 5)])

    def test_enemy_bullets_fall_and_leave_the_board(self) -> None:
        game = make_game()
        game.enemy_bullets = [(5, game.height - 2)]
        game.step()
        self.assertEqual(game.enemy_bullets, [])


class TestCollisionsAndScoring(unittest.TestCase):
    def test_bullet_kills_enemy_and_scores(self) -> None:
        game = make_game()
        x = game.player_x
        game.enemies = [(x, game.player_row - 2), (x + 5, 3)]
        game.fire()
        game.step()
        self.assertEqual(game.enemies, [(x + 5, 3)])
        self.assertEqual(game.score, 10)

    def test_enemy_bullet_hurts_player_and_costs_a_life(self) -> None:
        game = make_game()
        game.enemy_bullets = [(game.player_x, game.player_row - 1)]
        game.step()
        self.assertEqual(game.lives, 2)
        self.assertEqual(game.enemy_bullets, [])
        self.assertFalse(game.lost)
        self.assertEqual(game.player_x, game.width // 2)

    def test_player_dies_when_out_of_lives(self) -> None:
        game = make_game()
        game.lives = 1
        game.enemy_bullets = [(game.player_x, game.player_row - 1)]
        game.step()
        self.assertEqual(game.lives, 0)
        self.assertTrue(game.lost)
        self.assertFalse(game.running)

    def test_formation_reaching_player_row_ends_game(self) -> None:
        game = make_game()
        game.enemies = [(3, game.player_row)]
        game.step()
        self.assertTrue(game.lost)
        self.assertFalse(game.running)

    def test_step_is_a_no_op_after_game_over(self) -> None:
        game = make_game()
        game.enemies = []
        game.step()
        self.assertTrue(game.won)
        game.move_player(1)
        game.step()
        self.assertEqual(game.player_x, game.width // 2)
        self.assertEqual(game.score, 0)


class TestWinAndRestart(unittest.TestCase):
    def test_win_when_all_enemies_destroyed(self) -> None:
        game = make_game()
        game.enemies = []
        game.step()
        self.assertTrue(game.won)
        self.assertTrue(game.game_over)
        self.assertFalse(game.running)

    def test_restart_resets_state(self) -> None:
        game = make_game()
        game.fire()
        game.score = 99
        game.lives = 1
        game.move_player(-3)
        game.restart()
        self.assertTrue(game.running)
        self.assertFalse(game.game_over)
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.player_x, game.width // 2)
        self.assertEqual(len(game.enemies), 24)
        self.assertEqual(game.player_bullets, [])
        self.assertEqual(game.enemy_bullets, [])


class TestRendering(unittest.TestCase):
    def test_frame_contains_all_entities(self) -> None:
        game = make_game()
        game.fire()
        frame = build_frame(game)
        lines = frame.split("\n")
        self.assertEqual(len(lines), game.height)
        self.assertEqual(lines[0], "-" * game.width)
        self.assertEqual(lines[-1], "-" * game.width)
        player_line = lines[game.player_row]
        self.assertEqual(player_line[game.player_x], "@")
        bullet_line = lines[game.player_row - 1]
        self.assertEqual(bullet_line[game.player_x], "|")
        self.assertIn("M", lines[1])

    def test_hud_shows_score_and_lives(self) -> None:
        game = make_game()
        game.score = 30
        game.lives = 1
        self.assertEqual(build_hud(game), "Score: 30   Lives: 1")


if __name__ == "__main__":
    unittest.main()
