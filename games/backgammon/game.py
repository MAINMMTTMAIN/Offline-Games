import pygame
import random
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path

class Backgammon(BaseGame):
    """Two-player Backgammon with standard rules and cyberpunk visual theme."""

    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width  = screen.get_width()
        self.height = screen.get_height()

        # ── Palette ───────────────────────────────────────────────────────
        self.C = {
            "bg":           (10, 10, 20),
            "board_bg":     (16, 20, 38),
            "tri_a":        (0,  150, 195),   # cyan triangles
            "tri_a2":       (0,   90, 130),
            "tri_b":        (195,  55,  35),  # red triangles
            "tri_b2":       (130,  30,  20),
            "bar_bg":       (22, 25, 48),
            "border":       (0, 235, 255),
            "checker_p1":   (35, 205, 255),   # P1 – cyan
            "checker_p2":   (255, 80,  55),   # P2 – orange-red
            "ck_edge":      (0,   0,   0),
            "highlight":    (255, 230,  40),  # selected checker
            "valid":        (70,  255, 110),  # valid destination
            "panel":        (18, 20, 36),
            "panel_bd":     (0, 235, 255),
            "text":         (225, 230, 255),
            "text_dim":     (120, 128, 170),
            "dice_bg":      (28, 30, 55),
            "gold":         (255, 215, 0),
        }

        # ── Fonts ─────────────────────────────────────────────────────────
        self.fL  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 54) 
        self.fM  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 26)
        self.fS  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 18)
        self.fXS = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 13)

        # ── Layout ────────────────────────────────────────────────────────
        self._layout()

        # Button rects filled in draw()
        self.roll_btn    = pygame.Rect(0, 0, 0, 0)
        self.restart_btn = pygame.Rect(0, 0, 0, 0)
        
        self.reset_game()
        self.state = "INTRO"
    # ═════════════════════════════════════════════════════════════════════
    # Rules
    # ═════════════════════════════════════════════════════════════════════

    def _draw_rules(self):
        self.screen.fill(self.C["bg"])

        # Title
        title = self.fL.render("Backgammon Rules", True, self.C["checker_p1"])
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))

        # English Rules
        eng_rules = [
            "• Roll two dice to move your checkers.",
            "• Move all 15 checkers to your home board and bear them off.",
            "• You can hit opponent's single checker (blot) and send it to the bar.",
            "• First player to bear off all checkers wins.",
        ]

        y = 180
        for line in eng_rules:
            surf = self.fS.render(line, True, self.C["text"])
            self.screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))
            y += 35

        # Persian Rules
        persian_title = render_persian_text(self.fM, "قوانین تخته نرد", self.C["checker_p1"])
        self.screen.blit(persian_title, (self.width // 2 - persian_title.get_width() // 2, y + 30))

        persian_rules = [
            "• با دو تاس حرکت کنید.",
            "• تمام ۱۵ مهره خود را به خانه ببرید و خارج کنید.",
            "• شما میتوانید مهره های حریف را وقتی که تک هستند بزنید و به بار بفرستید.",
            "• اولین بازیکنی که همه مهره‌ها را خارج کند برنده است.",
        ]

        y += 90
        for line in persian_rules:
            surf = render_persian_text(self.fS, line, self.C["text"])
            self.screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))
            y += 38

        # Click to start
        start_text = "Click anywhere to start!"
        start_surf = self.fM.render(start_text, True, self.C["checker_p2"])
        self.screen.blit(start_surf, (self.width // 2 - start_surf.get_width() // 2, self.height - 120))

        persian_start = render_persian_text(self.fM, "برای شروع کلیک کنید!", self.C["checker_p2"])
        self.screen.blit(persian_start, (self.width // 2 - persian_start.get_width() // 2, self.height - 70))

        # Decorative line
        pygame.draw.line(self.screen, self.C["border"], 
                        (self.width//4, self.height-150), 
                        (self.width*3//4, self.height-150), 2)
    # ═════════════════════════════════════════════════════════════════════
    # Layout
    # ═════════════════════════════════════════════════════════════════════

    def _layout(self):
        W, H = self.width, self.height
        # Info panel – right side
        self.pnl_w  = max(180, int(W * 0.17))
        self.pnl_x  = W - self.pnl_w - 18
        self.pnl_y  = int(H * 0.07)
        self.pnl_h  = int(H * 0.86)

        # Board – rest of horizontal space
        self.bx = 18
        self.by = int(H * 0.07)
        self.bw = self.pnl_x - 36
        self.bh = int(H * 0.86)

        self.bar_w  = max(28, int(self.bw * 0.054))
        self.col_w  = (self.bw - self.bar_w) // 12
        self.tri_h  = int(self.bh * 0.44)
        self.ck_r   = max(9, int(self.col_w * 0.37))

        # Bar center x
        self.bar_cx = self.bx + 6 * self.col_w + self.bar_w // 2

    # ═════════════════════════════════════════════════════════════════════
    # Game State
    # ═════════════════════════════════════════════════════════════════════

    def reset_game(self):
        # board[i]  i∈[0..23]  →  point number = i+1
        # positive  =  P1 checkers   negative  =  P2 checkers
        self.board = [0] * 24
        self.board[23] =  2   # P1  pt 24
        self.board[12] =  5   # P1  pt 13
        self.board[7]  =  3   # P1  pt 8
        self.board[5]  =  5   # P1  pt 6
        self.board[0]  = -2   # P2  pt 1
        self.board[11] = -5   # P2  pt 12
        self.board[16] = -3   # P2  pt 17
        self.board[18] = -5   # P2  pt 19

        self.bar        = [0, 0]   # [P1 on bar, P2 on bar]
        self.borne_off  = [0, 0]   # [P1 borne, P2 borne]

        self.cur_p      = 1        # current player 1|2
        self.dice       = []       # remaining dice values
        self.state      = "ROLL"   # ROLL | MOVE | GAME_OVER
        self.winner     = None
        self.selected   = None     # int point 1-24 or "bar" or None
        self.v_dests    = []       # valid destinations for selected
        self.message    = ""
        self.pass_timer = 0        # auto-pass timestamp (ms)
        self.bot_timer  = 0

    # ─── helpers ─────────────────────────────────────────────────────────

    def _pid(self):  return self.cur_p - 1
    def _dir(self):  return -1 if self.cur_p == 1 else 1

    def _owns(self, pt):
        c = self.board[pt - 1]
        return (self.cur_p == 1 and c > 0) or (self.cur_p == 2 and c < 0)

    def _can_land(self, pt):
        """Can current player place a checker on point pt?"""
        if not (1 <= pt <= 24): return False
        c = self.board[pt - 1]
        return c > -2 if self.cur_p == 1 else c < 2

    def _all_home(self):
        """All current player's checkers in home board (none on bar)."""
        if self.bar[self._pid()] > 0: return False
        if self.cur_p == 1:
            for i in range(6, 24):
                if self.board[i] > 0: return False
        else:
            for i in range(0, 18):
                if self.board[i] < 0: return False
        return True

    def _highest_home_p1(self):
        """Highest occupied home point for P1 (points 1-6)."""
        for i in range(5, -1, -1):
            if self.board[i] > 0: return i + 1
        return 0

    def _lowest_home_p2(self):
        """Lowest occupied home point for P2 (points 19-24)."""
        for i in range(18, 24):
            if self.board[i] < 0: return i + 1
        return 25

    # ─── move validation ──────────────────────────────────────────────────

    def _valid_dests_for(self, from_pt):
        """Return list of valid destination point-numbers (0/25 = bear-off)."""
        dr   = self._dir()
        seen = set()
        res  = set()

        for die in self.dice:
            if die in seen: continue
            seen.add(die)

            if from_pt == "bar":
                entry = (25 - die) if self.cur_p == 1 else die
                if self._can_land(entry):
                    res.add(entry)
            else:
                to = from_pt + dr * die
                if self.cur_p == 1 and to <= 0:
                    if self._all_home():
                        if to == 0:
                            res.add(0)
                        elif from_pt >= self._highest_home_p1():
                            res.add(0)
                elif self.cur_p == 2 and to >= 25:
                    if self._all_home():
                        if to == 25:
                            res.add(25)
                        elif from_pt <= self._lowest_home_p2():
                            res.add(25)
                elif 1 <= to <= 24 and self._can_land(to):
                    res.add(to)
        return list(res)

    def _has_moves(self):
        """Does the current player have at least one legal move?"""
        if self.bar[self._pid()] > 0:
            return bool(self._valid_dests_for("bar"))
        for pt in range(1, 25):
            if self._owns(pt) and self._valid_dests_for(pt):
                return True
        return False

    def _die_for(self, from_pt, to_pt):
        """Find (smallest) die that produces this move; None if impossible."""
        if from_pt == "bar":
            need = (25 - to_pt) if self.cur_p == 1 else to_pt
            return need if need in self.dice else None

        if to_pt in (0, 25):
            # bearing off
            if self.cur_p == 1:
                exact = from_pt
                for d in sorted(self.dice):
                    if d == exact: return d
                for d in sorted(self.dice):
                    if d > exact: return d
            else:
                exact = 25 - from_pt
                for d in sorted(self.dice):
                    if d == exact: return d
                for d in sorted(self.dice):
                    if d > exact: return d
            return None

        need = abs(from_pt - to_pt)
        return need if need in self.dice else None

    # ─── execute move ─────────────────────────────────────────────────────

    def _do_move(self, from_pt, to_pt):
        die = self._die_for(from_pt, to_pt)
        if die is None: return

        pid = self._pid()

        # Remove from source
        if from_pt == "bar":
            self.bar[pid] -= 1
        else:
            if self.cur_p == 1: self.board[from_pt - 1] -= 1
            else:               self.board[from_pt - 1] += 1

        # Place at destination
        if to_pt == 0:    # P1 bears off
            self.borne_off[0] += 1
        elif to_pt == 25: # P2 bears off
            self.borne_off[1] += 1
        else:
            di = to_pt - 1
            # Hit detection
            if self.cur_p == 1 and self.board[di] == -1:
                self.board[di] = 0; self.bar[1] += 1
            elif self.cur_p == 2 and self.board[di] == 1:
                self.board[di] = 0; self.bar[0] += 1
            if self.cur_p == 1: self.board[di] += 1
            else:               self.board[di] -= 1

        # Consume die
        self.dice.remove(die)
        self.selected = None
        self.v_dests  = []

        # Win?
        if self.borne_off[0] == 15: self._win(1); return
        if self.borne_off[1] == 15: self._win(2); return

        # More moves?
        if not self.dice or not self._has_moves():
            if self.dice:
                self.message    = "No moves left – turn ends"
                self.pass_timer = pygame.time.get_ticks() + 1800
            else:
                self._end_turn()

    def _win(self, p):
        self.state  = "GAME_OVER"
        self.winner = p
        key = "player1" if p == 1 else "player2"
        self.session.scores[key] += 1

    def _end_turn(self):
        self.cur_p      = 2 if self.cur_p == 1 else 1
        self.dice       = []
        self.state      = "ROLL"
        self.selected   = None
        self.v_dests    = []
        self.message    = ""
        self.pass_timer = 0

    def _roll(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        self.dice     = [d1, d1, d1, d1] if d1 == d2 else [d1, d2]
        self.state    = "MOVE"
        self.selected = None
        self.v_dests  = []
        self.message  = ""
        if not self._has_moves():
            self.message    = "No moves available – turn passes"
            self.pass_timer = pygame.time.get_ticks() + 2200

    # ═════════════════════════════════════════════════════════════════════
    # Update
    # ═════════════════════════════════════════════════════════════════════

    def update(self):
        if self.pass_timer and pygame.time.get_ticks() >= self.pass_timer:
            self.pass_timer = 0
            self._end_turn()

        if getattr(self.session, 'is_single_player', False) and self.cur_p == 2 and self.state in ("ROLL", "MOVE"):
            if self.bot_timer == 0:
                self.bot_timer = pygame.time.get_ticks()
            
            if pygame.time.get_ticks() - self.bot_timer > 800:
                if self.state == "ROLL":
                    self._roll()
                    self.bot_timer = pygame.time.get_ticks()
                elif self.state == "MOVE":
                    self._make_bot_move()
                    self.bot_timer = pygame.time.get_ticks()

    def _make_bot_move(self):
        if not self.dice or not self._has_moves():
            return
            
        diff = getattr(self.session, 'bot_difficulty', 'medium')
        
        valid_moves = []
        if self.bar[1] > 0:
            dests = self._valid_dests_for("bar")
            for d in dests:
                valid_moves.append(("bar", d))
        else:
            for pt in range(1, 25):
                if self._owns(pt):
                    dests = self._valid_dests_for(pt)
                    for d in dests:
                        valid_moves.append((pt, d))
                        
        if not valid_moves:
            return
            
        import random
        if diff == "low":
            chosen = random.choice(valid_moves)
        else:
            best_score = -float('inf')
            best_move = valid_moves[0]
            
            for m in valid_moves:
                from_pt, to_pt = m
                score = self._evaluate_single_move(from_pt, to_pt, diff)
                if score > best_score:
                    best_score = score
                    best_move = m
            chosen = best_move
            
        self._do_move(chosen[0], chosen[1])

    def _evaluate_single_move(self, from_pt, to_pt, diff):
        score = 0
        if to_pt == 25:
            score += 1000
            
        if to_pt != 25:
            di = to_pt - 1
            if self.board[di] == 1:
                score += 500
            if self.board[di] < 0:
                score += 50
                
        if diff == "hard":
            if from_pt != "bar":
                if self.board[from_pt - 1] == -2:
                    score -= 200
                if to_pt != 25 and self.board[to_pt - 1] == 0:
                    score -= 100
        return score

    # ═════════════════════════════════════════════════════════════════════
    # Events
    # ═════════════════════════════════════════════════════════════════════

    def handle_events(self, events):
        super().handle_events(events)
        
        if getattr(self.session, 'is_single_player', False) and self.cur_p == 2:
            for ev in events:
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    self.running = False
            return
            
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                elif ev.key == pygame.K_SPACE:
                    if self.state == "INTRO":
                        self.state = "ROLL"
                    elif self.state == "ROLL":
                        self._roll()
                    elif self.state == "GAME_OVER":
                        self.reset_game()
                        self.state = "ROLL"

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state == "INTRO":
                    self.state = "ROLL"
                elif self.state == "ROLL":
                    if self.roll_btn.collidepoint(ev.pos):
                        self._roll()
                elif self.state == "MOVE":
                    self._board_click(ev.pos)
                elif self.state == "GAME_OVER":
                    if self.restart_btn.collidepoint(ev.pos):
                        self.reset_game()
                        self.state = "ROLL"

    def _board_click(self, pos):
        if self.pass_timer: return
        pid = self._pid()

        # ── Bar click ────────────────────────────────────────────────────
        if self._bar_rect().collidepoint(pos):
            if self.bar[pid] > 0:
                self.selected = "bar"
                self.v_dests  = self._valid_dests_for("bar")
            return

        # ── Bear-off panel click ─────────────────────────────────────────
        if self.selected is not None:
            bo_rect = pygame.Rect(self.pnl_x, self.pnl_y, self.pnl_w, self.pnl_h)
            if bo_rect.collidepoint(pos):
                if 0 in self.v_dests:
                    self._do_move(self.selected, 0); return
                if 25 in self.v_dests:
                    self._do_move(self.selected, 25); return

        # ── Board point click ────────────────────────────────────────────
        clicked = self._pos_to_pt(pos)
        if clicked is None:
            self.selected = None; self.v_dests = []; return

        if self.selected is not None and clicked in self.v_dests:
            self._do_move(self.selected, clicked)
        elif self.bar[pid] > 0:
            pass   # must move from bar
        elif self._owns(clicked):
            vd = self._valid_dests_for(clicked)
            if vd:
                self.selected = clicked
                self.v_dests  = vd
            else:
                self.selected = None; self.v_dests = []
        else:
            self.selected = None; self.v_dests = []

    # ═════════════════════════════════════════════════════════════════════
    # Geometry
    # ═════════════════════════════════════════════════════════════════════

    def _pt_cx(self, pt):
        """X-center of board point 1-24."""
        #  columns 0-5  →  pt 13-18 (top)  /  pt 12-7 (bottom)
        #  columns 6-11 →  pt 19-24 (top)  /  pt 6-1  (bottom)
        col = (12 - pt) if pt <= 12 else (pt - 13)
        if col < 6:
            return self.bx + col * self.col_w + self.col_w // 2
        else:
            return self.bx + col * self.col_w + self.bar_w + self.col_w // 2

    def _pos_to_pt(self, pos):
        mx, my = pos
        mid_y = self.by + self.bh // 2
        for pt in range(1, 25):
            cx = self._pt_cx(pt)
            if abs(mx - cx) <= self.col_w // 2:
                if pt <= 12 and mid_y <= my <= self.by + self.bh:
                    return pt
                if pt > 12 and self.by <= my <= mid_y:
                    return pt
        return None

    def _bar_rect(self):
        return pygame.Rect(self.bar_cx - self.bar_w // 2,
                           self.by, self.bar_w, self.bh)

    # ═════════════════════════════════════════════════════════════════════
    # Drawing
    # ═════════════════════════════════════════════════════════════════════

    def draw(self):
        if self.state == "INTRO":
            self._draw_rules()
        else:
            self.screen.fill(self.C["bg"])
            self._draw_board()
            self._draw_highlights()
            self._draw_checkers()
            self._draw_bar_checkers()
            self._draw_panel()
            if self.state == "GAME_OVER":
                self._draw_gameover()

    # ─── board ────────────────────────────────────────────────────────────

    def _draw_board(self):
        bx, by, bw, bh = self.bx, self.by, self.bw, self.bh

        # Background
        pygame.draw.rect(self.screen, self.C["board_bg"],
                         pygame.Rect(bx, by, bw, bh))
        pygame.draw.rect(self.screen, self.C["border"],
                         pygame.Rect(bx, by, bw, bh), 3, border_radius=4)

        # Triangles
        for pt in range(1, 25):
            cx = self._pt_cx(pt)
            hw = self.col_w // 2 - 2
            even = pt % 2 == 0
            ca  = self.C["tri_a"]  if even else self.C["tri_b"]
            ca2 = self.C["tri_a2"] if even else self.C["tri_b2"]

            if pt <= 12:   # bottom → tip up
                verts = [(cx, by + bh - self.tri_h),
                         (cx - hw, by + bh), (cx + hw, by + bh)]
            else:          # top → tip down
                verts = [(cx, by + self.tri_h),
                         (cx - hw, by), (cx + hw, by)]

            pygame.draw.polygon(self.screen, ca,  verts)
            pygame.draw.polygon(self.screen, ca2, verts, 2)

        # Center divider
        my = by + bh // 2
        pygame.draw.line(self.screen, self.C["border"], (bx + 4, my), (bx + bw - 4, my), 1)

        # Bar
        br = self._bar_rect()
        pygame.draw.rect(self.screen, self.C["bar_bg"], br)
        pygame.draw.rect(self.screen, self.C["border"], br, 2)

        # Point numbers
        for pt in range(1, 25):
            cx  = self._pt_cx(pt)
            ns  = self.fXS.render(str(pt), True, (110, 118, 160))
            ny  = by + bh - 15 if pt <= 12 else by + 3
            self.screen.blit(ns, (cx - ns.get_width() // 2, ny))

    # ─── highlights ───────────────────────────────────────────────────────

    def _draw_highlights(self):
        r  = self.ck_r
        by = self.by; bh = self.bh

        # Selected
        if self.selected is not None:
            if self.selected == "bar":
                br = self._bar_rect()
                pygame.draw.rect(self.screen, self.C["highlight"], br, 4)
            else:
                cx = self._pt_cx(self.selected)
                cy = by + bh - r - 2 if self.selected <= 12 else by + r + 2
                pygame.draw.circle(self.screen, self.C["highlight"], (cx, cy), r + 8, 4)

        # Valid destinations
        for d in self.v_dests:
            if d in (0, 25):
                pygame.draw.rect(self.screen, self.C["valid"],
                                 pygame.Rect(self.pnl_x - 3, self.pnl_y - 3,
                                             self.pnl_w + 6, self.pnl_h + 6), 4, border_radius=14)
            else:
                cx = self._pt_cx(d)
                cy = by + bh - r - 2 if d <= 12 else by + r + 2
                pygame.draw.circle(self.screen, self.C["valid"], (cx, cy), r + 8, 3)

    # ─── checkers ────────────────────────────────────────────────────────

    def _ck(self, cx, cy, color):
        r = self.ck_r
        pygame.draw.circle(self.screen, color, (cx, cy), r)
        pygame.draw.circle(self.screen, self.C["ck_edge"], (cx, cy), r, 2)
        shine = tuple(min(v + 70, 255) for v in color)
        pygame.draw.circle(self.screen, shine, (cx - r // 3, cy - r // 3), r // 3)

    def _draw_checkers(self):
        r  = self.ck_r
        by = self.by; bh = self.bh

        for pt in range(1, 25):
            cnt = self.board[pt - 1]
            if cnt == 0: continue
            p   = 1 if cnt > 0 else 2
            n   = abs(cnt)
            col = self.C["checker_p1"] if p == 1 else self.C["checker_p2"]
            cx  = self._pt_cx(pt)
            show = min(n, 5)

            for i in range(show):
                cy = (by + bh - r - 2 - i * r * 2) if pt <= 12 else (by + r + 2 + i * r * 2)
                self._ck(cx, cy, col)

            if n > 5:
                cy = (by + bh - r - 2 - 4 * r * 2) if pt <= 12 else (by + r + 2 + 4 * r * 2)
                badge = self.fXS.render(str(n), True, (0, 0, 0))
                self.screen.blit(badge, (cx - badge.get_width() // 2, cy - badge.get_height() // 2))

    def _draw_bar_checkers(self):
        mid_y = self.by + self.bh // 2
        cx    = self.bar_cx; r = self.ck_r
        for i in range(self.bar[0]):
            self._ck(cx, mid_y - r - i * (r * 2 + 2), self.C["checker_p1"])
        for i in range(self.bar[1]):
            self._ck(cx, mid_y + r + i * (r * 2 + 2), self.C["checker_p2"])

    # ─── info panel ──────────────────────────────────────────────────────

    def _draw_panel(self):
        px, py, pw, ph = self.pnl_x, self.pnl_y, self.pnl_w, self.pnl_h
        p1c = self.C["checker_p1"]
        p2c = self.C["checker_p2"]
        cur_c = p1c if self.cur_p == 1 else p2c

        # Panel bg
        pygame.draw.rect(self.screen, self.C["panel"],
                         pygame.Rect(px, py, pw, ph), border_radius=14)
        pygame.draw.rect(self.screen, cur_c if self.state != "GAME_OVER" else self.C["border"],
                         pygame.Rect(px, py, pw, ph), 3, border_radius=14)

        cy = py + 16

        def blit_c(surf):
            nonlocal cy
            self.screen.blit(surf, (px + pw // 2 - surf.get_width() // 2, cy))
            cy += surf.get_height() + 5

        # Player names
        blit_c(self.fS.render(reshape_persian(self.session.player1_name[:12]), True, p1c))
        blit_c(self.fS.render(reshape_persian(self.session.player2_name[:12]), True, p2c))
        cy += 6

        # Divider
        pygame.draw.line(self.screen, self.C["border"], (px + 8, cy), (px + pw - 8, cy), 1)
        cy += 10

        # Current turn
        blit_c(self.fXS.render("CURRENT TURN", True, self.C["text_dim"]))
        cur_name = reshape_persian(self.session.player1_name) if self.cur_p == 1 else reshape_persian(self.session.player2_name)
        blit_c(self.fM.render(cur_name[:9], True, cur_c))

        # Direction hint
        hint = "\u2190 moves 24\u21921" if self.cur_p == 1 else "\u2192 moves 1\u219224"
        blit_c(self.fXS.render(hint, True, cur_c))
        cy += 6

        pygame.draw.line(self.screen, self.C["border"], (px + 8, cy), (px + pw - 8, cy), 1)
        cy += 10

        # Borne-off progress bars
        blit_c(self.fXS.render("BORNE OFF", True, self.C["text_dim"]))
        for p_idx, col in enumerate([p1c, p2c]):
            count = self.borne_off[p_idx]
            bar_w = pw - 24
            filled = int(bar_w * count / 15)
            bg_r = pygame.Rect(px + 12, cy, bar_w, 14)
            fg_r = pygame.Rect(px + 12, cy, filled, 14)
            pygame.draw.rect(self.screen, self.C["dice_bg"], bg_r, border_radius=7)
            if filled > 0:
                pygame.draw.rect(self.screen, col, fg_r, border_radius=7)
            pygame.draw.rect(self.screen, col, bg_r, 1, border_radius=7)
            cnt_s = self.fXS.render(f"{count}/15", True, col)
            self.screen.blit(cnt_s, (px + pw - cnt_s.get_width() - 12, cy - 1))
            cy += 20

        cy += 6
        pygame.draw.line(self.screen, self.C["border"], (px + 8, cy), (px + pw - 8, cy), 1)
        cy += 10

        # Bar counts
        blit_c(self.fXS.render("ON BAR", True, self.C["text_dim"]))
        bar_s = self.fM.render(f"{self.bar[0]}  |  {self.bar[1]}", True, self.C["text"])
        blit_c(bar_s)
        cy += 8

        pygame.draw.line(self.screen, self.C["border"], (px + 8, cy), (px + pw - 8, cy), 1)
        cy += 10

        # Dice remaining
        if self.dice:
            blit_c(self.fXS.render("DICE REMAINING", True, self.C["text_dim"]))
            ds   = 44
            n    = len(self.dice)
            cols = max(1, (pw - 16) // (ds + 8))
            dx0  = px + pw // 2 - (min(n, cols) * (ds + 8) - 8) // 2
            dx   = dx0
            for i, dv in enumerate(self.dice):
                if i > 0 and i % cols == 0:
                    dx = dx0; cy += ds + 8
                dr = pygame.Rect(dx, cy, ds, ds)
                
                # رسم بدنه تاس با افکت تیره سایبرپانک
                pygame.draw.rect(self.screen, self.C["dice_bg"], dr, border_radius=10)
                # رسم حاشیه نئونی (رنگ بازیکن فعلی)
                pygame.draw.rect(self.screen, cur_c, dr, 2, border_radius=10)
                
                # اضافه کردن عمق یا افکت سایه داخلی لبه‌ها
                pygame.draw.rect(self.screen, (cur_c[0]//2, cur_c[1]//2, cur_c[2]//2), dr.inflate(-4, -4), width=1, border_radius=8)
                
                # فراخوانی متد جدید برای رندر کردن نقاط به جای متن عددی
                self._draw_die_dots(dr, dv, cur_c)
                
                dx += ds + 8
            cy += ds + 14

        # Message
        if self.message:
            msg_s = self.fXS.render(self.message, True, (255, 200, 80))
            self.screen.blit(msg_s, (px + pw // 2 - msg_s.get_width() // 2, cy))
            cy += msg_s.get_height() + 10

        # Roll button
        if self.state == "ROLL":
            bh2 = 48
            self.roll_btn = pygame.Rect(px + 10, cy, pw - 20, bh2)
            pygame.draw.rect(self.screen, cur_c, self.roll_btn, border_radius=12)
            bs = self.fM.render("ROLL  [SPACE]", True, (0, 0, 0))
            self.screen.blit(bs, (self.roll_btn.centerx - bs.get_width() // 2,
                                   self.roll_btn.centery - bs.get_height() // 2))
        else:
            self.roll_btn = pygame.Rect(0, 0, 0, 0)

        # Bear-off indicator
        if self.state == "MOVE" and self._all_home() and self.selected is not None:
            blit_c(self.fXS.render("\u25b6  Click here to", True, self.C["valid"]))
            blit_c(self.fXS.render("bear off checker!", True, self.C["valid"]))

        # Footer instructions
        footer_y = py + ph - 52
        for line in ["Click checker \u2192 click dest", "ESC: Main Menu"]:
            ls = self.fXS.render(line, True, self.C["text_dim"])
            self.screen.blit(ls, (px + pw // 2 - ls.get_width() // 2, footer_y))
            footer_y += ls.get_height() + 3

    # ─── game-over overlay ────────────────────────────────────────────────

    def _draw_gameover(self):
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 195))
        self.screen.blit(ov, (0, 0))

        wn   = reshape_persian(self.session.player1_name) if self.winner == 1 else reshape_persian(self.session.player2_name)
        wcol = self.C["checker_p1"] if self.winner == 1 else self.C["checker_p2"]

        cy = self.height // 2 - 110
        t1 = self.fL.render("GAME OVER", True, (255, 45, 45))
        t2 = self.fL.render(f"{wn} Wins!", True, self.C["gold"])
        self.screen.blit(t1, (self.width // 2 - t1.get_width() // 2, cy)); cy += 80
        self.screen.blit(t2, (self.width // 2 - t2.get_width() // 2, cy)); cy += 90

        bw2, bh2 = 290, 56
        self.restart_btn = pygame.Rect(self.width // 2 - bw2 // 2, cy, bw2, bh2)
        pygame.draw.rect(self.screen, wcol, self.restart_btn, border_radius=14)
        bs = self.fM.render("Play Again  [SPACE]", True, (0, 0, 0))
        self.screen.blit(bs, (self.restart_btn.centerx - bs.get_width() // 2,
                               self.restart_btn.centery - bs.get_height() // 2))
    def _draw_die_dots(self, rect, value, color):
        """رسم نقطه‌های استاندارد تاس درون مربع مشخص شده"""
        cx, cy = rect.centerx, rect.centery
        size = rect.width
        r = max(2, size // 12)  # شعاع نقطه‌ها
        
        # فاصله‌گذاری نقاط از لبه‌های تاس
        o = size // 4

        # موقعیت دقیق نقطه‌ها بر اساس عدد ۱ تا ۶
        dots = {
            1: [(cx, cy)],
            2: [(cx - o, cy - o), (cx + o, cy + o)],
            3: [(cx, cy), (cx - o, cy - o), (cx + o, cy + o)],
            4: [(cx - o, cy - o), (cx + o, cy - o), (cx - o, cy + o), (cx + o, cy + o)],
            5: [(cx, cy), (cx - o, cy - o), (cx + o, cy - o), (cx - o, cy + o), (cx + o, cy + o)],
            6: [(cx - o, cy - o), (cx + o, cy - o), (cx - o, cy), (cx + o, cy), (cx - o, cy + o), (cx + o, cy + o)]
        }

        # رسم نقطه‌ها به همراه یک هاله درخشان نئونی
        if value in dots:
            for pos in dots[value]:
                # هاله درخشش پشتی
                pygame.draw.circle(self.screen, (color[0], color[1], color[2]), pos, r + 1)
                # نقطه اصلی سفید و روشن
                pygame.draw.circle(self.screen, (255, 255, 255), pos, r)
