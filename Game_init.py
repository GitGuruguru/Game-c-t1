"""Core simulation and terminal renderer for the Starfall arcade shooter."""
import random
import time

try:
    import curses
except ImportError:  # Keep the simulation/rendering usable on stock Windows Python.
    import curses_compat as curses

from data.Saves import load_player, player_save_path


PLAYER = "/A\\"
ENEMY = "<W>"
ENEMY_TYPES = {
    "scout": {"sprite": "<w>", "color": 3, "hp": 1, "points": 10},
    "striker": {"sprite": "<S>", "color": 5, "hp": 2, "points": 20},
    "tank": {"sprite": "<T>", "color": 6, "hp": 3, "points": 35},
    "boss": {"sprite": "<B>", "color": 2, "hp": 18, "points": 250},
}
ITEMS = {
    "Rapid Fire": {"cost": 100, "power": "Assault", "description": "Shoot faster"},
    "Twin Cannons": {"cost": 160, "power": "Assault", "description": "Fire two bolts"},
    "Piercing Laser": {"cost": 220, "power": "Laser", "description": "Laser passes through enemies"},
    "Prism Beam": {"cost": 280, "power": "Laser", "description": "Beam splits into a wide blast"},
    "Aegis Shield": {"cost": 120, "power": "Defense", "description": "Start each wave with a shield"},
    "Repair Kit": {"cost": 90, "power": "Defense", "description": "Restore one life"},
    "Nova Core": {"cost": 300, "power": "Arcane", "description": "Explosive shots"},
    "Pulse Core": {"cost": 240, "power": "Arcane", "description": "Shock nearby enemies"},
    "Extra Life": {"cost": 120, "power": "Survival", "description": "Add one life", "repeatable": True},
}
POWER_SETS = {
    "Assault": ("Rapid Fire", "Twin Cannons"),
    "Laser": ("Piercing Laser", "Prism Beam"),
    "Defense": ("Aegis Shield", "Repair Kit"),
    "Arcane": ("Nova Core", "Pulse Core"),
}


def safe_addstr(screen, y, x, value, attr=0):
    """Write only the visible portion of a string, including on tiny terminals."""
    rows, cols = screen.getmaxyx()
    if 0 <= y < rows and 0 <= x < cols:
        try:
            screen.addstr(y, x, str(value)[:max(0, cols - x - 1)], attr)
        except curses.error:
            pass


