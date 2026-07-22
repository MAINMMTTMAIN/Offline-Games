import sys
import os
import pygame
import random
import math
from collections import deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import reshape_persian, render_persian_text
from main import resource_path
from .maze import MAP

ROWS = len(MAP)
COLS = len(MAP[0])
CELL = 24
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
NONE = (0, 0)

class Entity:
    def __init__(self, x, y, color):
        self.start_x = x
        self.start_y = y
        self.x = x
        self.y = y
        self.color = color
        self.dir = NONE
        self.next_dir = NONE
        self.speed = 3
        
    def reset_pos(self):
        self.x = self.start_x
        self.y = self.start_y
        self.dir = NONE
        self.next_dir = NONE

    def center_dist(self):
        cx = (self.x % CELL) - CELL/2
        cy = (self.y % CELL) - CELL/2
        return cx, cy

    def snap_to_center(self):
        self.x = int(self.x // CELL) * CELL + CELL / 2
        self.y = int(self.y // CELL) * CELL + CELL / 2

class PacmanEntity(Entity):
    def __init__(self, x, y, color, controls, is_bot):
        super().__init__(x, y, color)
        self.controls = controls
        self.is_bot = is_bot
        self.score = 0
        self.lives = 3
        self.speed = 2
        self.anim_frame = 0
        self.mouth_open = True
        self.is_dead = False

class GhostEntity(Entity):
    def __init__(self, x, y, color, name):
        super().__init__(x, y, color)
        self.name = name
        self.speed = 1.5
        self.mode = "scatter" # scatter, chase, frightened, dead
        self.frightened_timer = 0
        self.scatter_target = (0, 0)
        if name == "blinky": self.scatter_target = (COLS-2, 1)
        elif name == "pinky": self.scatter_target = (1, 1)
        elif name == "inky": self.scatter_target = (COLS-2, ROWS-2)
        elif name == "clyde": self.scatter_target = (1, ROWS-2)

class PacmanDuel(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.W = screen.get_width()
        self.H = screen.get_height()
        
        self.font_lg = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 48)
        self.font_md = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 24)
        self.font_sm = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        
        self.bx = (self.W - BOARD_W) // 2
        self.by = (self.H - BOARD_H) // 2 + 20
        
        self.level = 1
        self._init_sounds()
        self._init_game(full_reset=True)
        pygame.display.set_caption("Two-Player Pac-Man")

    def _init_sounds(self):
        try:
            pygame.mixer.init()
            self.snd_chomp0 = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/eat_dot_0.wav"))
            self.snd_chomp1 = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/eat_dot_1.wav"))
            self.snd_eat_ghost = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/eat_ghost.wav"))
            self.snd_power = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/fright.wav"))
            self.snd_death = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/death_0.wav"))
            self.snd_start = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/start.wav"))
            self.snd_fruit = pygame.mixer.Sound(resource_path("games/pacman_duel/pacman_sounds/eat_fruit.wav"))
            self.chomp_toggle = 0
        except:
            self.snd_chomp0 = self.snd_chomp1 = self.snd_eat_ghost = self.snd_power = self.snd_death = self.snd_start = self.snd_fruit = None
            self.chomp_toggle = 0

    def _play_sound(self, snd):
        if snd:
            try: snd.play()
            except: pass
        
    def _init_game(self, full_reset=False):
        self.grid = []
        self.pellets = set()
        self.power_pellets = set()
        
        p1_start = p2_start = (0, 0)
        ghost_starts = []
        
        for r in range(ROWS):
            row = []
            for c in range(COLS):
                char = MAP[r][c]
                if char == 'W': row.append(1)
                elif char == '-': row.append(2) # Ghost gate
                else:
                    row.append(0)
                    if char == '.': self.pellets.add((c, r))
                    elif char == 'o': self.power_pellets.add((c, r))
            self.grid.append(row)
            
        # Spawn points (approximate from standard maze)
        p1_start = (13 * CELL + CELL/2, 23 * CELL + CELL/2)
        p2_start = (14 * CELL + CELL/2, 23 * CELL + CELL/2)
        ghost_starts = [
            (13 * CELL + CELL/2, 11 * CELL + CELL/2), # Blinky (outside)
            (13 * CELL + CELL/2, 14 * CELL + CELL/2), # Pinky (inside)
            (11 * CELL + CELL/2, 14 * CELL + CELL/2), # Inky
            (15 * CELL + CELL/2, 14 * CELL + CELL/2)  # Clyde
        ]
        
        is_sp = getattr(self.session, 'is_single_player', False)
        self.difficulty = getattr(self.session, 'bot_difficulty', 'medium')
        
        if full_reset:
            self.p1 = PacmanEntity(p1_start[0], p1_start[1], (255, 255, 0), "arrows", False)
            self.p2 = PacmanEntity(p2_start[0], p2_start[1], (255, 150, 0), "wasd", is_sp)
            self.level = 1
            self._play_sound(getattr(self, 'snd_start', None))
        else:
            self.p1.start_x, self.p1.start_y = p1_start[0], p1_start[1]
            self.p2.start_x, self.p2.start_y = p2_start[0], p2_start[1]
            self.p1.reset_pos()
            self.p2.reset_pos()
            
        ghost_speed = 1.5 + (self.level - 1) * 0.25
        self.ghosts = [
            GhostEntity(ghost_starts[0][0], ghost_starts[0][1], (255, 0, 0), "blinky"),
            GhostEntity(ghost_starts[1][0], ghost_starts[1][1], (255, 180, 255), "pinky"),
            GhostEntity(ghost_starts[2][0], ghost_starts[2][1], (0, 255, 255), "inky"),
            GhostEntity(ghost_starts[3][0], ghost_starts[3][1], (255, 180, 80), "clyde")
        ]
        
        for g in self.ghosts:
            g.dir = UP
            g.speed = ghost_speed
        
        self.state = "READY"
        self.timer = pygame.time.get_ticks()
        self.global_mode = "scatter"
        self.mode_timer = pygame.time.get_ticks()
        self.scatter_duration = max(1000, 7000 - (self.level - 1) * 1000)
        self.chase_duration = 20000 + (self.level - 1) * 5000
        self.game_over = False
        self.fruit = None
        self.fruit_spawn_time = pygame.time.get_ticks() + random.randint(10000, 20000)
        
    def _is_wall(self, c, r, is_ghost=False):
        if c < 0 or c >= COLS or r < 0 or r >= ROWS:
            return False # Tunnels
        if self.grid[r][c] == 1: return True
        if self.grid[r][c] == 2 and not is_ghost: return True
        return False
        
    def _move_entity(self, ent, is_ghost=False):
        # Apply requested direction if valid
        if ent.next_dir != NONE:
            cx, cy = ent.center_dist()
            if abs(cx) <= ent.speed and abs(cy) <= ent.speed:
                # Check if next_dir is open
                curr_c = int(ent.x // CELL)
                curr_r = int(ent.y // CELL)
                next_c = curr_c + ent.next_dir[0]
                next_r = curr_r + ent.next_dir[1]
                
                # Handling tunnel wrap for check
                if next_c < 0: next_c = COLS - 1
                if next_c >= COLS: next_c = 0
                
                if not self._is_wall(next_c, next_r, is_ghost):
                    if ent.dir != ent.next_dir:
                        ent.snap_to_center()
                        ent.dir = ent.next_dir
                    ent.next_dir = NONE
        
        if ent.dir != NONE:
            # Check collision forward
            curr_c = int(ent.x // CELL)
            curr_r = int(ent.y // CELL)
            
            # Predict
            pred_x = ent.x + ent.dir[0] * ent.speed
            pred_y = ent.y + ent.dir[1] * ent.speed
            
            # Use a slightly smaller bounding box for wall collisions
            marg = CELL/2 - 2
            edge_c = int((pred_x + ent.dir[0]*marg) // CELL)
            edge_r = int((pred_y + ent.dir[1]*marg) // CELL)
            
            # Tunnel wrap
            if edge_c < 0:
                ent.x = BOARD_W
                return
            if edge_c >= COLS:
                ent.x = 0
                return
                
            if not self._is_wall(edge_c, edge_r, is_ghost):
                ent.x += ent.dir[0] * ent.speed
                ent.y += ent.dir[1] * ent.speed
            else:
                ent.snap_to_center()
                ent.dir = NONE

    def _get_valid_ghost_dirs(self, ghost):
        curr_c = int(ghost.x // CELL)
        curr_r = int(ghost.y // CELL)
        dirs = []
        for d in [UP, LEFT, DOWN, RIGHT]:
            if d == (-ghost.dir[0], -ghost.dir[1]) and ghost.dir != NONE and ghost.mode != "frightened":
                continue # Ghosts can't reverse unless frightened
            
            nc = curr_c + d[0]
            nr = curr_r + d[1]
            if nc < 0 or nc >= COLS:
                dirs.append(d)
                continue
            if not self._is_wall(nc, nr, True):
                dirs.append(d)
        return dirs

    def _update_ghost_ai(self, ghost):
        cx, cy = ghost.center_dist()
        if abs(cx) > ghost.speed or abs(cy) > ghost.speed:
            return # Only decide at intersections
            
        curr_c = int(ghost.x // CELL)
        curr_r = int(ghost.y // CELL)
        if ghost.dir != NONE and getattr(ghost, 'last_decision_tile', None) == (curr_c, curr_r):
            return
            
        valid_dirs = self._get_valid_ghost_dirs(ghost)
        if not valid_dirs:
            return
            
        if len(valid_dirs) == 1:
            ghost.next_dir = valid_dirs[0]
            ghost.last_decision_tile = (curr_c, curr_r)
            return

        if ghost.mode == "frightened":
            closest_p = None
            min_dist = 999999
            for p in [self.p1, self.p2]:
                if not p.is_dead:
                    d = (p.x - ghost.x)**2 + (p.y - ghost.y)**2
                    if d < min_dist:
                        min_dist = d
                        closest_p = p
            
            if closest_p:
                pc, pr = int(closest_p.x // CELL), int(closest_p.y // CELL)
                best_dir = valid_dirs[0]
                max_d = -1
                for d in valid_dirs:
                    nc = curr_c + d[0]
                    nr = curr_r + d[1]
                    dist = (nc - pc)**2 + (nr - pr)**2
                    if dist > max_d:
                        max_d = dist
                        best_dir = d
                ghost.next_dir = best_dir
            else:
                ghost.next_dir = random.choice(valid_dirs)
                
            ghost.last_decision_tile = (curr_c, curr_r)
            return

        if ghost.mode == "dead":
            target = (13, 11) # Ghost house
            if curr_c == 13 and curr_r in (11,12,13,14):
                ghost.mode = "scatter"
                ghost.speed = 1.5 + (self.level - 1) * 0.25
                ghost.last_decision_tile = None
        else:
            if self.global_mode == "scatter":
                target = ghost.scatter_target
            else:
                # Find closest pacman
                closest_p = None
                min_dist = 999999
                for p in [self.p1, self.p2]:
                    if not p.is_dead:
                        d = (p.x - ghost.x)**2 + (p.y - ghost.y)**2
                        if d < min_dist:
                            min_dist = d
                            closest_p = p
                            
                if not closest_p:
                    target = ghost.scatter_target
                else:
                    pc = int(closest_p.x // CELL)
                    pr = int(closest_p.y // CELL)
                    if ghost.name == "blinky":
                        target = (pc, pr)
                    elif ghost.name == "pinky":
                        lead = min(8, 2 + self.level)
                        target = (pc + closest_p.dir[0]*lead, pr + closest_p.dir[1]*lead)
                    elif ghost.name == "inky":
                        blinky = next((g for g in self.ghosts if g.name == "blinky"), None)
                        if blinky:
                            bc = blinky.x / CELL
                            br = blinky.y / CELL
                            lead = min(4, self.level)
                            pivot_c = pc + closest_p.dir[0]*lead
                            pivot_r = pr + closest_p.dir[1]*lead
                            target = (pivot_c + (pivot_c - bc), pivot_r + (pivot_r - br))
                        else:
                            target = (pc, pr)
                    elif ghost.name == "clyde":
                        rad = max(2, 8 - self.level)
                        if min_dist > (rad*CELL)**2: target = (pc, pr)
                        else: target = ghost.scatter_target

        best_dir = valid_dirs[0]
        min_d = 999999
        for d in valid_dirs:
            nc = curr_c + d[0]
            nr = curr_r + d[1]
            dist = (nc - target[0])**2 + (nr - target[1])**2
            if dist < min_d:
                min_d = dist
                best_dir = d
                
        ghost.next_dir = best_dir
        ghost.last_decision_tile = (curr_c, curr_r)

    def _update_bot_ai(self, bot):
        cx, cy = bot.center_dist()
        if abs(cx) > bot.speed or abs(cy) > bot.speed:
            return
            
        curr_c = int(bot.x // CELL)
        curr_r = int(bot.y // CELL)
        if bot.dir != NONE and getattr(bot, 'last_decision_tile', None) == (curr_c, curr_r):
            return
        
        valid_dirs = []
        for d in [UP, DOWN, LEFT, RIGHT]:
            nc, nr = curr_c + d[0], curr_r + d[1]
            if nc < 0 or nc >= COLS: valid_dirs.append(d); continue
            if not self._is_wall(nc, nr, False): valid_dirs.append(d)
            
        if not valid_dirs: return
        
        if self.difficulty == "low":
            if bot.dir not in valid_dirs or random.random() < 0.2:
                bot.next_dir = random.choice(valid_dirs)
        elif self.difficulty == "medium":
            best_dir = random.choice(valid_dirs)
            min_dist = 99999
            for p in list(self.pellets) + list(self.power_pellets):
                d = (p[0] - curr_c)**2 + (p[1] - curr_r)**2
                if d < min_dist:
                    min_dist = d
                    best_c, best_r = p
            for d in valid_dirs:
                nc, nr = curr_c + d[0], curr_r + d[1]
                dist = (nc - best_c)**2 + (nr - best_r)**2
                if dist < min_dist:
                    min_dist = dist
                    best_dir = d
            bot.next_dir = best_dir
        else:
            # Hard: BFS avoiding ghosts dynamically
            ghost_q = deque()
            ghost_dist = {}
            for g in self.ghosts:
                if g.mode in ("scatter", "chase"):
                    gc, gr = int(g.x//CELL), int(g.y//CELL)
                    ghost_q.append((gc, gr, 0))
                    ghost_dist[(gc, gr)] = 0
                    if g.dir != NONE:
                        ngc, ngr = gc + g.dir[0], gr + g.dir[1]
                        if 0 <= ngc < COLS and 0 <= ngr < ROWS:
                            ghost_q.append((ngc, ngr, 1))
                            ghost_dist[(ngc, ngr)] = 1
                            
            while ghost_q:
                c, r, dist = ghost_q.popleft()
                if dist >= 8: continue
                for d in [UP, DOWN, LEFT, RIGHT]:
                    nc, nr = c + d[0], r + d[1]
                    if 0 <= nc < COLS and 0 <= nr < ROWS and not self._is_wall(nc, nr, False):
                        if (nc, nr) not in ghost_dist or ghost_dist[(nc, nr)] > dist + 1:
                            ghost_dist[(nc, nr)] = dist + 1
                            ghost_q.append((nc, nr, dist + 1))
                            
            q = deque([(curr_c, curr_r, [], 0)])
            visited = set([(curr_c, curr_r)])
            found_path = []
            longest_safe_path = []
            
            while q:
                c, r, path, depth = q.popleft()
                
                if (c, r) in self.pellets or (c, r) in self.power_pellets:
                    found_path = path
                    break
                    
                if len(path) > len(longest_safe_path):
                    longest_safe_path = path
                    
                for d in [UP, DOWN, LEFT, RIGHT]:
                    nc, nr = c + d[0], r + d[1]
                    if 0 <= nc < COLS and 0 <= nr < ROWS and not self._is_wall(nc, nr, False):
                        if (nc, nr) not in visited:
                            g_d = ghost_dist.get((nc, nr), 999)
                            if g_d > depth + 1:
                                visited.add((nc, nr))
                                q.append((nc, nr, path + [d], depth + 1))
                                
            if found_path:
                bot.next_dir = found_path[0]
            elif longest_safe_path:
                bot.next_dir = longest_safe_path[0]
            else:
                bot.next_dir = random.choice(valid_dirs)
        bot.last_decision_tile = (curr_c, curr_r)

    def update(self):
        now = pygame.time.get_ticks()
        
        if self.state == "READY":
            if now - self.timer > 4500:
                self.state = "PLAY"
                self.mode_timer = now
            return
            
        if self.state == "DEAD_PAUSE":
            if now - self.timer > 1500:
                if self.p1.is_dead and self.p2.is_dead:
                    self.state = "GAME_OVER"
                else:
                    self.state = "READY"
                    self.timer = now
                    for p in [self.p1, self.p2]:
                        if not p.is_dead: p.reset_pos()
                    for g in self.ghosts:
                        g.reset_pos()
                        g.dir = UP
            return
            
        if self.state == "LEVEL_COMPLETE":
            if now - self.timer > 2000:
                self.level += 1
                self._init_game(full_reset=False)
            return
            
        if self.state == "GAME_OVER":
            return

        # Fruit logic
        if getattr(self, 'fruit', None):
            if now > self.fruit[3]:
                self.fruit = None
                self.fruit_spawn_time = now + random.randint(15000, 30000)
        else:
            if now > getattr(self, 'fruit_spawn_time', 0):
                spawn_c, spawn_r = 13, 17
                if not self._is_wall(spawn_c, spawn_r):
                    ftype = random.choice(["cherry", "strawberry", "orange", "apple", "melon"])
                    self.fruit = (spawn_c, spawn_r, ftype, now + 10000)

        # Mode switching
        if any(g.mode == "frightened" for g in self.ghosts):
            pass # Keep mode timer paused essentially
        else:
            elapsed = now - self.mode_timer
            if self.global_mode == "scatter" and elapsed > self.scatter_duration:
                self.global_mode = "chase"
                self.mode_timer = now
                for g in self.ghosts:
                    if g.mode != "dead": g.dir = (-g.dir[0], -g.dir[1])
            elif self.global_mode == "chase" and elapsed > self.chase_duration:
                self.global_mode = "scatter"
                self.mode_timer = now
                for g in self.ghosts:
                    if g.mode != "dead": g.dir = (-g.dir[0], -g.dir[1])

        # Ghost logic
        for g in self.ghosts:
            if g.mode == "frightened":
                if now - g.frightened_timer > 6000:
                    g.mode = self.global_mode
                    g.speed = 1.5 + (self.level - 1) * 0.25
                    g.last_decision_tile = None
            elif g.mode != "dead":
                g.mode = self.global_mode
                
            self._update_ghost_ai(g)
            self._move_entity(g, is_ghost=True)

        # Pacman logic
        for p in [self.p1, self.p2]:
            if p.is_dead: continue
            
            if p.is_bot:
                self._update_bot_ai(p)
                
            self._move_entity(p)
            
            # Animate mouth
            if p.dir != NONE:
                p.anim_frame = (p.anim_frame + 1) % 10
                p.mouth_open = p.anim_frame < 5
                
            # Eat pellets
            pc, pr = int(p.x // CELL), int(p.y // CELL)
            if (pc, pr) in self.pellets:
                self.pellets.remove((pc, pr))
                p.score += 10
                if getattr(self, 'chomp_toggle', 0) == 0:
                    self._play_sound(getattr(self, 'snd_chomp0', None))
                    self.chomp_toggle = 1
                else:
                    self._play_sound(getattr(self, 'snd_chomp1', None))
                    self.chomp_toggle = 0
            if (pc, pr) in self.power_pellets:
                self.power_pellets.remove((pc, pr))
                p.score += 50
                self._play_sound(self.snd_power)
                for g in self.ghosts:
                    if g.mode != "dead":
                        g.mode = "frightened"
                        g.frightened_timer = now
                        g.speed = 1.0
                        g.dir = (-g.dir[0], -g.dir[1])
                        g.last_decision_tile = None

            if getattr(self, 'fruit', None):
                fc, fr, ftype, _ = self.fruit
                if pc == fc and pr == fr:
                    pts = {"cherry": 100, "strawberry": 300, "orange": 500, "apple": 700, "melon": 1000}
                    p.score += pts.get(ftype, 100)
                    self.fruit = None
                    self.fruit_spawn_time = now + random.randint(15000, 30000)
                    self._play_sound(getattr(self, 'snd_fruit', None))
            
            # Ghost collision
            pr_rect = pygame.Rect(p.x - CELL/2 + 4, p.y - CELL/2 + 4, CELL - 8, CELL - 8)
            for g in self.ghosts:
                g_rect = pygame.Rect(g.x - CELL/2 + 4, g.y - CELL/2 + 4, CELL - 8, CELL - 8)
                if pr_rect.colliderect(g_rect):
                    if g.mode == "frightened":
                        g.mode = "dead"
                        g.speed = 5
                        p.score += 200
                        self._play_sound(self.snd_eat_ghost)
                    elif g.mode in ("scatter", "chase"):
                        p.lives -= 1
                        if p.lives <= 0:
                            p.is_dead = True
                        self._play_sound(self.snd_death)
                        self.state = "DEAD_PAUSE"
                        self.timer = now
                        
        if not self.pellets and not self.power_pellets and self.state == "PLAY":
            # Win/Next level
            self.state = "LEVEL_COMPLETE"
            self.timer = now

    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == "GAME_OVER" and ev.key == pygame.K_r:
                    self._init_game(full_reset=True)
                    
                if self.state == "PLAY":
                    if not self.p1.is_dead:
                        if ev.key == pygame.K_UP: self.p1.next_dir = UP
                        elif ev.key == pygame.K_DOWN: self.p1.next_dir = DOWN
                        elif ev.key == pygame.K_LEFT: self.p1.next_dir = LEFT
                        elif ev.key == pygame.K_RIGHT: self.p1.next_dir = RIGHT
                    
                    if not self.p2.is_bot and not self.p2.is_dead:
                        if ev.key == pygame.K_w: self.p2.next_dir = UP
                        elif ev.key == pygame.K_s: self.p2.next_dir = DOWN
                        elif ev.key == pygame.K_a: self.p2.next_dir = LEFT
                        elif ev.key == pygame.K_d: self.p2.next_dir = RIGHT

    def draw(self):
        self.screen.fill((10, 10, 20))
        
        # Draw Maze
        for r in range(ROWS):
            for c in range(COLS):
                char = MAP[r][c]
                rx = self.bx + c * CELL
                ry = self.by + r * CELL
                
                if char == 'W':
                    pygame.draw.rect(self.screen, (20, 50, 180), (rx, ry, CELL, CELL), 2)
                elif char == '-':
                    pygame.draw.line(self.screen, (255, 150, 150), (rx, ry + CELL/2), (rx + CELL, ry + CELL/2), 4)
                    
        # Draw Pellets
        for c, r in self.pellets:
            pygame.draw.circle(self.screen, (255, 200, 150), (self.bx + int(c*CELL + CELL/2), self.by + int(r*CELL + CELL/2)), 3)
        for c, r in self.power_pellets:
            if pygame.time.get_ticks() % 500 < 250:
                pygame.draw.circle(self.screen, (255, 200, 150), (self.bx + int(c*CELL + CELL/2), self.by + int(r*CELL + CELL/2)), 7)

        # Draw Fruit
        if getattr(self, 'fruit', None):
            fc, fr, ftype, _ = self.fruit
            fx = self.bx + int(fc*CELL + CELL/2)
            fy = self.by + int(fr*CELL + CELL/2)
            
            if ftype == "cherry":
                pygame.draw.circle(self.screen, (255, 0, 0), (fx - 4, fy + 2), 4)
                pygame.draw.circle(self.screen, (255, 0, 0), (fx + 4, fy + 2), 4)
                pygame.draw.line(self.screen, (0, 255, 0), (fx - 4, fy - 2), (fx, fy - 6), 2)
                pygame.draw.line(self.screen, (0, 255, 0), (fx + 4, fy - 2), (fx, fy - 6), 2)
            elif ftype == "strawberry":
                pygame.draw.circle(self.screen, (255, 0, 0), (fx, fy + 2), 6)
                pygame.draw.circle(self.screen, (0, 255, 0), (fx, fy - 4), 3)
            elif ftype == "orange":
                pygame.draw.circle(self.screen, (255, 128, 0), (fx, fy), 6)
                pygame.draw.circle(self.screen, (0, 255, 0), (fx, fy - 6), 2)
            elif ftype == "apple":
                pygame.draw.circle(self.screen, (255, 0, 0), (fx, fy), 6)
                pygame.draw.line(self.screen, (150, 75, 0), (fx, fy - 6), (fx, fy - 10), 2)
            elif ftype == "melon":
                pygame.draw.circle(self.screen, (0, 255, 0), (fx, fy), 7)
                pygame.draw.circle(self.screen, (0, 150, 0), (fx, fy), 7, 2)

        # Draw Pacmans
        for p in [self.p1, self.p2]:
            if p.is_dead: continue
            px = self.bx + int(p.x)
            py = self.by + int(p.y)
            angle = 0
            if p.dir == UP: angle = 90
            elif p.dir == DOWN: angle = -90
            elif p.dir == LEFT: angle = 180
            elif p.dir == RIGHT: angle = 0
            
            if p.mouth_open:
                start_a = math.radians(angle + 30)
                end_a = math.radians(angle + 330)
            else:
                start_a = math.radians(angle + 5)
                end_a = math.radians(angle + 355)
                
            rect = pygame.Rect(px - CELL/2 + 2, py - CELL/2 + 2, CELL - 4, CELL - 4)
            pygame.draw.arc(self.screen, p.color, rect, start_a, end_a, CELL//2)

        # Draw Ghosts
        for g in self.ghosts:
            px = self.bx + int(g.x)
            py = self.by + int(g.y)
            
            if g.mode == "dead":
                # Eyes only
                pygame.draw.circle(self.screen, (255,255,255), (px - 4, py - 2), 3)
                pygame.draw.circle(self.screen, (255,255,255), (px + 4, py - 2), 3)
                pygame.draw.circle(self.screen, (0,0,255), (px - 4 + g.dir[0], py - 2 + g.dir[1]), 1)
                pygame.draw.circle(self.screen, (0,0,255), (px + 4 + g.dir[0], py - 2 + g.dir[1]), 1)
            else:
                color = g.color
                if g.mode == "frightened":
                    if pygame.time.get_ticks() - g.frightened_timer > 4000 and pygame.time.get_ticks() % 400 < 200:
                        color = (255, 255, 255)
                    else:
                        color = (0, 50, 255)
                        
                # Ghost Body
                rect = pygame.Rect(px - CELL/2 + 2, py - CELL/2 + 2, CELL - 4, CELL - 4)
                pygame.draw.path = [(px - CELL/2 + 2, py + CELL/2 - 2), (px - CELL/2 + 2, py), (px + CELL/2 - 2, py), (px + CELL/2 - 2, py + CELL/2 - 2)]
                pygame.draw.circle(self.screen, color, (px, py - 2), CELL//2 - 2)
                pygame.draw.rect(self.screen, color, (px - CELL/2 + 2, py - 2, CELL - 4, CELL//2))
                # Eyes
                if g.mode != "frightened":
                    pygame.draw.circle(self.screen, (255,255,255), (px - 4, py - 4), 3)
                    pygame.draw.circle(self.screen, (255,255,255), (px + 4, py - 4), 3)
                    pygame.draw.circle(self.screen, (0,0,255), (px - 4 + g.dir[0]*2, py - 4 + g.dir[1]*2), 1)
                    pygame.draw.circle(self.screen, (0,0,255), (px + 4 + g.dir[0]*2, py - 4 + g.dir[1]*2), 1)

        # UI
        p1_name = reshape_persian(self.session.player1_name)
        p2_name = reshape_persian(self.session.player2_name)
        
        # P1 UI
        t1 = render_persian_text(self.font_md, f"{p1_name}: {self.p1.score}", self.p1.color)
        self.screen.blit(t1, (20, 20))
        for i in range(self.p1.lives):
            pygame.draw.circle(self.screen, self.p1.color, (30 + i*20, 60), 8)
            
        # P2 UI
        t2 = render_persian_text(self.font_md, f"{p2_name}: {self.p2.score}", self.p2.color)
        self.screen.blit(t2, (self.W - t2.get_width() - 20, 20))
        for i in range(self.p2.lives):
            pygame.draw.circle(self.screen, self.p2.color, (self.W - 30 - i*20, 60), 8)

        # Game Over / Ready
        if self.state == "READY":
            t = self.font_lg.render(f"LEVEL {self.level} - READY!", True, (255, 255, 0))
            self.screen.blit(t, (self.W//2 - t.get_width()//2, self.by + 16 * CELL))
        elif self.state == "LEVEL_COMPLETE":
            t = self.font_lg.render(f"LEVEL {self.level} COMPLETE!", True, (0, 255, 255))
            self.screen.blit(t, (self.W//2 - t.get_width()//2, self.by + 16 * CELL))
        elif self.state == "GAME_OVER":
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0,0,0,200))
            self.screen.blit(ov, (0,0))
            
            if self.p1.score > self.p2.score: win_txt = f"{p1_name} WINS!"
            elif self.p2.score > self.p1.score: win_txt = f"{p2_name} WINS!"
            else: win_txt = "DRAW!"
            
            wt = render_persian_text(self.font_lg, win_txt, (255, 255, 255))
            self.screen.blit(wt, (self.W//2 - wt.get_width()//2, self.H//2 - 50))
            
            st = self.font_sm.render("Press R to Restart | ESC to Quit", True, (150, 150, 150))
            self.screen.blit(st, (self.W//2 - st.get_width()//2, self.H//2 + 20))
