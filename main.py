import json
import math
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import pygame

pygame.init()

# ---------- Temel ayarlar ----------
WIDTH, HEIGHT = 1280, 760
SIDEBAR_W = 332
TOPBAR_H = 86
MAP_W = WIDTH - SIDEBAR_W
FPS = 60

# ---------- Renk paleti ----------
BG_DEEP = (8, 11, 22)
BG_MID = (18, 23, 42)
BG_TOP = (30, 38, 66)
PANEL = (24, 30, 48)
PANEL_2 = (34, 42, 66)
PANEL_3 = (52, 64, 94)
PANEL_HI = (74, 92, 132)
GRID_DIM = (42, 54, 82)
GRID_BRIGHT = (74, 90, 128)
GRASS_A = (30, 52, 46)
GRASS_B = (44, 72, 62)
PATH_A = (150, 118, 82)
PATH_B = (184, 150, 104)
PATH_EDGE = (86, 62, 40)
TEXT = (240, 244, 252)
MUTED = (158, 172, 198)
DIM = (108, 120, 148)
GREEN = (96, 228, 138)
GREEN_DK = (38, 138, 78)
RED = (242, 96, 104)
RED_DK = (158, 42, 52)
BLUE = (92, 168, 250)
BLUE_DK = (38, 90, 170)
YELLOW = (248, 210, 100)
GOLD = (255, 206, 84)
PURPLE = (180, 128, 255)
PURPLE_DK = (92, 58, 162)
CYAN = (90, 232, 248)
CYAN_DK = (30, 130, 158)
ORANGE = (255, 168, 78)
ORANGE_DK = (178, 94, 32)
TEAL = (72, 196, 176)
SHADOW = (4, 6, 12)
WHITE = (255, 255, 255)
CRIMSON = (212, 62, 88)

SAVE_PATH = Path(__file__).with_name("savegame.json")
SETTINGS_PATH = Path(__file__).with_name("settings.json")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense Deluxe")
clock = pygame.time.Clock()
FONT = pygame.font.SysFont("arial", 21)
SMALL = pygame.font.SysFont("arial", 15)
MINI = pygame.font.SysFont("arial", 13)
MED = pygame.font.SysFont("arial", 18, bold=True)
BIG = pygame.font.SysFont("arial", 38, bold=True)
HUGE = pygame.font.SysFont("arial", 64, bold=True)

TILE = 58
OFFSET_X = 22
OFFSET_Y = TOPBAR_H + 22
COLS = (MAP_W - 44) // TILE
ROWS = (HEIGHT - OFFSET_Y - 24) // TILE

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
    (15, 5), (15, 4), (16, 4),
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
    "normal": {"hp": 56, "speed": 1.35, "reward": 12, "color": BLUE, "radius": 15, "label": "Asker"},
    "fast":   {"hp": 34, "speed": 2.15, "reward": 10, "color": YELLOW, "radius": 12, "label": "Koşucu"},
    "tank":   {"hp": 145, "speed": 0.90, "reward": 18, "color": PURPLE, "radius": 19, "label": "Tank"},
    "boss":   {"hp": 300, "speed": 1.05, "reward": 50, "color": RED, "radius": 24, "label": "Boss"},
}

TOWER_TYPES = {
    "Blaster": {
        "cost": 70, "range": 130, "damage": 19, "cooldown": 30,
        "color": GREEN, "dark": GREEN_DK, "projectile_speed": 8,
        "upgrade_cost": 45, "accent": "Dengeli", "desc": "Çok yönlü savunma",
    },
    "Sniper": {
        "cost": 118, "range": 245, "damage": 46, "cooldown": 66,
        "color": CYAN, "dark": CYAN_DK, "projectile_speed": 11,
        "upgrade_cost": 70, "accent": "Uzak menzil", "desc": "Bosslara güçlü",
    },
    "Rapid": {
        "cost": 96, "range": 110, "damage": 10, "cooldown": 11,
        "color": ORANGE, "dark": ORANGE_DK, "projectile_speed": 9,
        "upgrade_cost": 55, "accent": "Hızlı ateş", "desc": "Hızlı düşmanlara",
    },
}

# ---------- Yardımcılar ----------
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

_glow_cache = {}

def make_glow(radius: int, color: tuple, intensity: float = 1.0) -> pygame.Surface:
    key = (radius, color, round(intensity, 2))
    if key in _glow_cache:
        return _glow_cache[key]
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    steps = 16
    for i in range(steps, 0, -1):
        r = int(radius * (i / steps))
        alpha = int(255 * (i / steps) ** 2.2 * 0.38 * intensity)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    _glow_cache[key] = surf
    return surf

def draw_glow(surf, pos, radius, color, intensity=1.0):
    g = make_glow(radius, color, intensity)
    surf.blit(g, (pos[0] - radius, pos[1] - radius), special_flags=pygame.BLEND_PREMULTIPLIED if False else 0)

def rounded_gradient_rect(surf, rect, c_top, c_bot, radius=16, border=None):
    grad = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for y in range(rect.h):
        t = y / max(1, rect.h - 1)
        c = lerp_color(c_top, c_bot, t)
        pygame.draw.line(grad, c, (0, y), (rect.w, y))
    mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(grad, rect.topleft)
    if border is not None:
        pygame.draw.rect(surf, border, rect, 1, border_radius=radius)

def shadow_rect(surf, rect, radius=16, offset=5, alpha=120):
    sh = pygame.Surface((rect.w + 12, rect.h + 12), pygame.SRCALPHA)
    pygame.draw.rect(sh, (0, 0, 0, alpha), sh.get_rect().inflate(-6, -6).move(0, offset), border_radius=radius)
    surf.blit(sh, (rect.x - 6, rect.y - 6))

def draw_polygon_filled(surf, color, points, glow_color=None):
    pygame.draw.polygon(surf, color, points)
    if glow_color is not None:
        pygame.draw.polygon(surf, glow_color, points, 2)

def tile_rect(col, row):
    return pygame.Rect(OFFSET_X + col * TILE, OFFSET_Y + row * TILE, TILE - 4, TILE - 4)

def tile_from_mouse(pos):
    x, y = pos
    if x >= MAP_W - 8 or x < OFFSET_X or y < OFFSET_Y:
        return None
    col = (x - OFFSET_X) // TILE
    row = (y - OFFSET_Y) // TILE
    if 0 <= col < COLS and 0 <= row < ROWS:
        return int(col), int(row)
    return None

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

# ---------- Parçacıklar ----------
@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple
    size: float
    gravity: float = 0.0
    fade: bool = True
    shape: str = "circle"  # circle / spark / ring

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.vy *= 0.94
        self.vy += self.gravity
        self.life -= 1

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        t = max(0.0, self.life / self.max_life)
        alpha = int(255 * t) if self.fade else 255
        if self.shape == "ring":
            r = int(self.size * (1.6 - t))
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r + 2, r + 2), r, 2)
            surf.blit(s, (self.x - r - 2, self.y - r - 2))
        elif self.shape == "spark":
            r = max(1, int(self.size * t))
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r + 1, r + 1), r)
            surf.blit(s, (self.x - r - 1, self.y - r - 1))
        else:
            r = max(1, int(self.size * t))
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (r + 1, r + 1), r)
            surf.blit(s, (self.x - r - 1, self.y - r - 1))

