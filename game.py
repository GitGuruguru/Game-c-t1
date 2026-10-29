"""Launch Starfall, a responsive terminal arcade shooter."""
import sys
import time
from pathlib import Path

try:
    import curses
except ImportError:  # Standard Windows Python does not ship _curses.
    import curses_compat as curses

from Game_init import Game
from data.Saves import load_player, player_save_path, save_player


def setup_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    try:
        curses.use_default_colors()
    except curses.error:
        pass
    pairs = ((1, curses.COLOR_CYAN), (2, curses.COLOR_RED), (3, curses.COLOR_GREEN),
             (4, curses.COLOR_YELLOW), (5, curses.COLOR_MAGENTA), (6, curses.COLOR_BLUE))
    for pair, foreground in pairs:
        try:
            curses.init_pair(pair, foreground, -1)
        except curses.error:
            pass


def main(stdscr):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.keypad(True)
    stdscr.nodelay(True)
    setup_colors()
    save_path = player_save_path()
    if getattr(sys, "frozen", False) and not Path(save_path).exists():
        bundled = Path(sys._MEIPASS) / "data" / "player.json"
        if bundled.exists():
            try:
                Path(save_path).write_bytes(bundled.read_bytes())
            except OSError:
                pass
    player = load_player(save_path)
    game = Game(player)
    while True:
        try:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")):
                break
            # Advance the simulation on every frame; -1 means only that no key
            # arrived during this poll, not that the game should pause.
            game.update(key, stdscr)
            game.draw(stdscr)
            time.sleep(1 / 60)
        except curses.error:
            continue
    game.sync_player_data()
    save_player(game.player_data, save_path)


if __name__ == "__main__":
    curses.wrapper(main)
