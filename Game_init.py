
import curses
import random
import time

from Shop import Game_ShopEvent
from data.Saves import load_player


WIDTH = 120
HEIGHT = 20

PLAYER = "<A>"
ENEMY = "<W>"
PLAYER_BULLET = "|"
ENEMY_BULLET = "`"


try:
    player = load_player("./data/player.json")
    if not isinstance(player, dict):
        raise ValueError("Invalid player data")

except (ReferenceError, FileNotFoundError, ValueError, KeyError) as er:
    print(f"Could not load player: {er}")
    player = {
        "score": 0,
        "lives": 3,
        "level": 1,
        "money": 0,
    }

# Ensure all required player fields exist.

class Game:
    def __init__(self):
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 2

        # Bullets are stored as [y, x].
        self.bullets = []
        self.enemy_bullets = []

        # Enemies are stored as [x, y, alive].
        self.enemies = []

        self.score = player["score"]
        self.lives = player["lives"]
        self.level = player["level"]
        self.money = player["money"]

        self.enemy_dir = 1
        self.frame = 0
        self.game_over = False

        # Damage and invulnerability timers.
        self.hit_until = 0.0
        self.invulnerable_until = 0.0

        # Create the shop only when a shop wave begins.
        self.shop = None

        self.spawn_enemies()

    def spawn_enemies(self):
        self.enemies = []

        rows = min(3 + (self.level - 1) // 2, 5)
        cols = 8

        for row in range(rows):
            for col in range(cols):
                x = 5 + col * 5
                y = 3 + row * 2

                self.enemies.append([x, y, True])

        self.enemy_dir = 1

    def alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy[2]]

    def sync_player_data(self):
        """Keep the loaded player dictionary synchronized."""
        player["score"] = self.score
        player["lives"] = self.lives
        player["level"] = self.level
        player["money"] = self.money

    def update(self, key):
        if self.game_over:
            return

        now = time.monotonic()
        self.frame += 1

        # Player movement.
        if key in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.player_x = max(3, self.player_x - 1)

        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_x = min(WIDTH - 4, self.player_x + 1)

        # Shooting: SPACE, W, or UP.
        if key in (
            ord(" "),
            ord("w"),
            ord("W"),
            curses.KEY_UP,
        ):
            if len(self.bullets) < 10:
                self.bullets.append(
                    [self.player_y - 1, self.player_x]
                )

        # Move enemies.
        speed = max(2, 6 - self.level)

        if self.frame % speed == 0:
            alive = self.alive_enemies()

            if alive:
                hit_edge = any(
                    enemy[0] + self.enemy_dir <= 2
                    or enemy[0] + len(ENEMY) + self.enemy_dir
                    >= WIDTH - 2
                    for enemy in alive
                )

                if hit_edge:
                    self.enemy_dir *= -1

                    for enemy in alive:
                        enemy[1] += 1
                else:
                    for enemy in alive:
                        enemy[0] += self.enemy_dir

        # Enemy shooting.
        alive = self.alive_enemies()

        if alive and self.frame % max(2, 10 - self.level) == 0:
            enemy = random.choice(alive)

            self.enemy_bullets.append(
                [enemy[1] + 1, enemy[0] + 1]
            )

        # Move player bullets and detect collisions.
        new_bullets = []

        for bullet in self.bullets:
            bullet[0] -= 1
            hit = False

            for enemy in self.alive_enemies():
                enemy_x, enemy_y, _ = enemy

                # The enemy sprite occupies three columns.
                if (
                    bullet[0] == enemy_y
                    and enemy_x <= bullet[1] < enemy_x + len(ENEMY)
                ):
                    enemy[2] = False
                    self.score += 10
                    hit = True
                    break

            if not hit and bullet[0] > 1:
                new_bullets.append(bullet)

        self.bullets = new_bullets

        # Move enemy bullets and check player damage.
        new_enemy_bullets = []

        for bullet in self.enemy_bullets:
            bullet[0] += 1

            if (
                bullet[0] >= self.player_y
                and abs(bullet[1] - self.player_x) <= 1
            ):
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

        # Enemies reaching the player ends the game.
        for enemy in self.alive_enemies():
            if enemy[1] >= self.player_y - 1:
                self.game_over = True
                break

        # Start the next wave when all enemies are defeated.
        if not self.game_over and not self.alive_enemies():
            self.level += 1
            self.spawn_enemies()

            self.bullets.clear()
            self.enemy_bullets.clear()

            # Open the shop on every third level.
            if self.level % 3 == 0:
                self.shop = Game_ShopEvent(player)
            else:
                self.shop = None

        self.sync_player_data()

    def draw(self, screen):
        screen.erase()

        rows, cols = screen.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            screen.addstr(
                0,
                0,
                f"Terminal too small! Required: {WIDTH}x{HEIGHT}."
            )
            screen.refresh()
            return

        screen.border()

        # HUD.
        hud = (
            f"Score: {self.score} "
            f"Lives: {self.lives} "
            f"Level: {self.level} "
            f"Money: {self.money}"
        )

        screen.addstr(
            0, 2, hud[:WIDTH - 4], curses.A_BOLD
        )

        # Player.
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

        # Enemies.
        enemy_color = curses.color_pair(3) | curses.A_BOLD

        for x, y, alive in self.enemies:
            if alive and 1 <= y < HEIGHT - 1:
                if 1 <= x and x + len(ENEMY) < WIDTH - 1:
                    screen.addstr(y, x, ENEMY, enemy_color)

        # Player bullets.
        bullet_color = curses.color_pair(4) | curses.A_BOLD

        for y, x in self.bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                screen.addch(y, x, PLAYER_BULLET, bullet_color)

        # Enemy bullets.
        enemy_bullet_color = curses.color_pair(2) | curses.A_BOLD

        for y, x in self.enemy_bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                screen.addch(y, x, ENEMY_BULLET, enemy_bullet_color)

        # Shop window. Reuse the existing shop instance.
        if self.shop is not None:
            self.shop.draw_fill_window_shop(screen)

        # Game over screen.
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