@dataclass
class FloatingText:
    x: float
    y: float
    text: str
    color: tuple
    life: int = 48
    max_life: int = 48
    vy: float = -0.9

    def update(self):
        self.y += self.vy
        self.vy *= 0.96
        self.life -= 1

    def alive(self):
        return self.life > 0

    def draw(self, surf):
        t = self.life / self.max_life
        alpha = int(255 * clamp(t * 1.4, 0, 1))
        label = SMALL.render(self.text, True, self.color)
        label.set_alpha(alpha)
        surf.blit(label, (self.x - label.get_width() // 2, self.y))

# ---------- Düşman ----------
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
    wobble: float = 0.0
    hit_flash: int = 0

    @classmethod
    def create(cls, kind: str, level_scale: float):
        s = ENEMY_STATS[kind]
        hp = s["hp"] * level_scale
        x, y = PATH_POINTS[0]
        spd = s["speed"] * min(1.85, 1 + (level_scale - 1) * 0.08)
        return cls(kind, hp, hp, spd, s["reward"], s["color"], s["radius"], x, y)

    def update(self):
        self.wobble += 0.15
        if self.hit_flash > 0:
            self.hit_flash -= 1
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

    def heading(self):
        if self.path_index >= len(PATH_POINTS) - 1:
            return 0.0
        tx, ty = PATH_POINTS[self.path_index + 1]
        return math.atan2(ty - self.y, tx - self.x)

    def draw(self, surf, t_frame):
        x, y = int(self.x), int(self.y)
        # gölge
        sh = pygame.Surface((self.radius * 3, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 110), sh.get_rect())
        surf.blit(sh, (x - self.radius * 3 // 2, y + self.radius - 4))
        # glow
        draw_glow(surf, (x, y), self.radius + 12, self.color, 0.9)
        ang = self.heading()
        c = self.color
        hi = lerp_color(c, WHITE, 0.35)
        dk = lerp_color(c, BG_DEEP, 0.55)
        flash = self.hit_flash > 0
        fill = WHITE if flash else c
        edge = WHITE if flash else hi

        if self.kind == "normal":
            # Hexagon asker
            r = self.radius + math.sin(self.wobble) * 0.8
            pts = [(x + math.cos(ang + i * math.pi / 3) * r,
                    y + math.sin(ang + i * math.pi / 3) * r) for i in range(6)]
            pygame.draw.polygon(surf, dk, pts)
            inner = [(x + math.cos(ang + i * math.pi / 3) * r * 0.65,
                      y + math.sin(ang + i * math.pi / 3) * r * 0.65) for i in range(6)]
            pygame.draw.polygon(surf, fill, inner)
            pygame.draw.polygon(surf, edge, pts, 2)
            # göz
            ex = x + math.cos(ang) * 5
            ey = y + math.sin(ang) * 5
            pygame.draw.circle(surf, WHITE, (int(ex), int(ey)), 3)
            pygame.draw.circle(surf, BG_DEEP, (int(ex), int(ey)), 1)
        elif self.kind == "fast":
            # Elmas
            r = self.radius
            pts = [
                (x + math.cos(ang) * r * 1.4, y + math.sin(ang) * r * 1.4),
                (x + math.cos(ang + math.pi / 2) * r * 0.7, y + math.sin(ang + math.pi / 2) * r * 0.7),
                (x - math.cos(ang) * r * 0.9, y - math.sin(ang) * r * 0.9),
                (x + math.cos(ang - math.pi / 2) * r * 0.7, y + math.sin(ang - math.pi / 2) * r * 0.7),
            ]
            pygame.draw.polygon(surf, dk, pts)
            pygame.draw.polygon(surf, fill, [(lerp(p[0], x, 0.35), lerp(p[1], y, 0.35)) for p in pts])
            pygame.draw.polygon(surf, edge, pts, 2)
            # iz
            for i in range(3):
                tx = x - math.cos(ang) * (r + 5 + i * 6)
                ty = y - math.sin(ang) * (r + 5 + i * 6)
                s = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(s, (*c, 90 - i * 28), (7, 7), 5 - i)
                surf.blit(s, (tx - 7, ty - 7))
        elif self.kind == "tank":
            # Zırhlı kare
            r = self.radius
            pts = []
            for i in range(4):
                a = ang + math.pi / 4 + i * math.pi / 2
                pts.append((x + math.cos(a) * r * 1.15, y + math.sin(a) * r * 1.15))
            pygame.draw.polygon(surf, dk, pts)
            pygame.draw.polygon(surf, fill, [(lerp(p[0], x, 0.25), lerp(p[1], y, 0.25)) for p in pts])
            pygame.draw.polygon(surf, edge, pts, 2)
            # zırh çivileri
            for i in range(4):
                a = ang + i * math.pi / 2
                sx = x + math.cos(a) * r * 0.6
                sy = y + math.sin(a) * r * 0.6
                pygame.draw.circle(surf, edge, (int(sx), int(sy)), 2)
            # top namlusu
            bx = x + math.cos(ang) * r * 1.4
            by = y + math.sin(ang) * r * 1.4
            pygame.draw.line(surf, edge, (x, y), (bx, by), 4)
        elif self.kind == "boss":
            # Boss: pulsing demon
            r = self.radius + math.sin(t_frame * 0.08) * 2.5
            # dış aura
            draw_glow(surf, (x, y), int(r + 18), RED, 1.2)
            # çokgen aura
            pts = []
            for i in range(8):
                a = ang + i * math.pi / 4 + t_frame * 0.02
                rr = r + (4 if i % 2 == 0 else 8)
                pts.append((x + math.cos(a) * rr, y + math.sin(a) * rr))
            pygame.draw.polygon(surf, dk, pts)
            pygame.draw.polygon(surf, fill, [(lerp(p[0], x, 0.4), lerp(p[1], y, 0.4)) for p in pts])
            pygame.draw.polygon(surf, WHITE, pts, 2)
            # core
            pygame.draw.circle(surf, WHITE, (x, y), 5)
            pygame.draw.circle(surf, RED_DK, (x, y), 3)

        # HP bar
        hp_ratio = max(0, self.hp / self.max_hp)
        bw = max(self.radius * 2 + 10, 28)
        bar_rect = pygame.Rect(self.x - bw / 2, self.y - self.radius - 20, bw, 7)
        pygame.draw.rect(surf, (12, 14, 22), bar_rect.inflate(2, 2), border_radius=4)
        pygame.draw.rect(surf, (40, 14, 18), bar_rect, border_radius=4)
        col = GREEN if hp_ratio > 0.55 else (YELLOW if hp_ratio > 0.3 else RED)
        pygame.draw.rect(surf, col, (bar_rect.x, bar_rect.y, int(bar_rect.w * hp_ratio), bar_rect.h), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255, 40), bar_rect, 1, border_radius=4)

    def serialize(self):
        return {
            "kind": self.kind, "hp": self.hp, "max_hp": self.max_hp,
            "speed": self.speed, "reward": self.reward, "color": list(self.color),
            "radius": self.radius, "x": self.x, "y": self.y,
            "path_index": self.path_index, "alive": self.alive,
        }

    @classmethod
    def deserialize(cls, data):
        return cls(
            data["kind"], data["hp"], data["max_hp"], data["speed"], data["reward"],
            tuple(data["color"]), data["radius"], data["x"], data["y"],
            data.get("path_index", 0), data.get("alive", True),
        )

# ---------- Mermi ----------
@dataclass
class Projectile:
    x: float
    y: float
    target: Enemy
    damage: float
    speed: float
    color: tuple
    alive: bool = True
    trail: List[Tuple[float, float]] = field(default_factory=list)

    def update(self, game_particles):
        if not self.target.alive:
            self.alive = False
            return
        self.trail.append((self.x, self.y))
        if len(self.trail) > 7:
            self.trail.pop(0)
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist <= self.speed + self.target.radius:
            self.target.hp -= self.damage
            self.target.hit_flash = 3
            if self.target.hp <= 0 and self.target.alive:
                self.target.alive = False
                # ölüm patlaması
                for _ in range(18):
                    ang = random.uniform(0, math.tau)
                    sp = random.uniform(1.5, 4.5)
                    game_particles.append(Particle(
                        self.target.x, self.target.y,
                        math.cos(ang) * sp, math.sin(ang) * sp,
                        random.randint(22, 38), 38, self.target.color,
                        random.uniform(2.5, 5), shape="spark"))
                game_particles.append(Particle(
                    self.target.x, self.target.y, 0, 0, 28, 28,
                    self.target.color, self.target.radius + 6, shape="ring"))
            # vuruş efekti
            for _ in range(8):
                ang = random.uniform(0, math.tau)
                sp = random.uniform(0.8, 2.8)
                game_particles.append(Particle(
                    self.x, self.y,
                    math.cos(ang) * sp, math.sin(ang) * sp,
                    random.randint(12, 20), 20, self.color,
                    random.uniform(1.5, 3), shape="spark"))
            self.alive = False
            return
        if dist > 0:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def draw(self, surf):
        for i, (tx, ty) in enumerate(self.trail):
            t = (i + 1) / (len(self.trail) + 1)
            r = int(2 + t * 3)
            s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, int(180 * t)), (r + 1, r + 1), r)
            surf.blit(s, (tx - r - 1, ty - r - 1))
        draw_glow(surf, (int(self.x), int(self.y)), 10, self.color, 1.0)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), 4)
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), 2)

