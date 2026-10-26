

import curses
import random
import time
import re

from Game_init import *
from data.Saves import *

WIDTH = 201
HEIGHT = 40

konami_code = []

DEF_ITEMS = [
    "turbomotors",
    "spacedefences",
    "termalshield",
    "misledefence",
    "hull reinforsments",
]

SPECIAL_ITEMS = {
    "state of the art defence system": 2505
}

DEF_POWERS = [
    "Tempester",
    "Ground Zero",
    "Nemesis",
    "Omega",
    "Alpha",
    "Delta",
    "Equilibrium",
]

SPECIAL_POWER = {
    "Fifth element": 20000
}

ITEM_PRICES = {
    "turbomotors": 100,
    "spacedefences": 150,
    "termalshield": 200,
    "misledefence": 250,
    "hull reinforsments": 300,
}

POWER_PRICE = 100


def init_shop_colors():
    """Initialize colors using the terminal's default background."""
    if not curses.has_colors():
        return

    curses.start_color()

    try:
        curses.use_default_colors()
        default_bg = -1
    except curses.error:
        default_bg = curses.COLOR_BLACK

    curses.init_pair(1, curses.COLOR_WHITE, default_bg)
    curses.init_pair(2, curses.COLOR_CYAN, default_bg)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(4, curses.COLOR_YELLOW, default_bg)
    curses.init_pair(5, curses.COLOR_GREEN, default_bg)


