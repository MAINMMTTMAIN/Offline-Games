import sys
import os
import pygame
import random
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import reshape_persian, render_persian_text
from main import resource_path

ROWS = 6
COLS = 7
CELL_SIZE = 80
RADIUS = int(CELL_SIZE / 2 - 5)
BOARD_WIDTH = COLS * CELL_SIZE
BOARD_HEIGHT = ROWS * CELL_SIZE

BG_COLOR = (15, 15, 26)
BOARD_COLOR = (25, 25, 40)
BOARD_BORDER = (0, 240, 255)
P1_COLOR = (255, 0, 80)
P2_COLOR = (0, 255, 255)
EMPTY_COLOR = (10, 10, 15)

# Gravity: pixels per second² (feel ≈ real gravity)
GRAVITY = 2500.0


class FallingPiece:
    """A disc that animates from the top of the column to its target row."""
    def __init__(self, col, target_row, piece, start_y, target_y):
        self.col = col
        self.target_row = target_row
        self.piece = piece          # 1 or 2
        self.y = float(start_y)     # current pixel-Y (screen space)
        self.target_y = float(target_y)
        self.vy = 0.0               # pixels / second
        self.done = False
        self.bounce_count = 0
        self.max_bounces = 2

    def update(self, dt):
        if self.done:
            return
        self.vy += GRAVITY * dt
        self.y += self.vy * dt
        if self.y >= self.target_y:
            # Bounce
            self.y = self.target_y
            self.vy = -self.vy * 0.35   # damping
            self.bounce_count += 1
            if abs(self.vy) < 80 or self.bounce_count >= self.max_bounces:
                self.y = self.target_y
                self.vy = 0.0
                self.done = True