# ---------- Kule ----------
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
        self.dark = base["dark"]
        self.projectile_speed = base["projectile_speed"]
        self.upgrade_cost = base["upgrade_cost"]
        self.kills = 0
        self.aim_angle = 0.0
        self.flash = 0
        self.spin = random.uniform(0, math.tau)
        self.place_anim = 18

    def update(self, enemies, projectiles):
        if self.place_anim > 0:
            self.place_anim -= 1
        if self.flash > 0:
            self.flash -= 1
        self.spin += 0.04
        if self.cooldown > 0:
            self.cooldown -= 1
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
            desired = math.atan2(target.y - self.y, target.x - self.x)
            # yumuşak nişan
            diff = (desired - self.aim_angle + math.pi) % math.tau - math.pi
            self.aim_angle += diff * 0.25
            if self.cooldown == 0:
                projectiles.append(Projectile(self.x, self.y, target, self.damage,
                                              self.projectile_speed, self.color))
                self.cooldown = self.cooldown_max
                self.flash = 6
                return True
        return False

    def upgrade(self):
        self.level += 1
        self.damage *= 1.34
        self.range += 12
        self.cooldown_max = max(6, int(self.cooldown_max * 0.9))
        self.projectile_speed += 0.8
        self.upgrade_cost = int(self.upgrade_cost * 1.45)

    def draw_base(self, surf):
        x, y = self.x, self.y
        # tile highlight
        rect = tile_rect(*self.grid_pos)
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (*self.color, 26), s.get_rect(), border_radius=10)
        surf.blit(s, rect.topleft)
        # gölge
        sh = pygame.Surface((48, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 150), sh.get_rect())
        surf.blit(sh, (x - 24, y + 12))
        # yerleştirme dalgası
        if self.place_anim > 0:
            t = self.place_anim / 18
            r = int(36 + (1 - t) * 30)
            rs = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            pygame.draw.circle(rs, (*self.color, int(180 * t)), (r + 3, r + 3), r, 3)
            surf.blit(rs, (x - r - 3, y - r - 3))

    def draw(self, surf, selected=False, hover=False, t_frame=0):
        x, y = self.x, self.y
        self.draw_base(surf)
        if selected or hover:
            draw_range_circle(surf, (x, y), int(self.range), self.color, selected)

        # Taban
        base_r = 22
        pygame.draw.circle(surf, self.dark, (x, y), base_r)
        pygame.draw.circle(surf, lerp_color(self.color, BG_DEEP, 0.3), (x, y), base_r - 3)
        pygame.draw.circle(surf, self.dark, (x, y), base_r, 2)
        # iç desen - dönen halka
        for i in range(8):
            a = self.spin + i * math.pi / 4
            px = x + math.cos(a) * (base_r - 6)
            py = y + math.sin(a) * (base_r - 6)
            pygame.draw.circle(surf, lerp_color(self.color, WHITE, 0.3), (int(px), int(py)), 2)

        if self.type == "Blaster":
            # Üç namlulu yeşil crystal
            ang = self.aim_angle
            core_r = 11
            pygame.draw.circle(surf, self.color, (x, y), core_r)
            pygame.draw.circle(surf, WHITE, (x - 3, y - 4), 3)
            # namlu
            bx = x + math.cos(ang) * 22
            by = y + math.sin(ang) * 22
            pygame.draw.line(surf, self.dark, (x, y), (bx, by), 7)
            pygame.draw.line(surf, self.color, (x, y), (bx, by), 4)
            pygame.draw.circle(surf, WHITE, (int(bx), int(by)), 3)
        elif self.type == "Sniper":
            # Uzun namlu + scope
            ang = self.aim_angle
            pygame.draw.circle(surf, self.color, (x, y), 10)
            bx = x + math.cos(ang) * 30
            by = y + math.sin(ang) * 30
            nx = x - math.sin(ang) * 4
            ny = y + math.cos(ang) * 4
            mx = x + math.sin(ang) * 4
            my = y - math.cos(ang) * 4
            pts = [(nx, ny), (mx, my),
                   (mx + math.cos(ang) * 30, my + math.sin(ang) * 30),
                   (nx + math.cos(ang) * 30, ny + math.sin(ang) * 30)]
            pygame.draw.polygon(surf, self.dark, pts)
            pygame.draw.polygon(surf, WHITE, pts, 1)
            # lazer işaret
            pygame.draw.line(surf, (*self.color, 180),
                             (bx, by),
                             (x + math.cos(ang) * (self.range * 0.9),
                              y + math.sin(ang) * (self.range * 0.9)), 1)
            pygame.draw.circle(surf, WHITE, (int(bx), int(by)), 3)
        elif self.type == "Rapid":
            # Gatling - çoklu namlu dönen
            ang = self.aim_angle
            pygame.draw.circle(surf, self.color, (x, y), 11)
            for i in range(4):
                a = ang + (self.spin * 3) + i * math.pi / 2
                off_x = math.cos(a + math.pi / 2) * 5
                off_y = math.sin(a + math.pi / 2) * 5
                bx = x + math.cos(ang) * 22 + off_x
                by = y + math.sin(ang) * 22 + off_y
                pygame.draw.line(surf, self.dark,
                                 (x + off_x, y + off_y), (bx, by), 4)
                pygame.draw.line(surf, self.color,
                                 (x + off_x, y + off_y), (bx, by), 2)

        # Muzzle flash
        if self.flash > 0:
            t = self.flash / 6
            ang = self.aim_angle
            fx = x + math.cos(ang) * 30
            fy = y + math.sin(ang) * 30
            r = int(10 * t)
            s = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, int(220 * t)), (r + 2, r + 2), r)
            pygame.draw.circle(s, (*self.color, int(140 * t)), (r + 2, r + 2), r + 2, 2)
            surf.blit(s, (fx - r - 2, fy - r - 2))

        # Seviye rozeti
        badge = pygame.Rect(x + 10, y - 30, 26, 16)
        pygame.draw.rect(surf, self.dark, badge, border_radius=8)
        pygame.draw.rect(surf, self.color, badge, 1, border_radius=8)
        lvl = MINI.render(f"Lv{self.level}", True, WHITE)
        surf.blit(lvl, lvl.get_rect(center=badge.center))

    def serialize(self):
        return {
            "grid_pos": list(self.grid_pos), "type": self.type, "level": self.level,
            "range": self.range, "damage": self.damage, "cooldown_max": self.cooldown_max,
            "cooldown": self.cooldown, "projectile_speed": self.projectile_speed,
            "upgrade_cost": self.upgrade_cost, "kills": self.kills,
        }

    @classmethod
    def deserialize(cls, data):
        t = cls(tuple(data["grid_pos"]), data["type"])
        t.level = data["level"]
        t.range = data["range"]
        t.damage = data["damage"]
        t.cooldown_max = data["cooldown_max"]
        t.cooldown = data["cooldown"]
        t.projectile_speed = data["projectile_speed"]
        t.upgrade_cost = data["upgrade_cost"]
        t.kills = data.get("kills", 0)
        t.place_anim = 0
        return t

def draw_range_circle(surf, center, radius, color, solid=False):
    size = radius * 2 + 8
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color, 26), (radius + 4, radius + 4), radius)
    pygame.draw.circle(s, (*color, 180 if solid else 90), (radius + 4, radius + 4), radius, 2)
    surf.blit(s, (center[0] - radius - 4, center[1] - radius - 4))

# ---------- Dalga yöneticisi ----------
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
            return True
        return False

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
            "level_index": self.level_index, "queue": self.queue, "spawn_gap": self.spawn_gap,
            "active": self.active, "total_this_wave": self.total_this_wave,
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

