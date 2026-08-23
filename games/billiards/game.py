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
        self.bot_start_dir = pymunk.Vec2d(1, 0)
        self.bot_target_force = 0
        
        # Ball-in-hand preview for bot
        self.bot_place_pos = None        # where the bot will place the cue ball
        self.bot_place_timer = 0         # ticks when preview started
        self.bot_placing = False         # True while showing preview before placing
        
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

        # Standard BCA/WPA rack: 8-ball in center (row 3, middle position)
        # Triangle (5 columns, apex at left):
        #  col0: [1]
        #  col1: [2][9]
        #  col2: [3][8][10]  <- 8 in the middle slot
        #  col3: [4][11][5][12]
        #  col4: [13][6][14][7][15]
        # Each column is centered vertically around the table mid-line.
        rack_cols = [
            [1],
            [2, 9],
            [3, 8, 10],
            [4, 11, 5, 12],
            [13, 6, 14, 7, 15],
        ]
        step = self.dia + 1          # gap between ball centers
        apex_x = 250 + self.offset_x
        center_y = 339 + self.offset_y   # vertical center of table
        for col_idx, col_balls in enumerate(rack_cols):
            x = apex_x + col_idx * step
            n = len(col_balls)
            # Center the column around center_y
            col_top_y = center_y - (n - 1) * step / 2
            for row_idx, ball_id in enumerate(col_balls):
                y = col_top_y + row_idx * step
                b = self.create_ball(self.dia / 2, (x, y), ball_id)
                self.balls.append(b)
                self.ball_types[b.body] = ball_id
            
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

        # Block all player mouse input during bot's turn
        is_bot_turn = getattr(self.session, 'is_single_player', False) and self.current_player == 2
        if is_bot_turn:
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
            # ── Open Table: Evaluate which group is easier ──────────────────
            solids = [b for b in self.balls if self.ball_types[b.body] in range(1, 8)]
            stripes = [b for b in self.balls if self.ball_types[b.body] in range(9, 16)]
            
            def eval_group(group_balls):
                if not group_balls: return 999999
                total_dist = 0
                for gb in group_balls:
                    best_d = 999999
                    for pocket in self.pockets:
                        px = pocket[0] + self.offset_x
                        py = pocket[1] + self.offset_y
                        d = (gb.body.position - pymunk.Vec2d(px, py)).length
                        if d < best_d: best_d = d
                    total_dist += best_d
                return total_dist / len(group_balls)
            
            score_solids = eval_group(solids)
            score_stripes = eval_group(stripes)
            
            if score_solids <= score_stripes:
                target_balls = solids
            else:
                target_balls = stripes

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

        # ── Helper: does the cue-ball path pass near any ball? ───────────────
        def path_hits_ball(start_pos, direction, distance, exclude_bodies):
            for ob in self.balls:
                if ob.body in exclude_bodies: continue
                ob_pos = ob.body.position
                to_ob = ob_pos - start_pos
                proj = to_ob.dot(direction)
                if proj < 0 or proj > distance: continue
                perp = (to_ob - direction * proj).length
                if perp < self.dia * 0.99:
                    return ob
            return None

        # ── Smart ball-in-hand placement ─────────────────────────────────────
        if self.ball_in_hand:
            if difficulty == 'hard' and target_balls:
                best_hand_pos = (888 + self.offset_x, 339 + self.offset_y)
                best_hand_score = -9999
                aim_pockets = [(75, 75), (592, 68), (1114, 75), (75, 604), (592, 610), (1114, 604)]
                
                min_x = self.offset_x + 77 + self.dia/2
                max_x = self.offset_x + 1122 - self.dia/2
                min_y = self.offset_y + 77 + self.dia/2
                max_y = self.offset_y + 600 - self.dia/2

                # Very fine grid search for hard bot over ENTIRE table
                for tx in range(100, 1100, 25):
                    for ty in range(100, 550, 25):
                        cand = pymunk.Vec2d(tx + self.offset_x, ty + self.offset_y)
                        
                        collision = False
                        for ob in self.balls:
                            if (ob.body.position - cand).length < self.dia * 1.2:
                                collision = True
                                break
                        if collision: continue
                        
                        for ball in target_balls:
                            for p_idx, pocket in enumerate(self.pockets):
                                px = aim_pockets[p_idx][0] + self.offset_x
                                py = aim_pockets[p_idx][1] + self.offset_y
                                b_pos = ball.body.position
                                v_pb = b_pos - pymunk.Vec2d(px, py)
                                dist_to_pocket = v_pb.length
                                if dist_to_pocket == 0: continue
                                
                                ball_travel_dir = -v_pb.normalized()
                                ghost = b_pos + v_pb.normalized() * self.dia
                                
                                if ghost.x < min_x or ghost.x > max_x or ghost.y < min_y or ghost.y > max_y:
                                    continue
                                    
                                shot_v = ghost - cand
                                dist_ghost = shot_v.length
                                if dist_ghost == 0: continue
                                shot_dir = shot_v.normalized()
                                
                                dot_cut = max(-1.0, min(1.0, shot_dir.dot(ball_travel_dir)))
                                cut_angle = math.acos(dot_cut)
                                if cut_angle > math.pi / 2 + 0.05: continue
                                
                                # Check paths
                                if path_hits_ball(cand, shot_dir, dist_ghost, {ball.body}): continue
                                if path_hits_ball(b_pos, ball_travel_dir, dist_to_pocket, {ball.body}): continue
                                
                                cut_penalty = cut_angle * (dist_to_pocket + 100) * 3.0
                                dist_penalty = dist_to_pocket * 1.5 + dist_ghost * 1.0
                                score = 10000.0 - dist_penalty - cut_penalty
                                
                                if score > best_hand_score:
                                    best_hand_score = score
                                    best_hand_pos = (cand.x, cand.y)
                # Store preview position – actual placement happens after a visual delay
                self.bot_place_pos = best_hand_pos
            else:
                self.bot_place_pos = (888 + self.offset_x, 339 + self.offset_y)
            
            # Start preview: show ball at bot_place_pos for 1.2 seconds before confirming
            self.bot_placing = True
            self.bot_place_timer = pygame.time.get_ticks()
            return  # Don't place yet; placement happens in update()

        cue_pos = self.cue_ball.body.position



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
            best_score = -99999
            best_dir   = pymunk.Vec2d(1, 0)
            best_force = 7000

            aim_pockets = [(75, 75), (592, 68), (1114, 75), (75, 604), (592, 610), (1114, 604)]
            for ball in target_balls:
                ball_body = ball.body
                for p_idx, pocket in enumerate(self.pockets):
                    px = aim_pockets[p_idx][0] + self.offset_x
                    py = aim_pockets[p_idx][1] + self.offset_y

                    b_pos = ball_body.position
                    # Vector from pocket to ball
                    v_pb  = b_pos - pymunk.Vec2d(px, py)
                    dist_to_pocket = v_pb.length
                    if dist_to_pocket == 0: continue

                    # Ghost ball position: where cue ball must be at impact
                    v_pb_norm = v_pb.normalized()
                    ghost_pos   = b_pos + v_pb_norm * self.dia
                    shot_v      = ghost_pos - cue_pos
                    dist_ghost  = shot_v.length
                    if dist_ghost == 0: continue

                    shot_dir = shot_v.normalized()

                    # ── Cut angle: how "straight" is this shot? ──────────────
                    # The target ball must travel from b_pos toward pocket.
                    # Direction ball travels after impact = -v_pb_norm (toward pocket)
                    ball_travel_dir = -v_pb_norm
                    # Cut angle = angle between cue direction and ball travel direction
                    # 0 = straight shot (easy), pi/2 = max thin cut (hard)
                    dot_cut = max(-1.0, min(1.0, shot_dir.dot(ball_travel_dir)))
                    cut_angle = math.acos(dot_cut)  # 0..pi

                    # Shots with cut_angle > 90 deg are physically impossible
                    # (cue would push ball away from pocket)
                    if cut_angle > math.pi / 2 + 0.05:
                        continue

                    # ── Check if ghost pos is valid (not inside cushion) ─────────
                    min_x = self.offset_x + 77 + self.dia/2
                    max_x = self.offset_x + 1122 - self.dia/2
                    min_y = self.offset_y + 77 + self.dia/2
                    max_y = self.offset_y + 600 - self.dia/2
                    if ghost_pos.x < min_x or ghost_pos.x > max_x or ghost_pos.y < min_y or ghost_pos.y > max_y:
                        continue # Impossible to hit ghost ball without hitting rail first
                        
                    # ── Check if any ball blocks the cue path to ghost ball ──────
                    blocker = path_hits_ball(cue_pos, shot_dir, dist_ghost,
                                             exclude_bodies={self.cue_ball.body, ball_body})
                    path_blocked = blocker is not None

                    # ── Check if target ball's path to pocket is blocked ─────────
                    target_blocker = path_hits_ball(b_pos, ball_travel_dir, dist_to_pocket,
                                                    exclude_bodies={ball_body, self.cue_ball.body})
                    target_path_blocked = target_blocker is not None

                    # ── 8-ball danger checks ────────────────────────────────────
                    eight_danger = False
                    if not shooting_eight:
                        if path_blocked and blocker is not None:
                            bid = self.ball_types[blocker.body]
                            if bid == 8:
                                eight_danger = True

                        # Check if target ball after impact could roll near 8-ball
                        if not eight_danger and eight_ball:
                            eight_pos = eight_ball[0].body.position
                            to_eight = eight_pos - b_pos
                            proj_eight = to_eight.dot(ball_travel_dir)
                            if 0 < proj_eight < dist_to_pocket:
                                perp_eight = (to_eight - ball_travel_dir * proj_eight).length
                                if perp_eight < self.dia * 1.5:
                                    eight_danger = True

                    # ── Opponent ball in cue path ───────────────────────────────
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

                    # ── Score calculation ───────────────────────────────────────
                    cut_penalty = cut_angle * (dist_to_pocket + 100) * 3.0
                    dist_penalty = dist_to_pocket * 1.5 + dist_ghost * 1.0
                    
                    score = 10000.0 - dist_penalty - cut_penalty

                    if path_blocked:    score -= 4000
                    if target_path_blocked: score -= 4000
                    if eight_danger:    score -= 5000
                    if opp_in_path:     score -= 2000

                    if score > best_score:
                        best_score = score
                        best_dir   = shot_dir
                        # Calculate force needed to reach pocket
                        needed = dist_to_pocket * 14 + dist_ghost * 8
                        # 5000 min force guarantees the ball reaches the pocket!
                        best_force = min(self.max_force, max(5000, needed))

            if difficulty == 'medium':
                # Medium: slight random aim error and force variation
                best_dir   = best_dir.rotated(random.uniform(-0.05, 0.05))
                best_force = min(self.max_force, max(4500, best_force * random.uniform(0.85, 1.1)))
            # hard: zero noise — perfect aim

            self.bot_start_dir    = self.bot_target_dir if self.bot_target_dir else pymunk.Vec2d(1, 0)
            self.bot_target_dir   = best_dir
            self.bot_target_force = best_force

        if self.bot_target_dir is None:
            self.bot_start_dir    = pymunk.Vec2d(1, 0)
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
        
        # Handle bot ball-in-hand visual preview
        if is_bot_turn and self.bot_placing:
            if self.bot_place_pos is not None:
                # Show cue ball at preview position during delay
                self.cue_ball.body.position = self.bot_place_pos
                self.cue_ball.body.velocity = (0, 0)
            # After 1.4 seconds, confirm placement
            if pygame.time.get_ticks() - self.bot_place_timer > 1400:
                self.bot_placing = False
                self.ball_in_hand = False
                self.bot_timer = 0  # reset so bot starts thinking fresh
            return  # Don't do anything else while placing
        
        if is_bot_turn and self.state == AIMING:
            if self.bot_timer == 0:
                # Compute shot IMMEDIATELY so we can visualize it during the thinking delay
                self._bot_play()
                if not self.bot_placing:
                    self.bot_timer = pygame.time.get_ticks() + 1800  # 1.8s show visualization
            elif pygame.time.get_ticks() > self.bot_timer:
                if not self.bot_placing:
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

    def _draw_prediction_for_dir(self, dir_x, dir_y):
        """Draw prediction line for a given normalized direction (used by bot visualization)."""
        if not self.cue_ball or self.ball_in_hand or self.state == MOVING: return
        length = math.hypot(dir_x, dir_y)
        if length == 0: return
        dir_x /= length
        dir_y /= length

        dir_vec = pymunk.Vec2d(dir_x, dir_y)
        cue_pos = self.cue_ball.body.position
        start = cue_pos
        end = start + dir_vec * 2000

        shapes_to_restore = list(self.cue_ball.body.shapes)
        for s in shapes_to_restore: self.space.remove(s)
        try:
            shape_filter = pymunk.ShapeFilter(mask=pymunk.ShapeFilter.ALL_MASKS())
            info = self.space.segment_query_first(start, end, self.dia / 2, shape_filter)
        finally:
            for s in shapes_to_restore: self.space.add(s)

        if info:
            impact_center = start + (end - start) * info.alpha
            pygame.draw.line(self.screen, (255, 255, 255),
                             (int(start.x), int(start.y)), (int(impact_center.x), int(impact_center.y)), 1)
            pygame.draw.circle(self.screen, (255, 255, 255),
                               (int(impact_center.x), int(impact_center.y)), int(self.dia / 2), 1)
            hit_body = info.shape.body
            if hit_body in self.ball_types and self.ball_types[hit_body] != 0:
                target_pos = hit_body.position
                target_dir = target_pos - impact_center
                if target_dir.length > 0:
                    target_dir = target_dir.normalized()
                    pred_end = target_pos + target_dir * 150
                    pygame.draw.line(self.screen, (255, 255, 0),
                                     (int(target_pos.x), int(target_pos.y)), (int(pred_end.x), int(pred_end.y)), 2)
                    dot = dir_vec.dot(target_dir)
                    cue_deflect_dir = dir_vec - target_dir * dot
                    if cue_deflect_dir.length > 0:
                        cue_deflect_dir = cue_deflect_dir.normalized()
                        cue_pred_end = impact_center + cue_deflect_dir * 100
                        pygame.draw.line(self.screen, (255, 255, 255),
                                         (int(impact_center.x), int(impact_center.y)),
                                         (int(cue_pred_end.x), int(cue_pred_end.y)), 1)

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
                
        is_bot_turn = getattr(self.session, 'is_single_player', False) and self.current_player == 2

        if self.state == AIMING and not self.ball_in_hand:
            cue_pos = self.cue_ball.body.position

            if is_bot_turn and self.bot_timer > 0 and self.bot_target_dir is not None:
                # ── Bot turn: sweeping aim and power visualization ───────────
                think_start = self.bot_timer - 1800
                elapsed_think = pygame.time.get_ticks() - think_start
                progress = max(0.0, min(1.0, elapsed_think / 1800.0))

                # Phase 1: Sweeping aim (0.0 to 0.6)
                # Phase 2: Powering up (0.6 to 1.0)
                aim_progress = min(1.0, progress / 0.6)
                power_progress = max(0.0, (progress - 0.6) / 0.4)

                start_angle = self.bot_start_dir.angle
                target_angle = self.bot_target_dir.angle

                # Shortest path interpolation for angles
                angle_diff = (target_angle - start_angle + math.pi) % (2 * math.pi) - math.pi
                # Ease-out sine interpolation
                current_angle = start_angle + angle_diff * math.sin(aim_progress * math.pi / 2)

                dir_x, dir_y = math.cos(current_angle), math.sin(current_angle)

                # Cue pullback animates from 0 → max during phase 2
                pull_ratio = self.bot_target_force / self.max_force
                pull_back = power_progress * pull_ratio * 40

                cue_angle = math.degrees(math.atan2(-dir_y, dir_x)) + 180
                cue_rotated = pygame.transform.rotate(self.cue_image_orig, cue_angle)
                offset_dist = self.dia / 2 + 10 + pull_back
                cue_rect = cue_rotated.get_rect(
                    center=(cue_pos.x - dir_x * offset_dist, cue_pos.y - dir_y * offset_dist)
                )
                self.screen.blit(cue_rotated, cue_rect)

                # Draw bot prediction line using current interpolated direction
                self._draw_prediction_for_dir(dir_x, dir_y)

                # Animated power bar
                bar_fill = power_progress * pull_ratio
                bar_w = int(bar_fill * 300)
                pygame.draw.rect(self.screen, (50, 50, 50),
                                 (self.width // 2 - 150, self.height - 45, 300, 22), border_radius=6)
                bar_color = (80, 220, 80) if bar_fill < 0.5 else (255, 160, 0) if bar_fill < 0.8 else (255, 50, 50)
                if bar_w > 0:
                    pygame.draw.rect(self.screen, bar_color,
                                     (self.width // 2 - 150, self.height - 45, bar_w, 22), border_radius=6)
                pygame.draw.rect(self.screen, (220, 220, 220),
                                 (self.width // 2 - 150, self.height - 45, 300, 22), 2, border_radius=6)
                # Label
                pow_label = self.font.render(f"Power: {int(bar_fill*100)}%", True, (255, 255, 255))
                self.screen.blit(pow_label, (self.width // 2 - 150, self.height - 70))

            else:
                # ── Player turn: normal mouse-based cue ──────────────────────
                mouse_pos = pygame.mouse.get_pos()
                dir_x = mouse_pos[0] - cue_pos.x
                dir_y = mouse_pos[1] - cue_pos.y

                cue_angle = math.degrees(math.atan2(-dir_y, dir_x)) + 180
                cue_rotated = pygame.transform.rotate(self.cue_image_orig, cue_angle)

                pull_back = 0
                if self.powering_up:
                    pull_back = (self.force / self.max_force) * 40

                offset_dist = self.dia / 2 + 10 + pull_back
                length = math.hypot(dir_x, dir_y)
                if length > 0:
                    dx = dir_x / length
                    dy = dir_y / length
                    cue_rect = cue_rotated.get_rect(
                        center=(cue_pos.x - dx * offset_dist, cue_pos.y - dy * offset_dist)
                    )
                    self.screen.blit(cue_rotated, cue_rect)

                self.draw_prediction_line()
        
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
            is_bot_turn = getattr(self.session, 'is_single_player', False) and self.current_player == 2
            if is_bot_turn:
                self.draw_persian_text("Bot choosing position...", (255, 180, 50), (self.width//2 - 160, 20), self.font)
            else:
                self.draw_persian_text("Ball in Hand - Click to place", (255, 100, 100), (self.width//2 - 150, 20), self.font)
        
        # Bot ball-in-hand preview: show ghost cue ball with animated ring
        is_bot_turn_draw = getattr(self.session, 'is_single_player', False) and self.current_player == 2
        if is_bot_turn_draw and self.bot_placing and self.bot_place_pos is not None:
            px, py = int(self.bot_place_pos[0]), int(self.bot_place_pos[1])
            # Draw cue ball image at preview position
            img = self.ball_images.get(0)
            if img:
                self.screen.blit(img, (px - self.dia//2, py - self.dia//2))
            # Pulsing ring to highlight placement
            elapsed = pygame.time.get_ticks() - self.bot_place_timer
            pulse = abs(math.sin(elapsed / 200.0))
            ring_r = int(self.dia * 0.8 + pulse * 10)
            ring_alpha = int(180 + pulse * 75)
            ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (255, 220, 50, ring_alpha), (ring_r+2, ring_r+2), ring_r, 3)
            self.screen.blit(ring_surf, (px - ring_r - 2, py - ring_r - 2))
        
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
