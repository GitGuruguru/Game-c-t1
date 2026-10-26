import curses
import random

from data.Saves import save_player

WIDTH = 160
HEIGHT =30
SAVE_PATH = "data/player.json"

DEF_ITEMS = [
    "turbomotors",
    "spacedefences",
    "termalshield",
    "misledefence",
    "hull reinforsments",
]

DEF_POWERS = [
    "Tempester",
    "Ground Zero",
    "Nemesis",
    "Omega",
    "Alpha",
    "Delta",
    "Equilibrium",
]

ITEM_PRICES = {
    "turbomotors": 100,
    "spacedefences": 150,
    "termalshield": 200,
    "misledefence": 250,
    "hull reinforsments": 300,
}

POWER_PRICE = 100


def init_shop_colors():
    """Initialize shop-specific color pairs."""
    if not curses.has_colors():
        return

    try:
        curses.start_color()
        try:
            curses.use_default_colors()
            background = -1
        except curses.error:
            background = curses.COLOR_BLACK

        # Use pairs 5-9 so they don't conflict with the game.
        curses.init_pair(5, curses.COLOR_WHITE, background)
        curses.init_pair(6, curses.COLOR_CYAN, background)
        curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(8, curses.COLOR_YELLOW, background)
        curses.init_pair(9, curses.COLOR_GREEN, background)

    except curses.error:
        pass


def safe_addstr(stdscr, y, x, text, attr=0):
    """Write text only when the target coordinates are valid."""
    rows, cols = stdscr.getmaxyx()

    if y < 0 or y >= rows or x < 0 or x >= cols:
        return

    text = str(text)
    available = cols - x

    if available <= 0:
        return

    try:
        stdscr.addnstr(y, x, text, available, attr)
    except curses.error:
        pass

def safe_addch(stdscr, y,x,text,attr=0):
    rows, cols = stdscr.grtmaxyx()
    if y < 0 or y >= rows or x < 0 or x >= cols :
        return 
    text = chr(text)
 
    avalible = cols - x
    if avalible <= 0 : 
        return 
    try:
        stdscr.addnchr(y,x,text,avalible, attr)
    except curses.error:
        pass
    
