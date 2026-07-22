import os
import sys
import pygame
import math
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import reshape_persian, render_persian_text
from main import resource_path

GRID_W, GRID_H = 10, 10
CELL = 46

# ship colors by type
SHIP_PALETTES = {
    "Carrier":    {"hull": (70,90,110),  "deck": (55,75,90),  "bridge": (45,65,80)},
    "Battleship": {"hull": (60,80,100),  "deck": (50,70,90),  "bridge": (80,60,40)},
    "Cruiser":    {"hull": (55,75,95),   "deck": (45,65,85),  "bridge": (70,55,40)},
    "Submarine":  {"hull": (50,70,60),   "deck": (40,60,50),  "bridge": (30,50,40)},
    "Destroyer":  {"hull": (75,85,95),   "deck": (65,75,85),  "bridge": (55,65,75)},
}


class Battleship(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.font_sm = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        self.font_md = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 26)
        self.font_lg = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 54)

        # Colors
        self.C_BG     = (5, 14, 38)
        self.C_OCEAN  = (8, 38, 88)
        self.C_OCEAN2 = (10, 45, 100)
        self.C_GRID   = (25, 70, 150)
        self.C_HIT    = (255, 75, 25)
        self.C_MISS   = (70, 155, 220)
        self.C_P1     = (0, 220, 255)
        self.C_P2     = (255, 200, 0)
        self.C_FIRE   = (255, 160, 0)

        board_w = GRID_W * CELL
        board_h = GRID_H * CELL
        gap      = 130
        total_w  = board_w * 2 + gap
        self.b1x = (self.W - total_w) // 2
        self.b2x = self.b1x + board_w + gap
        self.bby = (self.H - board_h) // 2 + 25

        self.ship_defs = [
            ("Carrier",    5),
            ("Battleship", 4),
            ("Cruiser",    3),
            ("Submarine",  3),
            ("Destroyer",  2),
        ]

        self.anim_hits  = []   # [(sx,sy, start_time)]
        self.wave_offset= 0.0

        self._full_reset()
        pygame.display.set_caption("Battleship")

    # ──────────────────── full reset ────────────────────
    def _full_reset(self):
        self.p1_board  = [['~']*GRID_W for _ in range(GRID_H)]
        self.p2_board  = [['~']*GRID_W for _ in range(GRID_H)]
        self.p1_ships  = []   # list of {"name":, "cells":[(r,c),...], "horiz":}
        self.p2_ships  = []
        self.p1_shots  = {}   # (r,c) → 'H'/'M'
        self.p2_shots  = {}
        self.game_over = False
        self.winner    = None
        self.msg       = ""
        self.msg_timer = 0
        self.extra_turn= False

        # Placement
        self.phase         = "place_p1"
        self.pl_idx        = 0       # which ship to place next
        self.pl_horiz      = True    # orientation
        self.hover_rc      = None
        self.hover_valid   = False

        # Drag-rearrange
        self.drag_ship     = None    # index into current player ships
        self.drag_offset_r = 0
        self.drag_offset_c = 0
        self.drag_cur_rc   = None

        # Turn transition
        self.transition     = True  # wait for player 1
        p1_name = reshape_persian(getattr(self, 'session', type('obj', (object,), {'player1_name': 'Player 1'})).player1_name)
        p2_name = reshape_persian(getattr(self, 'session', type('obj', (object,), {'player2_name': 'Player 2'})).player2_name)
        self.transition_msg = f"{p1_name} — place your ships\n({p2_name}, look away!)"

        self._make_confirm_btn()

    def _make_confirm_btn(self):
        self.confirm_btn = pygame.Rect(self.W//2 - 110, self.H - 70, 220, 48)

    # ──────────────────── helpers ────────────────────
    def _board_origin(self, player):
        return (self.b1x, self.bby) if player == 1 else (self.b2x, self.bby)

    def _rc_from_mouse(self, mx, my, player):
        ox, oy = self._board_origin(player)
        c = (mx - ox) // CELL
        r = (my - oy) // CELL
        if 0 <= r < GRID_H and 0 <= c < GRID_W:
            return (r, c)
        return None

    def _ship_cells(self, r, c, length, horiz):
        return [(r, c+i) for i in range(length)] if horiz else [(r+i, c) for i in range(length)]

    def _valid_placement(self, cells, board, ships, exclude_ship=None):
        existing_cells = set()
        for idx, s in enumerate(ships):
            if idx != exclude_ship:
                for cell in s["cells"]:
                    existing_cells.add(cell)
        for (sr, sc) in cells:
            if not (0 <= sr < GRID_H and 0 <= sc < GRID_W):
                return False
            if (sr, sc) in existing_cells:
                return False
        return True

    def _place_ship(self, cells, board, ships, name, horiz):
        for r, c in cells:
            board[r][c] = 'S'
        ships.append({"name": name, "cells": cells, "horiz": horiz})

    def _remove_ship_from_board(self, ship, board):
        for r, c in ship["cells"]:
            board[r][c] = '~'

    def _write_ship_to_board(self, ship, board):
        for r, c in ship["cells"]:
            board[r][c] = 'S'

    def _shoot(self, r, c, shooter):
        if shooter == 1:
            shots, board, ships, ox, oy = self.p1_shots, self.p2_board, self.p2_ships, *self._board_origin(2)
        else:
            shots, board, ships, ox, oy = self.p2_shots, self.p1_board, self.p1_ships, *self._board_origin(1)

        if (r, c) in shots:
            return

        px = ox + c * CELL + CELL // 2
        py = oy + r * CELL + CELL // 2
        self.anim_hits.append((px, py, pygame.time.get_ticks()))

        if board[r][c] == 'S':
            shots[(r, c)] = 'H'
            board[r][c]   = 'X'
            self.extra_turn = True
            # Check sunk
            for ship in ships:
                if (r, c) in ship["cells"]:
                    if all(board[sr][sc] == 'X' for sr, sc in ship["cells"]):
                        self.msg       = f"🚢 {ship['name']} sunk!"
                        self.msg_timer = pygame.time.get_ticks() + 1800
            # Check win
            if all(board[sr][sc] == 'X' for ship in ships for sr, sc in ship["cells"]):
                self.game_over = True
                self.winner    = shooter
                if shooter == 1: self.session.scores['player1'] += 1
                else:            self.session.scores['player2'] += 1
        else:
            shots[(r, c)] = 'M'
            board[r][c]   = 'O'
            self.extra_turn = False
            self.msg       = "Miss!"
            self.msg_timer = pygame.time.get_ticks() + 1000

    # ──────────────────── ship drawing ────────────────────
    def _draw_ship_graphic(self, ship, ox, oy, alpha=255):
        cells  = ship["cells"]
        horiz  = ship["horiz"]
        name   = ship["name"]
        pal    = SHIP_PALETTES.get(name, SHIP_PALETTES["Destroyer"])

        if not cells:
            return

        # Bounding box on screen
        min_r = min(r for r, c in cells)
        max_r = max(r for r, c in cells)
        min_c = min(c for r, c in cells)
        max_c = max(c for r, c in cells)

        x1 = ox + min_c * CELL + 3
        y1 = oy + min_r * CELL + 3
        x2 = ox + (max_c + 1) * CELL - 3
        y2 = oy + (max_r + 1) * CELL - 3
        sw = x2 - x1
        sh = y2 - y1

        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        hull_col   = (*pal["hull"],   alpha)
        deck_col   = (*pal["deck"],   alpha)
        bridge_col = (*pal["bridge"], alpha)

        # ── Hull ──
        pygame.draw.rect(surf, hull_col,   (0, 0, sw, sh), border_radius=6)
        pygame.draw.rect(surf, (255,255,255,60), (0,0,sw,sh), 1, border_radius=6)

        # Bow (tapered front)
        if horiz:
            # Bow on right side
            bow_pts = [(sw-12, 0), (sw, sh//2), (sw-12, sh)]
            pygame.draw.polygon(surf, deck_col, bow_pts)
            # Stern detail
            pygame.draw.rect(surf, (255,255,255,50), (0,0,6,sh), border_radius=3)
        else:
            bow_pts = [(0, sh-12), (sw//2, sh), (sw, sh-12)]
            pygame.draw.polygon(surf, deck_col, bow_pts)
            pygame.draw.rect(surf, (255,255,255,50), (0,0,sw,6), border_radius=3)

        # ── Superstructure deck ──
        if horiz:
            deck_rect = (8, sh//4, sw-24, sh//2)
        else:
            deck_rect = (sw//4, 8, sw//2, sh-24)
        pygame.draw.rect(surf, deck_col, deck_rect, border_radius=3)

        # ── Bridge / conning tower ──
        if horiz:
            br_w = max(10, sw//5)
            br_h = max(6, sh//3)
            br_x = (sw - br_w) // 2 - sw//8
            br_y = (sh - br_h) // 2
        else:
            br_w = max(6, sw//3)
            br_h = max(10, sh//5)
            br_x = (sw - br_w) // 2
            br_y = (sh - br_h) // 2 - sh//8

        pygame.draw.rect(surf, bridge_col, (br_x, br_y, br_w, br_h), border_radius=2)
        pygame.draw.rect(surf, (255,255,255,80), (br_x, br_y, br_w, br_h), 1, border_radius=2)

        # Portholes
        if horiz:
            for i in range(len(cells)-1):
                ph_x = 14 + i * (sw - 28) // max(1, len(cells)-1)
                pygame.draw.circle(surf, (200,220,240,160), (ph_x, sh-8), 3)
        else:
            for i in range(len(cells)-1):
                ph_y = 14 + i * (sh - 28) // max(1, len(cells)-1)
                pygame.draw.circle(surf, (200,220,240,160), (sw-8, ph_y), 3)

        # Special: Submarine has rounded silhouette
        if name == "Submarine":
            pygame.draw.ellipse(surf, (*pal["hull"], alpha), (0, sh//4, sw, sh//2))
            # Conning tower
            ct_x = sw//2 - 6; ct_y = sh//2 - 14
            pygame.draw.rect(surf, bridge_col, (ct_x, ct_y, 12, 14), border_radius=4)

        self.screen.blit(surf, (x1, y1))

    # ──────────────────── board drawing ────────────────────
    def _draw_grid(self, ox, oy, board, shots, reveal_ships,
                   hover_cells=None, hover_valid=True, ships=None):
        now = pygame.time.get_ticks()
        wave = int(4 * math.sin(now * 0.002))

        # Ocean bg
        pygame.draw.rect(self.screen, self.C_OCEAN,
                         (ox - 4, oy - 4, GRID_W*CELL+8, GRID_H*CELL+8),
                         border_radius=8)

        for r in range(GRID_H):
            for c in range(GRID_W):
                rx = ox + c * CELL
                ry = oy + r * CELL
                cell = pygame.Rect(rx+1, ry+1, CELL-2, CELL-2)
                val  = board[r][c]

                if val == 'X':
                    pygame.draw.rect(self.screen, self.C_HIT, cell, border_radius=3)
                    # fire flicker
                    for _ in range(2):
                        fx = rx + CELL//2 + random.randint(-8, 8)
                        fy = ry + CELL//2 + random.randint(-8, 8) + wave
                        pygame.draw.circle(self.screen, self.C_FIRE, (fx, fy), 4)
                elif val == 'O':
                    pygame.draw.rect(self.screen, (10, 50, 110), cell, border_radius=3)
                    pygame.draw.circle(self.screen, self.C_MISS,
                                       (rx+CELL//2, ry+CELL//2+wave), 7)
                else:
                    shade = (8, 40, 90) if (r+c) % 2 == 0 else self.C_OCEAN
                    pygame.draw.rect(self.screen, shade, cell, border_radius=2)

                pygame.draw.rect(self.screen, self.C_GRID, cell, 1, border_radius=2)

        # Hover preview (placement)
        if hover_cells:
            col = (0, 255, 100, 100) if hover_valid else (255, 50, 50, 100)
            hs  = pygame.Surface((CELL-2, CELL-2), pygame.SRCALPHA)
            hs.fill(col)
            for hr, hc in hover_cells:
                if 0 <= hr < GRID_H and 0 <= hc < GRID_W:
                    self.screen.blit(hs, (ox+hc*CELL+1, oy+hr*CELL+1))

        # Grid labels
        for c in range(GRID_W):
            lbl = self.font_sm.render(chr(ord('A')+c), True, (60,130,200))
            self.screen.blit(lbl, (ox + c*CELL + CELL//2 - lbl.get_width()//2, oy-22))
        for r in range(GRID_H):
            lbl = self.font_sm.render(str(r+1), True, (60,130,200))
            self.screen.blit(lbl, (ox - 22, oy + r*CELL + CELL//2 - lbl.get_height()//2))

        # Draw ship silhouettes
        if reveal_ships and ships:
            for ship in ships:
                self._draw_ship_graphic(ship, ox, oy)

    # ──────────────────── events ────────────────────
    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE: self.running = False
                elif ev.key == pygame.K_r and self.game_over: self._full_reset()
                elif ev.key == pygame.K_SPACE and not self.game_over:
                    if self.phase in ("place_p1","place_p2"):
                        p_num  = 1 if self.phase == "place_p1" else 2
                        ships  = self.p1_ships if p_num == 1 else self.p2_ships
                        board  = self.p1_board if p_num == 1 else self.p2_board
                        if getattr(self, 'drag_ship', None) is not None:
                            ship = ships[self.drag_ship]
                            ship["horiz"] = not ship["horiz"]
                            mx, my = pygame.mouse.get_pos()
                            rc = self._rc_from_mouse(mx, my, p_num)
                            if rc:
                                r0 = rc[0] - self.drag_offset_r
                                c0 = rc[1] - self.drag_offset_c
                                new_cells = self._ship_cells(r0, c0, len(ship["cells"]), ship["horiz"])
                                if self._valid_placement(new_cells, board, ships, exclude_ship=self.drag_ship):
                                    ship["cells"] = new_cells
                                    self.drag_cur_rc = new_cells
                        else:
                            self.pl_horiz = not self.pl_horiz
                

            # Transition screen – click to continue
            if self.transition:
                if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    self.transition = False
                continue

            if self.game_over:
                if ev.type == pygame.MOUSEBUTTONDOWN:
                    self._full_reset()
                continue

            mx, my = pygame.mouse.get_pos()

            # ── Placement phase ──
            if self.phase in ("place_p1", "place_p2"):
                p_num  = 1 if self.phase == "place_p1" else 2
                board  = self.p1_board if p_num == 1 else self.p2_board
                ships  = self.p1_ships if p_num == 1 else self.p2_ships
                ox, oy = self._board_origin(p_num)

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 3:
                    if self.drag_ship is not None:
                        ship = ships[self.drag_ship]
                        ship["horiz"] = not ship["horiz"]
                        rc = self._rc_from_mouse(mx, my, p_num)
                        if rc:
                            r0 = rc[0] - self.drag_offset_r
                            c0 = rc[1] - self.drag_offset_c
                            new_cells = self._ship_cells(r0, c0, len(ship["cells"]), ship["horiz"])
                            if self._valid_placement(new_cells, board, ships, exclude_ship=self.drag_ship):
                                ship["cells"] = new_cells
                                self.drag_cur_rc = new_cells
                    else:
                        self.pl_horiz = not self.pl_horiz

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Confirm button
                    if self.pl_idx >= len(self.ship_defs) and self.confirm_btn.collidepoint(mx, my):
                        if self.phase == "place_p1":
                            self.phase    = "place_p2"
                            self.pl_idx   = 0
                            self.pl_horiz = True
                            self.transition     = True
                            p1_name = reshape_persian(self.session.player1_name)
                            p2_name = reshape_persian(self.session.player2_name)
                            self.transition_msg = f"{p2_name} — place your ships\n({p1_name}, look away!)"
                        else:
                            self.phase      = "battle_p1"
                            self.transition = True
                            p1_name = reshape_persian(self.session.player1_name)
                            self.transition_msg = f"Battle begins!\n{p1_name} shoots first"
                        continue

                    rc = self._rc_from_mouse(mx, my, p_num)

                    # Try to pick up existing ship for drag
                    if rc and self.drag_ship is None:
                        for idx, ship in enumerate(ships):
                            if rc in ship["cells"]:
                                self.drag_ship     = idx
                                self.drag_offset_r = rc[0] - ship["cells"][0][0]
                                self.drag_offset_c = rc[1] - ship["cells"][0][1]
                                self._remove_ship_from_board(ship, board)
                                break
                        else:
                            # Place new ship
                            if self.pl_idx < len(self.ship_defs) and rc:
                                name, length = self.ship_defs[self.pl_idx]
                                cells = self._ship_cells(rc[0], rc[1], length, self.pl_horiz)
                                if self._valid_placement(cells, board, ships):
                                    self._place_ship(cells, board, ships, name, self.pl_horiz)
                                    self.pl_idx += 1

                if ev.type == pygame.MOUSEBUTTONUP and ev.button == 1 and self.drag_ship is not None:
                    ship   = ships[self.drag_ship]
                    old_cells = self.drag_cur_rc or ship["cells"]
                    # Try to drop
                    rc = self._rc_from_mouse(mx, my, p_num)
                    placed = False
                    if rc:
                        r0 = rc[0] - self.drag_offset_r
                        c0 = rc[1] - self.drag_offset_c
                        new_cells = self._ship_cells(r0, c0, len(ship["cells"]), ship["horiz"])
                        if self._valid_placement(new_cells, board, ships, exclude_ship=self.drag_ship):
                            ship["cells"] = new_cells
                            placed = True
                    if not placed:
                        pass  # keep old cells (from drag_cur_rc)
                    self._write_ship_to_board(ship, board)
                    self.drag_ship    = None
                    self.drag_cur_rc  = None

                if ev.type == pygame.MOUSEMOTION and self.drag_ship is not None:
                    rc = self._rc_from_mouse(mx, my, p_num)
                    if rc:
                        r0 = rc[0] - self.drag_offset_r
                        c0 = rc[1] - self.drag_offset_c
                        ship = ships[self.drag_ship]
                        new_cells = self._ship_cells(r0, c0, len(ship["cells"]), ship["horiz"])
                        if self._valid_placement(new_cells, board, ships, exclude_ship=self.drag_ship):
                            ship["cells"]    = new_cells
                            self.drag_cur_rc = new_cells

                if ev.type == pygame.MOUSEMOTION and self.pl_idx < len(self.ship_defs):
                    rc = self._rc_from_mouse(mx, my, p_num)
                    self.hover_rc = rc
                    if rc:
                        name, length = self.ship_defs[self.pl_idx]
                        hcells = self._ship_cells(rc[0], rc[1], length, self.pl_horiz)
                        self.hover_valid = self._valid_placement(hcells, board, ships)
                    else:
                        self.hover_valid = False

            # ── Battle phase ──
            elif self.phase in ("battle_p1", "battle_p2") and not self.game_over:
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.phase == "battle_p1":
                        rc = self._rc_from_mouse(mx, my, 2)
                        if rc and rc not in self.p1_shots:
                            self._shoot(rc[0], rc[1], 1)
                            if not self.game_over and not self.extra_turn:
                                self.phase      = "battle_p2"
                                self.transition = True
                                p2_name = reshape_persian(self.session.player2_name)
                                self.transition_msg = f"{p2_name}'s turn"
                    else:
                        rc = self._rc_from_mouse(mx, my, 1)
                        if rc and rc not in self.p2_shots:
                            self._shoot(rc[0], rc[1], 2)
                            if not self.game_over and not self.extra_turn:
                                self.phase      = "battle_p1"
                                self.transition = True
                                p1_name = reshape_persian(self.session.player1_name)
                                self.transition_msg = f"{p1_name}'s turn"

    # ──────────────────── update ────────────────────
    def update(self):
        self.wave_offset = (self.wave_offset + 0.02) % (2 * math.pi)
        now = pygame.time.get_ticks()
        self.anim_hits = [a for a in self.anim_hits if now - a[2] < 900]

    # ──────────────────── draw ────────────────────
    def draw(self):
        self.screen.fill(self.C_BG)
        now = pygame.time.get_ticks()

        # ── Ocean wave lines ──
        for i in range(0, self.H, 48):
            wo = int(5 * math.sin(self.wave_offset + i * 0.04))
            pygame.draw.line(self.screen, (8, 28, 72),
                             (0, i + wo), (self.W, i + wo), 1)

        p1_name = reshape_persian(self.session.player1_name)
        p2_name = reshape_persian(self.session.player2_name)

        # ── Transition screen ──
        if self.transition:
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 230))
            self.screen.blit(ov, (0,0))
            for i, line in enumerate(self.transition_msg.split('\n')):
                t = self.font_md.render(line, True, (200,220,255))
                self.screen.blit(t, (self.W//2 - t.get_width()//2, self.H//2 - 40 + i*50))
            hint = self.font_sm.render("Click or press any key to continue...", True, (120,140,180))
            self.screen.blit(hint, (self.W//2 - hint.get_width()//2, self.H//2 + 80))
            return

        # ── Placement phase ──
        if self.phase in ("place_p1", "place_p2"):
            p_num  = 1 if self.phase == "place_p1" else 2
            board  = self.p1_board if p_num == 1 else self.p2_board
            ships  = self.p1_ships if p_num == 1 else self.p2_ships
            ox, oy = self._board_origin(p_num)
            p_col  = self.C_P1 if p_num == 1 else self.C_P2
            p_name = p1_name   if p_num == 1 else p2_name

            # Hover cells for next ship
            hov = None
            if self.hover_rc and self.pl_idx < len(self.ship_defs):
                _, length = self.ship_defs[self.pl_idx]
                hov = self._ship_cells(self.hover_rc[0], self.hover_rc[1], length, self.pl_horiz)

            self._draw_grid(ox, oy, board, {}, True, hover_cells=hov,
                            hover_valid=self.hover_valid, ships=ships)

            # Draw dragged ship preview
            if self.drag_ship is not None:
                drag_ship = ships[self.drag_ship]
                self._draw_ship_graphic(drag_ship, ox, oy, alpha=160)

            # Title
            title = render_persian_text(self.font_md, f"Place ships — {reshape_persian(p_name)}", p_col)
            self.screen.blit(title, (self.W//2 - title.get_width()//2, 22))

            # Ship list on right
            panel_x = ox + GRID_W * CELL + 20
            if panel_x + 200 > self.W:
                panel_x = 20
            for idx, (sname, slen) in enumerate(self.ship_defs):
                done = idx < self.pl_idx
                cur  = idx == self.pl_idx
                col  = (0,255,100) if done else (p_col if cur else (80,80,100))
                lbl  = self.font_sm.render(
                    f"{'✓ ' if done else ('► ' if cur else '  ')}{sname} ({slen})",
                    True, col)
                self.screen.blit(lbl, (panel_x, oy + idx * 34))

            # Instructions
            instructions = [
                "Left click: place ship",
                "Right click / SPACE: rotate",
                "Drag placed ships to reposition",
                
            ]
            for i, ins in enumerate(instructions):
                s = self.font_sm.render(ins, True, (90,110,140))
                self.screen.blit(s, (20, self.H - 130 + i*26))

            # Confirm button (when all placed)
            if self.pl_idx >= len(self.ship_defs):
                pygame.draw.rect(self.screen, (0,180,80), self.confirm_btn, border_radius=10)
                pygame.draw.rect(self.screen, (0,255,120), self.confirm_btn, 2, border_radius=10)
                ct = self.font_md.render("✔  Confirm Layout", True, (255,255,255))
                self.screen.blit(ct, (self.confirm_btn.x+10, self.confirm_btn.y+10))

        # ── Battle phase ──
        elif self.phase in ("battle_p1", "battle_p2") or self.game_over:
            p1_act = self.phase == "battle_p1" and not self.game_over
            p2_act = self.phase == "battle_p2" and not self.game_over
            
            # P1 board (left) – hide P1's ships (unless game over)
            self._draw_grid(self.b1x, self.bby, self.p1_board, self.p2_shots,
                            reveal_ships=self.game_over, ships=self.p1_ships if self.game_over else None)
                            
            # P2 board (right) – hide P2's ships (unless game over)
            self._draw_grid(self.b2x, self.bby, self.p2_board, self.p1_shots,
                            reveal_ships=self.game_over, ships=self.p2_ships if self.game_over else None)

            

            # Player name labels
            for (ox, p_name, p_col, active) in [
                (self.b1x, reshape_persian(p1_name), self.C_P1, p1_act),
                (self.b2x, reshape_persian(p2_name), self.C_P2, p2_act),
            ]:
                border_col = p_col if active else (50,60,80)
                panel = pygame.Surface((GRID_W*CELL, 30), pygame.SRCALPHA)
                panel.fill((10,20,50,200))
                self.screen.blit(panel, (ox, self.bby - 36))
                pygame.draw.rect(self.screen, border_col,
                                 (ox, self.bby-36, GRID_W*CELL, 30), 1, border_radius=4)
                t = render_persian_text(self.font_sm, p_name, p_col)
                self.screen.blit(t, (ox + GRID_W*CELL//2 - t.get_width()//2, self.bby - 30))

            # Turn arrow / hit bonus label
            if not self.game_over:
                cur_name  = p1_name if p1_act else p2_name
                cur_col   = self.C_P1 if p1_act else self.C_P2
                shoot_txt = "Click enemy board to fire!"
                ti = render_persian_text(self.font_sm, f"🎯 {reshape_persian(cur_name)}'s turn — {shoot_txt}", cur_col)
                self.screen.blit(ti, (self.W//2 - ti.get_width()//2, self.H - 40))
                if self.extra_turn:
                    bonus = self.font_sm.render("✦ Hit! Bonus shot!", True, (255,200,50))
                    self.screen.blit(bonus, (self.W//2 - bonus.get_width()//2, self.H - 65))

        # ── Hit ripple animations ──
        for ax, ay, at in self.anim_hits:
            age = now - at
            r_s = int(age * 0.07)
            alp = max(0, 220 - int(age * 0.26))
            if r_s > 0 and alp > 0:
                rsurf = pygame.Surface((r_s*2+4, r_s*2+4), pygame.SRCALPHA)
                pygame.draw.circle(rsurf, (*self.C_HIT, alp), (r_s+2, r_s+2), r_s, 2)
                self.screen.blit(rsurf, (ax - r_s - 2, ay - r_s - 2))

        # ── Message ──
        if self.msg and now < self.msg_timer:
            ms = self.font_md.render(self.msg, True, (255, 210, 60))
            self.screen.blit(ms, (self.W//2 - ms.get_width()//2, self.H//2 - 50))

        # ── Win overlay ──
        if self.game_over:
            ov = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
            ov.fill((0,0,0,185))
            self.screen.blit(ov, (0,0))
            wn = p1_name if self.winner == 1 else p2_name
            wc = self.C_P1 if self.winner == 1 else self.C_P2
            wt = render_persian_text(self.font_lg, f"⚓ {reshape_persian(wn)} WINS!", wc)
            self.screen.blit(wt, (self.W//2 - wt.get_width()//2, self.H//2 - 60))
            re = self.font_sm.render("Click, or press R to restart | ESC to exit", True, (180,180,200))
            self.screen.blit(re, (self.W//2 - re.get_width()//2, self.H//2 + 50))
