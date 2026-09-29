"""Terminal Invaders CLI (standard library only).

Runs the pure logic from :mod:`invaders_game` in a ~10 FPS loop.
Renders with curses when a TTY and curses are available, otherwise
falls back to plain ANSI escape sequences (also usable headless via
``--ticks`` for smoke runs).
"""

from __future__ import annotations

import argparse
import os
import sys
import time

from invaders_game import (
    STATUS_GAME_OVER,
    STATUS_RUNNING,
    STATUS_VICTORY,
    TICK,
    GameState,
    new_game,
    step_game,
)


def _render_lines(state: GameState) -> list[str]:
    """Render the playfield as a list of plain-text lines."""
    grid = [[" "] * state.width for _ in range(state.height)]
    for x, y in state.enemies:
        if 0 <= y < state.height and 0 <= x < state.width:
            grid[y][x] = "M"
    for bullet in state.player_bullets:
        if 0 <= bullet.y < state.height:
            grid[bullet.y][bullet.x] = "|"
    for bullet in state.enemy_bullets:
        if 0 <= bullet.y < state.height:
            grid[bullet.y][bullet.x] = ":"
    grid[state.height - 1][state.player_x] = "^"
    return ["".join(row) for row in grid]


def _status_line(state: GameState) -> str:
    if state.status == STATUS_GAME_OVER:
        return f" GAME OVER - score {state.score} - press q to quit "
    if state.status == STATUS_VICTORY:
        return f" VICTORY - score {state.score} - press q to quit "
    return f" SCORE {state.score}  LIVES {state.lives}  (arrows/h+l move, space/j fire, q quit) "


def _curses_available() -> bool:
    if not sys.stdout.isatty():
        return False
    try:
        import curses  # noqa: F401

        return True
    except ImportError:
        return False


def _drain_curses_input(stdscr) -> tuple[int, bool, bool]:
    """Read all pending keys; returns (move, fire, quit)."""
    import curses

    move = 0
    fire = False
    quit_game = False
    while True:
        key = stdscr.getch()
        if key == -1:
            return move, fire, quit_game
        if key in (ord("q"), ord("Q")):
            quit_game = True
        elif key in (curses.KEY_LEFT, ord("h")):
            move = -1
        elif key in (curses.KEY_RIGHT, ord("l")):
            move = 1
        elif key in (ord(" "), ord("j")):
            fire = True


def _draw_curses(stdscr, state: GameState) -> None:
    max_y, max_x = stdscr.getmaxyx()
    stdscr.erase()
    try:
        stdscr.addstr(0, 0, (_status_line(state) + " " * 8)[: max(max_x - 1, 1)])
        for index, line in enumerate(_render_lines(state)):
            row = index + 1
            if row >= max_y - 1:
                break
            stdscr.addstr(row, 1, f" {line} "[: max(max_x - 2, 1)])
    except Exception:  # curses.error on tiny terminals; just skip the frame
        pass
    stdscr.refresh()


def _curses_loop(stdscr, max_ticks: int | None) -> int:
    import curses

    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    state = new_game()
    ticks = 0
    next_tick = time.monotonic()
    while True:
        _draw_curses(stdscr, state)
        move, fire, quit_game = _drain_curses_input(stdscr)
        if quit_game:
            return 0
        now = time.monotonic()
        if now >= next_tick:
            state = step_game(state, move, fire, now)
            ticks += 1
            if max_ticks is not None and ticks >= max_ticks:
                return 0
            next_tick += TICK
            if now - next_tick > 0.5:
                next_tick = now
        time.sleep(0.01)


class _AnsiInput:
    """Non-blocking key reader for the ANSI fallback (letters + arrows)."""

    def __init__(self) -> None:
        self.fd = sys.stdin.fileno()
        self.enabled = False
        self._old = None
        self._buf = b""
        if os.isatty(self.fd):
            import fcntl
            import termios
            import tty

            self._old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
            flags = fcntl.fcntl(self.fd, fcntl.F_GETFL)
            fcntl.fcntl(self.fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            self.enabled = True

    def read(self) -> tuple[int, bool, bool]:
        """Consume pending bytes; returns (move, fire, quit)."""
        move = 0
        fire = False
        quit_game = False
        if not self.enabled:
            return move, fire, quit_game
        try:
            self._buf += os.read(self.fd, 64)
        except (BlockingIOError, InterruptedError):
            pass
        while self._buf:
            if self._buf[0] == 0x1B:
                if len(self._buf) == 1:
                    break  # wait for the rest of a possible arrow sequence
                if len(self._buf) >= 3 and self._buf[1] == 0x5B and self._buf[2] in (0x43, 0x44):
                    move = 1 if self._buf[2] == 0x43 else -1
                    self._buf = self._buf[3:]
                else:
                    self._buf = self._buf[1:]
                continue
            byte = self._buf[0]
            self._buf = self._buf[1:]
            char = chr(byte)
            if char in ("q", "Q"):
                quit_game = True
            elif char == "h":
                move = -1
            elif char == "l":
                move = 1
            elif char in (" ", "j"):
                fire = True
        return move, fire, quit_game

    def restore(self) -> None:
        if self.enabled and self._old is not None:
            import termios

            termios.tcsetattr(self.fd, termios.TCSADRAIN, self._old)


def _ansi_loop(max_ticks: int | None) -> int:
    state = new_game()
    inp = _AnsiInput()
    out = sys.stdout
    ticks = 0
    next_tick = time.monotonic()
    try:
        out.write("\x1b[2J\x1b[?25l")
        out.flush()
        while True:
            move, fire, quit_game = inp.read()
            if quit_game or (max_ticks is not None and ticks >= max_ticks):
                break
            out.write(_status_line(state) + "\n")
            for line in _render_lines(state):
                out.write(f" {line} \n")
            out.write("\n")
            out.flush()
            now = time.monotonic()
            if now >= next_tick:
                state = step_game(state, move, fire, now)
                ticks += 1
                next_tick += TICK
                if now - next_tick > 0.5:
                    next_tick = now
            time.sleep(0.02)
    finally:
        out.write("\x1b[?25h\n")
        inp.restore()
        out.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="invaders-cli", description=__doc__)
    parser.add_argument(
        "--renderer",
        choices=("auto", "curses", "ansi"),
        default="auto",
        help="renderer to use (default: curses on a TTY, else ANSI)",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=None,
        help="stop after this many ticks (headless smoke run)",
    )
    args = parser.parse_args(argv)

    use_curses = args.renderer == "curses" or (
        args.renderer == "auto" and _curses_available()
    )
    if use_curses:
        import curses

        try:
            return curses.wrapper(_curses_loop, args.ticks)
        except Exception:
            if args.renderer == "curses":
                raise
            return _ansi_loop(args.ticks)
    return _ansi_loop(args.ticks)


if __name__ == "__main__":
    sys.exit(main())
