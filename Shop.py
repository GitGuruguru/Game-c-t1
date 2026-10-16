import curses , random , time 
from Game_init import *

WIDTH = 59
HEIGHT = 24

konami_code = []
DEF_ITEMS =  {
    "turbomotors" : 500,
    "spacedefences": 240, 
    "termalshield": 100,
    "misledefence": 2000,
    "hull reinforsments": 809
}
SPECIAL_ITEMS = {
    "state of the art defence system": 2505
}
DEF_POWERS = {
    "Tempester" : 2505,
    "Ground Zero" : 3005,
    "Nemesis" : 5005,
    "Omega" : 1205,
    "Alpha" : 14005,
    "Delta" : 2405,
    "Equilibrium": 3125,
}
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
        
    def draw_fill_window_shop(self,screen):

        if(self.MICROTRANSACTIONS == "enabled" and self.battle_pass == True):
            pass
        elif(self.MICROTRANSACTIONS != "enabled" or self.battle_pass != True):
            print("Wlacz Microtransacje albo/i  batlepass")
            self.fill_window()
        if(self.is_cheat_enabled == True):
            return
        
        screen.erase()

        rows,cols = screen.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            screen.addstr(
                0, 0,
                f"Terminal too small! Need {WIDTH}x{HEIGHT}."
            )
            screen.refresh()
            return

        screen.border()

        # Scoreboard
        hud = (
            f" Score:{self.score} "
            f" Zycia:{self.lives} "
            f" Poziom:{self.level} "
            f" Pieniandze:{self.money} "
        )
        screen.addstr(0, 2, hud[:WIDTH - 4], curses.A_BOLD)                                                                                                                                                                                                                                                                                                                                                                                                                               
        random_item = "random.choice(DEF_ITEMS)"
        random_power =" random.choice(DEF_POWERS)"
        
        screen.addstr(
            HEIGHT // 6 , 
           (WIDTH - len("Sklep")) // 5 - 1,
            "Sklep",
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            HEIGHT // 2,
            (WIDTH - len("Kup")) // 3,
            "Kup",
            curses.color_pair(2) | curses.A_BOLD
        )
        
        for i in range(3):
            i += 1
            for y in range(10):
                screen.addch(((HEIGHT - 16) + y) ,(WIDTH  - 10) * i  ,'|',curses.color_pair(2) | curses.A_BOLD )
                screen.addch(((HEIGHT - 16) + y) ,(WIDTH  - 40) * i  ,'|',curses.color_pair(2) | curses.A_BOLD )
                for x in range(29):
                    screen.addch(HEIGHT  -  17,((WIDTH  - 39) * i) + x ,'_',curses.color_pair(2) | curses.A_BOLD)
                    screen.addch(HEIGHT  -  7,((WIDTH  - 39) * i) + x ,'_',curses.color_pair(2) | curses.A_BOLD)
        screen.addstr(
            HEIGHT  - 4 ,
           (WIDTH - len("Przejdz do nastepnej rondy")) // 3,
           "Przejdz do nastepnej rondy",
           curses.color_pair(2) | curses.A_BOLD
        )
        
        for i in range(4):
            screen.addstr(
                HEIGHT // 2,
                (WIDTH - len(random_item)) // 2 + i * 40 ,
                random_item,
                curses.color_pair(2) | curses.A_BOLD
            )
        screen.addstr(
            HEIGHT // 3,
            (WIDTH - len(random_power)) // 2 + i * 40,
            random_power, 
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            (HEIGHT - 4),
            (WIDTH - len("Kup")) // 3 + 150,
            "Kup",
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
           (HEIGHT - 4),
           (WIDTH - len("Exit")) // 3 + 130,
           "Exit",
           curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            (HEIGHT - 4),
            (WIDTH - len("Reset")) // 3 + 110,
            "Randomiser",
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            (HEIGHT - 4),
            (WIDTH - len("Inventory")) // 3 + 90,
            "Inventory",
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            HEIGHT-4,
            (WIDTH - len("Save")) // 3 + 70,
            "Save",
            curses.color_pair(2) | curses.A_BOLD
        )
        screen.addstr(
            HEIGHT - 5 ,
            (WIDTH - len(self.player_name)) // 3 + 50,
            self.player_name,
            curses.color_pair(2) | curses.A_BLINK
        )