import curses , random , time
from Shop import Game_ShopEvent
from data.Saves  import *


WIDTH = 120
HEIGHT = 20
try:
    player = load_player("./data/player.json")
except ReferenceError as er:
    print(er)

PLAYER = "<A>"
ENEMY = r"<W>"
PLAYER_BULLET = "|"
ENEMY_BULLET = "`"
class Game:
    def __init__(self):
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 2
        
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.score = player["score"]
        self.lives = player["lives"]
        self.level = player["level"]
        self.money = player["money"]
        self.enemy_dir = 1
        self.frame = 0

        self.game_over = False

        # Iframes
        self.hit_until = 0
        self.invulnerable_until = 0

        self.spawn_enemies()

    def spawn_enemies(self):
        self.enemies = []
        enemy = []
        rows = min(3 + (self.level - 1) // 2, 5)
        cols = 8
     
        for row in range(rows):
            for col in range(cols):
                for e in range(3):
                    x = 5 + col * 5 + e
                    y = 3 + row * 2 
                    enemy.append([y,x])
                self.enemies.append([enemy,True])

    def alive_enemies(self):
        return [e for e in self.enemies if e[1]]

    def update(self, key):
        if self.game_over:
            return

        now = time.monotonic()
        self.frame += 1

        # Player movement
        if key in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.player_x = max(3, self.player_x - 1)

        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_x = min(WIDTH - 4, self.player_x + 1)

        # Shooting
        elif key in (
            ord(" "),
            ord("w"),
            ord("W"),
            curses.KEY_UP
        ):
            if len(self.bullets) < 10:
                self.bullets.append(
                    [self.player_y - 1, self.player_x]
                )
        if key in (curses.KEY_LEFT,ord("A")) or key in (curses.KEY_RIGHT,ord("D")) and key in(
                ord(" "),
                ord("w"),
                ord("W"),
                curses.KEY_UP
            ): 
                if key in (curses.KEY_LEFT, ord("a"), ord("A")):
                            self.player_x = max(3, self.player_x - 1)
                elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
                            self.player_x = min(WIDTH - 4, self.player_x + 1)
                if len(self.bullets) < 10:
                    self.bullets.append(
                        [self.player_y - 1, self.player_x])

            


        # Move enemies
        speed = max(2, 6 - self.level)

        if self.frame % speed == 0:
            alive = self.alive_enemies()
            print(self.alive_enemies)
            for enemy in alive:
                for enemy_part in enemy:
                    for enemy_part_1 in enemy:
                        for x in enemy_part_1:
                          hit_edge = any(enemy_part_1[0] + self.enemy_dir <= 2  or enemy_part_1[0] + self.enemy_dir >= WIDTH - 3)
                          
                if hit_edge:  
                    self.enemy_dir *= -1
                    for enemy in alive:
                        enemy[1] += 3
                else:
                    for enemy in alive:
                        enemy[0] += self.enemy_dir

        # Enemy shooting
        alive = self.alive_enemies()

        if alive and self.frame % max(2, 10 - self.level) == 0:
            enemy = random.choice(alive)
            self.enemy_bullets.append([enemy[1] + 1, enemy[0]])
        
        # Move player bullets and check collisions
        new_bullets = []

        for bullet in self.bullets:
            bullet[0] -= 1
            hit = False

            for enemy in self.alive_enemies():
                for enemy_part in enemy:
                    if bullet[0] == enemy_part[1] and bullet[1] == enemy_part[0]:
                        enemy[2] = False
                        self.score += 10
                        hit = True
                        break

            if not hit and bullet[0] > 1:
                new_bullets.append(bullet)

        self.bullets = new_bullets

        # Move enemy bullets and damage the player
        new_enemy_bullets = []

        for bullet in self.enemy_bullets:
            bullet[0] += 1

            if (
                bullet[0] >= self.player_y
                and abs(bullet[1] - self.player_x) <= 1
            ):
                # Each hit changes the player's color to red.
                if now >= self.invulnerable_until:
                    self.lives -= 1
                    self.hit_until = now + 0.7
                    self.invulnerable_until = now + 1.2

                    if self.lives <= 0:
                        self.game_over = True

                # Remove the bullet after contact.
                continue

            if bullet[0] < HEIGHT - 1:
                new_enemy_bullets.append(bullet)

        self.enemy_bullets = new_enemy_bullets

        # Invaders reaching the player means game over
        for enemy in self.alive_enemies():
            if enemy[1] >= self.player_y - 1:
                self.game_over = True

        # Start the next wave
        if not self.alive_enemies():
            self.level += 1
            self.spawn_enemies()
            self.bullets.clear()
            self.enemy_bullets.clear()
            if self.level % 3 == 0 :
                Game_ShopEvent(player)

        
    def draw(self, screen):
        screen.erase()

        # gg er 
        rows, cols = screen.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            screen.addstr(
                0, 0,
                f"Terminal jest za maly! Potrzebny {WIDTH}x{HEIGHT}."
            )
            screen.refresh()
            return

        screen.border()

       
        hud = (
            f"Score:{self.score} "
            f"Zycia:{self.lives} "
            f"Poziom:{self.level} "
        )
        screen.addstr(0, 2, hud[:WIDTH - 4], curses.A_BOLD)

                
        now = time.monotonic()

        if now < self.hit_until:
            player_color = curses.color_pair(2) | curses.A_BOLD
        else:
            player_color = curses.color_pair(1) | curses.A_BOLD

        
        screen.addstr(
            self.player_y,
            self.player_x - 1,
            PLAYER,
            player_color
        )

    
        enemy_color = curses.color_pair(3) | curses.A_BOLD

        for x, y, alive in self.enemies:
            if alive and 1 <= y < HEIGHT - 1:
                screen.addstr(y, x, ENEMY, enemy_color)

        # Player bullets
        bullet_color = curses.color_pair(4) | curses.A_BOLD
        
        for y, x in self.bullets:
            if 1 <= y < HEIGHT - 1 :
                screen.addch(y, x, PLAYER_BULLET, bullet_color)
                
                

        # Enemy bullets
        enemy_bullet_color = curses.color_pair(2) | curses.A_BOLD

        for y, x in self.enemy_bullets:
            if 1 <= y < HEIGHT - 1:
                screen.addch(y, x, ENEMY_BULLET, enemy_bullet_color)

        if self.level % 3 == 0:
            shop = Game_ShopEvent(player)
            shop.draw_fill_window_shop(screen)

        # Game over screen
        if self.game_over:
            message = "GAME OVER!"
            restart = "R = Restart | Q = Quit"

            screen.addstr(
                HEIGHT // 2,
                (WIDTH - len(message)) // 2,
                message,
                curses.color_pair(2) | curses.A_BOLD
            )

            screen.addstr(
                HEIGHT // 2 + 1,
                (WIDTH - len(restart)) // 2,
                restart
            )

        screen.refresh()
