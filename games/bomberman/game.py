import sys
import os
import pygame
import random
import math
import struct
import wave
import io
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import reshape_persian, render_persian_text
from main import resource_path

CELL = 50
COLS = 15
ROWS = 11
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

BG_COLOR = (15, 15, 26)
WALL_COLOR = (30, 35, 50)
SOFT_WALL_COLOR = (150, 100, 50)
P1_COLOR = (0, 255, 255)
P2_COLOR = (255, 0, 100)

# ─── Generate a simple explosion sound using raw PCM ─────────────────────────
def _make_explosion_sound():
    """Generates a procedural boom sound and returns a pygame Sound object."""
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
        sample_rate = 22050
        duration = 0.45  # seconds
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            # Layered frequencies with exponential decay
            env = math.exp(-8 * t)
            wave_val = (
                math.sin(2 * math.pi * 60 * t) * 0.5 +
                math.sin(2 * math.pi * 120 * t) * 0.3 +
                random.uniform(-1, 1) * 0.4  # noise
            )
            s = int(wave_val * env * 32000)
            s = max(-32768, min(32767, s))
            samples.append(s)

        raw = struct.pack(f"<{n}h", *samples)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(raw)
        buf.seek(0)
        return pygame.mixer.Sound(buf)
    except Exception:
        return None


# ─── Data Classes ─────────────────────────────────────────────────────────────
class Bomb:
    def __init__(self, c, r, radius, owner):
        self.c = c
        self.r = r
        self.radius = radius
        self.owner = owner
        self.timer = pygame.time.get_ticks()

class Flame:
    def __init__(self, c, r):
        self.c = c
        self.r = r
        self.timer = pygame.time.get_ticks()

class Shockwave:
    """Visual shockwave ring emitted at explosion center."""
    def __init__(self, cx, cy):
        self.cx = cx
        self.cy = cy
        self.radius = 5
        self.max_radius = 80
        self.alpha = 255
        self.timer = pygame.time.get_ticks()

    @property
    def alive(self):
        return self.radius < self.max_radius

    def update(self):
        self.radius += 6
        self.alpha = max(0, int(255 * (1 - self.radius / self.max_radius)))


# ─── Player ───────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, c, r, color, is_bot):
        self.x = c * CELL + CELL / 2
        self.y = r * CELL + CELL / 2
        self.color = color
        self.is_bot = is_bot
        self.speed = 3
        self.max_bombs = 1
        self.bomb_radius = 1
        self.bombs = []
        self.is_dead = False

    def move(self, dx, dy, grid, bombs):
        if self.is_dead:
            return
        new_x = self.x + dx * self.speed
        new_y = self.y + dy * self.speed

        margin = CELL / 2 - 8
        rect = pygame.Rect(new_x - margin, new_y - margin, margin * 2, margin * 2)

        for r in range(ROWS):
            for c in range(COLS):
                if grid[r][c] in (1, 2):
                    wall_rect = pygame.Rect(c * CELL, r * CELL, CELL, CELL)
                    if rect.colliderect(wall_rect):
                        return

        for b in bombs:
            b_rect = pygame.Rect(b.c * CELL, b.r * CELL, CELL, CELL)
            if rect.colliderect(b_rect):
                old_rect = pygame.Rect(self.x - margin, self.y - margin, margin * 2, margin * 2)
                if not old_rect.colliderect(b_rect):
                    return

        self.x = new_x
        self.y = new_y

    def draw(self, screen, offset_x, offset_y):
        if self.is_dead:
            return
        cx = int(offset_x + self.x)
        cy = int(offset_y + self.y)

        # Body
        pygame.draw.rect(screen, (40, 40, 50), (cx - 12, cy - 5, 24, 18), border_radius=4)
        # Glow outline on body
        pygame.draw.rect(screen, self.color, (cx - 12, cy - 5, 24, 18), 1, border_radius=4)
        # Head
        pygame.draw.circle(screen, (200, 200, 220), (cx, cy - 12), 14)
        # Visor
        pygame.draw.rect(screen, (20, 20, 20), (cx - 10, cy - 18, 20, 8), border_radius=2)
        pygame.draw.rect(screen, self.color, (cx - 8, cy - 16, 16, 4), border_radius=2)
        # Antenna
        pygame.draw.line(screen, (150, 150, 150), (cx, cy - 26), (cx, cy - 34), 2)
        pygame.draw.circle(screen, self.color, (cx, cy - 36), 3)
        # Legs
        bounce = math.sin(pygame.time.get_ticks() / 100) * 3
        pygame.draw.rect(screen, (80, 80, 80), (cx - 8, cy + 13 - int(bounce), 6, 8), border_radius=2)
        pygame.draw.rect(screen, (80, 80, 80), (cx + 2, cy + 13 + int(bounce), 6, 8), border_radius=2)


