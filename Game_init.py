import curses
import random
import time

WIDTH = 160 
HEIGHT = 30

PLAYER_NAME = r"</A\>"
ENEMY = r"\{}/"

PLAYER_BULLET = "*"
ENEMY_BULLET = "`"
LASER = "|"
ROCKET = "@"

SHOT_COOLDOWNS = {
    "bullet": 0.18,
    "lasers": 0.30,
    "rockets": 3.00,
}

ROCKET_RADIUS = 5
ROCKET_DAMAGE_SCORE = 20
EXPLOSION_DURATION = 5 # Frames


def init_game_colors(background=-1):
    """Initialize game colors without overwriting other color pairs."""
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
        self.player_name = PLAYER_NAME

        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 2

        self.bullet_state = "bullet"

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.lasers = []
        self.rockets = []
        self.explosions = []

        self.score = int(player.get("score", 0))
        self.lives = int(player.get("lives", 3))
        self.level = max(1, int(player.get("level", 1)))
        self.money = int(player.get("money", 0))

        self.enemy_dir = 1
        self.frame = 0
        self.game_over = self.lives <= 0

        self.hit_until = 0.0
        self.invulnerable_until = 0.0
        self.last_shot_time = 0.0

        self.shop = None

        items = self.player.setdefault("items", [])

        # Apply hull reinforcements once per Game initialization.
        if "hull reinforcements" in items:
            self.lives += 10
            items.remove("hull reinforcements")

        self.sync_player_data()
        self.spawn_enemies()

    def sync_player_data(self):
        """Keep gameplay statistics synchronized with player data."""
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

    def damage_enemy(self, enemy, points):
        """Destroy an enemy and award points and money exactly once."""
        if not enemy[2]:
            return

        enemy[2] = False
        self.score += points
        self.money += points

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

        # Weapon selection.
        if key == ord("0"):
            self.bullet_state = "bullet"
        elif key == ord("1"):
            self.bullet_state = "lasers"
        elif key == ord("2"):
            self.bullet_state = "rockets"

        # Shooting cooldown. Key-repeat cannot bypass this timer.
        shoot_keys = (
            ord(" "),
            ord("w"),
            ord("W"),
            curses.KEY_UP,
        )

        if key in shoot_keys:
            cooldown = SHOT_COOLDOWNS[self.bullet_state]

            if now - self.last_shot_time >= cooldown:
                if self.bullet_state == "bullet":
                    if len(self.bullets) < 100:
                        self.bullets.append([
                            self.player_y - 1,
                            self.player_x,
                        ])
                        self.last_shot_time = now

                elif self.bullet_state == "lasers":
                    if len(self.lasers) < 20:
                        self.lasers.append([
                            self.player_y - 1,
                            self.player_x,
                        ])
                        self.last_shot_time = now

                elif self.bullet_state == "rockets":
                    if len(self.rockets) < 10:
                        self.rockets.append([
                            self.player_y - 1,
                            self.player_x,
                        ])
                        self.last_shot_time = now

        # Enemy movement.
        speed = max(2, 6 - self.level)

        if "turbomotors" in self.player.get("items", []):
            speed = 1

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

        # Space defenses: destroy incoming bullets close to the player.
        if "spacedefances" in self.player.get("items", []):
            self.enemy_bullets = [
                bullet for bullet in self.enemy_bullets
                if not (
                    bullet[0] >= self.player_y - 3
                    and abs(bullet[1] - self.player_x) <= 1
                )
            ]

        # Move normal bullets and detect collisions.
        remaining_bullets = []

        for bullet in self.bullets:
            bullet[0] -= 1
            hit = False

            for enemy in alive:
                enemy_x, enemy_y, enemy_alive = enemy

                if (
                    enemy_alive
                    and bullet[0] == enemy_y
                    and enemy_x <= bullet[1] < enemy_x + len(ENEMY)
                ):
                    self.damage_enemy(enemy, 10)
                    hit = True
                    break

            if not hit and bullet[0] > 1:
                remaining_bullets.append(bullet)

        self.bullets = remaining_bullets

        # Move lasers and detect collisions.
        remaining_lasers = []

        for laser in self.lasers:
            laser[0] -= 2
            hit = False

            for enemy in self.alive_enemies():
                enemy_x, enemy_y, _ = enemy

                if (
                    enemy_y <= laser[0] <= enemy_y + 1
                    and enemy_x <= laser[1] < enemy_x + len(ENEMY)
                ):
                    self.damage_enemy(enemy, 10)
                    hit = True
                    break

            if not hit and laser[0] > 1:
                remaining_lasers.append(laser)

        self.lasers = remaining_lasers

        # Move rockets and trigger area-of-effect explosions.
        remaining_rockets = []

        for rocket in self.rockets:
            rocket[0] -= 2
            rocket_y, rocket_x = rocket
            hit = False

            # A rocket detonates when it reaches an enemy.
            for enemy in self.alive_enemies():
                enemy_x, enemy_y, _ = enemy

                if (
                    abs(rocket_y - enemy_y) <= 1
                    and enemy_x <= rocket_x < enemy_x + len(ENEMY)
                ):
                    hit = True
                    break

            if hit:
                # Store explosion center and expiration frame.
                self.explosions.append([
                    rocket_x,
                    rocket_y,
                    self.frame + EXPLOSION_DURATION,
                ])

                # Damage every living enemy in the blast radius.
                for enemy in self.alive_enemies():
                    enemy_x, enemy_y, _ = enemy
                    enemy_center_x = enemy_x + len(ENEMY) // 2

                    dx = abs(enemy_center_x - rocket_x)
                    dy = abs(enemy_y - rocket_y)

                    # Circular blast radius.
                    if dx * dx + dy * dy <= ROCKET_RADIUS ** 2:
                        self.damage_enemy(
                            enemy,
                            ROCKET_DAMAGE_SCORE,
                        )

            elif rocket_y > 1:
                remaining_rockets.append(rocket)

        self.rockets = remaining_rockets

        # Remove expired explosions.
        self.explosions = [
            explosion for explosion in self.explosions
            if explosion[2] > self.frame
        ]

        # Move enemy bullets and check player collisions.
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

                continue

            if bullet[0] < HEIGHT - 1:
                remaining_enemy_bullets.append(bullet)

        self.enemy_bullets = remaining_enemy_bullets

        # Enemies reaching the player ends the run.
        for enemy in self.alive_enemies():
            if enemy[1] >= self.player_y - 1:
                self.game_over = True
                break

        # Advance to the next level when the wave is cleared.
        if not self.game_over and not self.alive_enemies():
            self.level += 1
            self.spawn_enemies()

            self.bullets.clear()
            self.lasers.clear()
            self.rockets.clear()
            self.enemy_bullets.clear()
            self.explosions.clear()

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
                screen,
                0,
                0,
                f"Terminal too small! Required: {WIDTH}x{HEIGHT}.",
            )
            screen.refresh()
            return

        screen.border()
        is_reloaded = "Reloading... "
        reload_b = time.monotonic() - self.last_shot_time -4
        
        if self.bullet_state == "rocket":   
           reload_b = time.monotonic() - self.last_shot_time - 4
           if reload_b >= 0:
               reload_b = 0
               is_reloaded = " Done"
        elif self.bullet_state == "laser":
            reload_b = time.monotonic() - self.last_shot_time - 0.30
            if reload_b >= 0:
                reload_b = 0
                is_reloaded = "Done"
        elif self.bullet_state == "bullet":
            reload_b = time.monotonic() - self.last_shot_time - 0.18
            if reload_b >= 0:
                reload_b = 0
                is_reloaded = "Done"
        
        hud = (
            f"Score: {self.score} "
            f"Lives: {self.lives} "
            f"Level: {self.level} "
            f"Money: {self.money} "
            f"Weapon: {self.bullet_state}"
            f"Reload  {  reload_b , is_reloaded}"
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
            self.player_name,
            player_color,
        )

        # Draw enemies.
        enemy_color = curses.color_pair(3) | curses.A_BOLD

        for x, y, alive in self.enemies:
            if alive and 1 <= y < HEIGHT - 1:
                if 1 <= x and x + len(ENEMY) < WIDTH - 1:
                    safe_addstr(screen, y, x, ENEMY, enemy_color)

        # Draw normal bullets.
        bullet_color = curses.color_pair(4) | curses.A_BOLD

        for y, x in self.bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(
                    screen, y, x, PLAYER_BULLET, bullet_color
                )

        # Draw lasers.
        for y, x in self.lasers:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(
                    screen, y, x, LASER, bullet_color
                )

        # Draw rockets.
        for y, x in self.rockets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(
                    screen,
                    y,
                    x,
                    ROCKET,
                    curses.color_pair(2) | curses.A_BOLD,
                )

        # Draw explosions.
        for x, y, expires_at in self.explosions:
            remaining = expires_at - self.frame

            # A larger blast is drawn while the explosion is active.
            radius = min(ROCKET_RADIUS, max(1, remaining))

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue

                    blast_x = x + dy
                    blast_y = y +  (dx // 3)

                    if (
                        1 <= blast_x < WIDTH - 1
                        and 1 <= blast_y < HEIGHT - 1
                    ):
                        safe_addstr(
                            screen,
                            blast_y,
                            blast_x,
                            "*",
                            curses.color_pair(2) | curses.A_BOLD,
                        )

        # Draw enemy bullets.
        for y, x in self.enemy_bullets:
            if 1 <= y < HEIGHT - 1 and 1 <= x < WIDTH - 1:
                safe_addstr(
                    screen,
                    y,
                    x,
                    ENEMY_BULLET,
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