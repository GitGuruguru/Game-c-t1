import curses , random , time

WIDTH = 50
HEIGHT = 24

PLAYER = "<A>"
ENEMY = "W"
PLAYER_BULLET = "|"
ENEMY_BULLET = "!"

class Game:
    def __init__(self):
        self.player_x = WIDTH // 2
        self.player_y = HEIGHT - 2

        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []

        self.score = 0
        self.lives = 3
        self.level = 1

        self.enemy_dir = 1
        self.frame = 0

        self.game_over = False

        # Player color and damage protection
        self.hit_until = 0
        self.invulnerable_until = 0

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

    def alive_enemies(self):
        return [e for e in self.enemies if e[2]]

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
            if len(self.bullets) < 20:
                self.bullets.append(
                    [self.player_y - 1, self.player_x]
                )

        # Move enemies
        speed = max(2, 8 - self.level)

        if self.frame % speed == 0:
            alive = self.alive_enemies()

            hit_edge = any(
                e[0] + self.enemy_dir <= 2
                or e[0] + self.enemy_dir >= WIDTH - 3
                for e in alive
            )

            if hit_edge:
                self.enemy_dir *= -1

                for enemy in alive:
                    enemy[1] += 1
            else:
                for enemy in alive:
                    enemy[0] += self.enemy_dir

        # Enemy shooting
        alive = self.alive_enemies()

        if alive and self.frame % max(4, 20 - self.level) == 0:
            enemy = random.choice(alive)
            self.enemy_bullets.append([enemy[1] + 1, enemy[0]])

        # Move player bullets and check collisions
        new_bullets = []

        for bullet in self.bullets:
            bullet[0] -= 1
            hit = False

            for enemy in self.alive_enemies():
                if bullet[0] == enemy[1] and bullet[1] == enemy[0]:
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

    def draw(self, screen):
        screen.erase()

        # Terminal dimensions
        rows, cols = screen.getmaxyx()

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
            f"Lives:{self.lives} "
            f"Level:{self.level} "
        )
        screen.addstr(0, 2, hud[:WIDTH - 4], curses.A_BOLD)

        # Select player color
        now = time.monotonic()

        if now < self.hit_until:
            player_color = curses.color_pair(2) | curses.A_BOLD
        else:
            player_color = curses.color_pair(1) | curses.A_BOLD

        # Player
        screen.addstr(
            self.player_y,
            self.player_x - 1,
            PLAYER,
            player_color
        )

        # Invaders
        enemy_color = curses.color_pair(3) | curses.A_BOLD

        for x, y, alive in self.enemies:
            if alive and 1 <= y < HEIGHT - 1:
                screen.addch(y, x, ENEMY, enemy_color)

        # Player bullets
        bullet_color = curses.color_pair(4) | curses.A_BOLD

        for y, x in self.bullets:
            if 1 <= y < HEIGHT - 1:
                screen.addch(y, x, PLAYER_BULLET, bullet_color)

        # Enemy bullets
        enemy_bullet_color = curses.color_pair(2) | curses.A_BOLD

        for y, x in self.enemy_bullets:
            if 1 <= y < HEIGHT - 1:
                screen.addch(y, x, ENEMY_BULLET, enemy_bullet_color)

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
