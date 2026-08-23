import pygame
import random
import os
import math
from base_game import BaseGame
from main import resource_path, get_base_path
from persian_utils import render_persian_text, reshape_persian

class LumberjackBattle(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        
        self.colors = {
            "bg": (135, 206, 235),
            "ground": (34, 139, 34),
            "trunk": (120, 75, 40),
            "trunk_line": (80, 50, 20),
            "branch": (101, 67, 33),
            "player1": (255, 69, 0),
            "player2": (30, 144, 255),
            "timer_bg": (50, 50, 50),
            "timer_fg": (255, 215, 0),
            "crack": (0, 0, 0),
            "text": (255, 255, 255),
            "skin": (255, 224, 189),
            "shirt1": (200, 0, 0),
            "shirt2": (0, 100, 200),
            "pants": (50, 50, 50),
            "axe_handle": (139, 69, 19),
            "axe_blade": (192, 192, 192),
            "time_block": (50, 150, 255) # Blue tint for time block
        }
        
        self.w, self.h = screen.get_size()
        self.score_font = pygame.font.SysFont("arial", 36, bold=True)
        
        self.sounds = {}
        sound_dir = os.path.join(get_base_path(), "games", "lumberjack_battle", "sounds")
        try:
            pygame.mixer.init()
            for s in ["chop.wav", "crack.wav", "die.wav"]:
                path = os.path.join(sound_dir, s)
                if os.path.exists(path):
                    self.sounds[s.split('.')[0]] = pygame.mixer.Sound(path)
        except Exception as e:
            pass
            
        self.reset_game()
        
    def reset_game(self):
        self.players = {
            "p1": {
                "side": -1,
                "score": 0,
                "dead": False,
                "tree": self.generate_initial_tree(),
                "time": 100.0,
                "color": self.colors["player1"],
                "name": self.session.player1_name,
                "anim_timer": 0,
                "floating_texts": [],
                "death_anim_progress": 0.0,  # 0.0 = upright, 1.0 = fully fallen
                "death_star_angle": 0.0,      # rotating stars angle
            },
            "p2": {
                "side": 1,
                "score": 0,
                "dead": False,
                "tree": self.generate_initial_tree(),
                "time": 100.0,
                "color": self.colors["player2"],
                "name": self.session.player2_name,
                "anim_timer": 0,
                "floating_texts": [],
                "death_anim_progress": 0.0,
                "death_star_angle": 0.0,
            }
        }
        
        if getattr(self.session, 'is_single_player', False):
            self.players["p2"]["is_bot"] = True
            self.bot_timer = 0
            diff = self.session.bot_difficulty
            if diff == "low": self.bot_delay = 500
            elif diff == "medium": self.bot_delay = 300
            else: self.bot_delay = 150
        else:
            self.players["p2"]["is_bot"] = False
            
        self.waiting_to_start = True
        self.start_ticks = pygame.time.get_ticks()
        self.game_over = False

    def generate_initial_tree(self):
        tree = []
        for i in range(10):
            if i < 2:
                tree.append({"branch": 0, "type": "normal", "branch_shape": 0})
            else:
                tree.append(self.generate_tree_block(tree[-1]["branch"]))
        return tree

    def generate_tree_block(self, last_branch):
        if last_branch != 0 or random.random() < 0.3:
            branch = random.choice([-1, 1]) if last_branch == 0 else last_branch
            if random.random() < 0.5:
                branch = 0
        else:
            branch = random.choice([-1, 1, 0])
            
        block_type = "normal"
        if branch == 0:
            rand_val = random.random()
            if rand_val < 0.1:
                block_type = "2x"
            elif rand_val < 0.15:
                block_type = "time"
            
        # 0 to 4 for more varied branch shapes
        branch_shape = random.randint(0, 4)
            
        return {"branch": branch, "type": block_type, "hits": 0, "branch_shape": branch_shape}

    def play_sound(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def add_floating_text(self, p_key, text, side, color=(255, 255, 0)):
        self.players[p_key]["floating_texts"].append({
            "text": text,
            "y": 0,
            "alpha": 255,
            "side": side,
            "color": color
        })

    def chop(self, p_key, side):
        p = self.players[p_key]
        if p["dead"]: return
        
        p["side"] = side
        p["anim_timer"] = 8 # 8 frames for a snappy chop animation
        bottom_block = p["tree"][0]
        
        if bottom_block["branch"] == side:
            p["dead"] = True
            self.play_sound("die")
            return
            
        if bottom_block["type"] == "2x":
            if bottom_block["hits"] == 0:
                bottom_block["hits"] = 1
                self.play_sound("crack")
                return
                
        self.play_sound("chop")
        p["score"] += 1
        
        # Base time addition
        add_time = 15.0 * math.exp(-p["score"] / 300.0)
        
        if bottom_block["type"] == "time":
            self.add_floating_text(p_key, "+TIME!", side, color=(50, 255, 50))
            add_time += 30.0 # Extra time
        else:
            self.add_floating_text(p_key, "+1", side)
            
        p["time"] = min(100.0, p["time"] + add_time)
        
        p["tree"].pop(0)
        p["tree"].append(self.generate_tree_block(p["tree"][-1]["branch"]))
        
        if p["tree"][0]["branch"] == side:
            p["dead"] = True
            self.play_sound("die")

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False # Escape to menu
                
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                elif self.waiting_to_start:
                    if event.key == pygame.K_SPACE:
                        self.waiting_to_start = False
                        self.start_ticks = pygame.time.get_ticks()
                else:
                    if not self.players["p1"]["dead"]:
                        if event.key == pygame.K_a:
                            self.chop("p1", -1)
                        elif event.key == pygame.K_d:
                            self.chop("p1", 1)
                            
                    if not self.players["p2"]["dead"] and not self.players["p2"]["is_bot"]:
                        if event.key == pygame.K_LEFT:
                            self.chop("p2", -1)
                        elif event.key == pygame.K_RIGHT:
                            self.chop("p2", 1)

    def update(self):
        if self.game_over or self.waiting_to_start: return
            
        current_ticks = pygame.time.get_ticks()
        elapsed = (current_ticks - self.start_ticks) / 1000.0
        # Slower drain rate scaling
        drain_rate = 3.0 + (elapsed * 0.1) 
        
        both_dead = True
        for p_key, p in self.players.items():
            if p["anim_timer"] > 0:
                p["anim_timer"] -= 1
                
            for ft in p["floating_texts"]:
                ft["y"] -= 3
                ft["alpha"] -= 12
            p["floating_texts"] = [ft for ft in p["floating_texts"] if ft["alpha"] > 0]
            
            # Animate death fall
            if p["dead"]:
                if p["death_anim_progress"] < 1.0:
                    p["death_anim_progress"] = min(1.0, p["death_anim_progress"] + 0.04)
                p["death_star_angle"] += 3.0  # spin stars
            
            if not p["dead"]:
                both_dead = False
                p["time"] -= drain_rate * (1/60.0)
                if p["time"] <= 0:
                    p["dead"] = True
                    self.play_sound("die")
                    
        p2 = self.players["p2"]
        if p2["is_bot"] and not p2["dead"]:
            if current_ticks - self.bot_timer > self.bot_delay:
                self.bot_timer = current_ticks
                bottom_block = p2["tree"][0]
                if bottom_block["type"] == "2x" and bottom_block["hits"] == 0:
                    safe_side = p2["side"]
                    if bottom_block["branch"] != 0: safe_side = -bottom_block["branch"]
                    self.chop("p2", safe_side)
                else:
                    next_block = p2["tree"][1] if len(p2["tree"]) > 1 else None
                    if next_block and next_block["branch"] != 0:
                        safe_side = -next_block["branch"]
                        self.chop("p2", safe_side)
                    else:
                        safe_side = p2["side"]
                        if bottom_block["branch"] != 0: safe_side = -bottom_block["branch"] 
                        self.chop("p2", safe_side)
                self.bot_delay = max(60, self.bot_delay - 1)
                    
        if both_dead:
            self.game_over = True
            s1 = self.players["p1"]["score"]
            s2 = self.players["p2"]["score"]
            if s1 > s2:
                self.session.scores["player1"] += 1
            elif s2 > s1:
                self.session.scores["player2"] += 1

    def draw_lumberjack(self, surface, p_key, x, y, side, is_animating):
        p = self.players[p_key]
        shirt = self.colors["shirt1"] if p_key == "p1" else self.colors["shirt2"]
        
        # Legs
        leg_color = self.colors["pants"]
        pygame.draw.rect(surface, leg_color, (x-8, y-25, 6, 25))
        pygame.draw.rect(surface, leg_color, (x+2, y-25, 6, 25))
        
        # Body (plaid shirt approximation)
        pygame.draw.rect(surface, shirt, (x-15, y-55, 30, 32), border_radius=6)
        
        # Head with beard
        pygame.draw.circle(surface, self.colors["skin"], (x, y-65), 14)
        # Beard
        beard_color = (139, 69, 19)
        beard_pts = [(x-14, y-65), (x+14, y-65), (x+5, y-48), (x-5, y-48)]
        pygame.draw.polygon(surface, beard_color, beard_pts)
        
        # Two eyes with white sclera
        pygame.draw.circle(surface, (255, 255, 255), (x - 6, y-70), 4)   # left eye white
        pygame.draw.circle(surface, (255, 255, 255), (x + 6, y-70), 4)   # right eye white
        pygame.draw.circle(surface, (30, 30, 30),   (x - 5, y-70), 2)    # left pupil
        pygame.draw.circle(surface, (30, 30, 30),   (x + 7, y-70), 2)    # right pupil
        
        # Smile mouth (just below chin / above beard)
        mouth_rect = pygame.Rect(x - 6, y - 63, 12, 6)
        pygame.draw.arc(surface, (180, 80, 60), mouth_rect, 3.14, 0, 2)
        
        # Beanie (hat)
        pygame.draw.polygon(surface, (200, 50, 50), [(x-12, y-72), (x+12, y-72), (x, y-85)])
        pygame.draw.circle(surface, (220, 220, 220), (x, y-85), 4)

        # Arms and Axe
        arm_color = self.colors["skin"]
        if is_animating:
            # Chopping frame - Axe hits the tree (center of the screen)
            if side == -1:
                pygame.draw.line(surface, shirt, (x-5, y-45), (x+10, y-35), 6) # Arm reaching forward
                pygame.draw.line(surface, arm_color, (x+10, y-35), (x+25, y-25), 5) 
                axe_handle_start = (x, y-40)
                axe_handle_end = (x+50, y-15) # Reaches into tree
            else:
                pygame.draw.line(surface, shirt, (x+5, y-45), (x-10, y-35), 6)
                pygame.draw.line(surface, arm_color, (x-10, y-35), (x-25, y-25), 5)
                axe_handle_start = (x, y-40)
                axe_handle_end = (x-50, y-15)
        else:
            # Idle frame - holding axe back
            if side == -1:
                pygame.draw.line(surface, shirt, (x-5, y-45), (x-20, y-40), 6)
                pygame.draw.line(surface, arm_color, (x-20, y-40), (x-25, y-50), 5)
                axe_handle_start = (x-15, y-30)
                axe_handle_end = (x-30, y-75)
            else:
                pygame.draw.line(surface, shirt, (x+5, y-45), (x+20, y-40), 6)
                pygame.draw.line(surface, arm_color, (x+20, y-40), (x+25, y-50), 5)
                axe_handle_start = (x+15, y-30)
                axe_handle_end = (x+30, y-75)
            
        pygame.draw.line(surface, self.colors["axe_handle"], axe_handle_start, axe_handle_end, 5)
        
        # Axe Blade
        blade_x = axe_handle_end[0]
        blade_y = axe_handle_end[1]
        
        if is_animating:
            # Blade embedded in tree
            if side == -1:
                points = [(blade_x, blade_y-15), (blade_x+10, blade_y-5), (blade_x+5, blade_y+15), (blade_x-10, blade_y+10)]
            else:
                points = [(blade_x, blade_y-15), (blade_x-10, blade_y-5), (blade_x-5, blade_y+15), (blade_x+10, blade_y+10)]
        else:
            # Blade angled up
            if side == -1:
                points = [(blade_x, blade_y+10), (blade_x-15, blade_y+15), (blade_x-15, blade_y-15), (blade_x, blade_y-10)]
            else:
                points = [(blade_x, blade_y+10), (blade_x+15, blade_y+15), (blade_x+15, blade_y-15), (blade_x, blade_y-10)]
                
        pygame.draw.polygon(surface, self.colors["axe_blade"], points)

    def draw_dead_lumberjack(self, surface, p_key, x, y, side):
        """Draw a fallen lumberjack with X eyes and death animation."""
        p = self.players[p_key]
        shirt = self.colors["shirt1"] if p_key == "p1" else self.colors["shirt2"]
        progress = p["death_anim_progress"]  # 0.0 to 1.0

        # Ease-out interpolation for the fall angle
        fall_angle = math.sin(progress * math.pi / 2) * 90.0  # 0 -> 90 degrees

        # Direction of fall: Fall away from the tree based on current side
        fall_dir = p["side"]

        # Create a temporary surface to draw the upright character
        char_w, char_h = 80, 100
        char_surf = pygame.Surface((char_w, char_h), pygame.SRCALPHA)

        cx = char_w // 2
        cy = char_h - 5  # feet at bottom

        # --- Draw character on temp surface ---
        # Legs
        pygame.draw.rect(char_surf, self.colors["pants"], (cx-8, cy-25, 6, 25))
        pygame.draw.rect(char_surf, self.colors["pants"], (cx+2, cy-25, 6, 25))

        # Body
        pygame.draw.rect(char_surf, shirt, (cx-15, cy-55, 30, 32), border_radius=6)

        # Head
        pygame.draw.circle(char_surf, self.colors["skin"], (cx, cy-65), 14)

        # Beard
        beard_color = (139, 69, 19)
        beard_pts = [(cx-14, cy-65), (cx+14, cy-65), (cx+5, cy-48), (cx-5, cy-48)]
        pygame.draw.polygon(char_surf, beard_color, beard_pts)

        # Beanie (match shirt color)
        pygame.draw.polygon(char_surf, shirt, [(cx-12, cy-72), (cx+12, cy-72), (cx, cy-85)])
        pygame.draw.circle(char_surf, (220, 220, 220), (cx, cy-85), 4)

        # X Eyes (dead eyes)
        eye_color = (200, 0, 0)
        for ex, ey in [(cx - 6, cy - 70), (cx + 6, cy - 70)]:
            sz = 5
            pygame.draw.line(char_surf, eye_color, (ex-sz, ey-sz), (ex+sz, ey+sz), 3)
            pygame.draw.line(char_surf, eye_color, (ex+sz, ey-sz), (ex-sz, ey+sz), 3)

        # Squiggly mouth (dead)
        for i in range(4):
            mx = cx - 6 + i * 4
            my = cy - 56 + (2 if i % 2 == 0 else -2)
            pygame.draw.circle(char_surf, (180, 80, 60), (mx, my), 2)

        # Arms drooping down (dead)
        pygame.draw.line(char_surf, shirt, (cx-5, cy-45), (cx-20, cy-20), 6)
        pygame.draw.line(char_surf, self.colors["skin"], (cx-20, cy-20), (cx-25, cy-5), 5)
        pygame.draw.line(char_surf, shirt, (cx+5, cy-45), (cx+20, cy-20), 6)
        pygame.draw.line(char_surf, self.colors["skin"], (cx+20, cy-20), (cx+25, cy-5), 5)

        # Axe on ground next to body
        pygame.draw.line(char_surf, self.colors["axe_handle"], (cx+5, cy-10), (cx+30, cy-35), 4)
        axe_pts = [(cx+30, cy-35), (cx+40, cy-40), (cx+35, cy-52), (cx+25, cy-47)]
        pygame.draw.polygon(char_surf, self.colors["axe_blade"], axe_pts)

        # --- Rotate the surface by fall angle ---
        rotate_angle = fall_dir * fall_angle  # positive = clockwise
        rotated = pygame.transform.rotate(char_surf, -rotate_angle)

        # Pygame rotation expands the surface. To pivot around (cx, cy):
        # 1. Get original rect centered on some arbitrary point (0,0)
        orig_rect = char_surf.get_rect()
        # 2. Get the pivot vector relative to the center of the original rect
        pivot_vec = pygame.Vector2(cx - orig_rect.centerx, cy - orig_rect.centery)
        # 3. Rotate this vector
        # Note: pygame.transform.rotate uses counter-clockwise positive angles, 
        # so Vector2.rotate needs the negative of that if we want it to match
        pivot_vec_rot = pivot_vec.rotate(rotate_angle)
        # 4. Get the new rect, and set its center so that the rotated pivot aligns with the original pivot
        rot_rect = rotated.get_rect()
        
        # When fully fallen (progress=1.0, angle=90), the character's width becomes its height.
        # Ensure the body rests exactly on top of the ground (shift up by 15 pixels).
        rot_rect.center = (x - pivot_vec_rot.x,
                           y - pivot_vec_rot.y - 15 * progress)
        
        # Draw the rotated surface
        surface.blit(rotated, rot_rect)

        # --- Spinning stars around head (appear after fully fallen) ---
        if progress > 0.5:
            star_alpha = int(min(255, (progress - 0.5) * 2 * 255))
            star_angle = p["death_star_angle"]
            
            # Calculate head position based on rotation
            # Head is at (cx, cy - 65) in local space
            head_local = pygame.Vector2(0, -65) 
            head_rot = head_local.rotate(rotate_angle)
            head_screen_x = x + head_rot.x
            head_screen_y = y + head_rot.y - 15 * progress

            num_stars = 3
            for i in range(num_stars):
                angle_rad = math.radians(star_angle + i * (360 / num_stars))
                sx = int(head_screen_x + math.cos(angle_rad) * 22)
                sy = int(head_screen_y + math.sin(angle_rad) * 12)
                star_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                # Draw a simple 5-point star
                self._draw_star(star_surf, 10, 10, 8, 3, (255, 220, 0, star_alpha))
                surface.blit(star_surf, (sx - 10, sy - 10))

    def _draw_star(self, surface, cx, cy, outer_r, inner_r, color):
        """Draw a 5-point star on a surface."""
        points = []
        for i in range(10):
            angle = math.radians(-90 + i * 36)
            r = outer_r if i % 2 == 0 else inner_r
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        pygame.draw.polygon(surface, color, points)

    def draw_player_screen(self, surface, p_key, width, height):
        p = self.players[p_key]
        surface.fill(self.colors["bg"])
        
        ground_h = 100
        pygame.draw.rect(surface, self.colors["ground"], (0, height - ground_h, width, ground_h))
        
        block_w, block_h = 80, 80
        center_x = width // 2
        base_y = height - ground_h - block_h
        
        # Draw Tree
        for i, block in enumerate(p["tree"]):
            y = base_y - (i * block_h)
            if y < -block_h: break
            
            rect = pygame.Rect(center_x - block_w//2, y, block_w, block_h)
            color = self.colors["trunk"]
            if block["type"] == "2x":
                color = (200, 100, 50)
            elif block["type"] == "time":
                color = self.colors["time_block"]
                
            pygame.draw.rect(surface, color, rect)
            
            # Tree texture lines
            pygame.draw.line(surface, self.colors["trunk_line"], (rect.left+15, rect.top), (rect.left+15, rect.bottom), 2)
            pygame.draw.line(surface, self.colors["trunk_line"], (rect.right-15, rect.top), (rect.right-15, rect.bottom), 2)
            
            if block["type"] == "2x" and block.get("hits", 0) == 1:
                pygame.draw.line(surface, self.colors["crack"], (center_x - 30, y + 20), (center_x + 10, y + 40), 3)
                pygame.draw.line(surface, self.colors["crack"], (center_x + 10, y + 40), (center_x - 10, y + 70), 3)
                
            if block["type"] == "time":
                # Draw a little clock face
                pygame.draw.circle(surface, (255,255,255), (center_x, y + block_h//2), 15)
                pygame.draw.line(surface, (0,0,0), (center_x, y + block_h//2), (center_x, y + block_h//2 - 10), 2)
                pygame.draw.line(surface, (0,0,0), (center_x, y + block_h//2), (center_x + 8, y + block_h//2), 2)
                
            if block["branch"] != 0:
                # Highly organic shaped branches using random polygons based on branch_shape
                b_w = 120
                if block["branch"] == 1:
                    b_x_start = center_x + block_w//2
                    if block["branch_shape"] == 0:
                        pts = [(b_x_start, y+60), (b_x_start+b_w, y+40), (b_x_start+b_w-10, y+10), (b_x_start, y+20)]
                    elif block["branch_shape"] == 1:
                        pts = [(b_x_start, y+50), (b_x_start+b_w, y+80), (b_x_start+b_w-30, y+30), (b_x_start, y+10)]
                    elif block["branch_shape"] == 2:
                        pts = [(b_x_start, y+70), (b_x_start+b_w, y+20), (b_x_start+b_w, y), (b_x_start, y+30)]
                    elif block["branch_shape"] == 3:
                        pts = [(b_x_start, y+50), (b_x_start+b_w-40, y+80), (b_x_start+b_w, y+50), (b_x_start+b_w//2, y+10), (b_x_start, y+20)]
                    else:
                        pts = [(b_x_start, y+40), (b_x_start+b_w, y+30), (b_x_start+b_w-20, y+10), (b_x_start, y+20)]
                else:
                    b_x_start = center_x - block_w//2
                    if block["branch_shape"] == 0:
                        pts = [(b_x_start, y+60), (b_x_start-b_w, y+40), (b_x_start-b_w+10, y+10), (b_x_start, y+20)]
                    elif block["branch_shape"] == 1:
                        pts = [(b_x_start, y+50), (b_x_start-b_w, y+80), (b_x_start-b_w+30, y+30), (b_x_start, y+10)]
                    elif block["branch_shape"] == 2:
                        pts = [(b_x_start, y+70), (b_x_start-b_w, y+20), (b_x_start-b_w, y), (b_x_start, y+30)]
                    elif block["branch_shape"] == 3:
                        pts = [(b_x_start, y+50), (b_x_start-b_w+40, y+80), (b_x_start-b_w, y+50), (b_x_start-b_w//2, y+10), (b_x_start, y+20)]
                    else:
                        pts = [(b_x_start, y+40), (b_x_start-b_w, y+30), (b_x_start-b_w+20, y+10), (b_x_start, y+20)]
                pygame.draw.polygon(surface, self.colors["trunk"], pts)
                
        # Draw Player
        p_x = center_x + (block_w//2) + 35 if p["side"] == 1 else center_x - (block_w//2) - 35
        p_y = height - ground_h
        
        if not p["dead"]:
            self.draw_lumberjack(surface, p_key, p_x, p_y, p["side"], p["anim_timer"] > 0)
        else:
            # Fallen lumberjack death animation
            self.draw_dead_lumberjack(surface, p_key, p_x, p_y, p["side"])
            
        # Draw Floating Texts
        font_ft = pygame.font.SysFont("arial", 28, bold=True)
        for ft in p["floating_texts"]:
            c = ft.get("color", (255, 255, 0))
            txt_surf = font_ft.render(ft["text"], True, c)
            txt_surf.set_alpha(ft["alpha"])
            fx = center_x + 80 if ft["side"] == 1 else center_x - 100
            fy = base_y + 40 + ft["y"]
            surface.blit(txt_surf, (fx, fy))
            
        # UI (Score)
        score_surf = self.score_font.render(f"{p['score']}", True, (255,255,255))
        # Draw with outline
        outline = self.score_font.render(f"{p['score']}", True, (0,0,0))
        surface.blit(outline, (22, 22))
        surface.blit(score_surf, (20, 20))
        
        timer_w, timer_h = 200, 20
        timer_x = width // 2 - timer_w // 2
        timer_y = 60
        pygame.draw.rect(surface, self.colors["timer_bg"], (timer_x, timer_y, timer_w, timer_h), border_radius=10)
        fill_w = max(0, int(timer_w * (p["time"] / 100.0)))
        
        t_color = self.colors["timer_fg"]
        if p["time"] < 25: t_color = (255, 0, 0)
        elif p["time"] < 50: t_color = (255, 140, 0)
            
        pygame.draw.rect(surface, t_color, (timer_x, timer_y, fill_w, timer_h), border_radius=10)

    def draw(self):
        half_w = self.w // 2
        p1_surf = pygame.Surface((half_w, self.h))
        p2_surf = pygame.Surface((half_w, self.h))
        
        self.draw_player_screen(p1_surf, "p1", half_w, self.h)
        self.draw_player_screen(p2_surf, "p2", half_w, self.h)
        
        self.screen.blit(p1_surf, (0, 0))
        self.screen.blit(p2_surf, (half_w, 0))
        
        pygame.draw.line(self.screen, (0,0,0), (half_w, 0), (half_w, self.h), 5)
        
        self.draw_persian_text(self.players["p1"]["name"], self.players["p1"]["color"], (half_w//2 - 50, 10))
        self.draw_persian_text(self.players["p2"]["name"], self.players["p2"]["color"], (half_w + half_w//2 - 50, 10))

        if self.game_over:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            s1 = self.players["p1"]["score"]
            s2 = self.players["p2"]["score"]
            
            if s1 > s2: msg, c = f"{reshape_persian(self.players['p1']['name'])} Wins!", self.players["p1"]["color"]
            elif s2 > s1: msg, c = f"{reshape_persian(self.players['p2']['name'])} Wins!", self.players["p2"]["color"]
            else: msg, c = "Draw!", (255, 255, 255)
                
            font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
            surf = font_large.render(msg, True, c)
            self.screen.blit(surf, (self.w//2 - surf.get_width()//2, self.h//2 - 100))
            self.draw_persian_text("Press SPACE to play again", (255, 255, 255), (self.w//2 - 120, self.h//2 + 20))
            
        if self.waiting_to_start and not self.game_over:
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            font_title = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 48)
            font_keys = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)
            
            # Left player guide
            p1_name = reshape_persian(self.players["p1"]["name"])
            p1_title = font_title.render(p1_name, True, self.players["p1"]["color"])
            self.screen.blit(p1_title, (self.w//4 - p1_title.get_width()//2, self.h//2 - 120))
            
            p1_keys = font_keys.render("A = Left   |   D = Right", True, (255, 255, 255))
            self.screen.blit(p1_keys, (self.w//4 - p1_keys.get_width()//2, self.h//2 - 40))
            
            # Right player guide
            p2_name = reshape_persian(self.players["p2"]["name"])
            p2_title = font_title.render(p2_name, True, self.players["p2"]["color"])
            self.screen.blit(p2_title, (3*self.w//4 - p2_title.get_width()//2, self.h//2 - 120))
            
            if self.players["p2"]["is_bot"]:
                p2_keys = font_keys.render("Bot Player", True, (255, 255, 255))
            else:
                p2_keys = font_keys.render("<- Left   |   Right ->", True, (255, 255, 255))
            self.screen.blit(p2_keys, (3*self.w//4 - p2_keys.get_width()//2, self.h//2 - 40))
            
            # Start instruction
            start_msg = font_keys.render("Press SPACE to Start", True, (0, 255, 0))
            self.screen.blit(start_msg, (self.w//2 - start_msg.get_width()//2, self.h//2 + 80))
