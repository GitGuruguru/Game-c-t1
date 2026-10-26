import curses
import random
import time

from Game_init import Game
from Shop import Game_ShopEvent
from data.Saves import *

FRAME_DELAY = 40
player = load_player("data/player.json")
def main(stdscr):
    def shop_screen(stdscr, player):
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        stdscr.keypad(True)
        stdscr.timeout(-1)

        shop = Game_ShopEvent(player)

        while True:
            shop.draw_fill_window_shop(stdscr)
            action = shop.shop_items(stdscr)

            if action == "exit":
                break

            elif action == "inventory":
                shop.show_inventory(stdscr)

            elif action == "next_round":
                return "next_round"

            elif action == "save":
                # Connect this to your existing save system.
                return "save"

        return "exit"



    # Launch the shop:
    result = curses.wrapper(shop_screen, player)


    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(FRAME_DELAY)
    # Enable terminal colors
    if curses.has_colors():
        curses.start_color()
        if player["level"] == 3:
            shop_screen()
        try:
            curses.use_default_colors()
        except curses.error:
            pass

        curses.init_pair(1, curses.COLOR_MAGENTA, -1)
        curses.init_pair(2, curses.COLOR_RED, -1)
        curses.init_pair(3, curses.COLOR_GREEN, -1)
        curses.init_pair(4, curses.COLOR_YELLOW, -1)

    game = Game()
    shoplevel = Game_ShopEvent(player)
   


if __name__ == "__main__":
    curses.wrapper(main)
