import curses

from Game_init import Game, init_game_colors
from data.Saves import load_player, save_player

FRAME_DELAY = 40
SAVE_PATH = "data/player.json"


def get_player():
    """Load player data or create a safe default player."""
    try:
        player = load_player(SAVE_PATH)
        if not isinstance(player, dict):
            raise ValueError("Invalid player data")
    except (OSError, ValueError, KeyError, TypeError):
        player = {}

    defaults = {
        "name": "Player",
        "score": 0,
        "lives": 3,
        "level": 1,
        "money": 0,
        "items": [],
        "power": [],
    }

    for key, value in defaults.items():
        if key not in player or player[key] is None:
            player[key] = value.copy() if isinstance(value, list) else value

    # Normalize inventory fields.
    for key in ("items", "power"):
        if not isinstance(player[key], list):
            player[key] = [player[key]] if player[key] else []

    return player


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(FRAME_DELAY)

    if curses.has_colors():
        curses.start_color()
        try:
            curses.use_default_colors()
            background = -1
        except curses.error:
            background = curses.COLOR_BLACK

        init_game_colors(background)

    player = get_player()
    game = Game(player)

    while True:
        # Handle the shop as a separate game state.
        if game.shop is not None:
            shop = game.shop
            shop.sync_from_player()
            shop.draw_fill_window_shop(stdscr)

            key = stdscr.getch()

            if key == -1:
                continue

            action = shop.shop_items(stdscr, key)

            if action in ("next_round", "exit"):
                game.shop = None
                stdscr.timeout(FRAME_DELAY)

            elif action == "inventory":
                shop.show_inventory(stdscr)
                stdscr.timeout(FRAME_DELAY)

            elif action == "save":
                try:
                    save_player(player, SAVE_PATH)
                    shop.message = "Game saved successfully!"
                except (OSError, ValueError, TypeError) as error:
                    shop.message = f"Save failed: {error}"

            continue

        game.draw(stdscr)
        
        key = stdscr.getch()

        if game.game_over:
            if key in (ord("q"), ord("Q"), 27):
                break

            if key in (ord("r"), ord("R")):
                
                player["score"] = 0
                player["lives"] = 3
                player["level"] = 1

                game = Game(player)

            continue

        if key in (ord("q"), ord("Q"), 27):
            try:
                save_player(player, SAVE_PATH)
            except (OSError, ValueError, TypeError):
                pass
            break

        game.update(key)

    # Save on exit.
    try:
        save_player(player, SAVE_PATH)
    except (OSError, ValueError, TypeError):
        pass


if __name__ == "__main__":
    curses.wrapper(main)