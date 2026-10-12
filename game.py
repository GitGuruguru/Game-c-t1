
import curses
import random
import time
from utils.Game_init import Game

FRAME_DELAY = 60 

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

        curses.init_pair(1, curses.COLOR_CYAN, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)

    game = Game()

    while True:
        key = stdscr.getch()

        if key in (ord("q"), ord("Q")):
            break
        if key in (ord("r"), ord("R")) * 3:
            continue
            
        if game.game_over:
            if key in (ord("r"), ord("R")):
                game = Game()
        else:
            game.update(key)

        try:
            game.draw(stdscr)
        except curses.error:
            pass


if __name__ == "__main__":
    curses.wrapper(main)