class ConnectFour(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.W = screen.get_width()
        self.H = screen.get_height()
        self.start_x = (self.W - BOARD_WIDTH) // 2
        self.start_y = (self.H - BOARD_HEIGHT) // 2 + 50

        self.font_lg = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 48)
        self.font_md = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)

        self.board = [[0] * COLS for _ in range(ROWS)]
        self.turn = 1
        self.state = "PLAYING"
        self.winner = 0

        self.is_sp = getattr(self.session, 'is_single_player', False)
        self.difficulty = getattr(self.session, 'bot_difficulty', 'medium')

        # Animation state
        self.falling: FallingPiece | None = None
        self._pending_check = None   # (row, col, piece) to evaluate after animation

        self._last_time = pygame.time.get_ticks()

        pygame.display.set_caption("Connect Four - Cyberpunk Edition")

    # ─── Board helpers ───────────────────────────────────────────────────────

    def is_valid_location(self, board, col):
        return board[0][col] == 0

    def get_next_open_row(self, board, col):
        for r in range(ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return -1

    def drop_piece(self, board, row, col, piece):
        board[row][col] = piece

    def winning_move(self, board, piece):
        for c in range(COLS - 3):
            for r in range(ROWS):
                if all(board[r][c + i] == piece for i in range(4)):
                    return True
        for c in range(COLS):
            for r in range(ROWS - 3):
                if all(board[r + i][c] == piece for i in range(4)):
                    return True
        for c in range(COLS - 3):
            for r in range(ROWS - 3):
                if all(board[r + i][c + i] == piece for i in range(4)):
                    return True
        for c in range(COLS - 3):
            for r in range(3, ROWS):
                if all(board[r - i][c + i] == piece for i in range(4)):
                    return True
        return False

    # ─── AI helpers ──────────────────────────────────────────────────────────

    def evaluate_window(self, window, piece):
        score = 0
        opp = 1 if piece == 2 else 2
        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2
        if window.count(opp) == 3 and window.count(0) == 1:
            score -= 4
        return score

    def score_position(self, board, piece):
        score = 0
        center = [board[r][COLS // 2] for r in range(ROWS)]
        score += center.count(piece) * 3
        for r in range(ROWS):
            for c in range(COLS - 3):
                score += self.evaluate_window(board[r][c:c + 4], piece)
        for c in range(COLS):
            col_arr = [board[r][c] for r in range(ROWS)]
            for r in range(ROWS - 3):
                score += self.evaluate_window(col_arr[r:r + 4], piece)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += self.evaluate_window([board[r + i][c + i] for i in range(4)], piece)
                score += self.evaluate_window([board[r + 3 - i][c + i] for i in range(4)], piece)
        return score

    def get_valid_locations(self, board):
        return [c for c in range(COLS) if self.is_valid_location(board, c)]

    def is_terminal_node(self, board):
        return (self.winning_move(board, 1) or self.winning_move(board, 2)
                or len(self.get_valid_locations(board)) == 0)

    def minimax(self, board, depth, alpha, beta, maximizing):
        valid = self.get_valid_locations(board)
        terminal = self.is_terminal_node(board)
        if depth == 0 or terminal:
            if terminal:
                if self.winning_move(board, 2):  return None, 10 ** 14
                if self.winning_move(board, 1):  return None, -(10 ** 14)
                return None, 0
            return None, self.score_position(board, 2)
        if maximizing:
            value, column = -math.inf, random.choice(valid)
            for col in valid:
                row = self.get_next_open_row(board, col)
                b = [r[:] for r in board]
                self.drop_piece(b, row, col, 2)
                score = self.minimax(b, depth - 1, alpha, beta, False)[1]
                if score > value:
                    value, column = score, col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value
        else:
            value, column = math.inf, random.choice(valid)
            for col in valid:
                row = self.get_next_open_row(board, col)
                b = [r[:] for r in board]
                self.drop_piece(b, row, col, 1)
                score = self.minimax(b, depth - 1, alpha, beta, True)[1]
                if score < value:
                    value, column = score, col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value

    # ─── Drop with animation ──────────────────────────────────────────────────

    def _start_drop(self, col, piece):
        """Starts a falling animation for piece in col. Does NOT write to board yet."""
        row = self.get_next_open_row(self.board, col)
        if row < 0:
            return

        # Pixel coords
        start_y = self.start_y - CELL_SIZE        # just above the board
        target_y = self.start_y + row * CELL_SIZE + CELL_SIZE // 2

        self.falling = FallingPiece(col, row, piece, start_y + CELL_SIZE // 2, target_y)
        self._pending_check = (row, col, piece)

    def _finish_drop(self):
        """Called once the animation finishes; writes to board and checks win."""
        if self._pending_check is None:
            return
        row, col, piece = self._pending_check
        self._pending_check = None
        self.falling = None

        self.drop_piece(self.board, row, col, piece)

        if self.winning_move(self.board, piece):
            key = "player1" if piece == 1 else "player2"
            self.session.scores[key] += 1
            self.state = "WIN_P1" if piece == 1 else "WIN_P2"
            self.winner = piece
        elif len(self.get_valid_locations(self.board)) == 0:
            self.state = "DRAW"
        else:
            self.turn = 2 if piece == 1 else 1

    # ─── Bot move ────────────────────────────────────────────────────────────

    def bot_move(self):
        valid = self.get_valid_locations(self.board)
        if not valid:
            return
        if self.difficulty == "low":
            col = random.choice(valid)
        elif self.difficulty == "medium":
            col = random.choice(valid)
            # Win if possible
            for c in valid:
                r = self.get_next_open_row(self.board, c)
                b = [row[:] for row in self.board]
                self.drop_piece(b, r, c, 2)
                if self.winning_move(b, 2):
                    col = c
                    break
            else:
                # Block player win
                for c in valid:
                    r = self.get_next_open_row(self.board, c)
                    b = [row[:] for row in self.board]
                    self.drop_piece(b, r, c, 1)
                    if self.winning_move(b, 1):
                        col = c
                        break
        else:
            col, _ = self.minimax(self.board, 5, -math.inf, math.inf, True)
            if col is None:
                col = random.choice(valid)

        self._start_drop(col, 2)

    # ─── Events ──────────────────────────────────────────────────────────────

    def handle_events(self, events):
        for ev in events:
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state in ["WIN_P1", "WIN_P2", "DRAW"] and ev.key == pygame.K_r:
                    self.__init__(self.screen, self.session)
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state == "PLAYING" and self.falling is None:
                    if self.turn == 1 or (not self.is_sp and self.turn == 2):
                        mx, my = ev.pos
                        if (self.start_x <= mx <= self.start_x + BOARD_WIDTH and
                                self.start_y <= my <= self.start_y + BOARD_HEIGHT):
                            col = int((mx - self.start_x) // CELL_SIZE)
                            if 0 <= col < COLS and self.is_valid_location(self.board, col):
                                self._start_drop(col, self.turn)

    # ─── Update ──────────────────────────────────────────────────────────────

    def update(self):
        now = pygame.time.get_ticks()
        dt = (now - self._last_time) / 1000.0
        dt = min(dt, 0.05)   # cap at 50ms to avoid tunnelling
        self._last_time = now

        # Animate falling piece
        if self.falling is not None:
            self.falling.update(dt)
            if self.falling.done:
                self._finish_drop()
            return   # Block input and bot while animating

        # Bot's turn
        if self.state == "PLAYING" and self.is_sp and self.turn == 2:
            self.bot_move()

    # ─── Draw ────────────────────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(BG_COLOR)

        p1_name = reshape_persian(self.session.player1_name)
        p2_name = reshape_persian(self.session.player2_name)

        t1 = render_persian_text(self.font_md, f"{reshape_persian(p1_name)}: {self.session.scores['player1']}", P1_COLOR)
        self.screen.blit(t1, (50, 50))
        t2 = render_persian_text(self.font_md, f"{reshape_persian(p2_name)}: {self.session.scores['player2']}", P2_COLOR)
        self.screen.blit(t2, (self.W - t2.get_width() - 50, 50))

        if self.state == "PLAYING":
            turn_name = p1_name if self.turn == 1 else p2_name
            color = P1_COLOR if self.turn == 1 else P2_COLOR
            t = render_persian_text(self.font_md, reshape_persian(f"{turn_name}'s Turn"), color)
            self.screen.blit(t, (self.W // 2 - t.get_width() // 2, 50))

        # Board background
        pygame.draw.rect(self.screen, BOARD_COLOR,
                         (self.start_x - 10, self.start_y - 10, BOARD_WIDTH + 20, BOARD_HEIGHT + 20),
                         border_radius=15)
        pygame.draw.rect(self.screen, BOARD_BORDER,
                         (self.start_x - 10, self.start_y - 10, BOARD_WIDTH + 20, BOARD_HEIGHT + 20),
                         width=4, border_radius=15)

        # Cells
        for r in range(ROWS):
            for c in range(COLS):
                cx = self.start_x + c * CELL_SIZE + CELL_SIZE // 2
                cy = self.start_y + r * CELL_SIZE + CELL_SIZE // 2

                # Skip the cell that is being animated (we'll draw it separately)
                if (self.falling is not None and
                        self.falling.col == c and self.falling.target_row == r):
                    pygame.draw.circle(self.screen, EMPTY_COLOR, (cx, cy), RADIUS)
                    continue

                piece = self.board[r][c]
                if piece == 0:
                    pygame.draw.circle(self.screen, EMPTY_COLOR, (cx, cy), RADIUS)
                else:
                    color = P1_COLOR if piece == 1 else P2_COLOR
                    pygame.draw.circle(self.screen, color, (cx, cy), RADIUS)
                    # Inner highlight
                    pygame.draw.circle(self.screen, (255, 255, 255), (cx - 4, cy - 4), RADIUS // 4)
                    # Glow ring
                    pygame.draw.circle(self.screen, color, (cx, cy), RADIUS + 4, 2)

        # Falling piece animation
        if self.falling is not None:
            fx = self.start_x + self.falling.col * CELL_SIZE + CELL_SIZE // 2
            fy = int(self.falling.y)
            color = P1_COLOR if self.falling.piece == 1 else P2_COLOR
            pygame.draw.circle(self.screen, color, (fx, fy), RADIUS)
            pygame.draw.circle(self.screen, (255, 255, 255), (fx - 4, fy - 4), RADIUS // 4)
            pygame.draw.circle(self.screen, color, (fx, fy), RADIUS + 4, 2)

        # Hover preview (only when no animation)
        if self.state == "PLAYING" and self.falling is None:
            if self.turn == 1 or (not self.is_sp and self.turn == 2):
                mx, my = pygame.mouse.get_pos()
                if self.start_x <= mx <= self.start_x + BOARD_WIDTH:
                    col = int((mx - self.start_x) // CELL_SIZE)
                    if 0 <= col < COLS:
                        hx = self.start_x + col * CELL_SIZE + CELL_SIZE // 2
                        color = P1_COLOR if self.turn == 1 else P2_COLOR
                        s = pygame.Surface((RADIUS * 2 + 10, RADIUS * 2 + 10), pygame.SRCALPHA)
                        pygame.draw.circle(s, (*color, 140), (RADIUS + 5, RADIUS + 5), RADIUS)
                        self.screen.blit(s, (hx - RADIUS - 5, self.start_y - CELL_SIZE // 2 - RADIUS - 5))

        # Win / Draw overlay
        if self.state in ["WIN_P1", "WIN_P2", "DRAW"]:
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