class Game_ShopEvent:

    def __init__(self, player):
        self.player = player

        # Ensure these fields are present and normalized.
        self.player.setdefault("name", "Player")
        self.player.setdefault("money", 0)
        self.player.setdefault("score", 0)
        self.player.setdefault("level", 1)
        self.player.setdefault("lives", 3)

        if not isinstance(self.player.get("items"), list):
            value = self.player.get("items")
            self.player["items"] = [value] if value else []

        if not isinstance(self.player.get("power"), list):
            value = self.player.get("power")
            self.player["power"] = [value] if value else []

        self.items = self.player["items"]
        self.powers = self.player["power"]

        self.sync_from_player()

        self.offers = []
        self.selected_item = 0
        self.message = "Select an offer and press BUY."

        self.randomise_offers()

    def sync_from_player(self):
        """Refresh shop stats after gameplay or purchases."""
        self.money = self.player["money"]
        self.score = self.player["score"]
        self.level = self.player["level"]
        self.lives = self.player["lives"]

        self.items = self.player["items"]
        self.powers = self.player["power"]

    def randomise_offers(self):
        """Generate three distinct defensive-item offers."""
        selected_items = random.sample(
            DEF_ITEMS, k=min(3, len(DEF_ITEMS))
        )

        self.offers = []

        for item in selected_items:
            self.offers.append({
                "item": item,
                "power": random.choice(DEF_POWERS),
                "price": ITEM_PRICES[item] + POWER_PRICE,
            })

        self.selected_item = 0
        self.message = "New offers generated!"

    def buy_item(self):
        if not self.offers:
            self.message = "No offers available!"
            return False

        self.sync_from_player()
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

        # Update the shared player dictionary.
        self.player["money"] -= price
        self.items.append(item)
        self.powers.append(power)

        self.sync_from_player()
        self.message = f"Purchased {item} + {power} for {price}!"
        return True

    def draw_card(self, stdscr, x, y, width, height, offer, selected=False):
        normal = curses.color_pair(5) | curses.A_BOLD
        highlight = curses.color_pair(6) | curses.A_BOLD
        owned_color = curses.color_pair(9) | curses.A_BOLD

        border_color = highlight if selected else normal

        safe_addstr(stdscr, y, x, "+" + "-" * (width - 2) + "+", border_color)
        safe_addstr(
            stdscr, y + height - 1, x,
            "+" + "-" * (width - 2) + "+", border_color
        )

        for row in range(y + 1, y + height - 1):
            safe_addstr(stdscr, row, x, "|", border_color)
            safe_addstr(stdscr, row, x + width - 1, "|", border_color)

        def centered(row, value, attr=normal):
            value = str(value)[:width - 2]
            col = x + max(1, (width - len(value)) // 2)
            safe_addstr(stdscr, row, col, value, attr)

        centered(y + 1, f"Offer {self.offers.index(offer) + 1}")
        centered(y + 2, offer["item"])
        centered(y + 3, offer["power"])
        centered(y + 4, f"Price: {offer['price']}")
        
        if offer["item"] in self.items:
            centered(y + 5, "OWNED", owned_color)
        elif selected:
            centered(y + 5, "SELECTED", highlight)

    def draw_fill_window_shop(self, stdscr):
        rows, cols = stdscr.getmaxyx()
        stdscr.erase()

        if rows < HEIGHT or cols < WIDTH:
            safe_addstr(
                stdscr, 0, 0,
                f"Terminal too small! Need {WIDTH}x{HEIGHT}."
            )
            stdscr.refresh()
            return

        self.sync_from_player()

        stdscr.bkgd(" ", curses.color_pair(5))
        stdscr.border()

        hud = (
            f" Score:{self.score} Lives:{self.lives}"
            f" Level:{self.level} Money:{self.money} "
        )
        safe_addstr(stdscr, 0, 2, hud, curses.color_pair(5) | curses.A_BOLD)

        safe_addstr(
            stdscr, 1, (WIDTH - len("SPACE SHOP")) // 2,
            "SPACE SHOP", curses.color_pair(6) | curses.A_BOLD
        )

        card_y = 3
        card_height = 7
        gap = 1
        card_width = (WIDTH - 2 - 2 * gap) // 3

        for i, offer in enumerate(self.offers):
            x = 1 + i * (card_width + gap)
            self.draw_card(
                stdscr, x, card_y, card_width, card_height,
                offer, selected=(i == self.selected_item)
            )

        controls = (
            "[1-3] Select  [E] Buy  [R] Random  "
            "[I] Inventory  [Q] Resume"
        )
        safe_addstr(stdscr, 12, 2, controls, curses.color_pair(8) | curses.A_BOLD)

        safe_addstr(
            stdscr, 14, 2,
            self.message[:WIDTH - 4],
            curses.color_pair(5) | curses.A_BOLD
        )

        safe_addstr(
            stdscr, 17, 2,
            "[N] Next round    [S] Save",
            curses.color_pair(8) | curses.A_BOLD
        )

        stdscr.refresh()

    def shop_items(self, stdscr, key=None):
        """Process one shop key. Return an action when needed."""
        if key is None:
            key = stdscr.getch()

        if key == -1:
            return None

        if key in (ord("e"), ord("E")):
            self.buy_item()

        elif key in (ord("r"), ord("R")):
            self.randomise_offers()

        elif key in (ord("i"), ord("I")):
            return "inventory"

        elif key in (ord("n"), ord("N")):
            return "next_round"

        elif key in (ord("s"), ord("S")):
            try:
                save_player(self.player, SAVE_PATH)
                self.message = "Game saved!"
                return "save"
            except (OSError, ValueError, TypeError) as error:
                self.message = f"Save failed: {error}"

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

        return None

    def show_inventory(self, stdscr):
        """Display inventory without writing outside the terminal."""
        rows, cols = stdscr.getmaxyx()
        stdscr.erase()
        stdscr.border()

        safe_addstr(
            stdscr, 2, 2, "YOUR INVENTORY",
            curses.color_pair(6) | curses.A_BOLD
        )

        safe_addstr(stdscr, 4, 2, "Defensive items:")

        row = 5
        if self.items:
            for item in self.items:
                if row >= rows - 5:
                    break
                safe_addstr(stdscr, row, 4, f"- {item}")
                row += 1
        else:
            safe_addstr(stdscr, row, 4, "No items purchased.")
            row += 1

        row += 1
        if row < rows - 2:
            safe_addstr(stdscr, row, 2, "Powers:")
            row += 1

        if self.powers:
            for power in self.powers:
                if row >= rows - 2:
                    break
                safe_addstr(stdscr, row, 4, f"- {power}")
                row += 1
        elif row < rows - 2:
            safe_addstr(stdscr, row, 4, "No powers purchased.")

        safe_addstr(
            stdscr, rows - 2, 2,
            "Press any key to return.", curses.A_BOLD
        )

        stdscr.refresh()
        stdscr.getch()