import curses
import random
import time

WIDTH = 160
HEIGHT = 30

player_name = r"</A\>"
ENEMY = r"\{}/"
PLAYER_BULLET = "|"
ENEMY_BULLET = "`"


def init_game_colors(background=-1):
    """Initialize game colors without overwriting shop color pairs."""
    if not curses.has_colors():
        return

    try:
        curses.init_pair(1, curses.COLOR_MAGENTA, background)
        curses.init_pair(2, curses.COLOR_RED, background)
        curses.init_pair(3, curses.COLOR_GREEN, background)
        curses.init_pair(4, curses.COLOR_YELLOW, background)
    except curses.error:
        pass


def safe_addstr(screen, y, x, text, attr=0):
    """Draw text safely within the current terminal dimensions."""
    rows, cols = screen.getmaxyx()

    if y < 0 or y >= rows or x < 0 or x >= cols:
        return

    available = cols - x
    if available <= 0:
        return

    try:
        screen.addnstr(y, x, str(text), available, attr)
    except curses.error:
        pass


class Game:
    def __init__(self, player):
        self.player = player
    
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 2

        self.bullets = [] 
        self.enemy_bullets = []
        self.enemies = []

        self.score = int(player.get("score", 0))
        self.lives = int(player.get("lives", 3))
        self.level = max(1, int(player.get("level", 1)))
        self.money = int(player.get("money", 0))

        self.enemy_dir = 1
        self.frame = 0
        self.game_over = self.lives <= 0

        self.hit_until = 0.0
        self.invulnerable_until = 0.0

        self.shop = None
        if ["hull reinforcements"] in self.player["items"]:
            player_name = r"</A\>"
            self.player["lives"] += 10

        self.sync_player_data()
        self.spawn_enemies()
 
    def sync_player_data(self):
        """Keep all gameplay statistics in the shared player dictionary."""
        self.player["score"] = self.score
        self.player["lives"] = self.lives
        self.player["level"] = self.level
        self.player["money"] = self.money

    def spawn_enemies(self):
        self.enemies = []

        rows = min(1 + (self.level - 1) // 2, 5)
        cols = 8

        for row in range(rows):
            for col in range(cols):
                x = 5 + col * 5
                y = 3 + row * 2

                self.enemies.append([x, y, True])

        self.enemy_dir = 1

    def alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy[2]]

    def update(self, key):
        if self.game_over or self.shop is not None:
            return

        self.frame += 1
        now = time.monotonic()

        # Player movement.
        if key in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.player_x = max(3, self.player_x - 1)

        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_x = min(WIDTH - 4, self.player_x + 1)

        # Shooting.
        if key in (
            ord(" "),
            ord("w"),
            ord("W"),
            curses.KEY_UP,
        ):
            if len(self.bullets) < 10:
                if self.frame % 2 == 0 :
                    self.bullets.append([
                        self.player_y - 1,
                        self.player_x,
                    ])

        # Move enemies and reverse at the edges.
        speed = max(2, 6 - self.level)
        if "turbomotors" in self.player["items"]:
            speed  = 20
        if self.frame % speed == 0:
            alive = self.alive_enemies()

            if alive:
                hit_edge = any(
                    enemy[0] + self.enemy_dir < 2
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

        alive = self.alive_enemies()

        # Enemy shooting.
        if alive and self.frame % max(2, 10 - self.level) == 0:
            enemy = random.choice(alive)
            self.enemy_bullets.append([
                enemy[1] + 1,
                enemy[0] + 1,
            ])
        if ["spacedefances"] in self.player["items"]:
            for bulet in self.enemy_bullets:
               if  bulet[0] - self.player_y == 3  : 
                    rng =  random.randint(1,2)
                    if rng == 1:
                        self.enemy_bullets.pop(bullet)
      
        # Move player bullets and detect collisions.
        remaining_bullets = []

        for bullet in self.bullets:
            bullet[0] -= 1
            hit = False

            for enemy in alive:
                enemy_x, enemy_y, _ = enemy

                if (
                    bullet[0] == enemy_y
                    and enemy_x <= bullet[1] < enemy_x + len(ENEMY)
                ):
                    enemy[2] = False
                    self.score += 10
                    self.money += 10
                    hit = True
                    break

            if not hit and bullet[0] > 1:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # Move enemy bullets and check collisions with the player.
        remaining_enemy_bullets = []

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
                        self.lives = 0
                        self.game_over = True

                # Remove the bullet even when the player is invulnerable.
                continue

            if bullet[0] < HEIGHT - 1:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets

        # Enemies reaching the player ends the run.
        for enemy in self.alive_enemies():
            if enemy[1] >= self.player_y - 1:
                self.game_over = True
                break

        # Clear the wave and advance to the next level.
        if not self.game_over and not self.alive_enemies():
            self.level += 1
            self.spawn_enemies()

            self.bullets.clear()
            self.enemy_bullets.clear()

            self.sync_player_data()

            # Open the shop every third level.
            if self.level % 3 == 0:
                from Shop import Game_ShopEvent
                self.shop = Game_ShopEvent(self.player)

        self.sync_player_data()

    def draw(self, screen):
        screen.erase()

        rows, cols = screen.getmaxyx()

        if rows < HEIGHT or cols < WIDTH:
            safe_addstr(
                screen, 0, 0,
                f"Terminal too small! Required: {WIDTH}x{HEIGHT}."
            )
            screen.refresh()
            return

        screen.border()

        hud = (
            f"Score: {self.score} "
            f"Lives: {self.lives} "
            f"Level: {self.level} "
            f"Money: {self.money}"
        )

        safe_addstr(screen, 0, 2, hud, curses.A_BOLD)

        now = time.monotonic()

        player_color = (
            curses.color_pair(2) | curses.A_BOLD
            if now < self.hit_until
            else curses.color_pair(1) | curses.A_BOLD
        )

        safe_addstr(
            screen,
            self.player_y,
            self.player_x - 1,
            player_name,
            player_color,
        )

        # Draw enemies.
        enemy_color = curses.color_pair(3) | curses.A_BOLD

        for x, y, alive in self.enemies:
            if alive and 1 <= y < HEIGHT - 1:
                if 1 <= x and x + len(ENEMY) < WIDTH - 1:
                    safe_addstr(screen, y, x, ENEMY, enemy_color)

        # Draw player bullets.
        bullet_color = curses.color_pair(4) | curses.A_BOLD

        for y, x in self.bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(screen, y, x, PLAYER_BULLET, bullet_color)

        # Draw enemy bullets.
        for y, x in self.enemy_bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(
                    screen, y, x, ENEMY_BULLET,
                    curses.color_pair(2) | curses.A_BOLD,
                )

        # Game over overlay.
        if self.game_over:
            message = "GAME OVER!"
            restart = "R = Restart | Q = Quit"

            safe_addstr(
                screen,
                HEIGHT // 2,
                (WIDTH - len(message)) // 2,
                message,
                curses.color_pair(2) | curses.A_BOLD,
            )

            safe_addstr(
                screen,
                HEIGHT // 2 + 1,
                (WIDTH - len(restart)) // 2,
                restart,
                curses.A_BOLD,
            )

        screen.refresh()