class Game:
    def __init__(self, player=None):
        self.player_data = player if player is not None else load_player("./data/player.json")
        self.player_data.setdefault("name", "Pilot")
        self.player_data.setdefault("items", {})
        self.player_data.setdefault("power", self.player_data.get("powers", {}))
        self.player_data.setdefault("powers", self.player_data["power"])
        self.player_x = 30
        self.player_y = 20
        self.width = 80
        self.height = 24
        self.bullets = []  # dicts: x, y, type, pierce
        self.enemy_bullets = []
        self.enemies = []  # dicts with position, type, hp, and alive
        self.score = int(self.player_data.get("score", 0))
        self.lives = max(1, int(self.player_data.get("lives", 3)))
        self.level = max(1, int(self.player_data.get("level", 1)))
        self.money = int(self.player_data.get("money", 0))
        self.enemy_dir = 1
        self.frame = 0
        self.game_over = False
        self.hit_until = 0.0
        self.invulnerable_until = 0.0
        self.shop_open = False
        self.shop_selection = 0
        self.message = "Arrows/A,D move   Space shoots   B buys   T power ability"
        self.message_until = time.monotonic() + 5
        self.last_shot = 0.0
        self.ability_until = 0.0
        self.ability_ready = False
        self.spawn_enemies()

    def dimensions(self, screen):
        rows, cols = screen.getmaxyx()
        return max(20, cols), max(12, rows)

    def sync_player_data(self):
        self.player_data.update(score=self.score, lives=self.lives, level=self.level, money=self.money)
        self.player_data["power"] = self.player_data.get("powers", self.player_data.get("power", {}))
        self.player_data["powers"] = self.player_data["power"]

    def owned(self, name):
        return bool(self.player_data.get("items", {}).get(name))

    def spawn_enemies(self):
        self.enemies = []
        rows = min(2 + (self.level - 1) // 2, 4)
        cols = min(8, max(4, (self.width - 8) // 7))
        start_x = max(2, (self.width - cols * 6) // 2)
        # A named boss appears every fourth wave; normal waves mix distinct enemy classes.
        boss_wave = self.level % 4 == 0
        if boss_wave:
            self.enemies.append({"x": max(1, self.width // 2 - 2), "y": 3, "kind": "boss", "hp": ENEMY_TYPES["boss"]["hp"] + self.level, "alive": True})
            for col in range(min(cols, 5)):
                self.enemies.append({"x": start_x + col * 6, "y": 6, "kind": "striker", "hp": 2, "alive": True})
        else:
            for row in range(rows):
                for col in range(cols):
                    kind = "scout" if row == 0 else random.choice(("scout", "striker", "tank"))
                    self.enemies.append({"x": start_x + col * 6, "y": 3 + row * 2, "kind": kind, "hp": ENEMY_TYPES[kind]["hp"], "alive": True})
        self.enemy_dir = 1

    def alive_enemies(self):
        return [enemy for enemy in self.enemies if enemy["alive"]]

    def _shoot(self):
        now = time.monotonic()
        cooldown = .12 if self.owned("Rapid Fire") else .27
        if now - self.last_shot < cooldown:
            return
        self.last_shot = now
        laser = self.owned("Piercing Laser")
        bullet_type = "laser" if laser else ("nova" if self.owned("Nova Core") else "bolt")
        offsets = (-1, 1) if self.owned("Twin Cannons") else (0,)
        for offset in offsets:
            self.bullets.append({"y": self.player_y - 1, "x": self.player_x + offset, "type": bullet_type, "pierce": laser})

    def activate_set_ability(self):
        items = self.player_data.get("items", {})
        complete_sets = [name for name, members in POWER_SETS.items() if all(items.get(member) for member in members)]
        if complete_sets:
            self.ability_ready = True
            self.ability_until = time.monotonic() + 2.5
            if complete_sets[-1] == "Defense":
                self.lives += 1
            else:
                for enemy in self.alive_enemies():
                    enemy["hp"] -= 4 if enemy["kind"] == "boss" else 999
                    if enemy["hp"] <= 0:
                        enemy["alive"] = False
                        self._reward(enemy)
            self.message = f"{complete_sets[-1]} set ability unleashed!"
        else:
            self.message = "Complete a matching item pair to unlock a T ability."
        self.message_until = time.monotonic() + 2.5

    def _reward(self, enemy):
        info = ENEMY_TYPES[enemy["kind"]]
        self.score += info["points"]
        self.money += max(8, info["points"] // 2)

    def _buy(self):
        choices = list(ITEMS)
        name = choices[self.shop_selection % len(choices)]
        item = ITEMS[name]
        if self.owned(name) and not item.get("repeatable"):
            self.message = f"{name} already owned."
        elif self.money < item["cost"]:
            self.message = f"Need {item['cost'] - self.money} more credits for {name}."
        else:
            self.money -= item["cost"]
            if item.get("repeatable"):
                self.lives += 1
            else:
                self.player_data.setdefault("items", {})[name] = True
            if name == "Repair Kit":
                self.lives += 1
            self.message = f"Bought {name}! {item['description']}."
        self.message_until = time.monotonic() + 2.4

    def update(self, key, screen):
        width, height = self.dimensions(screen)
        self.width, self.height = width, height
        self.player_y = height - 2
        self.player_x = min(max(2, self.player_x), width - 3)
        if self.game_over:
            if key in (ord("r"), ord("R")):
                self.player_data["lives"] = 3
                self.__init__(self.player_data)
            return
        if self.shop_open:
            if key in (curses.KEY_LEFT, ord("a"), ord("A"), curses.KEY_UP):
                self.shop_selection = (self.shop_selection - 1) % len(ITEMS)
            elif key in (curses.KEY_RIGHT, ord("d"), ord("D"), curses.KEY_DOWN):
                self.shop_selection = (self.shop_selection + 1) % len(ITEMS)
            elif key in (ord("b"), ord("B"), ord(" ")):
                self._buy()
            elif key in (ord("s"), ord("S")):
                from data.Saves import save_player
                self.sync_player_data()
                save_player(self.player_data, player_save_path())
                self.message = "Progress saved."
                self.message_until = time.monotonic() + 2
            elif key in (ord("n"), ord("N"), ord("q"), ord("Q"), 10, 13):
                self.shop_open = False
                self.spawn_enemies()
            return
        self.frame += 1
        if key in (curses.KEY_LEFT, ord("a"), ord("A")):
            self.player_x = max(2, self.player_x - 2)
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_x = min(width - 3, self.player_x + 2)
        elif key in (ord(" "), ord("w"), ord("W"), curses.KEY_UP):
            self._shoot()
        elif key in (ord("t"), ord("T")):
            self.activate_set_ability()

        speed = max(10, 20 - self.level)
        if self.frame % speed == 0:
            alive = self.alive_enemies()
            hit_edge = any(e["x"] + self.enemy_dir < 1 or e["x"] + 4 + self.enemy_dir >= width - 1 for e in alive)
            if hit_edge:
                self.enemy_dir *= -1
                for enemy in alive:
                    enemy["y"] += 1
            else:
                for enemy in alive:
                    enemy["x"] += self.enemy_dir
        alive = self.alive_enemies()
        if alive and self.frame % max(3, 14 - self.level) == 0:
            shooter = random.choice(alive)
            self.enemy_bullets.append({"x": shooter["x"] + 1, "y": shooter["y"] + 1, "kind": shooter["kind"]})

        next_bullets = []
        for bullet in self.bullets:
            bullet["y"] -= 1
            hits = [e for e in self.alive_enemies() if bullet["y"] == e["y"] and e["x"] <= bullet["x"] < e["x"] + 3]
            for enemy in hits:
                damage = 2 if bullet["type"] in ("laser", "nova") else 1
                enemy["hp"] -= damage
                if enemy["hp"] <= 0:
                    enemy["alive"] = False
                    self._reward(enemy)
                if not bullet["pierce"]:
                    break
            if bullet["y"] > 1 and (bullet["pierce"] or not hits):
                next_bullets.append(bullet)
            elif bullet["type"] == "nova" and hits:
                for enemy in self.alive_enemies():
                    if abs(enemy["x"] - bullet["x"]) < 7 and abs(enemy["y"] - bullet["y"]) < 3:
                        enemy["hp"] -= 2
                        if enemy["hp"] <= 0:
                            enemy["alive"] = False
                            self._reward(enemy)
        self.bullets = next_bullets

        next_enemy_bullets = []
        for bullet in self.enemy_bullets:
            bullet["y"] += 1
            if bullet["y"] >= self.player_y and abs(bullet["x"] - self.player_x) <= 1 and time.monotonic() >= self.invulnerable_until:
                self.lives = max(0, self.lives - 1)
                self.hit_until = time.monotonic() + .4
                self.invulnerable_until = time.monotonic() + 1.1
                if self.lives <= 0:
                    self.game_over = True
                continue
            if bullet["y"] < height - 1:
                next_enemy_bullets.append(bullet)
        self.enemy_bullets = next_enemy_bullets
        if any(e["y"] >= self.player_y - 1 for e in alive):
            self.game_over = True
        if not self.game_over and not self.alive_enemies():
            self.level += 1
            self.money += 50 + self.level * 8
            self.bullets.clear()
            self.enemy_bullets.clear()
            self.shop_open = True
            self.shop_selection = (self.level - 2) % len(ITEMS)
            self.message = f"Wave cleared! +{50 + self.level * 8} credits. Visit the shop, then press N."
            self.message_until = time.monotonic() + 4
        self.sync_player_data()

    def draw(self, screen):
        screen.erase()
        rows, cols = screen.getmaxyx()
        width, height = self.dimensions(screen)
        self.width, self.height = width, height
        if rows < 12 or cols < 20:
            safe_addstr(screen, 0, 0, "Resize terminal to at least 20x12 to play.", curses.A_BOLD)
            screen.refresh()
            return
        try:
            screen.border()
        except curses.error:
            pass
        self.player_y = height - 2
        self.player_x = min(max(2, self.player_x), width - 3)
        safe_addstr(screen, 0, 2, f" STARFALL  |  Score {self.score}  Lives {self.lives}  Wave {self.level}  Credits {self.money} "[:cols - 4], curses.A_BOLD)
        if not self.shop_open:
            color = curses.color_pair(2 if time.monotonic() < self.hit_until else 1) | curses.A_BOLD
            safe_addstr(screen, self.player_y, self.player_x - 1, PLAYER, color)
            for enemy in self.enemies:
                if not enemy["alive"]:
                    continue
                info = ENEMY_TYPES[enemy["kind"]]
                safe_addstr(screen, enemy["y"], enemy["x"], info["sprite"], curses.color_pair(info["color"]) | curses.A_BOLD)
                if enemy["kind"] == "boss" and enemy["y"] + 1 < height - 1:
                    safe_addstr(screen, enemy["y"] + 1, enemy["x"], f"HP {enemy['hp']}", curses.color_pair(2))
            for bullet in self.bullets:
                glyph, color = {"bolt": ("|", 4), "laser": ("║", 5), "nova": ("*", 6)}[bullet["type"]]
                safe_addstr(screen, bullet["y"], bullet["x"], glyph, curses.color_pair(color) | curses.A_BOLD)
            for bullet in self.enemy_bullets:
                safe_addstr(screen, bullet["y"], bullet["x"], "v", curses.color_pair(2) | curses.A_BOLD)
        if self.shop_open:
            safe_addstr(screen, 2, 3, "ARMORY  |  ←/→ select   B buy   S save   N continue", curses.A_BOLD | curses.color_pair(4))
            names = list(ITEMS)
            visible = names[max(0, min(self.shop_selection - 2, len(names) - 4)):max(4, min(self.shop_selection - 2, len(names) - 4)) + 4]
            if len(visible) < 4:
                visible = names[:4]
            for i, name in enumerate(visible):
                item = ITEMS[name]
                y = 5 + i * 3
                selected = name == names[self.shop_selection]
                owned = self.owned(name)
                locked = not owned and self.money < item["cost"]
                status = "OWNED" if owned else ("LOCKED" if locked else f"{item['cost']} cr")
                color = 2 if locked else (3 if owned else (4 if selected else 0))
                safe_addstr(screen, y, 4, ("> " if selected else "  ") + name, curses.color_pair(color) | (curses.A_BOLD if selected else 0))
                safe_addstr(screen, y, min(cols - 20, 26), f"{status}  |  {item['power']}", curses.color_pair(color))
                safe_addstr(screen, y + 1, 7, item["description"])
            sets = [power for power, members in POWER_SETS.items() if all(self.owned(name) for name in members)]
            safe_addstr(screen, min(height - 3, 18), 4, f"T ability: {', '.join(sets) if sets else 'collect both items of any power'}")
        elif time.monotonic() < self.message_until:
            safe_addstr(screen, height - 1, 2, self.message[:cols - 4], curses.A_BOLD)
        else:
            safe_addstr(screen, height - 1, 2, "Move: ←/→ or A/D    Fire: Space    Set ability: T", curses.A_DIM)
        if self.game_over:
            safe_addstr(screen, height // 2, max(1, (cols - 12) // 2), "GAME OVER", curses.color_pair(2) | curses.A_BOLD)
            safe_addstr(screen, height // 2 + 1, max(1, (cols - 27) // 2), "Press R to restart, Q to exit")
        screen.refresh()
