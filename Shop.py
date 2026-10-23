import curses , random , time 
from Game_init import *
import re as re
WIDTH = 59
HEIGHT = 22

konami_code = []
DEF_ITEMS =  [
    "turbomotors",
    "spacedefences", 
    "termalshield",
    "misledefence",
    "hull reinforsments"
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
    "Fifth element" : 20000
}

class Game_ShopEvent():
    def __init__(self,player):
        self.player_name = player["name"]
        self.money = player["money"]
        self.score =player["score"]
        self.level = player["level"] 
        self.items = player["items"]
        self.powers = player["power"]
        self.lives = player["lives"]
        self.is_cheat_enabled = False
        self.battle_pass = True
        self.MICROTRANSACTIONS = "enabled"

    def get_cheat_code_classic(stdscr):
        
        key = stdscr.getch()
        konami_code.append(key)
        if konami_code == ["W","A","S","D","R"]:
            return True
        return False
    def get_cheat_code_konami(stdscr):
        key = stdscr.getch()
        konami_code.append(key)
        if konami_code == [curses.KEY_UP ,curses.KEY_UP,curses.KEY_DOWN,curses.KEY_DOWN,curses.KEY_RIGHT,curses.KEY_LEFT,curses.KEY_RIGHT,curses.KEY_LEFT,"B","A"]:
        
            return True
        return False
    def shop_items(self,stdscr):
        buttons = {
                    "buy": (HEIGHT - 4, 3, 10),
                    "next_round": (HEIGHT - 4, 15, 26),
                    "randomiser": (HEIGHT - 4, 30, 42),
                    "inventory": (HEIGHT - 4, 43, 55),
                    "save": (HEIGHT - 2, 3, 10),
                    "exit": (HEIGHT - 2, 15, 22),
                }
        key = stdscr.getch()
        if key == curses.KEY_MOUSE:
            try:
                _, mouse_x, mouse_y, _, button_state = curses.getmouse()
        
                if button_state & curses.BUTTON1_CLICKED:
        
                    # BUY
                    row, start_x, end_x = buttons["buy"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        self.buy_item(stdscr)
        
                    # NEXT ROUND
                    row, start_x, end_x = buttons["next_round"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        return "next_round"
        
                    # RANDOMISER
                    row, start_x, end_x = buttons["randomiser"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        return "randomiser"
        
                    # INVENTORY
                    row, start_x, end_x = buttons["inventory"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        return "inventory"
        
                    # SAVE
                    row, start_x, end_x = buttons["save"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        return "save"
        
                    # EXIT
                    row, start_x, end_x = buttons["exit"]
                    if mouse_y == row and start_x <= mouse_x <= end_x:
                        return "exit"
        
            except curses.error:
                pass
        
        stdscr.refresh()
    def draw_fill_window_shop(self,stdscr):
       
        if(self.MICROTRANSACTIONS == "enabled" and self.battle_pass == True):
            pass
        elif(self.MICROTRANSACTIONS != "enabled" or self.battle_pass != True):
            print("Wlacz Microtransacje albo/i  batlepass")
            self.fill_window()
        if(self.is_cheat_enabled == True):
            return
        
        stdscr.erase()
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

        rows,cols = stdscr.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            stdscr.addstr(
                0, 0,
                f"Terminal too small! Need {WIDTH}x{HEIGHT}."
            )
            stdscr.refresh()
            return

        stdscr.border()

        # Scoreboard
        hud = (
            f" Score:{self.score} "
            f" Zycia:{self.lives} "
            f" Poziom:{self.level} "
            f" Pieniandze:{self.money} "
        )
        stdscr.addstr(0, 2, hud[:WIDTH - 4], curses.A_BOLD)                                                                                                                                                                                                                                                                                                                                                                                                                               
        
        random_item = random.randint(0,4)
        random_power = random.choice(DEF_POWERS)

        

        
        stdscr.addstr(
            HEIGHT // 6 , 
           (WIDTH - len("Sklep")) // 5 - 1,
            "Sklep",
            curses.color_pair(2) | curses.A_BOLD
        )
      
        stdscr.addstr(
            HEIGHT // 2,
            (WIDTH - len("Kup")) // 3,
            "Kup",
            curses.color_pair(2) | curses.A_BOLD
        )
        
        for i in range(3):
            i += 1
            for y in range(10):
                stdscr.addch(((HEIGHT - 16) + y) ,(WIDTH  - 10) * i  ,'|',curses.color_pair(2) | curses.A_BOLD )
                stdscr.addch(((HEIGHT - 16) + y) ,(WIDTH  - 40) * i  ,'|',curses.color_pair(2) | curses.A_BOLD )
                for x in range(29):
                    stdscr.addch(HEIGHT  -  17,((WIDTH  - 39) * i) + x ,'_',curses.color_pair(2) | curses.A_BOLD)
                    stdscr.addch(HEIGHT  -  7,((WIDTH  - 39) * i) + x ,'_',curses.color_pair(2) | curses.A_BOLD)
        
        stdscr.addstr(
            HEIGHT  - 4 ,
           (WIDTH - len("Przejdz do nastepnej rondy")) // 3,
           "Przejdz do nastepnej rondy",
           curses.color_pair(2) | curses.A_BOLD
        )
        
        for i in range(4):
             
            stdscr.addstr(
                HEIGHT // 2,
                (WIDTH - len(DEF_ITEMS[random_item])) // 2 + i * 40 ,
                DEF_ITEMS[random_item],
                curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
            HEIGHT // 3,
            (WIDTH - len(random_power)) // 2 + i * 40,
            random_power, 
            curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
           (HEIGHT - 4),
           (WIDTH - len("Exit")) // 3 + 130,
           "Exit",
           curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
            (HEIGHT - 4),
            (WIDTH - len("Reset")) // 3 + 110,
            "Randomiser",
            curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
            (HEIGHT - 4),
            (WIDTH - len("Inventory")) // 3 + 90,
            "Inventory",
            curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
            HEIGHT-4,
            (WIDTH - len("Save")) // 3 + 70,
            "Save",
            curses.color_pair(2) | curses.A_BOLD
        )
        stdscr.addstr(
            HEIGHT - 5 ,
            (WIDTH - len(self.player_name)) // 3 + 50,
            self.player_name,
            curses.color_pair(2) | curses.A_BLINK
        )
     