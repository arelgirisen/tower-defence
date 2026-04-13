import json
import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pygame

pygame.init()

WIDTH, HEIGHT = 1280, 720
SIDEBAR_W = 320
TOPBAR_H = 78
MAP_W = WIDTH - SIDEBAR_W
FPS = 60

BG = (15, 19, 28)
BG2 = (24, 30, 44)
PANEL = (27, 33, 47)
PANEL_2 = (36, 43, 60)
PANEL_3 = (48, 58, 79)
GRID = (57, 68, 92)
PATH = (137, 108, 79)
TEXT = (238, 242, 250)
MUTED = (165, 175, 195)
GREEN = (92, 220, 132)
RED = (230, 95, 102)
BLUE = (88, 158, 245)
YELLOW = (244, 205, 95)
PURPLE = (171, 118, 255)
CYAN = (84, 226, 245)
ORANGE = (255, 164, 72)
TEAL = (69, 185, 165)
SHADOW = (7, 10, 16)
WHITE = (255, 255, 255)

SAVE_PATH = Path(__file__).with_name("savegame.json")
SETTINGS_PATH = Path(__file__).with_name("settings.json")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense Deluxe")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 21)
small_font = pygame.font.SysFont("arial", 16)
mini_font = pygame.font.SysFont("arial", 14)
big_font = pygame.font.SysFont("arial", 40, bold=True)
huge_font = pygame.font.SysFont("arial", 62, bold=True)

TILE = 58
OFFSET_X = 20
OFFSET_Y = TOPBAR_H + 18
COLS = (MAP_W - 40) // TILE
ROWS = (HEIGHT - OFFSET_Y - 18) // TILE

PATH_TILES = [
    (0, 4), (1, 4), (2, 4), (3, 4),
    (3, 3), (3, 2), (3, 1),
    (4, 1), (5, 1), (6, 1),
    (6, 2), (6, 3), (6, 4), (6, 5),
    (7, 5), (8, 5), (9, 5),
    (9, 4), (9, 3),
    (10, 3), (11, 3), (12, 3),
    (12, 4), (12, 5), (12, 6),
    (13, 6), (14, 6), (15, 6),
    (15, 5), (15, 4), (16, 4)
]
PATH_SET = set(PATH_TILES)
PATH_POINTS = [
    (OFFSET_X + c * TILE + TILE // 2, OFFSET_Y + r * TILE + TILE // 2)
    for c, r in PATH_TILES
]

LEVELS = [
    [("normal", 8, 40)],
    [("normal", 10, 34), ("fast", 6, 24)],
    [("normal", 10, 28), ("tank", 4, 48), ("fast", 10, 20)],
    [("fast", 18, 18), ("normal", 12, 24)],
    [("tank", 8, 40), ("normal", 12, 18), ("boss", 1, 0)],
    [("fast", 24, 14), ("normal", 14, 20), ("tank", 6, 34)],
    [("normal", 20, 18), ("tank", 10, 28), ("fast", 14, 15)],
    [("boss", 2, 24), ("fast", 16, 15), ("normal", 20, 18)],
    [("tank", 16, 18), ("fast", 22, 13), ("normal", 26, 13)],
    [("boss", 3, 26), ("tank", 18, 18), ("fast", 28, 12), ("normal", 30, 12)],
]

ENEMY_STATS = {
    "normal": {"hp": 56, "speed": 1.35, "reward": 12, "color": BLUE, "radius": 15},
    "fast": {"hp": 34, "speed": 2.15, "reward": 10, "color": YELLOW, "radius": 12},
    "tank": {"hp": 145, "speed": 0.90, "reward": 18, "color": PURPLE, "radius": 19},
    "boss": {"hp": 300, "speed": 1.05, "reward": 50, "color": RED, "radius": 24},
}

TOWER_TYPES = {
    "Blaster": {
        "cost": 70, "range": 130, "damage": 19, "cooldown": 30,
        "color": GREEN, "projectile_speed": 8, "upgrade_cost": 45,
        "accent": "Dengeli"
    },
    "Sniper": {
        "cost": 118, "range": 245, "damage": 46, "cooldown": 66,
        "color": CYAN, "projectile_speed": 11, "upgrade_cost": 70,
        "accent": "Uzak menzil"
    },
    "Rapid": {
        "cost": 96, "range": 110, "damage": 10, "cooldown": 11,
        "color": ORANGE, "projectile_speed": 9, "upgrade_cost": 55,
        "accent": "Hızlı ateş"
    },
}


@dataclass
class Enemy:
    kind: str
    hp: float
    max_hp: float
    speed: float
    reward: int
    color: tuple
    radius: int
    x: float
    y: float
    path_index: int = 0
    alive: bool = True

    @classmethod
    def create(cls, kind: str, level_scale: float):
        s = ENEMY_STATS[kind]
        hp = s["hp"] * level_scale
        x, y = PATH_POINTS[0]
        return cls(kind, hp, hp, s["speed"] * min(1.85, 1 + (level_scale - 1) * 0.08), s["reward"], s["color"], s["radius"], x, y)

    def update(self):
        if self.path_index >= len(PATH_POINTS) - 1:
            return True
        tx, ty = PATH_POINTS[self.path_index + 1]
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist <= self.speed:
            self.x, self.y = tx, ty
            self.path_index += 1
        elif dist > 0:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed
        return False

    def draw(self, surf):
        pos = (int(self.x), int(self.y))
        pygame.draw.circle(surf, (255, 255, 255), pos, self.radius + 2)
        pygame.draw.circle(surf, self.color, pos, self.radius)
        hp_ratio = max(0, self.hp / self.max_hp)
        bw = self.radius * 2 + 6
        bar_rect = pygame.Rect(self.x - bw / 2, self.y - self.radius - 18, bw, 7)
        pygame.draw.rect(surf, (60, 20, 24), bar_rect, border_radius=4)
        pygame.draw.rect(surf, GREEN, (bar_rect.x, bar_rect.y, bar_rect.w * hp_ratio, bar_rect.h), border_radius=4)

    def serialize(self):
        return {
            "kind": self.kind,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "speed": self.speed,
            "reward": self.reward,
            "color": list(self.color),
            "radius": self.radius,
            "x": self.x,
            "y": self.y,
            "path_index": self.path_index,
            "alive": self.alive,
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            data["kind"], data["hp"], data["max_hp"], data["speed"], data["reward"], tuple(data["color"]),
            data["radius"], data["x"], data["y"], data.get("path_index", 0), data.get("alive", True)
        )


@dataclass
class Projectile:
    x: float
    y: float
    target: Enemy
    damage: float
    speed: float
    color: tuple
    alive: bool = True

    def update(self):
        if not self.target.alive:
            self.alive = False
            return
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist <= self.speed + self.target.radius:
            self.target.hp -= self.damage
            if self.target.hp <= 0 and self.target.alive:
                self.target.alive = False
            self.alive = False
            return
        if dist > 0:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def draw(self, surf):
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 5)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 3)