class Game_ShopEvent:

    def __init__(self, player):
        self.player = player

        self.player_name = player["name"]
        self.money = player["money"]
        self.score = player["score"]
        self.level = player["level"]
        self.lives = player["lives"]

        # Ensure inventory and powers are lists.
        if isinstance(player.get("items"), list):
            self.items = player["items"]
        elif player.get("items") is None:
            self.items = []
        else:
            self.items = [player["items"]]

        if isinstance(player.get("power"), list):
            self.powers = player["power"]
        elif player.get("power") is None:
            self.powers = []
        else:
            self.powers = [player["power"]]

        self.player["items"] = self.items
        self.player["power"] = self.powers

        self.is_cheat_enabled = False
        self.battle_pass = True
        self.MICROTRANSACTIONS = "enabled"

        self.offers = []
        self.selected_item = 0
        self.message = "Select an offer and press BUY."

        self.randomise_offers()

    # --------------------------------------------------
    # CHEAT CODES
    # --------------------------------------------------

    @staticmethod
    def get_cheat_code_classic(stdscr):
        key = stdscr.getch()
        konami_code.append(key)

        sequence = [
            ord("W"), ord("A"), ord("S"),
            ord("D"), ord("R")
        ]

        if len(konami_code) > len(sequence):
            del konami_code[:-len(sequence)]

        return konami_code == sequence

    @staticmethod
    def get_cheat_code_konami(stdscr):
        key = stdscr.getch()
        konami_code.append(key)

        sequence = [
            curses.KEY_UP,
            curses.KEY_UP,
            curses.KEY_DOWN,
            curses.KEY_DOWN,
            curses.KEY_RIGHT,
            curses.KEY_LEFT,
            curses.KEY_RIGHT,
            curses.KEY_LEFT,
            ord("B"),
            ord("A"),
        ]

        if len(konami_code) > len(sequence):
            del konami_code[:-len(sequence)]

        return konami_code == sequence

    # --------------------------------------------------
    # OFFER GENERATION
    # --------------------------------------------------

    def randomise_offers(self):
        """Generate three different offers."""
        selected_items = random.sample(
            DEF_ITEMS, k=min(3, len(DEF_ITEMS))
        )

        self.offers = []

        for item in selected_items:
            power = random.choice(DEF_POWERS)
            price = ITEM_PRICES.get(item, 100) + POWER_PRICE

            self.offers.append({
                "item": item,
                "power": power,
                "price": price,
            })

        self.selected_item = 0
        self.message = "New offers generated!"

    # --------------------------------------------------
    # BUY FUNCTION
    # --------------------------------------------------

    def buy_item(self, stdscr=None):
        if not self.offers:
            self.message = "No offers available!"
            return False

        offer = self.offers[self.selected_item]

        item = offer["item"]
        power = offer["power"]
        price = offer["price"]

        if item in self.items:
            self.message = "You already own this item!"
            return False

        if self.money < price:
            self.message = f"Not enough money! Need {price}."
            return False

        self.money -= price
        self.items.append(item)
        self.powers.append(power)

        self.player["money"] = self.money
        self.player["items"] = self.items
        self.player["power"] = self.powers

        self.message = f"Purchased {item} + {power} for {price}!"
        return True

    # --------------------------------------------------
    # DRAW A SINGLE SHOP CARD
    # --------------------------------------------------

    def draw_card(
        self, stdscr, x, y, width, height,
        offer, selected=False
    ):
        # Use explicit foreground/background color pairs.
        normal_color = curses.color_pair(3) | curses.A_BOLD
        selected_color =  curses.color_pair(2) | curses.A_BOLD
        owned_color = curses.color_pair(5) | curses.A_BOLD

        border_color = selected_color if selected else normal_color
        text_color = normal_color

        # Card borders.
        stdscr.addstr(
            y, x, "+" + "-" * (width - 2) + "+",
            border_color
        )
        stdscr.addstr(
            y + height - 1, x,
            "+" + "-" * (width - 2) + "+",
            border_color
        )

        for row in range(y + 1, y + height - 1):
            stdscr.addch(row, x, "|", border_color)
            stdscr.addch(row, x + width - 1, "|", border_color)

        item = offer["item"]
        power = offer["power"]
        price = offer["price"]

        def centered_text(row, text, attr=None):
            text = str(text)[:width - 2]
            col = x + max(1, (width - len(text)) // 2)

            stdscr.addstr(
                row, col, text,
                text_color if attr is None else attr
            )

        centered_text(
            y + 1, f"Offer {self.offers.index(offer) + 1}"
        )
        centered_text(y + 3, item)
        centered_text(y + 4, power)
        centered_text(y + 6, f"Price: {price}")

        if item in self.items:
            centered_text(y + 7, "OWNED", owned_color)
        elif selected:
            centered_text(y + 7, "SELECTED", selected_color)

    # --------------------------------------------------
    # DRAW THE SHOP WINDOW
    # --------------------------------------------------

    def draw_fill_window_shop(self, stdscr):
        if self.is_cheat_enabled:
            return

        stdscr.erase()

        rows, cols = stdscr.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            stdscr.addstr(
                0, 0,
                f"Terminal too small! Need {WIDTH}x{HEIGHT}."
            )
            stdscr.refresh()
            return

        # Apply a clean background without reverse video.
        stdscr.bkgd(" ", curses.color_pair(1))
        stdscr.border()

        hud = (
            f" Score:{self.score} "
            f" Lives:{self.lives} "
            f" Level:{self.level} "
            f" Money:{self.money} "
        )

        stdscr.addstr(
            0, 2, hud[:cols - 4],
            curses.color_pair(1) | curses.A_BOLD
        )

        title = "SPACE SHOP"
        stdscr.addstr(
            2, (WIDTH - len(title)) // 2,
            title,
            curses.color_pair(2) | curses.A_BOLD
        )

        card_y = 4
        card_height = 10
        gap = 1
        inner_width = WIDTH - 2
        card_width = (inner_width - 2 * gap) // 3

        for i, offer in enumerate(self.offers):
            x = 1 + i * (card_width + gap)

            self.draw_card(
                stdscr, x, card_y,
                card_width, card_height,
                offer,
                selected=(i == self.selected_item)
            )

        button_color = curses.color_pair(4) | curses.A_BOLD

        stdscr.addstr(HEIGHT - 4, 2, "[B] BUY", button_color)
        stdscr.addstr(HEIGHT - 4, 13, "[R] RANDOM", button_color)
        stdscr.addstr(HEIGHT - 4, 29, "[I] INVENTORY", button_color)
        stdscr.addstr(HEIGHT - 4, 47, "[Q] EXIT", button_color)

        stdscr.addstr(HEIGHT - 2, 2, "[N] NEXT ROUND", button_color)
        stdscr.addstr(HEIGHT - 2, 22, "[S] SAVE", button_color)

        message = self.message[:WIDTH - 4]
        stdscr.addstr(
            HEIGHT - 6, 2,
            message,
            curses.color_pair(1) | curses.A_BOLD
        )

        stdscr.refresh()

    # --------------------------------------------------
    # MOUSE AND KEYBOARD CONTROLS
    # --------------------------------------------------

    def shop_items(self, stdscr):
        buttons = {
            "buy": (HEIGHT - 4, 2, 9),
            "randomiser": (HEIGHT - 4, 13, 25),
            "inventory": (HEIGHT - 4, 29, 42),
            "exit": (HEIGHT - 4, 47, 56),
            "next_round": (HEIGHT - 2, 2, 17),
            "save": (HEIGHT - 2, 22, 29),
        }

        key = stdscr.getch()

        if key in (ord("b"), ord("B")):
            self.buy_item(stdscr)

        elif key in (ord("r"), ord("R")):
            self.randomise_offers()

        elif key in (ord("i"), ord("I")):
            return "inventory"

        elif key in (ord("n"), ord("N")):
            return "next_round"

        elif key in (ord("s"), ord("S")):
            save_player(self.player, "data/player.json")
            self.message = "Game saved!"

        elif key in (ord("q"), ord("Q"), 27):
            return "exit"

        elif key in (ord("1"), ord("2"), ord("3")):
            index = key - ord("1")

            if index < len(self.offers):
                self.selected_item = index
                self.message = f"Selected: {self.offers[index]['item']}"

        elif key == curses.KEY_LEFT:
            if self.offers:
                self.selected_item = (
                    self.selected_item - 1
                ) % len(self.offers)

        elif key == curses.KEY_RIGHT:
            if self.offers:
                self.selected_item = (
                    self.selected_item + 1
                ) % len(self.offers)

        elif key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, button_state = curses.getmouse()

                if button_state & (
                    curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED
                ):
                    card_y = 4
                    card_height = 10
                    gap = 1
                    card_width = (WIDTH - 2 - 2 * gap) // 3

                    if card_y <= mouse_y < card_y + card_height:
                        for i in range(len(self.offers)):
                            x = 1 + i * (card_width + gap)

                            if x <= mouse_x < x + card_width:
                                self.selected_item = i
                                self.message = (
                                    f"Selected: {self.offers[i]['item']}"
                                )
                                break

                    for name, bounds in buttons.items():
                        row, start_x, end_x = bounds

                        if (
                            mouse_y == row
                            and start_x <= mouse_x <= end_x
                        ):
                            if name == "buy":
                                self.buy_item(stdscr)
                            elif name == "randomiser":
                                self.randomise_offers()
                            elif name == "save":
                                save_player(
                                    self.player, "data/player.json"
                                )
                                self.message = "Game saved!"
                            else:
                                return name

            except curses.error:
                pass

        return None

    # --------------------------------------------------
    # BUY PAGE
    # --------------------------------------------------

    def draw_buy_page(self, stdscr):
        self.draw_fill_window_shop(stdscr)

    # --------------------------------------------------
    # INVENTORY DISPLAY
    # --------------------------------------------------

    def show_inventory(self, stdscr):
        stdscr.erase()
        stdscr.border()

        stdscr.addstr(
            2, 2, "YOUR INVENTORY",
            curses.color_pair(2) | curses.A_BOLD
        )

        stdscr.addstr(4, 2, "Defensive items:")

        if self.items:
            for i, item in enumerate(self.items[:HEIGHT - 10]):
                stdscr.addstr(5 + i, 4, f"- {item}")
        else:
            stdscr.addstr(5, 4, "No items purchased.")

        power_y = min(5 + len(self.items), HEIGHT - 5)
        stdscr.addstr(power_y, 2, "Powers:")

        if self.powers:
            for i, power in enumerate(self.powers):
                row = power_y + 1 + i

                if row >= HEIGHT - 2:
                    break

                stdscr.addstr(row, 4, f"- {power}")
        else:
            stdscr.addstr(
                min(power_y + 1, HEIGHT - 2),
                4, "No powers purchased."
            )

        stdscr.addstr(
            HEIGHT - 2, 2,
            "Press any key to return.",
            curses.A_BOLD
        )

        stdscr.refresh()
        stdscr.getch()