# ─── Main Game Class ──────────────────────────────────────────────────────────
class Bomberman(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.start_x = (self.W - BOARD_W) // 2
        self.start_y = (self.H - BOARD_H) // 2 + 50

        self.font_lg = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 48)
        self.font_md = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)
        self.font_sm = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)

        self.is_sp = getattr(self.session, 'is_single_player', False)
        self.difficulty = getattr(self.session, 'bot_difficulty', 'medium')

        self.explosion_sound = _make_explosion_sound()

        self.state = "INSTRUCTIONS"
        self._init_game()
        pygame.display.set_caption("Bomberman - Cyberpunk Edition")

    # ── Map Generation ──
    def _init_game(self):
        self.grid = [[0] * COLS for _ in range(ROWS)]
        map_type = random.choice(["classic", "open", "tunnel", "boxy"])

        for r in range(ROWS):
            for c in range(COLS):
                if c == 0 or c == COLS - 1 or r == 0 or r == ROWS - 1:
                    self.grid[r][c] = 1
                else:
                    is_solid = False
                    if map_type == "classic":
                        is_solid = (c % 2 == 0 and r % 2 == 0)
                    elif map_type == "tunnel":
                        is_solid = (r % 2 == 0) and 2 < c < COLS - 3
                    elif map_type == "boxy":
                        is_solid = (c % 3 == 0 and r % 3 == 0)

                    if is_solid:
                        self.grid[r][c] = 1
                    else:
                        safe = [(1, 1), (1, 2), (2, 1),
                                (ROWS - 2, COLS - 2), (ROWS - 2, COLS - 3), (ROWS - 3, COLS - 2)]
                        if (r, c) not in safe:
                            density = 0.35 if map_type == "open" else 0.55
                            if random.random() < density:
                                self.grid[r][c] = 2

        self.p1 = Player(1, 1, P1_COLOR, False)
        self.p2 = Player(COLS - 2, ROWS - 2, P2_COLOR, self.is_sp)

        self.bombs = []
        self.flames = []
        self.shockwaves = []
        self.powerups = {}

        self.bot_timer = 0
        # After placing a bomb, bot needs to track the escape path
        self._bot_escape_path = []
        self._bot_escape_step_time = 0
        
        self.random_bomb_interval = 15000
        self.last_random_bomb_time = pygame.time.get_ticks()

    # ── Bomb Planting ──
    def plant_bomb(self, player):
        if player.is_dead:
            return
        if len(player.bombs) < player.max_bombs:
            bc = int(player.x // CELL)
            br = int(player.y // CELL)
            for b in self.bombs:
                if b.c == bc and b.r == br:
                    return
            nb = Bomb(bc, br, player.bomb_radius, player)
            self.bombs.append(nb)
            player.bombs.append(nb)
            return nb
        return None

    # ── Danger Map ──
    def get_danger_map(self, include_own_bomb=True):
        """Returns a 2D grid of booleans: True = dangerous cell."""
        danger = [[False] * COLS for _ in range(ROWS)]
        for b in self.bombs:
            danger[b.r][b.c] = True
            for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                for i in range(1, b.radius + 1):
                    nc, nr = b.c + d[0] * i, b.r + d[1] * i
                    if not (0 <= nr < ROWS and 0 <= nc < COLS):
                        break
                    if self.grid[nr][nc] == 1:
                        break
                    danger[nr][nc] = True
                    if self.grid[nr][nc] == 2:
                        break
        for f in self.flames:
            danger[f.r][f.c] = True
        return danger

    # ── BFS pathfinding ──
    def bfs_find(self, start_c, start_r, target_fn, danger_map=None, ignore_danger=False, max_depth=30):
        """
        BFS that returns the first move direction toward the target.
        target_fn(c, r) -> bool: True when the target is reached.
        """
        q = deque([(start_c, start_r, [])])
        visited = {(start_c, start_r)}
        while q:
            c, r, path = q.popleft()
            if len(path) > max_depth:
                break
            if target_fn(c, r):
                return path
            for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nc, nr = c + d[0], r + d[1]
                if not (0 <= nr < ROWS and 0 <= nc < COLS):
                    continue
                if self.grid[nr][nc] != 0:
                    continue
                if (nc, nr) in visited:
                    continue
                is_bomb_cell = any(b.c == nc and b.r == nr for b in self.bombs)
                if is_bomb_cell:
                    continue
                is_flame_cell = any(f.c == nc and f.r == nr for f in self.flames)
                if is_flame_cell:
                    continue
                if danger_map is not None and not ignore_danger and danger_map[nr][nc]:
                    continue
                visited.add((nc, nr))
                q.append((nc, nr, path + [d]))
        return []

    # ── Bot Logic ──
    def bot_ai(self):
        """
        Relentless Hunt AI:
        1. Survival: Flee immediate danger.
        2. Opportunistic Bomb: If aligned with player or near player, drop bomb (if escape route exists).
        3. Powerups: Grab them if safe.
        4. Hunt: Pathfind directly to player.
        5. Break Walls: If player unreachable, find nearest soft wall and break it.
        6. Wander: Safely move around if stuck or waiting for own bomb.
        """
        now = pygame.time.get_ticks()
        bot_intervals = {"low": 60, "medium": 30, "hard": 20}
        if now - self.bot_timer < bot_intervals.get(self.difficulty, 30):
            return
        self.bot_timer = now

        bc, br = int(self.p2.x // CELL), int(self.p2.y // CELL)
        p1_c, p1_r = int(self.p1.x // CELL), int(self.p1.y // CELL)
        danger = self.get_danger_map()

        def can_escape_after_bomb():
            if len(self.p2.bombs) >= self.p2.max_bombs: return False
            sim = Bomb(bc, br, self.p2.bomb_radius, self.p2)
            self.bombs.append(sim)
            fd = self.get_danger_map()
            self.bombs.remove(sim)
            return bool(self.bfs_find(bc, br, lambda c, r: not fd[r][c], danger_map=fd, ignore_danger=True, max_depth=15))

        def move_towards(target_fn, ignore_danger=False):
            path = self.bfs_find(bc, br, target_fn, danger_map=danger, ignore_danger=ignore_danger)
            if path:
                dx, dy = path[0][0], path[0][1]
                # Auto-center bot on the perpendicular axis
                center_x = bc * CELL + CELL / 2
                center_y = br * CELL + CELL / 2
                if dx != 0:
                    if self.p2.y < center_y - 2: self.p2.y += min(self.p2.speed, center_y - self.p2.y)
                    elif self.p2.y > center_y + 2: self.p2.y -= min(self.p2.speed, self.p2.y - center_y)
                    else: self.p2.y = center_y
                if dy != 0:
                    if self.p2.x < center_x - 2: self.p2.x += min(self.p2.speed, center_x - self.p2.x)
                    elif self.p2.x > center_x + 2: self.p2.x -= min(self.p2.speed, self.p2.x - center_x)
                    else: self.p2.x = center_x
                
                self.p2.move(dx, dy, self.grid, self.bombs)
                return True
            return False

        # 1. SURVIVAL
        if danger[br][bc]:
            if not move_towards(lambda c, r: not danger[r][c], ignore_danger=True):
                # Desperate move
                dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
                random.shuffle(dirs)
                for d in dirs:
                    nc, nr = bc + d[0], br + d[1]
                    if (0 <= nr < ROWS and 0 <= nc < COLS and self.grid[nr][nc] == 0 
                        and not any(b.c == nc and b.r == nr for b in self.bombs)):
                        if move_towards(lambda c, r: c == nc and r == nr, ignore_danger=True):
                            break
            return

        # Easy mode logic
        if self.difficulty == "low":
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(dirs)
            for d in dirs:
                nc, nr = bc + d[0], br + d[1]
                if (0 <= nr < ROWS and 0 <= nc < COLS and self.grid[nr][nc] == 0
                        and not danger[nr][nc] and not any(b.c == nc and b.r == nr for b in self.bombs)):
                    if move_towards(lambda c, r: c == nc and r == nr):
                        break
            if random.random() < 0.05 and can_escape_after_bomb():
                self.plant_bomb(self.p2)
            return

        # 2. OPPORTUNISTIC BOMB
        aligned = False
        if bc == p1_c:
            aligned = abs(br - p1_r) <= self.p2.bomb_radius and all(self.grid[r][bc] != 1 for r in range(min(br, p1_r)+1, max(br, p1_r)))
        elif br == p1_r:
            aligned = abs(bc - p1_c) <= self.p2.bomb_radius and all(self.grid[br][c] != 1 for c in range(min(bc, p1_c)+1, max(bc, p1_c)))
        
        dist_to_player = abs(bc - p1_c) + abs(br - p1_r)
        
        if (aligned or dist_to_player <= 2) and len(self.p2.bombs) < self.p2.max_bombs:
            if can_escape_after_bomb():
                self.plant_bomb(self.p2)
                return

        # 3. COLLECT POWERUPS
        if move_towards(lambda c, r: (c, r) in self.powerups):
            return

        # 4. HUNT PLAYER
        if move_towards(lambda c, r: c == p1_c and r == p1_r):
            return

        # 5. BREAK WALLS
        adj_soft = any(0 <= br+d[1] < ROWS and 0 <= bc+d[0] < COLS and self.grid[br+d[1]][bc+d[0]] == 2 for d in [(1,0),(-1,0),(0,1),(0,-1)])
        if adj_soft and len(self.p2.bombs) < self.p2.max_bombs:
            if can_escape_after_bomb():
                self.plant_bomb(self.p2)
                return
        
        if move_towards(lambda c, r: any(0 <= r+d[1] < ROWS and 0 <= c+d[0] < COLS and self.grid[r+d[1]][c+d[0]] == 2 for d in [(1,0),(-1,0),(0,1),(0,-1)])):
            return

        # 6. WANDER SAFELY
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        random.shuffle(dirs)
        for d in dirs:
            nc, nr = bc + d[0], br + d[1]
            if (0 <= nr < ROWS and 0 <= nc < COLS and self.grid[nr][nc] == 0
                    and not danger[nr][nc] and not any(b.c == nc and b.r == nr for b in self.bombs)):
                if move_towards(lambda c, r: c == nc and r == nr):
                    break

    # ── Events ──
    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False

                if self.state == "INSTRUCTIONS":
                    self.state = "PLAYING"
                elif self.state in ["WIN_P1", "WIN_P2", "DRAW"]:
                    if ev.key == pygame.K_r:
                        self.state = "PLAYING"
                        self._init_game()
                elif self.state == "PLAYING":
                    if ev.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                        self.plant_bomb(self.p1)
                    if not self.is_sp and ev.key == pygame.K_SPACE:
                        self.plant_bomb(self.p2)

    # ── Update ──
    def update(self):
        now = pygame.time.get_ticks()

        # Always clean up visual effects regardless of game state
        for f in self.flames[:]:
            if now - f.timer > 600:
                self.flames.remove(f)
        for sw in self.shockwaves[:]:
            sw.update()
            if not sw.alive:
                self.shockwaves.remove(sw)

        if self.state != "PLAYING":
            return

        # Random Bomb Spawner
        if now - self.last_random_bomb_time >= self.random_bomb_interval:
            self.last_random_bomb_time = now
            self.random_bomb_interval = max(1000, self.random_bomb_interval - 1000)
            
            empty_cells = []
            for r in range(1, ROWS - 1):
                for c in range(1, COLS - 1):
                    if self.grid[r][c] == 0:
                        has_bomb = any(b.r == r and b.c == c for b in self.bombs)
                        has_flame = any(f.r == r and f.c == c for f in self.flames)
                        if not has_bomb and not has_flame:
                            empty_cells.append((c, r))
                            
            if empty_cells:
                c, r = random.choice(empty_cells)
                self.bombs.append(Bomb(c, r, radius=2, owner=None))

        # Player 1 movement
        keys = pygame.key.get_pressed()
        if not self.p1.is_dead:
            dx, dy = 0, 0
            if keys[pygame.K_UP]:    dy = -1
            if keys[pygame.K_DOWN]:  dy = 1
            if keys[pygame.K_LEFT]:  dx = -1
            if keys[pygame.K_RIGHT]: dx = 1
            if dx != 0 and dy != 0:
                dx = 0  # Prefer vertical
            if dx != 0 or dy != 0:
                self.p1.move(dx, dy, self.grid, self.bombs)

        # Player 2 movement (2P or bot)
        if not self.p2.is_dead:
            if self.is_sp:
                self.bot_ai()
            else:
                dx, dy = 0, 0
                if keys[pygame.K_w]: dy = -1
                if keys[pygame.K_s]: dy = 1
                if keys[pygame.K_a]: dx = -1
                if keys[pygame.K_d]: dx = 1
                if dx != 0 and dy != 0:
                    dx = 0
                if dx != 0 or dy != 0:
                    self.p2.move(dx, dy, self.grid, self.bombs)

        # Bomb explosion
        for b in self.bombs[:]:
            if now - b.timer > 3000:
                self.bombs.remove(b)
                if b.owner and b in b.owner.bombs:
                    b.owner.bombs.remove(b)

                # Play sound
                if self.explosion_sound:
                    try:
                        self.explosion_sound.play()
                    except Exception:
                        pass

                # Add shockwave at explosion center
                sx = self.start_x + b.c * CELL + CELL // 2
                sy = self.start_y + b.r * CELL + CELL // 2
                self.shockwaves.append(Shockwave(sx, sy))

                # Spawn flames
                self.flames.append(Flame(b.c, b.r))
                for d in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    for i in range(1, b.radius + 1):
                        nc, nr = b.c + d[0] * i, b.r + d[1] * i
                        if not (0 <= nr < ROWS and 0 <= nc < COLS):
                            break
                        if self.grid[nr][nc] == 1:
                            break
                        elif self.grid[nr][nc] == 2:
                            self.grid[nr][nc] = 0
                            self.flames.append(Flame(nc, nr))
                            if random.random() < 0.2:
                                self.powerups[(nc, nr)] = random.choice(["bomb", "flame", "speed"])
                            break
                        else:
                            self.flames.append(Flame(nc, nr))



        # Powerup pickup
        for p in [self.p1, self.p2]:
            if p.is_dead:
                continue
            pc, pr = int(p.x // CELL), int(p.y // CELL)
            if (pc, pr) in self.powerups:
                ptype = self.powerups.pop((pc, pr))
                if ptype == "bomb":  p.max_bombs += 1
                elif ptype == "flame": p.bomb_radius += 1
                elif ptype == "speed": p.speed = min(p.speed + 1, 6)

        # Kill check
        for p in [self.p1, self.p2]:
            if p.is_dead:
                continue
            pc, pr = int(p.x // CELL), int(p.y // CELL)
            for f in self.flames:
                if f.c == pc and f.r == pr:
                    p.is_dead = True

        # Win check
        if self.p1.is_dead or self.p2.is_dead:
            if self.p1.is_dead and self.p2.is_dead:
                self.state = "DRAW"
            elif self.p2.is_dead:
                self.state = "WIN_P1"
                self.session.scores["player1"] += 1
            elif self.p1.is_dead:
                self.state = "WIN_P2"
                self.session.scores["player2"] += 1

    # ── Draw Helpers ──
    def draw_instructions(self):
        ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 230))
        self.screen.blit(ov, (0, 0))

        title = self.font_lg.render("HOW TO PLAY", True, (0, 240, 255))
        self.screen.blit(title, (self.W // 2 - title.get_width() // 2, self.H // 2 - 160))

        p1_name = reshape_persian(self.session.player1_name)
        p1_surf = render_persian_text(self.font_md, f"{reshape_persian(p1_name)} Controls:", P1_COLOR)
        self.screen.blit(p1_surf, (self.W // 2 - 300, self.H // 2 - 60))
        p1_ctrl = self.font_sm.render("Move: Arrow Keys  |  Bomb: CTRL", True, (200, 200, 200))
        self.screen.blit(p1_ctrl, (self.W // 2 - 300, self.H // 2))

        p2_name = reshape_persian(self.session.player2_name)
        p2_surf = render_persian_text(self.font_md, f"{reshape_persian(p2_name)} Controls:", P2_COLOR)
        self.screen.blit(p2_surf, (self.W // 2 + 50, self.H // 2 - 60))
        if self.is_sp:
            p2_ctrl = self.font_sm.render("Bot is playing", True, (150, 150, 150))
        else:
            p2_ctrl = self.font_sm.render("Move: W A S D  |  Bomb: SPACE", True, (200, 200, 200))
        self.screen.blit(p2_ctrl, (self.W // 2 + 50, self.H // 2))

        st = self.font_md.render("Press ANY KEY to Start", True, (255, 255, 0))
        self.screen.blit(st, (self.W // 2 - st.get_width() // 2, self.H // 2 + 130))

    # ── Main Draw ──
    def draw(self):
        self.screen.fill(BG_COLOR)

        p1_name = reshape_persian(self.session.player1_name)
        p2_name = reshape_persian(self.session.player2_name)

        t1 = render_persian_text(self.font_md, f"{reshape_persian(p1_name)}: {self.session.scores['player1']}", P1_COLOR)
        self.screen.blit(t1, (50, 50))
        t2 = render_persian_text(self.font_md, f"{reshape_persian(p2_name)}: {self.session.scores['player2']}", P2_COLOR)
        t2_x = self.W - t2.get_width() - 50
        self.screen.blit(t2, (t2_x, 50))

        # Board floor
        pygame.draw.rect(self.screen, (20, 20, 30), (self.start_x, self.start_y, BOARD_W, BOARD_H))

        # Tiles
        for r in range(ROWS):
            for c in range(COLS):
                rx = self.start_x + c * CELL
                ry = self.start_y + r * CELL
                if self.grid[r][c] == 1:
                    pygame.draw.rect(self.screen, WALL_COLOR, (rx, ry, CELL, CELL))
                    pygame.draw.rect(self.screen, (60, 65, 80), (rx, ry, CELL, 5))
                    pygame.draw.rect(self.screen, (15, 20, 30), (rx, ry + CELL - 5, CELL, 5))
                    pygame.draw.rect(self.screen, (20, 25, 40), (rx, ry, CELL, CELL), 2)
                elif self.grid[r][c] == 2:
                    pygame.draw.rect(self.screen, SOFT_WALL_COLOR, (rx + 2, ry + 2, CELL - 4, CELL - 4))
                    pygame.draw.line(self.screen, (100, 50, 20), (rx + 2, ry + 2), (rx + CELL - 2, ry + CELL - 2), 2)
                    pygame.draw.line(self.screen, (100, 50, 20), (rx + CELL - 2, ry + 2), (rx + 2, ry + CELL - 2), 2)
                    pygame.draw.rect(self.screen, (200, 120, 50), (rx + 2, ry + 2, CELL - 4, CELL - 4), 2)

                if (c, r) in self.powerups:
                    pt = self.powerups[(c, r)]
                    color = {"bomb": (0, 0, 0), "flame": (255, 0, 0), "speed": (0, 0, 255)}.get(pt, (255, 255, 255))
                    pygame.draw.circle(self.screen, (255, 255, 255), (rx + CELL // 2, ry + CELL // 2), CELL // 2 - 5)
                    pygame.draw.circle(self.screen, color, (rx + CELL // 2, ry + CELL // 2), CELL // 2 - 10)

        # Flames
        now = pygame.time.get_ticks()
        for f in self.flames:
            rx = self.start_x + f.c * CELL
            ry = self.start_y + f.r * CELL
            cx = rx + CELL // 2
            cy = ry + CELL // 2
            age = now - f.timer          # 0..600ms
            scale = max(0.0, 1.0 - age / 1200.0)  # shrinks over time, clamped
            s = int(22 * scale)
            if s <= 1:
                continue
            outer  = [(cx, cy - s), (cx + int(s*0.55), cy - int(s*0.55)), (cx + s, cy),
                      (cx + int(s*0.55), cy + int(s*0.55)), (cx, cy + s),
                      (cx - int(s*0.55), cy + int(s*0.55)), (cx - s, cy), (cx - int(s*0.55), cy - int(s*0.55))]
            ms = max(2, int(s * 0.7))
            mid    = [(cx, cy - ms), (cx + int(ms*0.55), cy - int(ms*0.55)), (cx + ms, cy),
                      (cx + int(ms*0.55), cy + int(ms*0.55)), (cx, cy + ms),
                      (cx - int(ms*0.55), cy + int(ms*0.55)), (cx - ms, cy), (cx - int(ms*0.55), cy - int(ms*0.55))]
            ins = max(1, int(s * 0.4))
            inner  = [(cx, cy - ins), (cx + int(ins*0.55), cy - int(ins*0.55)), (cx + ins, cy),
                      (cx + int(ins*0.55), cy + int(ins*0.55)), (cx, cy + ins),
                      (cx - int(ins*0.55), cy + int(ins*0.55)), (cx - ins, cy), (cx - int(ins*0.55), cy - int(ins*0.55))]
            if len(outer) >= 3:
                pygame.draw.polygon(self.screen, (255, 50, 0), outer)
            if len(mid) >= 3:
                pygame.draw.polygon(self.screen, (255, 200, 0), mid)
            if len(inner) >= 3:
                pygame.draw.polygon(self.screen, (255, 255, 255), inner)

        # Bombs
        for b in self.bombs:
            rx = self.start_x + b.c * CELL
            ry = self.start_y + b.r * CELL
            cx = rx + CELL // 2
            cy = ry + CELL // 2
            fuse_ratio = (pygame.time.get_ticks() - b.timer) / 3000.0
            # Pulse faster as timer runs out
            pulse = math.sin(pygame.time.get_ticks() / (200 - 150 * fuse_ratio)) * 3
            pygame.draw.circle(self.screen, (30, 30, 30), (cx, cy + 4), int(14 + pulse))
            pygame.draw.circle(self.screen, (70, 70, 70), (cx - 4, cy - 2), 5)
            # Fuse arc
            pygame.draw.arc(self.screen, (150, 150, 150), (cx - 5, cy - 18, 15, 15), 0, math.pi, 2)
            # Spark
            spark = random.randint(2, 6)
            spark_color = (255, 255, 0) if fuse_ratio < 0.7 else (255, 80, 0)
            pygame.draw.circle(self.screen, spark_color, (cx + 10, cy - 14), spark)
            pygame.draw.circle(self.screen, (255, 100, 0), (cx + 10, cy - 14), spark + 3, 2)

        # Shockwaves
        for sw in self.shockwaves:
            if sw.alpha > 0 and sw.radius > 0:
                surf = pygame.Surface((sw.radius * 2 + 4, sw.radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 200, 50, sw.alpha), (sw.radius + 2, sw.radius + 2), sw.radius, 3)
                self.screen.blit(surf, (sw.cx - sw.radius - 2, sw.cy - sw.radius - 2))

        # Players
        self.p1.draw(self.screen, self.start_x, self.start_y)
        self.p2.draw(self.screen, self.start_x, self.start_y)

        # Overlays
        if self.state == "INSTRUCTIONS":
            self.draw_instructions()
        elif self.state in ["WIN_P1", "WIN_P2", "DRAW"]:
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 200))
            self.screen.blit(ov, (0, 0))

            if self.state == "WIN_P1":   txt = f"{reshape_persian(p1_name)} WINS!"
            elif self.state == "WIN_P2": txt = f"{reshape_persian(p2_name)} WINS!"
            else:                        txt = "DRAW!"

            wt = render_persian_text(self.font_lg, txt, (255, 255, 255))
            self.screen.blit(wt, (self.W // 2 - wt.get_width() // 2, self.H // 2 - 50))
            st = self.font_md.render("Press R to Restart  |  ESC to Quit", True, (150, 150, 150))
            self.screen.blit(st, (self.W // 2 - st.get_width() // 2, self.H // 2 + 20))
