import pygame
import pymunk
import pymunk.pygame_util
import math
import os
import sys
import random

# To import base_game and persian_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path, get_base_path

AIMING = 0
MOVING = 1

class Billiards(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        # Pymunk Space
        self.space = pymunk.Space()
        self.space.damping = 0.5 
        self.static_body = self.space.static_body
        
        # Game logic variables
        self.state = AIMING
        self.current_player = 1
        self.p1_group = None # "solids" or "stripes"
        self.p2_group = None
        self.balls_potted_this_turn = []
        self.foul = False
        self.first_ball_hit = None
        self.winner = None
        self.ball_in_hand = False
        
        # Physics vars
        self.dia = 36
        self.pocket_dia = 66
        self.force = 0
        self.max_force = 10000
        self.force_direction = 1
        self.powering_up = False
        
        self.bot_timer = 0
        self.bot_target_dir = None
        self.bot_target_force = 0
        
        self.load_assets()
        
        # Table offset for centering
        self.table_w = self.table_image.get_width()
        self.table_h = self.table_image.get_height()
        self.offset_x = (self.width - self.table_w) // 2
        self.offset_y = (self.height - self.table_h) // 2
        
        self.setup_table()
        
        # Colors & Fonts
        self.BG = (15, 15, 26)
        self.TEXT_COL = (240, 240, 255)
        self.ACCENT = (0, 240, 255)
        
        self.font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 24)
        self.large_font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 48)

    def load_assets(self):
        assets_dir = os.path.join(get_base_path(), "games", "billiards", "assets")
        img_dir = os.path.join(assets_dir, "images")
        snd_dir = os.path.join(assets_dir, "sounds")
        
        # Load Images
        self.cue_image_orig = pygame.image.load(os.path.join(img_dir, "cue.png")).convert_alpha()
        self.table_image = pygame.image.load(os.path.join(img_dir, "table.png")).convert_alpha()
        
        self.ball_images = {}
        self.small_ball_images = {}
        for i in range(1, 16):
            try:
                img = pygame.image.load(os.path.join(img_dir, f"ball_{i}.png")).convert_alpha()
                self.ball_images[i] = img
                self.small_ball_images[i] = pygame.transform.smoothscale(img, (24, 24))
            except: pass
        try:
            img = pygame.image.load(os.path.join(img_dir, f"ball_16.png")).convert_alpha()
            self.ball_images[0] = img
            self.small_ball_images[0] = pygame.transform.smoothscale(img, (24, 24))
        except: pass
                
        # Load Sounds
        pygame.mixer.init()
        try:
            self.snd_hit = pygame.mixer.Sound(os.path.join(snd_dir, "hit.wav"))
            self.snd_cushion = pygame.mixer.Sound(os.path.join(snd_dir, "cushion.wav"))
            self.snd_pocket = pygame.mixer.Sound(os.path.join(snd_dir, "pocket.wav"))
            self.snd_cue = pygame.mixer.Sound(os.path.join(snd_dir, "cue.wav"))
        except:
            self.snd_hit = self.snd_cushion = self.snd_pocket = self.snd_cue = None

    def setup_table(self):
        self.balls = []
        self.ball_types = {} 
        
        cushions = [
          [(88, 56), (109, 77), (555, 77), (564, 56)],
          [(621, 56), (630, 77), (1081, 77), (1102, 56)],
          [(89, 621), (110, 600),(556, 600), (564, 621)],
          [(622, 621), (630, 600), (1081, 600), (1102, 621)],
          [(56, 96), (77, 117), (77, 560), (56, 581)],
          [(1143, 96), (1122, 117), (1122, 560), (1143, 581)]
        ]
        
        for c in cushions:
            shifted = [(p[0] + self.offset_x, p[1] + self.offset_y) for p in c]
            body = pymunk.Body(body_type = pymunk.Body.STATIC)
            shape = pymunk.Poly(body, shifted)
            shape.elasticity = 0.8
            shape.collision_type = 2 
            self.space.add(body, shape)
            
        # Collision Handlers
        self.space.on_collision(1, 1, begin=self.ball_collision_snd)
        self.space.on_collision(1, 2, begin=self.cushion_collision_snd)

        rack_ids = [1, 9, 2, 10, 8, 3, 4, 11, 5, 12, 13, 6, 14, 7, 15]
        
        idx = 0
        rows = 5
        start_x = 250 + self.offset_x
        start_y = 267 + self.offset_y
        for col in range(5):
            for row in range(rows):
                pos = (start_x + (col * (self.dia + 1)), start_y + (row * (self.dia + 1)) + (col * self.dia / 2))
                ball_id = rack_ids[idx]
                idx += 1
                b = self.create_ball(self.dia/2, pos, ball_id)
                self.balls.append(b)
                self.ball_types[b.body] = ball_id
            rows -= 1
            
        self.cue_ball_pos = (888 + self.offset_x, 339 + self.offset_y) 
        self.cue_ball = self.create_ball(self.dia/2, self.cue_ball_pos, 0)
        self.balls.append(self.cue_ball)
        self.ball_types[self.cue_ball.body] = 0
        
        self.pockets = [
          (55, 63), (592, 48), (1134, 64),
          (55, 616), (592, 629), (1134, 616)
        ]
        
    def ball_collision_snd(self, arbiter, space, data):
        if self.snd_hit:
            self.snd_hit.set_volume(0.5)
            self.snd_hit.play()
        
        if self.state == MOVING and self.first_ball_hit is None:
            s1, s2 = arbiter.shapes
            type1 = self.ball_types.get(s1.body, -1)
            type2 = self.ball_types.get(s2.body, -1)
            
            if type1 == 0: self.first_ball_hit = type2
            elif type2 == 0: self.first_ball_hit = type1
                
        return True
        
    def cushion_collision_snd(self, arbiter, space, data):
        if self.snd_cushion:
            self.snd_cushion.set_volume(0.3)
            self.snd_cushion.play()
        return True

    def create_ball(self, radius, pos, ball_id):
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Circle(body, radius)
        shape.mass = 5
        shape.elasticity = 0.8
        shape.collision_type = 1
        
        pivot = pymunk.PivotJoint(self.static_body, body, (0, 0), (0, 0))
        pivot.max_bias = 0
        pivot.max_force = 1000
        
        self.space.add(body, shape, pivot)
        return shape

    def get_group_name(self, ball_id):
        if 1 <= ball_id <= 7: return "solids"
        if 9 <= ball_id <= 15: return "stripes"
        if ball_id == 8: return "black"
        return "cue"

    def is_ball_on_table(self, ball_id):
        for ball in self.balls:
            if self.ball_types[ball.body] == ball_id:
                return True
        return False

    def is_on_black(self, player):
        group = self.p1_group if player == 1 else self.p2_group
        if group is None: return False
        
        for ball in self.balls:
            ball_id = self.ball_types[ball.body]
            if self.get_group_name(ball_id) == group:
                return False
        return True

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
        
        if self.winner is not None:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and self.state == AIMING:
                if self.ball_in_hand:
                    self.cue_ball.body.position = event.pos
                    self.ball_in_hand = False
                else:
                    self.powering_up = True
            
            if event.type == pygame.MOUSEBUTTONUP and self.state == AIMING:
                if self.powering_up:
                    self.powering_up = False
                    self.shoot()

    def _bot_play(self):
        difficulty = getattr(self.session, 'bot_difficulty', 'medium')
        
        # ── Determine legal target balls (strict rules) ──────────────────────
        # Bot is always player 2.
        own_group  = self.p2_group    # 'solids', 'stripes', or None
        opp_group  = self.p1_group
        eight_ball = [b for b in self.balls if self.ball_types[b.body] == 8]

        if own_group == 'solids':
            target_balls = [b for b in self.balls if self.ball_types[b.body] in range(1, 8)]
        elif own_group == 'stripes':
            target_balls = [b for b in self.balls if self.ball_types[b.body] in range(9, 16)]
        else:
            # Group not yet assigned – avoid 8-ball and opponent balls if possible
            target_balls = [b for b in self.balls if self.ball_types[b.body] not in [0, 8]]

        shooting_eight = False
        if not target_balls:
            # All own balls pocketed → now legally shoot the 8
            target_balls = eight_ball
            shooting_eight = True

        # Opponent ball IDs – we must NOT pocket these (it gives them ball-in-hand)
        if opp_group == 'solids':
            opp_ids = set(range(1, 8))
        elif opp_group == 'stripes':
            opp_ids = set(range(9, 16))
        else:
            opp_ids = set()

        # ── Smart ball-in-hand placement ─────────────────────────────────────
        if self.ball_in_hand:
            if difficulty == 'hard' and target_balls:
                best_hand_pos = (888 + self.offset_x, 339 + self.offset_y)
                best_hand_score = -9999
                for tx in [550, 700, 850, 950, 1050]:
                    for ty in [200, 339, 480]:
                        cand = pymunk.Vec2d(tx + self.offset_x, ty + self.offset_y)
                        for ball in target_balls:
                            for pocket in self.pockets:
                                px = pocket[0] + self.offset_x
                                py = pocket[1] + self.offset_y
                                b_pos = ball.body.position
                                v_pb = b_pos - pymunk.Vec2d(px, py)
                                if v_pb.length == 0: continue
                                ghost = b_pos + v_pb.normalized() * self.dia
                                shot_v = ghost - cand
                                if shot_v.length == 0: continue
                                angle_diff = abs(shot_v.normalized().angle - (-v_pb).normalized().angle)
                                score = 1000 - v_pb.length - shot_v.length
                                if angle_diff > math.pi / 4:
                                    score -= 400
                                if score > best_hand_score:
                                    best_hand_score = score
                                    best_hand_pos = (cand.x, cand.y)
                self.cue_ball.body.position = best_hand_pos
            else:
                self.cue_ball.body.position = (888 + self.offset_x, 339 + self.offset_y)
            self.ball_in_hand = False

        cue_pos = self.cue_ball.body.position

        # ── Helper: does the cue-ball path pass near any ball? ───────────────
        def path_hits_ball(cue, direction, distance, exclude_bodies):
            """Very rough: check if shot direction passes within 2*dia of any non-target ball."""
            for ob in self.balls:
                if ob.body in exclude_bodies: continue
                ob_pos = ob.body.position
                # Project ob_pos onto the ray
                to_ob = ob_pos - cue
                proj = to_ob.dot(direction)
                if proj < 0 or proj > distance: continue
                perp = (to_ob - direction * proj).length
                if perp < self.dia * 2:
                    return ob
            return None

        # ── Easy bot ─────────────────────────────────────────────────────────
        if difficulty == 'easy':
            target_ball = random.choice(target_balls) if target_balls else None
            if target_ball:
                pocket = random.choice(self.pockets)
                px = pocket[0] + self.offset_x
                py = pocket[1] + self.offset_y
                v_x = target_ball.body.position.x - px
                v_y = target_ball.body.position.y - py
                mag = math.hypot(v_x, v_y)
                if mag > 0:
                    ghost_pos = target_ball.body.position + pymunk.Vec2d(v_x/mag * self.dia, v_y/mag * self.dia)
                    shot_v = ghost_pos - cue_pos
                    shot_v = shot_v.rotated(random.uniform(-0.18, 0.18))
                    self.bot_target_dir = shot_v.normalized() if shot_v.length > 0 else pymunk.Vec2d(1, 0)
                    self.bot_target_force = random.randint(3000, 6000)

        # ── Medium / Hard bot ────────────────────────────────────────────────
        else:
            best_score = -10000
            best_dir   = pymunk.Vec2d(1, 0)
            best_force = 7000

            for ball in target_balls:
                ball_body = ball.body
                for pocket in self.pockets:
                    px = pocket[0] + self.offset_x
                    py = pocket[1] + self.offset_y

                    b_pos = ball_body.position
                    v_pb  = b_pos - pymunk.Vec2d(px, py)
                    dist_to_pocket = v_pb.length
                    if dist_to_pocket == 0: continue

                    ghost_pos   = b_pos + v_pb.normalized() * self.dia
                    shot_v      = ghost_pos - cue_pos
                    dist_ghost  = shot_v.length
                    if dist_ghost == 0: continue

                    shot_dir = shot_v.normalized()

                    # ── Rule: do not accidentally pocket 8-ball unless it's the target
                    if not shooting_eight:
                        blocker = path_hits_ball(cue_pos, shot_dir, dist_ghost,
                                                 exclude_bodies={self.cue_ball.body, ball_body})
                        if blocker is not None:
                            bid = self.ball_types[blocker.body]
                            if bid == 8:
                                continue  # Skip this shot – would tap the 8-ball

                    # ── Rule: cue must not pocket opponent balls directly
                    # (we penalise rather than discard, for robustness)
                    opp_in_path = False
                    for ob in self.balls:
                        ob_id = self.ball_types[ob.body]
                        if ob_id not in opp_ids: continue
                        to_ob  = ob.body.position - cue_pos
                        proj   = to_ob.dot(shot_dir)
                        if proj < 0 or proj > dist_ghost: continue
                        if (to_ob - shot_dir * proj).length < self.dia * 1.5:
                            opp_in_path = True
                            break

                    # Angle quality
                    angle_diff = abs(shot_dir.angle - (-v_pb).normalized().angle)
                    while angle_diff > math.pi: angle_diff = abs(angle_diff - 2 * math.pi)

                    score = 1500 - dist_to_pocket * 0.8 - dist_ghost * 0.5
                    if opp_in_path:       score -= 1200   # heavy penalty for hitting opponent ball
                    if angle_diff > math.pi / 4: score -= 500
                    if angle_diff > math.pi / 2: score -= 1000

                    if score > best_score:
                        best_score = score
                        best_dir   = shot_dir
                        needed     = dist_to_pocket * 14 + dist_ghost * 9
                        best_force = min(self.max_force, max(6500, needed))

            if difficulty == 'medium':
                best_dir   = best_dir.rotated(random.uniform(-0.03, 0.03))
                best_force = min(self.max_force, max(5000, best_force * random.uniform(0.9, 1.05)))
            # hard: no noise at all

            self.bot_target_dir   = best_dir
            self.bot_target_force = best_force

        if self.bot_target_dir is None:
            self.bot_target_dir   = pymunk.Vec2d(1, 0)
            self.bot_target_force = 7000

    def shoot(self, override_dir=None, override_force=None):
        if self.snd_cue: self.snd_cue.play()
        
        if override_dir is not None and override_force is not None:
            dir_x, dir_y = override_dir.x, override_dir.y
            force = override_force
        else:
            mouse_pos = pygame.mouse.get_pos()
            cue_pos = self.cue_ball.body.position
            
            dir_x = mouse_pos[0] - cue_pos.x
            dir_y = mouse_pos[1] - cue_pos.y
            length = math.hypot(dir_x, dir_y)
            if length > 0:
                dir_x /= length
                dir_y /= length
            force = self.force
            
        self.cue_ball.body.apply_impulse_at_local_point((force * dir_x, force * dir_y), (0, 0))
        self.force = 0
        self.force_direction = 1
        self.state = MOVING

    def update(self):
        if self.winner is not None:
            return

        is_bot_turn = getattr(self.session, 'is_single_player', False) and self.current_player == 2
        
        if is_bot_turn and self.state == AIMING:
            if self.bot_timer == 0:
                self.bot_timer = pygame.time.get_ticks() + 1500 # 1.5s thinking time
            elif pygame.time.get_ticks() > self.bot_timer:
                self._bot_play()
                self.shoot(override_dir=self.bot_target_dir, override_force=self.bot_target_force)
                self.bot_timer = 0

        self.space.step(1 / 120.0)
        
        # Powering up logic
        if self.powering_up and self.state == AIMING:
            self.force += 100 * self.force_direction
            if self.force >= self.max_force or self.force <= 0:
                self.force_direction *= -1

        # Pocket checking
        balls_to_remove = []
        for ball in self.balls:
            for pocket in self.pockets:
                px = pocket[0] + self.offset_x
                py = pocket[1] + self.offset_y
                dist = math.hypot(ball.body.position.x - px, ball.body.position.y - py)
                if dist <= self.pocket_dia / 2:
                    balls_to_remove.append(ball)
                    break
                    
        for ball in balls_to_remove:
            ball_id = self.ball_types[ball.body]
            if ball_id == 0:
                self.foul = True
                self.ball_in_hand = True
                ball.body.position = (-1000, -1000)
                ball.body.velocity = (0, 0)
            else:
                self.space.remove(ball.body, *list(ball.body.shapes), *list(ball.body.constraints))
                self.balls.remove(ball)
                self.balls_potted_this_turn.append(ball_id)
                if self.snd_pocket: self.snd_pocket.play()
                
        # Check if movement stopped
        if self.state == MOVING:
            moving = False
            for ball in self.balls:
                if abs(ball.body.velocity.x) > 0.1 or abs(ball.body.velocity.y) > 0.1:
                    moving = True
                    break
                    
            if not moving:
                self.end_turn()

    def end_turn(self):
        self.state = AIMING
        
        current_group = self.p1_group if self.current_player == 1 else self.p2_group
        
        # Determine Groups
        if current_group is None:
            for b in self.balls_potted_this_turn:
                if b != 8 and b != 0:
                    group = self.get_group_name(b)
                    if self.current_player == 1:
                        self.p1_group = group
                        self.p2_group = "stripes" if group == "solids" else "solids"
                    else:
                        self.p2_group = group
                        self.p1_group = "stripes" if group == "solids" else "solids"
                    current_group = group
                    break
        
        turn_continues = False
        
        if self.first_ball_hit is None:
            self.foul = True
        elif current_group is not None:
            hit_group = self.get_group_name(self.first_ball_hit)
            if hit_group != current_group and hit_group != "black": 
                self.foul = True
            elif hit_group == "black" and not self.is_on_black(self.current_player):
                self.foul = True

        # Check win/loss conditions
        # If 8 ball is potted
        if 8 in self.balls_potted_this_turn:
            if self.is_on_black(self.current_player) and not self.foul:
                self.winner = self.current_player
                self.session.scores["player1" if self.winner == 1 else "player2"] += 1
            else:
                self.winner = 2 if self.current_player == 1 else 1
                self.session.scores["player1" if self.winner == 1 else "player2"] += 1
            return
        elif current_group is not None:
            for b in self.balls_potted_this_turn:
                if self.get_group_name(b) == current_group:
                    turn_continues = True
                
        if self.foul:
            self.ball_in_hand = True
            turn_continues = False
            
        self.balls_potted_this_turn = []
        self.first_ball_hit = None
        self.foul = False
        
        if not turn_continues:
            self.current_player = 2 if self.current_player == 1 else 1
            
        if self.ball_in_hand:
            self.cue_ball.body.position = (888 + self.offset_x, 339 + self.offset_y)
            self.cue_ball.body.velocity = (0, 0)

    def draw_prediction_line(self):
        if not self.cue_ball or self.ball_in_hand or self.state == MOVING: return
        
        mouse_pos = pygame.mouse.get_pos()
        cue_pos = self.cue_ball.body.position
        
        dir_x = mouse_pos[0] - cue_pos.x
        dir_y = mouse_pos[1] - cue_pos.y
        length = math.hypot(dir_x, dir_y)
        if length == 0: return
        dir_x /= length
        dir_y /= length
        
        dir_vec = pymunk.Vec2d(dir_x, dir_y)
        start = cue_pos
        end = start + dir_vec * 2000
        
        shapes_to_restore = list(self.cue_ball.body.shapes)
        for s in shapes_to_restore: self.space.remove(s)
        
        try:
            shape_filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
            info = self.space.segment_query_first(start, end, self.dia/2, shape_filter)
        finally:
            for s in shapes_to_restore: self.space.add(s)
        
        if info:
            impact_center = start + (end - start) * info.alpha
            
            pygame.draw.line(self.screen, (255, 255, 255), (int(start.x), int(start.y)), (int(impact_center.x), int(impact_center.y)), 1)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(impact_center.x), int(impact_center.y)), int(self.dia/2), 1)
            
            hit_body = info.shape.body
            if hit_body in self.ball_types and self.ball_types[hit_body] != 0:
                target_pos = hit_body.position
                target_dir = target_pos - impact_center
                if target_dir.length > 0:
                    target_dir = target_dir.normalized()
                    pred_end = target_pos + target_dir * 150
                    pygame.draw.line(self.screen, (255, 255, 0), (int(target_pos.x), int(target_pos.y)), (int(pred_end.x), int(pred_end.y)), 2)
                    
                    dot = dir_vec.dot(target_dir)
                    cue_deflect_dir = dir_vec - target_dir * dot
                    if cue_deflect_dir.length > 0:
                        cue_deflect_dir = cue_deflect_dir.normalized()
                        cue_pred_end = impact_center + cue_deflect_dir * 100
                        pygame.draw.line(self.screen, (255, 255, 255), (int(impact_center.x), int(impact_center.y)), (int(cue_pred_end.x), int(cue_pred_end.y)), 1)

    def draw_player_balls(self, player, x, y):
        group = self.p1_group if player == 1 else self.p2_group
        if not group: return
        
        if group == "solids": target_balls = list(range(1, 8))
        else: target_balls = list(range(9, 16))
            
        active_balls = [b for b in target_balls if self.is_ball_on_table(b)]
        if len(active_balls) == 0:
            target_balls = [8]
            active_balls = [8] if self.is_ball_on_table(8) else []
            
        for i, b_id in enumerate(target_balls):
            img = self.small_ball_images.get(b_id)
            if img:
                if b_id not in active_balls:
                    img = img.copy()
                    img.set_alpha(80)
                self.screen.blit(img, (x + i * 28, y))

    def draw(self):
        self.screen.fill(self.BG)
        self.screen.blit(self.table_image, (self.offset_x, self.offset_y))
        
        for ball in self.balls:
            ball_id = self.ball_types[ball.body]
            if ball_id == 0 and self.ball_in_hand:
                continue 
            img = self.ball_images.get(ball_id)
            if img:
                pos = ball.body.position
                self.screen.blit(img, (pos.x - self.dia/2, pos.y - self.dia/2))
                
        if self.ball_in_hand:
            mpos = pygame.mouse.get_pos()
            img = self.ball_images.get(0)
            if img:
                self.screen.blit(img, (mpos[0] - self.dia/2, mpos[1] - self.dia/2))
                
        if self.state == AIMING and not self.ball_in_hand:
            mouse_pos = pygame.mouse.get_pos()
            cue_pos = self.cue_ball.body.position
            dir_x = mouse_pos[0] - cue_pos.x
            dir_y = mouse_pos[1] - cue_pos.y
            
            cue_angle = math.degrees(math.atan2(-dir_y, dir_x)) + 180
            cue_rotated = pygame.transform.rotate(self.cue_image_orig, cue_angle)
            
            pull_back = 0
            if self.powering_up:
                pull_back = (self.force / self.max_force) * 40
            
            offset_dist = self.dia/2 + 10 + pull_back
            
            length = math.hypot(dir_x, dir_y)
            if length > 0:
                dx = dir_x / length
                dy = dir_y / length
                cue_rect = cue_rotated.get_rect(center=(cue_pos.x - dx * offset_dist, cue_pos.y - dy * offset_dist))
                self.screen.blit(cue_rotated, cue_rect)
                
        self.draw_prediction_line()
        
        # Bot aiming line visualization
        is_bot_turn = getattr(self.session, 'is_single_player', False) and self.current_player == 2
        if is_bot_turn and self.state == AIMING and self.bot_timer > 0:
            pygame.draw.circle(self.screen, (255, 0, 0), (int(self.cue_ball.body.position.x), int(self.cue_ball.body.position.y)), 10, 2)
            self.draw_persian_text("Bot Thinking...", (255, 100, 100), (int(self.cue_ball.body.position.x) - 40, int(self.cue_ball.body.position.y) - 40), self.font)
        
        # UI
        p1_name = self.session.player1_name
        p2_name = self.session.player2_name
        
        # Draw turn indicator in center
        current_name = p1_name if self.current_player == 1 else p2_name
        turn_raw = f"turn's: {reshape_persian(current_name)}"
        self.draw_persian_text(reshape_persian(turn_raw), (0, 255, 100), (self.width//2 - 100, 20), self.font)
        
        # Player indicators
        p1_color = self.ACCENT if self.current_player == 1 else (100, 100, 100)
        p2_color = self.ACCENT if self.current_player == 2 else (100, 100, 100)
        
        p1_raw = f"{'▶ ' if self.current_player == 1 else ''}{reshape_persian(p1_name)}"
        p2_raw = f"{'▶ ' if self.current_player == 2 else ''}{reshape_persian(p2_name)}"
        
        self.draw_persian_text(reshape_persian(p1_raw), p1_color, (50, 15), self.font)
        self.draw_persian_text(reshape_persian(p2_raw), p2_color, (self.width - 350, 15), self.font)
        
        # Draw small ball icons
        self.draw_player_balls(1, 50, 50)
        self.draw_player_balls(2, self.width - 350, 50)
        
        if self.ball_in_hand and self.state == AIMING:
            self.draw_persian_text("Ball in Hand - Click to place", (255, 100, 100), (self.width//2 - 150, 20), self.font)
        
        if self.powering_up:
            bar_w = int(self.force / self.max_force * 300)
            pygame.draw.rect(self.screen, (255,0,0), (self.width//2 - 150, self.height - 40, bar_w, 20))
            pygame.draw.rect(self.screen, (255,255,255), (self.width//2 - 150, self.height - 40, 300, 20), 2)
            
        if self.winner is not None:
            winner_name = self.session.player1_name if self.winner == 1 else self.session.player2_name
            win_raw = f"{reshape_persian(winner_name)} Wins!"
            self.draw_persian_text(reshape_persian(win_raw), (255, 255, 0), (self.width//2 - 100, self.height//2 - 50), self.large_font)
            self.draw_persian_text(reshape_persian("To exit the game click esc"), (200, 200, 200), (self.width//2 - 150, self.height//2 + 20), self.font)
        else:
            if self.foul:
                self.draw_persian_text(reshape_persian("foul!"), (255, 100, 100), (self.width//2 - 40, self.height - 50), self.large_font)