# ---------- Buton ----------
class Button:
    def __init__(self, rect, label, color, action=None, small=False, icon=None, disabled=False):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.action = action
        self.small = small
        self.icon = icon
        self.disabled = disabled
        self.hover_amt = 0.0

    def update(self, mouse_pos):
        target = 1.0 if self.rect.collidepoint(mouse_pos) and not self.disabled else 0.0
        self.hover_amt += (target - self.hover_amt) * 0.18

    def draw(self, surf, mouse_pos):
        self.update(mouse_pos)
        r = self.rect
        shadow_rect(surf, r, radius=14, offset=4 + int(self.hover_amt * 2), alpha=110)
        base = self.color if not self.disabled else PANEL_3
        c_top = lerp_color(base, WHITE, 0.18 + self.hover_amt * 0.12)
        c_bot = lerp_color(base, BG_DEEP, 0.15)
        rounded_gradient_rect(surf, r, c_top, c_bot, radius=14)
        border = lerp_color(base, WHITE, 0.4 + self.hover_amt * 0.3)
        pygame.draw.rect(surf, border, r, 2, border_radius=14)
        use_font = FONT if not self.small else SMALL
        text_color = TEXT if not self.disabled else DIM
        label = use_font.render(self.label, True, text_color)
        surf.blit(label, label.get_rect(center=r.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos) and not self.disabled

# ---------- Game ----------
class Game:
    def __init__(self):
        self.settings = safe_load_json(SETTINGS_PATH, {"show_grid": True, "auto_save": True})
        if not isinstance(self.settings, dict):
            self.settings = {"show_grid": True, "auto_save": True}
        self.settings.setdefault("show_grid", True)
        self.settings.setdefault("auto_save", True)
        self.best_wave = 0
        self.total_wins = 0
        self.last_status = "Hoş geldin. Kuleni seç ve savunmaya başla."
        self.status_time = 0
        self.scene = "menu"
        self.selected_tile = None
        self.selected_tower = None
        self.selected_type = "Blaster"
        self.hover_tile = None
        self.autosave_timer = 0
        self.t_frame = 0
        self.shake = 0.0
        self.particles: List[Particle] = []
        self.floats: List[FloatingText] = []
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                       random.uniform(0.2, 1.0), random.uniform(0.3, 1.2)) for _ in range(90)]
        self.banner_time = 0
        self.banner_text = ""
        self._build_static_buttons()
        self.reset_runtime(keep_meta=True)
        self.load_meta_only()

    def reset_runtime(self, keep_meta=False):
        if not keep_meta:
            self.best_wave = 0
            self.total_wins = 0
        self.gold = 260
        self.lives = 20
        self.towers: List[Tower] = []
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.wave_manager = WaveManager()
        self.selected_tile = None
        self.selected_tower = None
        self.selected_type = "Blaster"
        self.game_over = False
        self.victory = False
        self.stats = {"enemies_defeated": 0, "gold_earned": 0, "shots_fired": 0}
        self.particles = []
        self.floats = []
        self.shake = 0.0
        self.banner_time = 0

    def _build_static_buttons(self):
        cx = WIDTH // 2 - 150
        self.menu_buttons = [
            Button((cx, 300, 300, 56), "Yeni Oyun", BLUE, "new_game"),
            Button((cx, 370, 300, 56), "Devam Et", TEAL, "continue"),
            Button((cx, 440, 300, 56), "Nasıl Oynanır", PURPLE, "help"),
            Button((cx, 510, 300, 56), "Ayarlar", ORANGE, "settings"),
            Button((cx, 580, 300, 56), "Çıkış", RED, "quit"),
        ]
        self.help_buttons = [Button((40, HEIGHT - 78, 200, 46), "Geri Dön", PANEL_3, "menu", small=True)]
        self.settings_buttons = [Button((40, HEIGHT - 78, 200, 46), "Menüye Dön", PANEL_3, "menu", small=True)]
        self.pause_buttons = [
            Button((WIDTH // 2 - 150, 300, 300, 56), "Oyuna Dön", TEAL, "resume"),
            Button((WIDTH // 2 - 150, 370, 300, 56), "Kaydet ve Menü", BLUE, "save_menu"),
            Button((WIDTH // 2 - 150, 440, 300, 56), "Yeni Oyun", ORANGE, "new_game"),
        ]
        self.end_buttons = [
            Button((WIDTH // 2 - 150, 450, 300, 56), "Ana Menü", BLUE, "menu"),
            Button((WIDTH // 2 - 150, 520, 300, 56), "Yeni Oyun", TEAL, "new_game"),
        ]

    # -------- Oyun mekanikleri --------
    def tower_at(self, grid_pos):
        for tower in self.towers:
            if tower.grid_pos == grid_pos:
                return tower
        return None

    def sell_value(self, tower):
        value = TOWER_TYPES[tower.type]["cost"]
        cl = 1
        uc = TOWER_TYPES[tower.type]["upgrade_cost"]
        while cl < tower.level:
            value += uc
            uc = int(uc * 1.45)
            cl += 1
        return int(value * 0.65)

    def set_status(self, text):
        self.last_status = text
        self.status_time = FPS * 3

    def place_tower(self, grid_pos):
        if grid_pos in PATH_SET or self.tower_at(grid_pos):
            self.set_status("Bu kareye kule koyamazsın.")
            return False
        cfg = TOWER_TYPES[self.selected_type]
        if self.gold < cfg["cost"]:
            self.set_status("Yeterli altın yok.")
            return False
        self.gold -= cfg["cost"]
        tower = Tower(grid_pos, self.selected_type)
        self.towers.append(tower)
        self.selected_tower = tower
        self.selected_tile = grid_pos
        # yerleştirme partikülleri
        for _ in range(14):
            ang = random.uniform(0, math.tau)
            sp = random.uniform(1, 3)
            self.particles.append(Particle(tower.x, tower.y,
                                           math.cos(ang) * sp, math.sin(ang) * sp,
                                           30, 30, cfg["color"], 3, shape="spark"))
        self.set_status(f"{self.selected_type} yerleştirildi.")
        self.maybe_autosave(force=True)
        return True

    def start_wave(self):
        if self.wave_manager.active or self.wave_manager.level_index >= 10:
            return False
        started = self.wave_manager.start_level()
        if started:
            self.banner_text = f"Bölüm {self.wave_manager.current_label()} başlıyor"
            self.banner_time = 90
            self.set_status(f"Bölüm {self.wave_manager.current_label()} başladı.")
            self.maybe_autosave(force=True)
        return started

    def update(self):
        self.t_frame += 1
        if self.shake > 0:
            self.shake *= 0.88
            if self.shake < 0.2:
                self.shake = 0
        if self.status_time > 0:
            self.status_time -= 1
        if self.banner_time > 0:
            self.banner_time -= 1

        # arkaplan yıldızları
        new_stars = []
        for x, y, spd, size in self.stars:
            y += spd * 0.3
            if y > HEIGHT:
                y = 0
                x = random.randint(0, WIDTH)
            new_stars.append((x, y, spd, size))
        self.stars = new_stars

        # parçacıklar
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive()]
        for f in self.floats:
            f.update()
        self.floats = [f for f in self.floats if f.alive()]

        if self.scene != "play" or self.game_over or self.victory:
            return

        completed = self.wave_manager.update(self.enemies)
        if completed:
            bonus = 35 + self.wave_manager.level_index * 8
            self.gold += bonus
            self.stats["gold_earned"] += bonus
            self.best_wave = max(self.best_wave, self.wave_manager.level_index)
            self.floats.append(FloatingText(MAP_W // 2, 160, f"+{bonus} Bonus!", GOLD, 72, 72))
            self.set_status(f"Bölüm tamamlandı. Bonus +{bonus} altın.")
            self.banner_text = "Dalga tamamlandı!"
            self.banner_time = 80
            self.maybe_autosave(force=True)

        for tower in self.towers:
            fired = tower.update(self.enemies, self.projectiles)
            if fired:
                self.stats["shots_fired"] += 1

        for projectile in self.projectiles:
            projectile.update(self.particles)
        self.projectiles = [p for p in self.projectiles if p.alive]

        remaining = []
        for enemy in self.enemies:
            was_alive = enemy.alive
            if not enemy.alive:
                self.gold += enemy.reward
                self.stats["gold_earned"] += enemy.reward
                self.stats["enemies_defeated"] += 1
                self.floats.append(FloatingText(enemy.x, enemy.y - 20, f"+{enemy.reward}", GOLD))
                if enemy.kind == "boss":
                    self.shake = 10
                continue
            reached_end = enemy.update()
            if reached_end:
                dmg = 3 if enemy.kind == "boss" else 1
                self.lives -= dmg
                self.shake = max(self.shake, 6 if enemy.kind == "boss" else 3)
                self.floats.append(FloatingText(PATH_POINTS[-1][0], PATH_POINTS[-1][1] - 20,
                                                f"-{dmg} can", RED))
                self.set_status("Bir düşman çıkışa ulaştı.")
                continue
            if was_alive and not enemy.alive:
                self.stats["enemies_defeated"] += 1
            remaining.append(enemy)
        self.enemies = remaining

        if self.lives <= 0:
            self.lives = 0
            self.game_over = True
            self.scene = "end"
            self.set_status("Savunma çöktü.")
            self.maybe_autosave(force=True, allow_delete=True)

        if self.wave_manager.level_index >= 10 and not self.wave_manager.active and not self.enemies:
            self.victory = True
            self.scene = "end"
            self.total_wins += 1
            self.best_wave = 10
            self.set_status("Tüm 10 bölümü tamamladın!")
            self.maybe_autosave(force=True, allow_delete=True)

        self.maybe_autosave()

    # -------- Kayıt --------
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
            "gold": self.gold, "lives": self.lives, "selected_type": self.selected_type,
            "wave_manager": self.wave_manager.serialize(),
            "towers": [t.serialize() for t in self.towers],
            "enemies": [e.serialize() for e in self.enemies],
            "stats": self.stats, "last_status": self.last_status,
            "best_wave": self.best_wave, "total_wins": self.total_wins,
        }
        save_json(SAVE_PATH, data)
        self.save_meta_only()

    def save_meta_only(self):
        data = {"best_wave": self.best_wave, "total_wins": self.total_wins, "settings": self.settings}
        save_json(SETTINGS_PATH, data)

    def load_meta_only(self):
        meta = safe_load_json(SETTINGS_PATH, {})
        if isinstance(meta, dict):
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
            self.set_status("Kayıt bulunamadı.")
            return False
        self.reset_runtime(keep_meta=True)
        self.gold = data.get("gold", 260)
        self.lives = data.get("lives", 20)
        self.selected_type = data.get("selected_type", "Blaster")
        self.wave_manager = WaveManager.deserialize(data.get("wave_manager", {}))
        self.towers = [Tower.deserialize(t) for t in data.get("towers", [])]
        self.enemies = [Enemy.deserialize(e) for e in data.get("enemies", [])]
        self.stats = data.get("stats", self.stats)
        self.set_status(data.get("last_status", "Kayıt yüklendi."))
        self.best_wave = max(self.best_wave, data.get("best_wave", 0))
        self.total_wins = max(self.total_wins, data.get("total_wins", 0))
        self.scene = "play"
        self.game_over = False
        self.victory = False
        return True

    def new_game(self):
        self.reset_runtime(keep_meta=True)
        self.scene = "play"
        self.set_status("Yeni oyun başladı. İyi savunmalar!")
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
                self.set_status("Önce bir kayıt oluşturmalısın.")
        elif action == "help":
            self.scene = "help"
        elif action == "settings":
            self.scene = "settings"
        elif action == "menu":
            self.scene = "menu"
            self.save_meta_only()
        elif action == "quit":
            if self.scene in {"play", "pause"}:
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
            g = pygame.Rect(380, 220, 520, 54)
            a = pygame.Rect(380, 290, 520, 54)
            if g.collidepoint(pos):
                self.toggle_setting("show_grid")
            if a.collidepoint(pos):
                self.toggle_setting("auto_save")
            return
        if self.scene == "pause":
            for b in self.pause_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            return
        if self.scene == "end":
            for b in self.end_buttons:
                if b.is_clicked(pos):
                    self.handle_action(b.action)
            return

        if self.scene != "play":
            return

        clicked_btn = self.sidebar_button_at(pos)
        if clicked_btn:
            action, value = clicked_btn
            if action == "select_type":
                self.selected_type = value
                self.set_status(f"{value} seçildi.")
            elif action == "start":
                self.start_wave()
            elif action == "upgrade" and self.selected_tower:
                if self.gold >= self.selected_tower.upgrade_cost:
                    self.gold -= self.selected_tower.upgrade_cost
                    self.selected_tower.upgrade()
                    self.selected_tower.place_anim = 14
                    self.set_status("Kule geliştirildi.")
                    self.maybe_autosave(force=True)
                else:
                    self.set_status("Yeterli altın yok.")
            elif action == "sell" and self.selected_tower:
                self.gold += self.sell_value(self.selected_tower)
                self.floats.append(FloatingText(self.selected_tower.x, self.selected_tower.y - 20,
                                                f"+{self.sell_value(self.selected_tower)}", GOLD))
                self.towers.remove(self.selected_tower)
                self.selected_tower = None
                self.selected_tile = None
                self.set_status("Kule satıldı.")
                self.maybe_autosave(force=True)
            elif action == "save":
                self.save_game()
                self.set_status("Oyun kaydedildi.")
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
        tower_y = 270
        idx = (y - tower_y) // 82
        names = list(TOWER_TYPES.keys())
        if 0 <= idx < len(names):
            rect = pygame.Rect(MAP_W + 18, tower_y + idx * 82, SIDEBAR_W - 36, 72)
            if rect.collidepoint(pos):
                return ("select_type", names[idx])
        buttons = {
            "start":   pygame.Rect(MAP_W + 20, HEIGHT - 168, 140, 46),
            "save":    pygame.Rect(MAP_W + 170, HEIGHT - 168, 140, 46),
            "upgrade": pygame.Rect(MAP_W + 20, HEIGHT - 112, 140, 46),
            "sell":    pygame.Rect(MAP_W + 170, HEIGHT - 112, 140, 46),
            "pause":   pygame.Rect(MAP_W + 20, HEIGHT - 56, 290, 38),
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
            self.set_status("Oyun kaydedildi.")
        elif key == pygame.K_u and self.selected_tower:
            if self.gold >= self.selected_tower.upgrade_cost:
                self.gold -= self.selected_tower.upgrade_cost
                self.selected_tower.upgrade()
                self.selected_tower.place_anim = 14
                self.set_status("Kule geliştirildi.")

    # -------- Çizim --------
    def draw(self):
        target = screen
        shake_x = random.uniform(-self.shake, self.shake)
        shake_y = random.uniform(-self.shake, self.shake)

        if self.scene == "menu":
            self.draw_menu()
        elif self.scene == "help":
            self.draw_help()
        elif self.scene == "settings":
            self.draw_settings()
        else:
            self.draw_gameplay(shake_x, shake_y)
            if self.scene == "pause":
                self.draw_pause_overlay()
            elif self.scene == "end":
                self.draw_end_overlay()

    def draw_background(self):
        # dikey gradient
        for y in range(HEIGHT):
            t = y / HEIGHT
            if t < 0.5:
                c = lerp_color(BG_TOP, BG_MID, t * 2)
            else:
                c = lerp_color(BG_MID, BG_DEEP, (t - 0.5) * 2)
            pygame.draw.line(screen, c, (0, y), (WIDTH, y))
        # nebula bulutları
        for i, (ox, oy, scale, color) in enumerate([
            (200, 150, 260, (70, 40, 140)),
            (WIDTH - 300, 100, 300, (30, 80, 150)),
            (WIDTH // 2, HEIGHT - 150, 240, (80, 30, 100)),
        ]):
            s = pygame.Surface((scale * 2, scale * 2), pygame.SRCALPHA)
            wobble = math.sin(self.t_frame * 0.01 + i) * 10
            for r in range(scale, 0, -40):
                a = int(18 * (r / scale))
                pygame.draw.circle(s, (*color, a), (scale, scale), r)
            screen.blit(s, (ox - scale + wobble, oy - scale))
        # yıldızlar
        for x, y, spd, size in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.t_frame * 0.04 + x)
            c = int(180 + 60 * tw)
            pygame.draw.circle(screen, (c, c, c), (int(x), int(y)), max(1, int(size)))

    def draw_card(self, rect, color=PANEL, border=PANEL_3, radius=18, gradient=True):
        shadow_rect(screen, rect, radius=radius, offset=6, alpha=130)
        if gradient:
            rounded_gradient_rect(screen, rect, lerp_color(color, WHITE, 0.06),
                                  lerp_color(color, BG_DEEP, 0.2), radius=radius, border=border)
        else:
            pygame.draw.rect(screen, color, rect, border_radius=radius)
            pygame.draw.rect(screen, border, rect, 1, border_radius=radius)

    def draw_icon(self, kind, pos, size=18, color=TEXT):
        x, y = pos
        if kind == "wave":
            for i in range(3):
                pygame.draw.arc(screen, color,
                                (x - size / 2, y - size / 2 + i * 3, size, size * 0.8),
                                3.2, 6.1, 2)
        elif kind == "heart":
            pygame.draw.polygon(screen, color,
                [(x, y + size * 0.55), (x - size * 0.55, y - size * 0.1), (x - size * 0.28, y - size * 0.45),
                 (x, y - size * 0.25), (x + size * 0.28, y - size * 0.45), (x + size * 0.55, y - size * 0.1)])
        elif kind == "coin":
            pygame.draw.circle(screen, color, (x, y), int(size * 0.5))
            pygame.draw.circle(screen, lerp_color(color, BG_DEEP, 0.3), (x, y), int(size * 0.5), 2)
            lb = MINI.render("$", True, BG_DEEP)
            screen.blit(lb, lb.get_rect(center=(x, y)))
        elif kind == "star":
            pts = []
            for i in range(10):
                r = size * 0.5 if i % 2 == 0 else size * 0.22
                a = -math.pi / 2 + i * math.pi / 5
                pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
            pygame.draw.polygon(screen, color, pts)

    def draw_topbar(self):
        rect = pygame.Rect(16, 12, WIDTH - 32, TOPBAR_H - 14)
        self.draw_card(rect, color=PANEL, border=PANEL_3)
        # logo parıltısı
        tshine = 0.5 + 0.5 * math.sin(self.t_frame * 0.03)
        title = BIG.render("Tower Defense Deluxe", True, lerp_color(TEXT, CYAN, tshine * 0.35))
        screen.blit(title, (36, 28))
        sub = MINI.render("2D görsel savunma deneyimi", True, MUTED)
        screen.blit(sub, (40, 62))

        stats = [
            ("wave", "Bölüm", f"{min(self.wave_manager.current_label(), 10)}/10", BLUE),
            ("heart", "Can", str(self.lives), RED),
            ("coin", "Altın", str(self.gold), GOLD),
            ("star", "En İyi", str(self.best_wave), CYAN),
        ]
        x = 440
        for icon, label, value, color in stats:
            card = pygame.Rect(x, 22, 128, 46)
            rounded_gradient_rect(screen, card, lerp_color(PANEL_2, WHITE, 0.05),
                                  lerp_color(PANEL_2, BG_DEEP, 0.25), radius=12,
                                  border=lerp_color(color, PANEL_3, 0.4))
            self.draw_icon(icon, (card.x + 22, card.y + 23), 20, color)
            screen.blit(MINI.render(label, True, MUTED), (card.x + 42, card.y + 6))
            screen.blit(MED.render(value, True, TEXT), (card.x + 42, card.y + 20))
            x += 136

    def draw_map(self, shake_x=0, shake_y=0):
        area = pygame.Rect(16, TOPBAR_H + 8, MAP_W - 24, HEIGHT - TOPBAR_H - 22)
        self.draw_card(area, color=(20, 26, 38), border=PANEL_3)

        map_surf = pygame.Surface((area.w, area.h), pygame.SRCALPHA)
        # alan
        for row in range(ROWS):
            for col in range(COLS):
                rect_tile = pygame.Rect(
                    OFFSET_X - area.x + col * TILE,
                    OFFSET_Y - area.y + row * TILE,
                    TILE - 4, TILE - 4
                )
                if (col, row) in PATH_SET:
                    c = PATH_A if (col + row) % 2 == 0 else PATH_B
                    pygame.draw.rect(map_surf, c, rect_tile, border_radius=8)
                    pygame.draw.rect(map_surf, PATH_EDGE, rect_tile, 1, border_radius=8)
                    # küçük taş noktaları
                    for i in range(3):
                        sx = rect_tile.x + (i * 17 + (col * 7) % 15) % rect_tile.w
                        sy = rect_tile.y + (i * 11 + (row * 5) % 13) % rect_tile.h
                        pygame.draw.circle(map_surf, PATH_EDGE, (sx, sy), 1)
                else:
                    c = GRASS_A if (col + row) % 2 == 0 else GRASS_B
                    pygame.draw.rect(map_surf, c, rect_tile, border_radius=8)
                    if self.settings.get("show_grid", True):
                        pygame.draw.rect(map_surf, GRID_DIM, rect_tile, 1, border_radius=8)

        # yol akış efekti
        flow_t = (self.t_frame * 0.6) % 40
        for i in range(len(PATH_POINTS) - 1):
            p1 = PATH_POINTS[i]
            p2 = PATH_POINTS[i + 1]
            steps = 6
            for s in range(steps):
                t = (s / steps + flow_t / 40) % 1
                fx = lerp(p1[0], p2[0], t) - area.x
                fy = lerp(p1[1], p2[1], t) - area.y
                ss = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(ss, (255, 240, 200, 35), (7, 7), 5)
                map_surf.blit(ss, (fx - 7, fy - 7))

        # Giriş / Çıkış portalları
        start = PATH_POINTS[0]
        end = PATH_POINTS[-1]
        for pos, color, label in [(start, GREEN, "GİRİŞ"), (end, RED, "ÇIKIŞ")]:
            lx = pos[0] - area.x
            ly = pos[1] - area.y
            pulse = 4 + math.sin(self.t_frame * 0.1) * 2
            # glow
            g = make_glow(32, color, 1.2)
            map_surf.blit(g, (lx - 32, ly - 32))
            pygame.draw.circle(map_surf, color, (int(lx), int(ly)), int(14 + pulse))
            pygame.draw.circle(map_surf, WHITE, (int(lx), int(ly)), int(14 + pulse), 2)
            lab = MINI.render(label, True, WHITE)
            lbg = pygame.Rect(lx - lab.get_width() // 2 - 6, ly - 38,
                              lab.get_width() + 12, lab.get_height() + 4)
            pygame.draw.rect(map_surf, (0, 0, 0, 140), lbg, border_radius=6)
            map_surf.blit(lab, (lbg.x + 6, lbg.y + 2))

        # hover/selected
        if self.hover_tile and self.scene == "play":
            c, r = self.hover_tile
            rect_h = pygame.Rect(OFFSET_X - area.x + c * TILE,
                                 OFFSET_Y - area.y + r * TILE, TILE - 4, TILE - 4)
            valid = self.hover_tile not in PATH_SET and not self.tower_at(self.hover_tile)
            col = GREEN if valid else RED
            sh = pygame.Surface((rect_h.w, rect_h.h), pygame.SRCALPHA)
            pygame.draw.rect(sh, (*col, 60), sh.get_rect(), border_radius=8)
            pygame.draw.rect(sh, (*col, 200), sh.get_rect(), 2, border_radius=8)
            map_surf.blit(sh, rect_h.topleft)
            if valid and not self.tower_at(self.hover_tile):
                cfg = TOWER_TYPES[self.selected_type]
                cx = OFFSET_X - area.x + c * TILE + TILE // 2
                cy = OFFSET_Y - area.y + r * TILE + TILE // 2
                draw_range_circle(map_surf, (cx, cy), cfg["range"], cfg["color"], False)

        if self.selected_tile:
            c, r = self.selected_tile
            rect_s = pygame.Rect(OFFSET_X - area.x + c * TILE,
                                 OFFSET_Y - area.y + r * TILE, TILE - 4, TILE - 4)
            pygame.draw.rect(map_surf, CYAN, rect_s, 3, border_radius=8)

        # Kuleler
        # map_surf is relative; we need to blit area first then draw towers in world coordinates
        screen.blit(map_surf, (area.x + shake_x, area.y + shake_y))

        # Dünya koordinatlarında çizim (gölge için ayrı yüzey offset'i uygulanacak)
        world = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for tower in self.towers:
            tower.draw(world, selected=(self.selected_tower is tower),
                       hover=False, t_frame=self.t_frame)
        for enemy in self.enemies:
            enemy.draw(world, self.t_frame)
        for projectile in self.projectiles:
            projectile.draw(world)
        for p in self.particles:
            p.draw(world)
        for f in self.floats:
            f.draw(world)
        screen.blit(world, (shake_x, shake_y))

        # Banner
        if self.banner_time > 0:
            t = self.banner_time / 90
            alpha = int(255 * clamp(t * 2, 0, 1))
            s = HUGE.render(self.banner_text, True, WHITE)
            s.set_alpha(alpha)
            bx = area.x + area.w // 2 - s.get_width() // 2
            by = area.y + 120 - int((1 - t) * 40)
            bg = pygame.Surface((s.get_width() + 60, s.get_height() + 24), pygame.SRCALPHA)
            pygame.draw.rect(bg, (0, 0, 0, int(alpha * 0.55)), bg.get_rect(), border_radius=18)
            pygame.draw.rect(bg, (*CYAN, int(alpha * 0.7)), bg.get_rect(), 2, border_radius=18)
            screen.blit(bg, (bx - 30, by - 12))
            screen.blit(s, (bx, by))

    def draw_sidebar(self):
        rect = pygame.Rect(MAP_W + 6, TOPBAR_H + 8, SIDEBAR_W - 12, HEIGHT - TOPBAR_H - 22)
        self.draw_card(rect)

        y = TOPBAR_H + 22
        screen.blit(MED.render("DALGA DURUMU", True, MUTED), (MAP_W + 22, y))
        y += 26
        progress_back = pygame.Rect(MAP_W + 22, y, SIDEBAR_W - 44, 22)
        pygame.draw.rect(screen, PANEL_2, progress_back, border_radius=11)
        inner = pygame.Rect(progress_back.x + 2, progress_back.y + 2,
                            int((progress_back.w - 4) * self.wave_manager.progress_ratio()),
                            progress_back.h - 4)
        rounded_gradient_rect(screen, inner, lerp_color(BLUE, WHITE, 0.2), BLUE_DK, radius=10)
        pygame.draw.rect(screen, PANEL_HI, progress_back, 1, border_radius=11)
        lbl = "Aktif dalga" if self.wave_manager.active else "Hazır"
        screen.blit(MINI.render(lbl, True, MUTED), (progress_back.x, progress_back.y + 26))

        y += 56
        alive = len([e for e in self.enemies if e.alive])
        info = [
            ("Sahadaki düşman", str(alive), RED),
            ("Toplam kule", str(len(self.towers)), GREEN),
            ("Yok edilen", str(self.stats['enemies_defeated']), PURPLE),
            ("Altın kazancı", str(self.stats['gold_earned']), GOLD),
        ]
        for label, val, col in info:
            r = pygame.Rect(MAP_W + 22, y, SIDEBAR_W - 44, 26)
            pygame.draw.rect(screen, PANEL_2, r, border_radius=8)
            pygame.draw.circle(screen, col, (r.x + 12, r.y + 13), 4)
            screen.blit(SMALL.render(label, True, MUTED), (r.x + 24, r.y + 5))
            t = MED.render(val, True, TEXT)
            screen.blit(t, (r.right - t.get_width() - 10, r.y + 4))
            y += 30

        y += 8
        screen.blit(MED.render("KULELER", True, MUTED), (MAP_W + 22, y))
        y += 12
        mouse_pos = pygame.mouse.get_pos()
        for idx, (name, cfg) in enumerate(TOWER_TYPES.items()):
            card = pygame.Rect(MAP_W + 20, 270 + idx * 82, SIDEBAR_W - 40, 72)
            hover = card.collidepoint(mouse_pos)
            selected = (self.selected_type == name)
            base = PANEL_2 if not hover else PANEL_3
            rounded_gradient_rect(screen, card, lerp_color(base, WHITE, 0.05),
                                  lerp_color(base, BG_DEEP, 0.3), radius=14)
            if selected:
                pygame.draw.rect(screen, cfg["color"], card, 3, border_radius=14)
            else:
                pygame.draw.rect(screen, PANEL_HI, card, 1, border_radius=14)

            # kule mini önizleme
            cx = card.x + 32
            cy = card.y + 36
            draw_glow(screen, (cx, cy), 22, cfg["color"], 0.8)
            pygame.draw.circle(screen, cfg["dark"], (cx, cy), 18)
            pygame.draw.circle(screen, cfg["color"], (cx, cy), 13)
            pygame.draw.circle(screen, WHITE, (cx - 4, cy - 5), 3)
            if name == "Sniper":
                pygame.draw.line(screen, cfg["dark"], (cx, cy), (cx + 16, cy), 5)
                pygame.draw.line(screen, WHITE, (cx, cy), (cx + 16, cy), 1)
            elif name == "Rapid":
                for i in range(3):
                    pygame.draw.line(screen, cfg["dark"], (cx, cy - 4 + i * 4), (cx + 14, cy - 4 + i * 4), 2)

            screen.blit(FONT.render(name, True, TEXT), (card.x + 62, card.y + 8))
            screen.blit(MINI.render(cfg["accent"], True, MUTED), (card.x + 62, card.y + 32))
            cost = MED.render(f"{cfg['cost']}", True, GOLD)
            screen.blit(cost, (card.right - cost.get_width() - 14, card.y + 10))
            screen.blit(MINI.render("altın", True, MUTED),
                        (card.right - 42, card.y + 30))
            # shortcut
            sc = MINI.render(str(idx + 1), True, MUTED)
            sb = pygame.Rect(card.right - 22, card.bottom - 22, 16, 16)
            pygame.draw.rect(screen, PANEL_3, sb, border_radius=4)
            screen.blit(sc, sc.get_rect(center=sb.center))

        # Seçili kule detay
        detail_rect = pygame.Rect(MAP_W + 20, HEIGHT - 300, SIDEBAR_W - 40, 120)
        rounded_gradient_rect(screen, detail_rect, PANEL_2,
                              lerp_color(PANEL_2, BG_DEEP, 0.4), radius=14, border=PANEL_HI)
        if self.selected_tower:
            t = self.selected_tower
            cfg = TOWER_TYPES[t.type]
            screen.blit(MED.render(f"{t.type}  •  Lv{t.level}", True, cfg["color"]),
                        (detail_rect.x + 14, detail_rect.y + 10))
            rows = [
                ("Hasar", f"{int(t.damage)}", RED),
                ("Menzil", f"{int(t.range)}", BLUE),
                ("Ateş hızı", f"{60 / max(1, t.cooldown_max):.1f}/s", ORANGE),
            ]
            for i, (a, b, col) in enumerate(rows):
                screen.blit(MINI.render(a, True, MUTED),
                            (detail_rect.x + 14, detail_rect.y + 38 + i * 18))
                pygame.draw.circle(screen, col,
                                   (detail_rect.x + 108, detail_rect.y + 46 + i * 18), 3)
                screen.blit(SMALL.render(b, True, TEXT),
                            (detail_rect.x + 118, detail_rect.y + 36 + i * 18))
            # geliştirme/sat bilgisi
            up = MINI.render(f"Upgrade: {t.upgrade_cost}", True, GREEN)
            sl = MINI.render(f"Satış: {self.sell_value(t)}", True, GOLD)
            screen.blit(up, (detail_rect.right - up.get_width() - 14, detail_rect.y + 40))
            screen.blit(sl, (detail_rect.right - sl.get_width() - 14, detail_rect.y + 60))
        else:
            screen.blit(MED.render("Seçili kule yok", True, TEXT),
                        (detail_rect.x + 14, detail_rect.y + 12))
            screen.blit(SMALL.render("Boş kareye tıkla → kule yerleştir",
                                     True, MUTED), (detail_rect.x + 14, detail_rect.y + 42))
            screen.blit(SMALL.render("1 / 2 / 3: kule seçimi",
                                     True, MUTED), (detail_rect.x + 14, detail_rect.y + 62))
            screen.blit(SMALL.render("SPACE: dalga başlat", True, MUTED),
                        (detail_rect.x + 14, detail_rect.y + 82))

        # Butonlar
        ym = HEIGHT - 168
        specs = [
            (pygame.Rect(MAP_W + 20, ym, 140, 46), "▶ Başlat", BLUE, "start"),
            (pygame.Rect(MAP_W + 170, ym, 140, 46), "💾 Kaydet", TEAL, "save"),
            (pygame.Rect(MAP_W + 20, ym + 56, 140, 46), "▲ Geliştir",
             PURPLE if self.selected_tower else PANEL_3, "upgrade"),
            (pygame.Rect(MAP_W + 170, ym + 56, 140, 46), "✖ Sat",
             ORANGE if self.selected_tower else PANEL_3, "sell"),
            (pygame.Rect(MAP_W + 20, ym + 112, 290, 38), "Duraklat (ESC)", PANEL_3, "pause"),
        ]
        mouse_pos = pygame.mouse.get_pos()
        for rect_btn, label_btn, color, _a in specs:
            disabled = (_a in ("upgrade", "sell") and self.selected_tower is None)
            btn = Button(rect_btn, label_btn, color, small=True, disabled=disabled)
            btn.draw(screen, mouse_pos)

    def draw_statusbar(self):
        if self.status_time <= 0:
            return
        t = clamp(self.status_time / (FPS * 3), 0, 1)
        rect = pygame.Rect(28, HEIGHT - 44, MAP_W - 44, 30)
        s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (0, 0, 0, int(180 * t)), s.get_rect(), border_radius=14)
        pygame.draw.rect(s, (*CYAN, int(160 * t)), s.get_rect(), 1, border_radius=14)
        screen.blit(s, rect.topleft)
        text = SMALL.render(self.last_status, True, TEXT)
        text.set_alpha(int(255 * t))
        screen.blit(text, (rect.x + 14, rect.y + 7))

    def draw_gameplay(self, shake_x=0, shake_y=0):
        self.draw_background()
        self.draw_topbar()
        self.draw_map(shake_x, shake_y)
        self.draw_sidebar()
        self.draw_statusbar()

    def draw_menu(self):
        self.draw_background()
        # Büyük başlık parıltısı
        tshine = 0.5 + 0.5 * math.sin(self.t_frame * 0.04)
        title = HUGE.render("TOWER DEFENSE", True, lerp_color(TEXT, CYAN, 0.2 + tshine * 0.4))
        shadow = HUGE.render("TOWER DEFENSE", True, (0, 0, 0))
        screen.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 4, 170 + 4)))
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 170)))
        sub = MED.render("DELUXE EDITION  •  10 Bölüm  •  2D Savunma", True, MUTED)
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 220)))

        info_card = pygame.Rect(WIDTH // 2 - 300, 255, 600, 32)
        pygame.draw.rect(screen, (0, 0, 0, 0), info_card)
        rounded_gradient_rect(screen, info_card, PANEL, lerp_color(PANEL, BG_DEEP, 0.4),
                              radius=14, border=PANEL_HI)
        line = f"En iyi: {self.best_wave}/10   •   Galibiyet: {self.total_wins}   •   "
        line += "Kayıt var ✓" if self.has_savegame() else "Kayıt yok"
        ls = SMALL.render(line, True, TEXT)
        screen.blit(ls, ls.get_rect(center=info_card.center))

        mouse_pos = pygame.mouse.get_pos()
        for b in self.menu_buttons:
            if b.action == "continue" and not self.has_savegame():
                disabled = Button(b.rect, b.label, PANEL_3, b.action, disabled=True)
                disabled.draw(screen, mouse_pos)
            else:
                b.draw(screen, mouse_pos)

        # dekoratif küçük kuleler
        for i, (name, cfg) in enumerate(TOWER_TYPES.items()):
            x = 120 + i * 110
            y = HEIGHT - 110
            draw_glow(screen, (x, y), 36, cfg["color"], 1.0)
            pygame.draw.circle(screen, cfg["dark"], (x, y), 24)
            pygame.draw.circle(screen, cfg["color"], (x, y), 16)
            pygame.draw.circle(screen, WHITE, (x - 5, y - 6), 4)
            screen.blit(MINI.render(name, True, MUTED), (x - 20, y + 30))

        tip = MINI.render("ESC ile menüye dönebilirsin • Otomatik kayıt aktif", True, DIM)
        screen.blit(tip, tip.get_rect(center=(WIDTH // 2, HEIGHT - 30)))

    def draw_help(self):
        self.draw_background()
        card = pygame.Rect(60, 60, WIDTH - 120, HEIGHT - 140)
        self.draw_card(card)
        screen.blit(BIG.render("Nasıl Oynanır", True, TEXT), (90, 80))
        lines = [
            ("🎯", "Boş kareye tıkla → seçili kuleyi yerleştir."),
            ("🔢", "1 / 2 / 3 ile kule türünü değiştir."),
            ("▶", "SPACE veya Başlat düğmesi ile dalgayı başlat."),
            ("▲", "Kule seçip Geliştir'e bas (kısayol: U)."),
            ("✖", "Sat düğmesi ile altının %65'ini geri al."),
            ("💾", "S veya Kaydet: anlık kayıt. Oto-kayıt aktif."),
            ("⏸", "ESC: duraklat veya menüye dön."),
            ("🏆", "Amaç: 10 bölümün tamamını tamamlamak."),
        ]
        y = 150
        for icon, text in lines:
            screen.blit(MED.render(icon, True, CYAN), (100, y))
            screen.blit(FONT.render(text, True, TEXT), (150, y + 2))
            y += 46

        tip_rect = pygame.Rect(90, y + 10, WIDTH - 240, 84)
        rounded_gradient_rect(screen, tip_rect, lerp_color(PANEL_2, CYAN, 0.08),
                              PANEL_2, radius=14, border=CYAN)
        screen.blit(MED.render("İpuçları", True, CYAN), (tip_rect.x + 18, tip_rect.y + 10))
        screen.blit(SMALL.render("• Sniper uzun menzil + yüksek hasar, boss için ideal.", True, TEXT),
                    (tip_rect.x + 18, tip_rect.y + 36))
        screen.blit(SMALL.render("• Rapid hızlı düşmanlara karşı sürü temizliği yapar.", True, TEXT),
                    (tip_rect.x + 18, tip_rect.y + 56))

        for b in self.help_buttons:
            b.draw(screen, pygame.mouse.get_pos())

    def draw_settings(self):
        self.draw_background()
        card = pygame.Rect(260, 100, 760, 440)
        self.draw_card(card)
        screen.blit(BIG.render("Ayarlar", True, TEXT), (300, 130))

        options = [
            (pygame.Rect(380, 220, 520, 54), "Grid göster", self.settings.get("show_grid", True)),
            (pygame.Rect(380, 290, 520, 54), "Otomatik kayıt", self.settings.get("auto_save", True)),
        ]
        mouse_pos = pygame.mouse.get_pos()
        for rect, label, state in options:
            rounded_gradient_rect(screen, rect, PANEL_2,
                                  lerp_color(PANEL_2, BG_DEEP, 0.4), radius=14,
                                  border=CYAN if state else PANEL_3)
            screen.blit(FONT.render(label, True, TEXT), (rect.x + 22, rect.y + 14))
            # toggle pill
            pill_w = 70
            pill = pygame.Rect(rect.right - pill_w - 12, rect.y + 10, pill_w, 34)
            pygame.draw.rect(screen, GREEN_DK if state else RED_DK, pill, border_radius=17)
            knob_x = pill.right - 16 if state else pill.x + 16
            pygame.draw.circle(screen, WHITE, (knob_x, pill.centery), 12)
            st = MINI.render("Açık" if state else "Kapalı", True, WHITE)
            screen.blit(st, st.get_rect(center=(pill.centerx - (14 if state else -14), pill.centery)))

        screen.blit(SMALL.render("Değişiklikler otomatik kaydedilir.", True, MUTED), (382, 370))
        for b in self.settings_buttons:
            b.draw(screen, mouse_pos)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 6, 12, 180))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 200, 220, 400, 340)
        self.draw_card(panel)
        title = BIG.render("Duraklatıldı", True, TEXT)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 260)))
        sub = SMALL.render("ESC ile oyuna geri dön", True, MUTED)
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 290)))
        mouse_pos = pygame.mouse.get_pos()
        for b in self.pause_buttons:
            b.draw(screen, mouse_pos)

    def draw_end_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((4, 6, 12, 200))
        screen.blit(overlay, (0, 0))
        panel = pygame.Rect(WIDTH // 2 - 250, 170, 500, 440)
        self.draw_card(panel)
        title_text = "Kazandın!" if self.victory else "Kaybettin"
        color = GREEN if self.victory else RED
        t = BIG.render(title_text, True, color)
        screen.blit(t, t.get_rect(center=(WIDTH // 2, 220)))
        emoji = HUGE.render("🏆" if self.victory else "💀", True, color)
        screen.blit(emoji, emoji.get_rect(center=(WIDTH // 2, 300)))

        stats = [
            ("Ulaşılan bölüm", f"{self.best_wave}/10"),
            ("Yok edilen düşman", f"{self.stats['enemies_defeated']}"),
            ("Kazanılan altın", f"{self.stats['gold_earned']}"),
            ("Atılan mermi", f"{self.stats['shots_fired']}"),
        ]
        y = 360
        for label, val in stats:
            screen.blit(SMALL.render(label, True, MUTED), (WIDTH // 2 - 150, y))
            v = MED.render(val, True, TEXT)
            screen.blit(v, (WIDTH // 2 + 150 - v.get_width(), y - 2))
            y += 22

        mouse_pos = pygame.mouse.get_pos()
        for b in self.end_buttons:
            b.draw(screen, mouse_pos)


# ---------- main ----------
def main():
    game = Game()
    while True:
        clock.tick(FPS)
        if game.scene == "play":
            game.hover_tile = tile_from_mouse(pygame.mouse.get_pos())
        else:
            game.hover_tile = None

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