import curses
import random
import time

from Game_init import Game
from Shop import Game_ShopEvent
from data.Saves import *

FRAME_DELAY = 40

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(FRAME_DELAY)
    # Enable terminal colors
    if curses.has_colors():
        curses.start_color()
        
        try:
            curses.use_default_colors()
        except curses.error:
            pass

        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)
    player = load_player("./data/player.json")
    game = Game()
    shoplevel = Game_ShopEvent(player)
    while True:
        key = stdscr.getch()
        # if game.level  == 1:
        shoplevel.draw_fill_window_shop(stdscr)
        #    pass
        # if game.game_over:
            
        #     if key in (ord("r"), ord("R")):
        #         game = Game()
        #     if key in (ord("q"), ord("Q")):
        #         break
        # else:
        #     game.update(key)
        # try:
        #     game.draw(stdscr)
        # except curses.error:
        #     pass


if __name__ == "__main__":
    curses.wrapper(main)
