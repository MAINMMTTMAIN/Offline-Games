import pygame
import random
import math
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path

class Snakeladders(BaseGame):
    """Custom Cyberpunk Snakes and Ladders with high-end animations and manual piece activation."""
    
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width  = screen.get_width()
        self.height = screen.get_height()

        # ── پالت رنگی سایبرپانک ارتقا یافته ───────────────────────────────────
        self.C = {
            "bg":           (10, 10, 20),
            "board_bg":     (14, 16, 32),
            "grid_border":  (25, 32, 58),
            "cell_even":    (20, 24, 45),
            "cell_odd":     (25, 30, 56),
            "border":       (0, 235, 255),
            "ladder":       (0, 255, 160),    # سبز فسفری نئون
            "ladder_rail":  (0, 150, 100),
            "snake":        (255, 0, 100),    # صورتی/قرمز نئون داغ
            "snake_head":   (255, 80, 150),
            "p1":           (0, 235, 255),    # فیروزه‌ای
            "p2":           (255, 215, 0),    # طلایی
            "panel":        (16, 18, 32),
            "text":         (225, 230, 255),
            "text_dim":     (100, 110, 150),
            "dice_bg":      (22, 24, 44),
        }

        self.fL  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 46)
        self.fM  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 24)
        self.fS  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        self.fXS = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 12)

        # مارها و نردبان‌های سفارشی شما
        self.ladders = {3: 22, 8: 30, 28: 65, 52: 75, 58: 77, 62: 81, 69: 91}
        self.snakes  = {17: 4, 43: 18, 54: 31, 67: 46, 89: 48, 93: 71, 98: 79}

        self._layout()
        self.reset_game()

    def _layout(self):
        W, H = self.width, self.height
        self.pnl_w = max(180, int(W * 0.18))
        self.pnl_x = W - self.pnl_w - 18
        self.pnl_y = int(H * 0.07)
        self.pnl_h = int(H * 0.86)

        self.bx = 18
        self.by = int(H * 0.07)
        self.bw = self.pnl_x - 36
        self.bh = int(H * 0.86)
        
        self.cell_w = self.bw // 10
        self.cell_h = self.bh // 10
        self.roll_btn = pygame.Rect(0, 0, 0, 0)

    def reset_game(self):
        self.p_pos = [1, 1]  
        self.cur_p = 1       
        self.last_roll = 1
        self.state = "ROLL"  # ROLL | ANIMATING_DICE | WAIT_CLICK | MOVING_STEPS | MOVING_SPECIAL | GAME_OVER
        self.winner = None
        self.message = "Roll to start!"
        
        # سیستم انیمیشن تاس
        self.anim_frames_left = 0
        self.anim_current_val = 1

        # سیستم انیمیشن حرکت مهره‌ها روی ماتریکس صفحه
        self.anim_path = []       # لیست نقاط (x, y) برای حرکت نرم
        self.anim_step_index = 0
        self.target_cell_after_steps = None

    def _get_cell_coords(self, num):
        if num < 1 or num > 100: return (0, 0)
        zero_indexed = num - 1
        row = zero_indexed // 10
        col = zero_indexed % 10
        if row % 2 == 1:
            col = 9 - col
        x = self.bx + col * self.cell_w + self.cell_w // 2
        y = self.by + self.bh - (row * self.cell_h) - self.cell_h // 2
        return (x, y)

    def _roll(self):
        if self.state != "ROLL": return
        self.state = "ANIMATING_DICE"
        self.anim_frames_left = 15

    def _start_player_movement(self):
        """ساخت مسیر حرکت خانه‌به-خانه بعد از کلیک روی مهره"""
        p_idx = self.cur_p - 1
        start = self.p_pos[p_idx]
        steps = self.last_roll
        
        if start + steps > 100:
            self.message = "Need exact roll to win!"
            self.cur_p = 2 if self.cur_p == 1 else 1
            self.state = "ROLL"
            return

        # ایجاد مسیر فریم‌به-فریم برای حرکت بین خانه‌ها
        self.anim_path = []
        current = start
        for _ in range(steps):
            next_cell = current + 1
            p_from = self._get_cell_coords(current)
            p_to = self._get_cell_coords(next_cell)
            # ۱۰ فریم انیمیشن رفتن از یک خانه به خانه بعدی
            for f in range(11):
                t = f / 10.0
                cx = p_from[0] + (p_to[0] - p_from[0]) * t
                cy = p_from[1] + (p_to[1] - p_from[1]) * t
                self.anim_path.append((cx, cy))
            current = next_cell

        self.p_pos[p_idx] = current
        self.target_cell_after_steps = current
        self.anim_step_index = 0
        self.state = "MOVING_STEPS"

    def update(self):
        # ۱. انیمیشن چرخیدن تاس
        if self.state == "ANIMATING_DICE":
            if self.anim_frames_left > 0:
                self.anim_current_val = random.randint(1, 6)
                self.anim_frames_left -= 1
            else:
                self.last_roll = random.randint(1, 6)
                self.state = "WAIT_CLICK"
                self.message = "Click your checker to move!"

        # ۲. انیمیشن حرکت دونه‌دونه خانه‌ها
        elif self.state == "MOVING_STEPS":
            if self.anim_step_index < len(self.anim_path):
                self.anim_step_index += 2  # سرعت حرکت بین خانه‌ها
            else:
                # پایان حرکت عادی، حالا بررسی مار یا نردبان
                cell = self.target_cell_after_steps
                p_idx = self.cur_p - 1
                
                if cell in self.ladders:
                    self._setup_special_move(cell, self.ladders[cell], is_snake=False)
                elif cell in self.snakes:
                    self._setup_special_move(cell, self.snakes[cell], is_snake=True)
                else:
                    self._finish_turn()

        # ۳. انیمیشن صعود نردبان یا سر خوردن مارپیچ مار
        elif self.state == "MOVING_SPECIAL":
            if self.anim_step_index < len(self.anim_path):
                self.anim_step_index += 1  # حرکت نرم روی سازه‌ها
            else:
                self._finish_turn()

    def _setup_special_move(self, start_cell, end_cell, is_snake):
        p_from = self._get_cell_coords(start_cell)
        p_to = self._get_cell_coords(end_cell)
        self.anim_path = []
        
        frames = 40
        for f in range(frames + 1):
            t = f / float(frames)
            # خط مستقیم پایه
            cx = p_from[0] + (p_to[0] - p_from[0]) * t
            cy = p_from[1] + (p_to[1] - p_from[1]) * t
            
            if is_snake:
                # فرمول ریاضی سینوسی برای ایجاد پیچ و تاب مهره هنگام پایین آمدن از مار
                wave = math.sin(t * math.pi * 3) * 25 
                cx += wave
                
            self.anim_path.append((cx, cy))
            
        self.p_pos[self.cur_p - 1] = end_cell
        self.anim_step_index = 0
        self.message = "Sssnake bite!" if is_snake else "Climbing Ladder!"
        self.state = "MOVING_SPECIAL"

    def _finish_turn(self):
        p_idx = self.cur_p - 1
        if self.p_pos[p_idx] == 100:
            self.state = "GAME_OVER"
            self.winner = self.cur_p
            key = "player1" if self.cur_p == 1 else "player2"
            self.session.scores[key] += 1
            return
            
        self.state = "ROLL"
        self.message = "Next roll!"
        self.cur_p = 2 if self.cur_p == 1 else 1

    def handle_events(self, events):
        super().handle_events(events)
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                elif ev.key == pygame.K_SPACE:
                    if self.state == "ROLL": self._roll()
                    elif self.state == "GAME_OVER": self.reset_game()
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state == "ROLL" and self.roll_btn.collidepoint(ev.pos):
                    self._roll()
                elif self.state == "WAIT_CLICK":
                    # بررسی کلیک روی مهره بازیکن نوبت فعلی
                    p_coord = self._get_cell_coords(self.p_pos[self.cur_p - 1])
                    p_rect = pygame.Rect(p_coord[0] - 20, p_coord[1] - 20, 40, 40)
                    if p_rect.collidepoint(ev.pos):
                        self._start_player_movement()

    # ═════════════════════════════════════════════════════════════════════
    # بخش رندرینگ گرافیکی پیشرفته
    # ═════════════════════════════════════════════════════════════════════

    def draw(self):
        self.screen.fill(self.C["bg"])
        self._draw_board()
        self._draw_ladders_graphic()
        self._draw_snakes_graphic()
        self._draw_players()
        self._draw_panel()
        if self.state == "GAME_OVER":
            self._draw_gameover()

    def _draw_board(self):
        pygame.draw.rect(self.screen, self.C["board_bg"], (self.bx, self.by, self.bw, self.bh))
        pygame.draw.rect(self.screen, self.C["border"], (self.bx, self.by, self.bw, self.bh), 3, border_radius=4)

        for i in range(1, 101):
            cx, cy = self._get_cell_coords(i)
            rx, ry = cx - self.cell_w // 2, cy - self.cell_h // 2
            cell_color = self.C["cell_even"] if i % 2 == 0 else self.C["cell_odd"]
            pygame.draw.rect(self.screen, cell_color, (rx, ry, self.cell_w, self.cell_h))
            pygame.draw.rect(self.screen, self.C["grid_border"], (rx, ry, self.cell_w, self.cell_h), 1)
            num_s = self.fXS.render(str(i), True, self.C["text_dim"])
            self.screen.blit(num_s, (rx + 5, ry + 5))

    def _draw_ladders_graphic(self):
        """رسم سازه واقعی نردبان با دو ریل نئونی و پله‌های داخلی متقاطع"""
        for start, end in self.ladders.items():
            p1 = self._get_cell_coords(start)
            p2 = self._get_cell_coords(end)
            
            # محاسبه زاویه و بردار عمود برای ایجاد عرض نردبان
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            length = math.hypot(dx, dy)
            if length == 0: continue
            ux, uy = dx / length, dy / length
            vx, vy = -uy * 10, ux * 10  # آفست ۱۰ پیکسلی به طرفین
            
            # ریل چپ و راست
            r1_s = (p1[0] + vx, p1[1] + vy)
            r1_e = (p2[0] + vx, p2[1] + vy)
            r2_s = (p1[0] - vx, p1[1] - vy)
            r2_e = (p2[0] - vx, p2[1] - vy)
            
            pygame.draw.line(self.screen, self.C["ladder_rail"], r1_s, r1_e, 3)
            pygame.draw.line(self.screen, self.C["ladder_rail"], r2_s, r2_e, 3)
            
            # رسم پله‌های نردبان به فواصل منظم
            steps = int(length / 20)
            for s in range(1, steps):
                t = s / float(steps)
                lx = r1_s[0] + (r1_e[0] - r1_s[0]) * t
                ly = r1_s[1] + (r1_e[1] - r1_s[1]) * t
                rx = r2_s[0] + (r2_e[0] - r2_s[0]) * t
                ry = r2_s[1] + (r2_e[1] - r2_s[1]) * t
                pygame.draw.line(self.screen, self.C["ladder"], (lx, ly), (rx, ry), 2)

    def _draw_snakes_graphic(self):
        """رسم مار واقعی‌تر با بدن چند ضلعی و طرح دار"""
        for start, end in self.snakes.items():
            p_head = self._get_cell_coords(start)
            p_tail = self._get_cell_coords(end)
            
            points_center = []
            segments = 40
            
            for s in range(segments + 1):
                t = s / float(segments)
                cx = p_head[0] + (p_tail[0] - p_head[0]) * t
                cy = p_head[1] + (p_tail[1] - p_head[1]) * t
                
                wave = math.sin(t * math.pi * 3) * 20
                
                dx = p_tail[0] - p_head[0]
                dy = p_tail[1] - p_head[1]
                length = math.hypot(dx, dy)
                if length == 0: continue
                
                nx, ny = -dy/length, dx/length
                
                cx += nx * wave
                cy += ny * wave
                
                points_center.append((cx, cy))
                
            if len(points_center) < 2:
                continue
                
            poly_points_left = []
            poly_points_right = []
            
            for s in range(len(points_center)):
                t = s / float(len(points_center) - 1)
                
                max_width = 12
                if t < 0.1:
                    width = max_width * (0.5 + 5 * t)
                elif t > 0.8:
                    width = max_width * (1.0 - (t - 0.8) * 5)
                else:
                    width = max_width
                    
                pt = points_center[s]
                
                if s < len(points_center) - 1:
                    nxt = points_center[s+1]
                else:
                    nxt = points_center[s]
                    pt = points_center[s-1]
                    
                dx = nxt[0] - pt[0]
                dy = nxt[1] - pt[1]
                length = math.hypot(dx, dy)
                if length == 0:
                    nx, ny = 1, 0
                else:
                    nx, ny = -dy/length, dx/length
                    
                pt_left = (points_center[s][0] + nx * width, points_center[s][1] + ny * width)
                pt_right = (points_center[s][0] - nx * width, points_center[s][1] - ny * width)
                
                poly_points_left.append(pt_left)
                poly_points_right.append(pt_right)
                
            poly_points = poly_points_left + list(reversed(poly_points_right))
            
            pygame.draw.polygon(self.screen, (30, 200, 80), poly_points)
            pygame.draw.polygon(self.screen, (10, 100, 40), poly_points, 2)
            
            for s in range(4, len(points_center) - 4, 3):
                l_pt = poly_points_left[s]
                r_pt = poly_points_right[s]
                pygame.draw.line(self.screen, (200, 255, 100), l_pt, r_pt, 2)
                
            hx, hy = points_center[0]
            dx = points_center[0][0] - points_center[2][0]
            dy = points_center[0][1] - points_center[2][1]
            length = math.hypot(dx, dy)
            if length == 0:
                nx, ny = 1, 0
            else:
                nx, ny = -dy/length, dx/length
                
            head_pts = [
                (hx + dx*1.5, hy + dy*1.5),
                (hx + nx*14, hy + ny*14),
                (hx - dx*0.5, hy - dy*0.5),
                (hx - nx*14, hy - ny*14)
            ]
            pygame.draw.polygon(self.screen, (255, 50, 50), head_pts)
            pygame.draw.polygon(self.screen, (150, 0, 0), head_pts, 2)
            
            eye1 = (hx + nx*7 + dx*0.5, hy + ny*7 + dy*0.5)
            eye2 = (hx - nx*7 + dx*0.5, hy - ny*7 + dy*0.5)
            pygame.draw.circle(self.screen, (255, 255, 0), (int(eye1[0]), int(eye1[1])), 3)
            pygame.draw.circle(self.screen, (255, 255, 0), (int(eye2[0]), int(eye2[1])), 3)
            
            pygame.draw.circle(self.screen, (0, 0, 0), (int(eye1[0] + dx*0.1), int(eye1[1] + dy*0.1)), 1)
            pygame.draw.circle(self.screen, (0, 0, 0), (int(eye2[0] + dx*0.1), int(eye2[1] + dy*0.1)), 1)
            
            tongue_start = head_pts[0]
            tongue_end1 = (tongue_start[0] + dx*1.5 + nx*2, tongue_start[1] + dy*1.5 + ny*2)
            tongue_end2 = (tongue_start[0] + dx*1.5 - nx*2, tongue_start[1] + dy*1.5 - ny*2)
            tongue_mid = (tongue_start[0] + dx*0.8, tongue_start[1] + dy*0.8)
            pygame.draw.line(self.screen, (255, 0, 0), tongue_start, tongue_mid, 2)
            pygame.draw.line(self.screen, (255, 0, 0), tongue_mid, tongue_end1, 2)
            pygame.draw.line(self.screen, (255, 0, 0), tongue_mid, tongue_end2, 2)

    def _draw_players(self):
        r = min(self.cell_w, self.cell_h) // 4
        
        # موقعیت متحرک یا ثابت بازیکن ۱
        if self.state in ("MOVING_STEPS", "MOVING_SPECIAL") and self.cur_p == 1 and self.anim_step_index < len(self.anim_path):
            c1 = self.anim_path[min(self.anim_step_index, len(self.anim_path)-1)]
        else:
            c1 = self._get_cell_coords(self.p_pos[0])
            
        # موقعیت متحرک یا ثابت بازیکن ۲
        if self.state in ("MOVING_STEPS", "MOVING_SPECIAL") and self.cur_p == 2 and self.anim_step_index < len(self.anim_path):
            c2 = self.anim_path[min(self.anim_step_index, len(self.anim_path)-1)]
        else:
            c2 = self._get_cell_coords(self.p_pos[1])

        # رسم فیزیکی مهره‌ها با افکت هاله نور
        pygame.draw.circle(self.screen, self.C["p1"], (int(c1[0]), int(c1[1])), r)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(c1[0]), int(c1[1])), r, 2)
        
        pygame.draw.circle(self.screen, self.C["p2"], (int(c2[0]), int(c2[1])), r)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(c2[0]), int(c2[1])), r, 2)

        # افکت چشمک‌زن روی مهره فعال برای راهنمایی جهت کلیک
        if self.state == "WAIT_CLICK":
            active_coord = c1 if self.cur_p == 1 else c2
            if (pygame.time.get_ticks() % 500) < 250:
                pygame.draw.circle(self.screen, (255, 255, 255), (int(active_coord[0]), int(active_coord[1])), r + 4, 2)

    def _draw_die_dots(self, rect, value, color):
        cx, cy = rect.centerx, rect.centery
        size = rect.width
        r = max(2, size // 12)
        o = size // 4
        dots = {
            1: [(cx, cy)],
            2: [(cx - o, cy - o), (cx + o, cy + o)],
            3: [(cx, cy), (cx - o, cy - o), (cx + o, cy + o)],
            4: [(cx - o, cy - o), (cx + o, cy - o), (cx - o, cy + o), (cx + o, cy + o)],
            5: [(cx, cy), (cx - o, cy - o), (cx + o, cy - o), (cx - o, cy + o), (cx + o, cy + o)],
            6: [(cx - o, cy - o), (cx + o, cy - o), (cx - o, cy), (cx + o, cy), (cx - o, cy + o), (cx + o, cy + o)]
        }
        if value in dots:
            for pos in dots[value]:
                pygame.draw.circle(self.screen, color, pos, r + 1)
                pygame.draw.circle(self.screen, (255, 255, 255), pos, r)

    def _draw_panel(self):
        px, py, pw, ph = self.pnl_x, self.pnl_y, self.pnl_w, self.pnl_h
        cur_c = self.C["p1"] if self.cur_p == 1 else self.C["p2"]

        pygame.draw.rect(self.screen, self.C["panel"], (px, py, pw, ph), border_radius=14)
        pygame.draw.rect(self.screen, cur_c if self.state != "GAME_OVER" else self.C["border"], (px, py, pw, ph), 3, border_radius=14)

        cy = py + 20
        def blit_c(surf):
            nonlocal cy
            self.screen.blit(surf, (px + pw // 2 - surf.get_width() // 2, cy))
            cy += surf.get_height() + 8

        blit_c(self.fS.render(reshape_persian(self.session.player1_name[:12]), True, self.C["p1"]))
        blit_c(self.fS.render(reshape_persian(self.session.player2_name[:12]), True, self.C["p2"]))
        cy += 10
        pygame.draw.line(self.screen, self.C["grid_border"], (px + 10, cy), (px + pw - 10, cy), 1)
        cy += 15

        blit_c(self.fXS.render("CURRENT TURN", True, self.C["text_dim"]))
        p_name = reshape_persian(self.session.player1_name) if self.cur_p == 1 else reshape_persian(self.session.player2_name)
        blit_c(self.fM.render(p_name[:10], True, cur_c))
        
        blit_c(self.fXS.render(f"{reshape_persian(self.session.player1_name)} Square: {self.p_pos[0]}", True, self.C["p1"]))
        blit_c(self.fXS.render(f"{reshape_persian(self.session.player2_name)} Square: {self.p_pos[1]}", True, self.C["p2"]))

        cy += 15
        pygame.draw.line(self.screen, self.C["grid_border"], (px + 10, cy), (px + pw - 10, cy), 1)
        cy += 20

        blit_c(self.fXS.render("DICE RESULT", True, self.C["text_dim"]))
        ds = 55
        dr = pygame.Rect(px + pw // 2 - ds // 2, cy, ds, ds)
        
        dice_color = cur_c if "ANIMATING" not in self.state else (random.randint(100, 255), random.randint(100, 255), 255)
        pygame.draw.rect(self.screen, self.C["dice_bg"], dr, border_radius=10)
        pygame.draw.rect(self.screen, dice_color, dr, 2, border_radius=10)
        
        val_to_draw = self.anim_current_val if self.state == "ANIMATING_DICE" else self.last_roll
        self._draw_die_dots(dr, val_to_draw, dice_color)
        cy += ds + 25

        if self.message:
            msg_s = self.fXS.render(self.message, True, (255, 200, 80))
            self.screen.blit(msg_s, (px + pw // 2 - msg_s.get_width() // 2, cy))
            cy += msg_s.get_height() + 15

        if self.state == "ROLL":
            self.roll_btn = pygame.Rect(px + 12, cy, pw - 24, 44)
            pygame.draw.rect(self.screen, cur_c, self.roll_btn, border_radius=10)
            bs = self.fM.render("ROLL [SPACE]", True, (0, 0, 0))
            self.screen.blit(bs, (self.roll_btn.centerx - bs.get_width() // 2, self.roll_btn.centery - bs.get_height() // 2))

    def _draw_gameover(self):
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 200))
        self.screen.blit(ov, (0, 0))
        wn = reshape_persian(self.session.player1_name) if self.winner == 1 else reshape_persian(self.session.player2_name)
        wcol = self.C["p1"] if self.winner == 1 else self.C["p2"]
        cy = self.height // 2 - 100
        t1 = self.fL.render("MATCH FINISHED", True, (255, 60, 60))
        t2 = self.fL.render(f"{wn} Wins!", True, wcol)
        self.screen.blit(t1, (self.width // 2 - t1.get_width() // 2, cy)); cy += 75
        self.screen.blit(t2, (self.width // 2 - t2.get_width() // 2, cy)); cy += 90
