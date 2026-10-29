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
    "Afterburner": {"cost": 170, "power": "Mobility", "description": "Move farther per tap"},
    "Phase Drive": {"cost": 230, "power": "Mobility", "description": "Mobility set ability"},
    "Rocket Pod": {"cost": 260, "power": "Ordnance", "description": "Low damage rockets with splash"},
    "Blast Capacitor": {"cost": 190, "power": "Ordnance", "description": "Widen rocket splash"},
    "Extra Life": {"cost": 120, "power": "Survival", "description": "Add one life", "repeatable": True},
}
POWER_SETS = {
    "Assault": ("Rapid Fire", "Twin Cannons"),
    "Laser": ("Piercing Laser", "Prism Beam"),
    "Defense": ("Aegis Shield", "Repair Kit"),
    "Arcane": ("Nova Core", "Pulse Core"),
    "Mobility": ("Afterburner", "Phase Drive"),
    "Ordnance": ("Rocket Pod", "Blast Capacitor"),
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
        self.ability_ready_at = {name: 0.0 for name in POWER_SETS}
        self.ability_menu_open = False
        self.ability_selection = 0
        self.ability_until = 0.0
        self.ability_ready = False
        self.shield_charges = 1 if self.owned("Aegis Shield") else 0
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
        self.shield_charges = 1 if self.owned("Aegis Shield") else 0
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
        cooldown = self.shot_cooldown()
        if now - self.last_shot < cooldown:
            return
        self.last_shot = now
        laser = self.owned("Piercing Laser")
        bullet_type = "rocket" if self.owned("Rocket Pod") else ("laser" if laser else ("nova" if self.owned("Nova Core") else "bolt"))
        offsets = (-1, 1) if self.owned("Twin Cannons") else (0,)
        for offset in offsets:
            self.bullets.append({"y": self.player_y - 1, "x": self.player_x + offset, "type": bullet_type, "pierce": laser and bullet_type != "rocket"})

    def shot_cooldown(self):
        if self.owned("Rocket Pod"):
            return 1.5
        return .12 if self.owned("Rapid Fire") else .27

    def available_abilities(self):
        items = self.player_data.get("items", {})
        return [name for name, members in POWER_SETS.items() if all(items.get(member) for member in members)]

    def activate_set_ability(self, name):
        now = time.monotonic()
        if now < self.ability_ready_at[name]:
            self.message = f"{name} reload: {self.ability_ready_at[name] - now:.1f}s"
            self.message_until = now + 2
            return

        if name == "Defense":
            self.lives += 1
            self.invulnerable_until = now + 2
        elif name == "Arcane":
            first_row = min((enemy["y"] for enemy in self.alive_enemies()), default=None)
            for enemy in self.alive_enemies():
                if enemy["y"] == first_row:
                    enemy["hp"] -= 1
                    if enemy["hp"] <= 0:
                        enemy["alive"] = False
                        self._reward(enemy)
        elif name == "Laser":
            target_row = max((enemy["y"] for enemy in self.alive_enemies()), default=None)
            for enemy in self.alive_enemies():
                if enemy["y"] == target_row:
                    enemy["hp"] -= 3
                    if enemy["hp"] <= 0:
                        enemy["alive"] = False
                        self._reward(enemy)
        elif name == "Mobility":
            self.invulnerable_until = now + 3
        elif name in ("Ordnance", "Assault"):
            limit, damage = (3, 2) if name == "Ordnance" else (4, 2)
            targets = sorted(self.alive_enemies(), key=lambda enemy: enemy["y"], reverse=True)[:limit]
            for enemy in targets:
                enemy["hp"] -= damage
                if enemy["hp"] <= 0:
                    enemy["alive"] = False
                    self._reward(enemy)
        self.ability_ready_at[name] = now + 12
        self.message = f"{name} ability activated! Reload: 12s."
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
        if self.ability_menu_open:
            abilities = self.available_abilities()
            if key in (curses.KEY_LEFT, curses.KEY_UP, ord("a"), ord("A")):
                self.ability_selection = (self.ability_selection - 1) % len(abilities)
            elif key in (curses.KEY_RIGHT, curses.KEY_DOWN, ord("d"), ord("D")):
                self.ability_selection = (self.ability_selection + 1) % len(abilities)
            elif key in (10, 13, ord("t"), ord("T")):
                self.activate_set_ability(abilities[self.ability_selection])
                self.ability_menu_open = False
            elif key == 27:
                self.ability_menu_open = False
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
            self.player_x = max(2, self.player_x - (3 if self.owned("Afterburner") else 2))
        elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
            self.player_x = min(width - 3, self.player_x + (3 if self.owned("Afterburner") else 2))
        elif key in (ord(" "), ord("w"), ord("W"), curses.KEY_UP):
            self._shoot()
        elif key in (ord("t"), ord("T")):
            abilities = self.available_abilities()
            if len(abilities) == 1:
                self.activate_set_ability(abilities[0])
            elif abilities:
                self.ability_menu_open = True
                self.ability_selection = 0
            else:
                self.message = "Complete a matching item pair to unlock an ability."
                self.message_until = time.monotonic() + 2.5

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
                damage = 1 if bullet["type"] == "rocket" else (2 if bullet["type"] in ("laser", "nova") else 1)
                enemy["hp"] -= damage
                if enemy["hp"] <= 0:
                    enemy["alive"] = False
                    self._reward(enemy)
                if not bullet["pierce"]:
                    break
            if bullet["type"] == "rocket" and hits:
                radius = 3 if self.owned("Blast Capacitor") else 2
                direct_hits = {id(enemy) for enemy in hits}
                for enemy in self.alive_enemies():
                    if id(enemy) not in direct_hits and abs(enemy["x"] - bullet["x"]) <= radius and abs(enemy["y"] - bullet["y"]) <= 1:
                        enemy["hp"] -= 1
                        if enemy["hp"] <= 0:
                            enemy["alive"] = False
                            self._reward(enemy)
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
                if self.shield_charges:
                    self.shield_charges -= 1
                else:
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
        now = time.monotonic()
        reload_hud = []
        if self.owned("Rocket Pod"):
            reload_hud.append(f"Rocket {max(0.0, self.last_shot + self.shot_cooldown() - now):.1f}s")
        for ability in self.available_abilities():
            remaining = max(0.0, self.ability_ready_at[ability] - now)
            if remaining > 0:
                reload_hud.append(f"{ability} {remaining:.0f}s")
        if self.shield_charges:
            reload_hud.append(f"Shield x{self.shield_charges}")
        if reload_hud:
            safe_addstr(screen, 1, 2, "Reloads: " + " | ".join(reload_hud), curses.A_DIM)
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
                glyph, color = {"bolt": ("|", 4), "laser": ("║", 5), "nova": ("*", 6), "rocket": ("R", 2)}[bullet["type"]]
                safe_addstr(screen, bullet["y"], bullet["x"], glyph, curses.color_pair(color) | curses.A_BOLD)
            for bullet in self.enemy_bullets:
                safe_addstr(screen, bullet["y"], bullet["x"], "v", curses.color_pair(2) | curses.A_BOLD)
        if self.shop_open:
            safe_addstr(screen, 2, 3, "ARMORY  |  ←/→ select   B buy   S save   N continue", curses.A_BOLD | curses.color_pair(4))
            names = list(ITEMS)
            visible_count = min(4, max(1, (height - 8) // 2))
            start = max(0, min(self.shop_selection - visible_count // 2, len(names) - visible_count))
            visible = names[start:start + visible_count]
            for i, name in enumerate(visible):
                item = ITEMS[name]
                y = 4 + i * 2
                selected = name == names[self.shop_selection]
                owned = self.owned(name)
                locked = not owned and self.money < item["cost"]
                status = "OWNED" if owned else ("LOCKED" if locked else f"{item['cost']} cr")
                color = 2 if locked else (3 if owned else (4 if selected else 0))
                safe_addstr(screen, y, 4, ("> " if selected else "  ") + name, curses.color_pair(color) | (curses.A_BOLD if selected else 0))
                safe_addstr(screen, y, min(cols - 20, 26), f"{status}  |  {item['power']}", curses.color_pair(color))
                safe_addstr(screen, y + 1, 7, item["description"])
            sets = self.available_abilities()
            hint = f"T abilities ready: {', '.join(sets)}" if sets else "Abilities unlock when you collect a matching item pair."
            safe_addstr(screen, height - 3, 3, hint, curses.A_DIM)
            safe_addstr(screen, height - 2, 3, "Arrows select | B buy | S save | N continue", curses.A_BOLD)
        elif time.monotonic() < self.message_until:
            safe_addstr(screen, height - 1, 2, self.message[:cols - 4], curses.A_BOLD)
        else:
            safe_addstr(screen, height - 1, 2, "Move: ←/→ or A/D    Fire: Space    Set ability: T", curses.A_DIM)
        if self.ability_menu_open:
            abilities = self.available_abilities()
            top = max(2, height // 2 - len(abilities) // 2 - 1)
            safe_addstr(screen, top, 4, "CHOOSE AN ABILITY | arrows select, Enter activate, Esc cancel", curses.A_BOLD | curses.color_pair(4))
            for index, ability in enumerate(abilities):
                remaining = max(0.0, self.ability_ready_at[ability] - now)
                state = "READY" if remaining <= 0 else f"RELOAD {remaining:.1f}s"
                prefix = "> " if index == self.ability_selection else "  "
                attr = curses.A_BOLD if index == self.ability_selection else 0
                safe_addstr(screen, top + 1 + index, 6, f"{prefix}{ability} [{state}]", attr)
        if self.game_over:
            safe_addstr(screen, height // 2, max(1, (cols - 12) // 2), "GAME OVER", curses.color_pair(2) | curses.A_BOLD)
            safe_addstr(screen, height // 2 + 1, max(1, (cols - 27) // 2), "Press R to restart, Q to exit")
        screen.refresh()