class Tower:
    def __init__(self, grid_pos, tower_type):
        gx, gy = grid_pos
        self.grid_pos = grid_pos
        self.x = OFFSET_X + gx * TILE + TILE // 2
        self.y = OFFSET_Y + gy * TILE + TILE // 2
        self.type = tower_type
        base = TOWER_TYPES[tower_type]
        self.level = 1
        self.range = base["range"]
        self.damage = base["damage"]
        self.cooldown_max = base["cooldown"]
        self.cooldown = random.randint(0, max(1, self.cooldown_max // 2))
        self.color = base["color"]
        self.projectile_speed = base["projectile_speed"]
        self.upgrade_cost = base["upgrade_cost"]
        self.kills = 0

    def update(self, enemies, projectiles):
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        target = None
        farthest = -1
        lowest_hp = 1e9
        for enemy in enemies:
            if not enemy.alive:
                continue
            d = math.hypot(enemy.x - self.x, enemy.y - self.y)
            if d <= self.range:
                if enemy.path_index > farthest or (enemy.path_index == farthest and enemy.hp < lowest_hp):
                    farthest = enemy.path_index
                    lowest_hp = enemy.hp
                    target = enemy
        if target:
            projectiles.append(Projectile(self.x, self.y, target, self.damage, self.projectile_speed, self.color))
            self.cooldown = self.cooldown_max

    def upgrade(self):
        self.level += 1
        self.damage *= 1.34
        self.range += 12
        self.cooldown_max = max(6, int(self.cooldown_max * 0.9))
        self.projectile_speed += 0.8
        self.upgrade_cost = int(self.upgrade_cost * 1.45)

    def draw(self, surf, selected=False):
        if selected:
            pygame.draw.circle(surf, (*self.color,), (self.x, self.y), self.range, 1)
        pygame.draw.circle(surf, SHADOW, (self.x + 3, self.y + 4), 21)
        pygame.draw.circle(surf, self.color, (self.x, self.y), 20)
        pygame.draw.circle(surf, PANEL, (self.x, self.y), 9)
        pygame.draw.circle(surf, WHITE, (self.x - 6, self.y - 7), 4)
        lvl = mini_font.render(f"Lv{self.level}", True, TEXT)
        surf.blit(lvl, lvl.get_rect(center=(self.x, self.y - 30)))

    def serialize(self):
        return {
            "grid_pos": list(self.grid_pos),
            "type": self.type,
            "level": self.level,
            "range": self.range,
            "damage": self.damage,
            "cooldown_max": self.cooldown_max,
            "cooldown": self.cooldown,
            "projectile_speed": self.projectile_speed,
            "upgrade_cost": self.upgrade_cost,
            "kills": self.kills,
        }

    @classmethod
    def deserialize(cls, data):
        tower = cls(tuple(data["grid_pos"]), data["type"])
        tower.level = data["level"]
        tower.range = data["range"]
        tower.damage = data["damage"]
        tower.cooldown_max = data["cooldown_max"]
        tower.cooldown = data["cooldown"]
        tower.projectile_speed = data["projectile_speed"]
        tower.upgrade_cost = data["upgrade_cost"]
        tower.kills = data.get("kills", 0)
        return tower


class WaveManager:
    def __init__(self):
        self.level_index = 0
        self.queue = []
        self.spawn_gap = 0
        self.active = False
        self.total_this_wave = 0
        self.spawned_this_wave = 0

    def start_level(self):
        if self.level_index >= len(LEVELS):
            return False
        self.queue.clear()
        scale = 1 + self.level_index * 0.18
        self.total_this_wave = 0
        self.spawned_this_wave = 0
        for kind, count, gap in LEVELS[self.level_index]:
            self.total_this_wave += count
            for _ in range(count):
                self.queue.append((kind, scale, gap))
        self.active = True
        self.spawn_gap = 0
        return True

    def update(self, enemies):
        if not self.active:
            return False
        wave_completed = False
        if self.spawn_gap > 0:
            self.spawn_gap -= 1
            return False
        if self.queue:
            kind, scale, gap = self.queue.pop(0)
            enemies.append(Enemy.create(kind, scale))
            self.spawn_gap = gap
            self.spawned_this_wave += 1
        elif not enemies:
            self.active = False
            self.level_index += 1
            wave_completed = True
        return wave_completed

    def current_label(self):
        return min(self.level_index + 1, 10)

    def progress_ratio(self):
        if self.total_this_wave <= 0:
            return 0
        remaining = len(self.queue)
        done = self.total_this_wave - remaining
        return max(0, min(1, done / self.total_this_wave))

    def serialize(self):
        return {
            "level_index": self.level_index,
            "queue": self.queue,
            "spawn_gap": self.spawn_gap,
            "active": self.active,
            "total_this_wave": self.total_this_wave,
            "spawned_this_wave": self.spawned_this_wave,
        }

    @classmethod
    def deserialize(cls, data):
        wm = cls()
        wm.level_index = data["level_index"]
        wm.queue = [tuple(item) for item in data.get("queue", [])]
        wm.spawn_gap = data.get("spawn_gap", 0)
        wm.active = data.get("active", False)
        wm.total_this_wave = data.get("total_this_wave", 0)
        wm.spawned_this_wave = data.get("spawned_this_wave", 0)
        return wm


class Button:
    def __init__(self, rect, label, color, action=None, small=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.action = action
        self.small = small

    def draw(self, surf, mouse_pos):
        hover = self.rect.collidepoint(mouse_pos)
        shadow = self.rect.move(0, 4)
        pygame.draw.rect(surf, SHADOW, shadow, border_radius=16)
        fill = tuple(min(255, c + 18) for c in self.color) if hover else self.color
        pygame.draw.rect(surf, fill, self.rect, border_radius=16)
        pygame.draw.rect(surf, WHITE, self.rect, 2 if hover else 1, border_radius=16)
        use_font = font if not self.small else small_font
        label = use_font.render(self.label, True, TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


def safe_load_json(path, fallback):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return fallback


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class Game:
    def __init__(self):
        self.settings = safe_load_json(SETTINGS_PATH, {"show_grid": True, "auto_save": True})
        self.best_wave = 0
        self.total_wins = 0
        self.last_status = "Hoş geldin."
        self.scene = "menu"
        self.menu_buttons = []
        self.help_buttons = []
        self.settings_buttons = []
        self.pause_buttons = []
        self.end_buttons = []
        self.selected_tile = None
        self.selected_tower = None
        self.selected_type = "Blaster"
        self.hover_tile = None
        self.autosave_timer = 0
        self._build_static_buttons()
        self.reset_runtime(keep_meta=True)
        self.load_meta_only()

    def reset_runtime(self, keep_meta=False):
        if not keep_meta:
            self.best_wave = 0
            self.total_wins = 0
            self.last_status = "Yeni oyun hazır."
        self.gold = 260
        self.lives = 20
        self.towers = []
        self.enemies = []
        self.projectiles = []
        self.wave_manager = WaveManager()
        self.selected_tile = None
        self.selected_tower = None
        self.selected_type = "Blaster"
        self.game_over = False
        self.victory = False
        self.stats = {"enemies_defeated": 0, "gold_earned": 0, "shots_fired": 0}

    def _build_static_buttons(self):
        cx = WIDTH // 2 - 140
        self.menu_buttons = [
            Button((cx, 270, 280, 56), "Yeni Oyun", BLUE, "new_game"),
            Button((cx, 340, 280, 56), "Devam Et", TEAL, "continue"),
            Button((cx, 410, 280, 56), "Nasıl Oynanır", PURPLE, "help"),
            Button((cx, 480, 280, 56), "Ayarlar", ORANGE, "settings"),
            Button((cx, 550, 280, 56), "Çıkış", RED, "quit"),
        ]
        self.help_buttons = [Button((40, HEIGHT - 78, 200, 46), "Geri Dön", PANEL_3, "menu", small=True)]
        self.settings_buttons = [Button((40, HEIGHT - 78, 200, 46), "Menüye Dön", PANEL_3, "menu", small=True)]
        self.pause_buttons = [
            Button((WIDTH // 2 - 140, 290, 280, 56), "Oyuna Dön", TEAL, "resume"),
            Button((WIDTH // 2 - 140, 360, 280, 56), "Kaydet ve Menü", BLUE, "save_menu"),
            Button((WIDTH // 2 - 140, 430, 280, 56), "Yeni Oyun", ORANGE, "new_game"),
        ]
        self.end_buttons = [
            Button((WIDTH // 2 - 140, 430, 280, 56), "Ana Menü", BLUE, "menu"),
            Button((WIDTH // 2 - 140, 500, 280, 56), "Yeni Oyun", TEAL, "new_game"),
        ]

    def tower_at(self, grid_pos):
        for tower in self.towers:
            if tower.grid_pos == grid_pos:
                return tower
        return None

    def sell_value(self, tower):
        value = TOWER_TYPES[tower.type]["cost"]
        current_level = 1
        upgrade_cost = TOWER_TYPES[tower.type]["upgrade_cost"]
        while current_level < tower.level:
            value += upgrade_cost
            upgrade_cost = int(upgrade_cost * 1.45)
            current_level += 1
        return int(value * 0.65)

    def place_tower(self, grid_pos):
        if grid_pos in PATH_SET or self.tower_at(grid_pos):
            self.last_status = "Bu kareye kule koyamazsın."
            return False
        cfg = TOWER_TYPES[self.selected_type]
        if self.gold < cfg["cost"]:
            self.last_status = "Yeterli altın yok."
            return False
        self.gold -= cfg["cost"]
        tower = Tower(grid_pos, self.selected_type)
        self.towers.append(tower)
        self.selected_tower = tower
        self.selected_tile = grid_pos
        self.last_status = f"{self.selected_type} yerleştirildi."
        self.maybe_autosave(force=True)
        return True

    def start_wave(self):
        if self.wave_manager.active or self.wave_manager.level_index >= 10:
            return False
        started = self.wave_manager.start_level()
        if started:
            self.last_status = f"Bölüm {self.wave_manager.current_label()} başladı."
            self.maybe_autosave(force=True)
        return started

    def update(self):
        if self.scene != "play" or self.game_over or self.victory:
            return

        completed = self.wave_manager.update(self.enemies)
        if completed:
            bonus = 35 + self.wave_manager.level_index * 8
            self.gold += bonus
            self.stats["gold_earned"] += bonus
            self.best_wave = max(self.best_wave, self.wave_manager.level_index)
            self.last_status = f"Bölüm tamamlandı. Bonus +{bonus} altın."
            self.maybe_autosave(force=True)

        for tower in self.towers:
            before = len(self.projectiles)
            tower.update(self.enemies, self.projectiles)
            if len(self.projectiles) > before:
                self.stats["shots_fired"] += len(self.projectiles) - before

        for projectile in self.projectiles:
            projectile.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        remaining = []
        for enemy in self.enemies:
            was_alive = enemy.alive
            if not enemy.alive:
                self.gold += enemy.reward
                self.stats["gold_earned"] += enemy.reward
                self.stats["enemies_defeated"] += 1
                continue
            reached_end = enemy.update()
            if reached_end:
                self.lives -= 1 if enemy.kind != "boss" else 3
                self.last_status = "Bir düşman çıkışa ulaştı."
                continue
            if was_alive and not enemy.alive:
                self.stats["enemies_defeated"] += 1
            remaining.append(enemy)
        self.enemies = remaining

        if self.lives <= 0:
            self.game_over = True
            self.scene = "end"
            self.last_status = "Savunma çöktü."
            self.maybe_autosave(force=True, allow_delete=True)

        if self.wave_manager.level_index >= 10 and not self.wave_manager.active and not self.enemies:
            self.victory = True
            self.scene = "end"
            self.total_wins += 1
            self.best_wave = 10
            self.last_status = "Tüm 10 bölümü tamamladın."
            self.maybe_autosave(force=True, allow_delete=True)

        self.maybe_autosave()

    def maybe_autosave(self, force=False, allow_delete=False):
        if not self.settings.get("auto_save", True):
            return
        self.autosave_timer += 1
        if force or self.autosave_timer >= FPS * 5:
            self.autosave_timer = 0
            if allow_delete and (self.game_over or self.victory):
                self.delete_savegame()
            else:
                self.save_game()

    def save_game(self):
        data = {
            "gold": self.gold,
            "lives": self.lives,
            "selected_type": self.selected_type,
            "wave_manager": self.wave_manager.serialize(),
            "towers": [t.serialize() for t in self.towers],
            "enemies": [e.serialize() for e in self.enemies],
            "stats": self.stats,
            "last_status": self.last_status,
            "best_wave": self.best_wave,
            "total_wins": self.total_wins,
        }
        save_json(SAVE_PATH, data)
        self.save_meta_only()

    def save_meta_only(self):
        data = {
            "best_wave": self.best_wave,
            "total_wins": self.total_wins,
            "settings": self.settings,
        }
        save_json(SETTINGS_PATH, data)

    def load_meta_only(self):
        meta = safe_load_json(SETTINGS_PATH, {})
        self.best_wave = meta.get("best_wave", self.best_wave)
        self.total_wins = meta.get("total_wins", self.total_wins)
        if "settings" in meta and isinstance(meta["settings"], dict):
            self.settings.update(meta["settings"])

    def delete_savegame(self):
        try:
            if SAVE_PATH.exists():
                SAVE_PATH.unlink()
        except Exception:
            pass
        self.save_meta_only()

    def has_savegame(self):
        return SAVE_PATH.exists()

    def load_game(self):
        data = safe_load_json(SAVE_PATH, None)
        if not data:
            self.last_status = "Kayıt bulunamadı."
            return False
        self.reset_runtime(keep_meta=True)
        self.gold = data.get("gold", 260)
        self.lives = data.get("lives", 20)
        self.selected_type = data.get("selected_type", "Blaster")
        self.wave_manager = WaveManager.deserialize(data.get("wave_manager", {}))
        self.towers = [Tower.deserialize(t) for t in data.get("towers", [])]
        self.enemies = [Enemy.deserialize(e) for e in data.get("enemies", [])]
        self.stats = data.get("stats", self.stats)
        self.last_status = data.get("last_status", "Kayıt yüklendi.")
        self.best_wave = max(self.best_wave, data.get("best_wave", 0))
        self.total_wins = max(self.total_wins, data.get("total_wins", 0))
        self.scene = "play"
        self.game_over = False
        self.victory = False
        return True

    def new_game(self):
        self.reset_runtime(keep_meta=True)
        self.scene = "play"
        self.last_status = "Yeni oyun başladı."
        self.maybe_autosave(force=True)

    def toggle_setting(self, key):
        self.settings[key] = not self.settings.get(key, False)
        self.save_meta_only()

    def handle_action(self, action):
        if action == "new_game":
            self.new_game()
        elif action == "continue":
            if self.has_savegame():
                self.load_game()
            else:
                self.last_status = "Önce bir kayıt oluşturmalısın."
        elif action == "help":
            self.scene = "help"
        elif action == "settings":
            self.scene = "settings"
        elif action == "menu":
            self.scene = "menu"
            self.save_meta_only()
        elif action == "quit":
            self.save_game()
            self.save_meta_only()
            pygame.quit()
            sys.exit()
        elif action == "resume":
            self.scene = "play"
        elif action == "save_menu":
            self.save_game()
            self.scene = "menu"

    def handle_mouse_down(self, pos):
        if self.scene == "menu":
            for b in self.menu_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            return
        if self.scene == "help":
            for b in self.help_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            return
        if self.scene == "settings":
            for b in self.settings_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            grid_toggle = pygame.Rect(380, 220, 390, 54)
            autosave_toggle = pygame.Rect(380, 300, 390, 54)
            if grid_toggle.collidepoint(pos):
                self.toggle_setting("show_grid")
            if autosave_toggle.collidepoint(pos):
                self.toggle_setting("auto_save")
            return
        if self.scene == "end":
            for b in self.end_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            return

        if self.scene != "play":
            return

        button = self.sidebar_button_at(pos)
        if button:
            action, value = button
            if action == "select_type":
                self.selected_type = value
                self.last_status = f"{value} seçildi."
            elif action == "start":
                self.start_wave()
            elif action == "upgrade" and self.selected_tower:
                if self.gold >= self.selected_tower.upgrade_cost:
                    self.gold -= self.selected_tower.upgrade_cost
                    self.selected_tower.upgrade()
                    self.last_status = "Kule geliştirildi."
                    self.maybe_autosave(force=True)
                else:
                    self.last_status = "Yeterli altın yok."
            elif action == "sell" and self.selected_tower:
                self.gold += self.sell_value(self.selected_tower)
                self.towers.remove(self.selected_tower)
                self.selected_tower = None
                self.selected_tile = None
                self.last_status = "Kule satıldı."
                self.maybe_autosave(force=True)
            elif action == "save":
                self.save_game()
                self.last_status = "Oyun kaydedildi."
            elif action == "pause":
                self.scene = "pause"
            return

        tile = tile_from_mouse(pos)
        if tile:
            self.selected_tile = tile
            tower = self.tower_at(tile)
            self.selected_tower = tower
            if tower is None:
                self.place_tower(tile)

    def sidebar_button_at(self, pos):
        x, y = pos
        if x < MAP_W:
            return None
        tower_y = 200
        idx = (y - tower_y) // 82
        names = list(TOWER_TYPES.keys())
        if 0 <= idx < len(names):
            rect = pygame.Rect(MAP_W + 18, tower_y + idx * 82, SIDEBAR_W - 36, 66)
            if rect.collidepoint(pos):
                return ("select_type", names[idx])
        buttons = {
            "start": pygame.Rect(MAP_W + 20, HEIGHT - 160, 136, 46),
            "save": pygame.Rect(MAP_W + 164, HEIGHT - 160, 136, 46),
            "upgrade": pygame.Rect(MAP_W + 20, HEIGHT - 104, 136, 46),
            "sell": pygame.Rect(MAP_W + 164, HEIGHT - 104, 136, 46),
            "pause": pygame.Rect(MAP_W + 20, HEIGHT - 48, 280, 36),
        }
        for action, rect in buttons.items():
            if rect.collidepoint(pos):
                return (action, None)
        return None

    def handle_key_down(self, key):
        if key == pygame.K_ESCAPE:
            if self.scene == "play":
                self.scene = "pause"
            elif self.scene == "pause":
                self.scene = "play"
            elif self.scene in {"help", "settings", "end"}:
                self.scene = "menu"
            return

        if self.scene != "play":
            return

        if key == pygame.K_r:
            self.new_game()
        elif key == pygame.K_SPACE:
            self.start_wave()
        elif key == pygame.K_1:
            self.selected_type = "Blaster"
        elif key == pygame.K_2:
            self.selected_type = "Sniper"
        elif key == pygame.K_3:
            self.selected_type = "Rapid"
        elif key == pygame.K_s:
            self.save_game()
            self.last_status = "Oyun kaydedildi."

    def draw(self):
        if self.scene == "menu":
            self.draw_menu()
        elif self.scene == "help":
            self.draw_help()
        elif self.scene == "settings":
            self.draw_settings()
        else:
            self.draw_gameplay()
            if self.scene == "pause":
                self.draw_pause_overlay()
            elif self.scene == "end":
                self.draw_end_overlay()

    def draw_background(self):
        screen.fill(BG)
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = (
                int(BG[0] * (1 - ratio) + BG2[0] * ratio),
                int(BG[1] * (1 - ratio) + BG2[1] * ratio),
                int(BG[2] * (1 - ratio) + BG2[2] * ratio),
            )
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))
        for i in range(18):
            px = (i * 97 + 40) % WIDTH
            py = (i * 53 + 22) % HEIGHT
            pygame.draw.circle(screen, (255, 255, 255), (px, py), 1)

    def draw_card(self, rect, color=PANEL, border=PANEL_3, radius=18):
        shadow = pygame.Rect(rect.x, rect.y + 6, rect.w, rect.h)
        pygame.draw.rect(screen, SHADOW, shadow, border_radius=radius)
        pygame.draw.rect(screen, color, rect, border_radius=radius)
        pygame.draw.rect(screen, border, rect, 1, border_radius=radius)

    def draw_topbar(self):
        rect = pygame.Rect(16, 14, WIDTH - 32, TOPBAR_H - 12)
        self.draw_card(rect, color=PANEL, border=PANEL_3)
        title = big_font.render("Tower Defense Deluxe", True, TEXT)
        screen.blit(title, (34, 26))

        stats = [
            ("Bölüm", f"{min(self.wave_manager.current_label(), 10)}/10", BLUE),
            ("Can", str(self.lives), RED),
            ("Altın", str(self.gold), YELLOW),
            ("En İyi", str(self.best_wave), CYAN),
        ]
        x = 420
        for label, value, color in stats:
            card = pygame.Rect(x, 22, 105, 46)
            pygame.draw.rect(screen, PANEL_2, card, border_radius=14)
            pygame.draw.rect(screen, color, card, 2, border_radius=14)
            screen.blit(mini_font.render(label, True, MUTED), (card.x + 10, card.y + 7))
            screen.blit(font.render(value, True, TEXT), (card.x + 10, card.y + 22))
            x += 118

    def draw_map(self):
        area = pygame.Rect(16, TOPBAR_H + 10, MAP_W - 24, HEIGHT - TOPBAR_H - 24)
        self.draw_card(area, color=(20, 26, 37), border=PANEL_3)

        for row in range(ROWS):
            for col in range(COLS):
                rect = grid_to_rect(col, row)
                fill = (31, 39, 55)
                if (col, row) in PATH_SET:
                    fill = PATH
                pygame.draw.rect(screen, fill, rect, border_radius=8)
                if self.settings.get("show_grid", True):
                    pygame.draw.rect(screen, GRID, rect, 1, border_radius=8)

        start = PATH_POINTS[0]
        end = PATH_POINTS[-1]
        pygame.draw.circle(screen, GREEN, start, 16)
        pygame.draw.circle(screen, RED, end, 16)
        screen.blit(mini_font.render("Giriş", True, TEXT), (start[0] - 14, start[1] - 34))
        screen.blit(mini_font.render("Çıkış", True, TEXT), (end[0] - 14, end[1] - 34))

        if self.hover_tile:
            rect = grid_to_rect(*self.hover_tile)
            pygame.draw.rect(screen, WHITE, rect, 2, border_radius=8)
        if self.selected_tile:
            rect = grid_to_rect(*self.selected_tile)
            pygame.draw.rect(screen, CYAN, rect, 3, border_radius=8)

        for tower in self.towers:
            tower.draw(screen, selected=(self.selected_tower is tower))
        for enemy in self.enemies:
            enemy.draw(screen)
        for projectile in self.projectiles:
            projectile.draw(screen)

    def draw_sidebar(self):
        rect = pygame.Rect(MAP_W + 8, TOPBAR_H + 10, SIDEBAR_W - 16, HEIGHT - TOPBAR_H - 24)
        self.draw_card(rect)

        y = TOPBAR_H + 24
        screen.blit(font.render("Kontrol Paneli", True, TEXT), (MAP_W + 28, y))
        y += 34
        progress_back = pygame.Rect(MAP_W + 28, y, SIDEBAR_W - 56, 18)
        pygame.draw.rect(screen, PANEL_2, progress_back, border_radius=9)
        pygame.draw.rect(screen, BLUE, (progress_back.x, progress_back.y, progress_back.w * self.wave_manager.progress_ratio(), progress_back.h), border_radius=9)
        label = f"Aktif dalga" if self.wave_manager.active else "Hazır"
        screen.blit(mini_font.render(label, True, MUTED), (progress_back.x, progress_back.y - 16))
        y += 34

        alive_count = len([e for e in self.enemies if e.alive])
        info_lines = [
            f"Sahadaki düşman: {alive_count}",
            f"Toplam kule: {len(self.towers)}",
            f"Yok edilen düşman: {self.stats['enemies_defeated']}",
            f"Kazanılan altın: {self.stats['gold_earned']}",
        ]
        for line in info_lines:
            screen.blit(small_font.render(line, True, TEXT), (MAP_W + 28, y))
            y += 24

        y += 10
        screen.blit(font.render("Kuleler", True, TEXT), (MAP_W + 28, y))
        y += 14
        mouse_pos = pygame.mouse.get_pos()
        for idx, (name, cfg) in enumerate(TOWER_TYPES.items()):
            card = pygame.Rect(MAP_W + 20, y + idx * 82, SIDEBAR_W - 40, 66)
            hover = card.collidepoint(mouse_pos)
            base_color = PANEL_2 if not hover else PANEL_3
            pygame.draw.rect(screen, base_color, card, border_radius=16)
            if self.selected_type == name:
                pygame.draw.rect(screen, cfg["color"], card, 3, border_radius=16)
            pygame.draw.circle(screen, cfg["color"], (card.x + 28, card.y + 33), 15)
            screen.blit(font.render(name, True, TEXT), (card.x + 52, card.y + 10))
            detail = f"{cfg['accent']}  |  {cfg['cost']} altın"
            screen.blit(mini_font.render(detail, True, MUTED), (card.x + 52, card.y + 36))

        y = HEIGHT - 178
        button_specs = [
            (pygame.Rect(MAP_W + 20, y, 136, 46), "Başlat", BLUE),
            (pygame.Rect(MAP_W + 164, y, 136, 46), "Kaydet", TEAL),
            (pygame.Rect(MAP_W + 20, y + 56, 136, 46), "Geliştir", PURPLE),
            (pygame.Rect(MAP_W + 164, y + 56, 136, 46), "Sat", ORANGE),
            (pygame.Rect(MAP_W + 20, y + 112, 280, 36), "Menü / Duraklat", PANEL_3),
        ]
        for rect_btn, label_btn, color in button_specs:
            btn = Button(rect_btn, label_btn, color, small=True)
            btn.draw(screen, mouse_pos)

        detail_rect = pygame.Rect(MAP_W + 20, HEIGHT - 290, 280, 92)
        pygame.draw.rect(screen, PANEL_2, detail_rect, border_radius=16)
        if self.selected_tower:
            tower = self.selected_tower
            screen.blit(font.render(f"{tower.type}  Lv{tower.level}", True, TEXT), (detail_rect.x + 12, detail_rect.y + 10))
            stats = f"Hasar {int(tower.damage)} | Menzil {int(tower.range)}"
            screen.blit(mini_font.render(stats, True, MUTED), (detail_rect.x + 12, detail_rect.y + 38))
            stats2 = f"Upgrade {tower.upgrade_cost} | Sell {self.sell_value(tower)}"
            screen.blit(mini_font.render(stats2, True, MUTED), (detail_rect.x + 12, detail_rect.y + 60))
        else:
            screen.blit(font.render("Seçili kule yok", True, TEXT), (detail_rect.x + 12, detail_rect.y + 16))
            screen.blit(mini_font.render("Haritada boş kareye tıklayıp kule kur.", True, MUTED), (detail_rect.x + 12, detail_rect.y + 48))

    def draw_statusbar(self):
        rect = pygame.Rect(18, HEIGHT - 42, MAP_W - 28, 28)
        pygame.draw.rect(screen, PANEL, rect, border_radius=14)
        text = small_font.render(self.last_status, True, TEXT)
        screen.blit(text, (rect.x + 12, rect.y + 6))

    def draw_gameplay(self):
        self.draw_background()
        self.draw_topbar()
        self.draw_map()
        self.draw_sidebar()
        self.draw_statusbar()

    def draw_menu(self):
        self.draw_background()
        title = huge_font.render("Tower Defense Deluxe", True, TEXT)
        subtitle = font.render("10 bölümlü savunma oyunu", True, MUTED)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
        screen.blit(subtitle, subtitle.get_rect(center=(WIDTH // 2, 205)))

        info_card = pygame.Rect(WIDTH // 2 - 280, 70, 560, 165)
        self.draw_card(info_card, color=PANEL)
        lines = [
            f"En iyi ulaşılan bölüm: {self.best_wave}/10",
            f"Toplam galibiyet: {self.total_wins}",
            "Kayıt dosyası otomatik oluşur. Devam Et ile geri dönebilirsin." if self.has_savegame() else "Henüz kayıt yok. Yeni Oyun ile başlayabilirsin.",
        ]
        for i, line in enumerate(lines):
            screen.blit(font.render(line, True, TEXT if i < 2 else MUTED), (info_card.x + 22, info_card.y + 28 + i * 36))

        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            if button.action == "continue" and not self.has_savegame():
                disabled = Button(button.rect, button.label, PANEL_3, button.action)
                disabled.draw(screen, (-999, -999))
                text = small_font.render("Kayıt bulunamadı", True, MUTED)
                screen.blit(text, (button.rect.x + 78, button.rect.y + 62))
            else:
                button.draw(screen, mouse_pos)

    def draw_help(self):
        self.draw_background()
        card = pygame.Rect(40, 50, WIDTH - 80, HEIGHT - 120)
        self.draw_card(card)
        screen.blit(big_font.render("Nasıl Oynanır", True, TEXT), (64, 72))
        lines = [
            "• Boş kareye tıkla: seçili kuleyi yerleştir.",
            "• 1 / 2 / 3: kule türü değiştir.",
            "• SPACE veya Başlat: sıradaki bölümü başlat.",
            "• Sağ panelden kule geliştir veya sat.",
            "• S tuşu ya da Kaydet düğmesi: anlık kayıt al.",
            "• ESC: duraklat veya menüye dön.",
            "• Amaç: 10 bölümün hepsini tamamlamak.",
        ]
        y = 140
        for line in lines:
            screen.blit(font.render(line, True, TEXT), (72, y))
            y += 46
        hint = "İpucu: Sniper bosslara karşı, Rapid hızlı düşmanlara karşı güçlüdür."
        screen.blit(font.render(hint, True, CYAN), (72, y + 20))
        for b in self.help_buttons:
            b.draw(screen, pygame.mouse.get_pos())

    def draw_settings(self):
        self.draw_background()
        card = pygame.Rect(280, 90, 720, 430)
        self.draw_card(card)
        screen.blit(big_font.render("Ayarlar", True, TEXT), (320, 120))

        options = [
            (pygame.Rect(380, 220, 390, 54), "Grid göster", self.settings.get("show_grid", True)),
            (pygame.Rect(380, 300, 390, 54), "Otomatik kayıt", self.settings.get("auto_save", True)),
        ]
        mouse_pos = pygame.mouse.get_pos()
        for rect, label, state in options:
            pygame.draw.rect(screen, PANEL_2, rect, border_radius=16)
            pygame.draw.rect(screen, CYAN if state else PANEL_3, rect, 2, border_radius=16)
            screen.blit(font.render(label, True, TEXT), (rect.x + 18, rect.y + 14))
            pill = pygame.Rect(rect.right - 92, rect.y + 10, 70, 34)
            pygame.draw.rect(screen, GREEN if state else RED, pill, border_radius=17)
            screen.blit(small_font.render("Açık" if state else "Kapalı", True, TEXT), (pill.x + 12, pill.y + 8))
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, WHITE, rect, 1, border_radius=16)
        screen.blit(small_font.render("Değişiklikler otomatik kaydedilir.", True, MUTED), (382, 382))
        for b in self.settings_buttons:
            b.draw(screen, mouse_pos)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 180))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 190, 200, 380, 320)
        self.draw_card(panel, color=PANEL_2)
        screen.blit(big_font.render("Duraklatıldı", True, TEXT), (WIDTH // 2 - 120, 230))
        mouse_pos = pygame.mouse.get_pos()
        for b in self.pause_buttons:
            b.draw(screen, mouse_pos)

    def draw_end_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((8, 10, 16, 190))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 230, 170, 460, 420)
        self.draw_card(panel, color=PANEL_2)
        title = "Kazandın" if self.victory else "Kaybettin"
        color = GREEN if self.victory else RED
        screen.blit(big_font.render(title, True, color), (WIDTH // 2 - 80, 210))
        lines = [
            f"Ulaşılan bölüm: {self.best_wave}/10",
            f"Yok edilen düşman: {self.stats['enemies_defeated']}",
            f"Kazanılan altın: {self.stats['gold_earned']}",
        ]
        y = 292
        for line in lines:
            screen.blit(font.render(line, True, TEXT), (WIDTH // 2 - 120, y))
            y += 42
        mouse_pos = pygame.mouse.get_pos()
        for b in self.end_buttons:
            b.draw(screen, mouse_pos)


def grid_to_rect(col, row):
    return pygame.Rect(OFFSET_X + col * TILE, OFFSET_Y + row * TILE, TILE - 4, TILE - 4)


def tile_from_mouse(pos):
    x, y = pos
    if x >= MAP_W or x < OFFSET_X or y < OFFSET_Y:
        return None
    col = (x - OFFSET_X) // TILE
    row = (y - OFFSET_Y) // TILE
    if 0 <= col < COLS and 0 <= row < ROWS:
        return int(col), int(row)
    return None


def main():
    game = Game()

    while True:
        clock.tick(FPS)
        game.hover_tile = tile_from_mouse(pygame.mouse.get_pos()) if game.scene == "play" else None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if game.scene in {"play", "pause"}:
                    game.save_game()
                else:
                    game.save_meta_only()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                game.handle_key_down(event.key)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game.handle_mouse_down(event.pos)

        game.update()
        game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
