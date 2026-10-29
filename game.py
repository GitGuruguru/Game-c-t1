"""Launch Starfall, a responsive terminal arcade shooter."""
import curses
import os
import sys
import time
from pathlib import Path

from Game_init import Game
from data.Saves import load_player, save_player


def player_save_path():
    if getattr(sys, "frozen", False):
        save_dir = Path(os.environ.get("APPDATA", Path.home())) / "Starfall"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / "player.json"
        if not save_path.exists():
            bundled = Path(sys._MEIPASS) / "data" / "player.json"
            if bundled.exists():
                save_path.write_bytes(bundled.read_bytes())
        return str(save_path)
    return "./data/player.json"


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
    player = load_player(save_path)
    game = Game(player)
    last_key_time = 0.0
    while True:
        try:
            key = stdscr.getch()
            if key in (ord("q"), ord("Q")) and (game.game_over or game.shop_open):
                break
            # Repeating movement while a key is held keeps motion smooth on terminals
            # that emit a key only once; curses keypad repeat still handles arrows.
            now = time.monotonic()
            if key != -1:
                game.update(key, stdscr)
                last_key_time = now
            elif now - last_key_time < 0.20:
                pass
            game.draw(stdscr)
            time.sleep(1 / 60)
        except curses.error:
            continue
    game.sync_player_data()
    save_player(game.player_data, save_path)


if __name__ == "__main__":
    curses.wrapper(main)
