import os
import sys
import pygame
import chess  # کتابخانه مدیریت قوانین شطرنج
from persian_utils import render_persian_text, reshape_persian
from main import resource_path
# اضافه کردن مسیر پوشه اصلی پروژه به پایتون
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame

class Chess(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        pygame.display.set_caption("Chess - Chess.com Style")
        
        self.SCREEN_WIDTH = screen.get_width()
        self.SCREEN_HEIGHT = screen.get_height()
        
        # --- رنگ‌های اختصاصی تم Chess.com ---
        self.BG_COLOR = (49, 46, 43)          # پس‌زمینه تیره Chess.com
        self.LIGHT_SQ = (235, 236, 208)       # خانه‌های روشن (کرمی)
        self.DARK_SQ = (119, 149, 86)         # خانه‌های تیره (سبز Chess.com)
        self.HIGHLIGHT_COLOR = (247, 247, 105) # هایلایت زرد برای آخرین حرکت
        self.SELECTED_COLOR = (186, 202, 43)  # هایلایت مهره انتخاب شده
        self.TEXT_COLOR = (255, 255, 255)
        self.PANEL_COLOR = (38, 36, 33)        # پنل سمت راست برای لیست حرکت‌ها
        
        # --- تنظیمات ابعاد صفحه شطرنج ---
        self.board_size = min(self.SCREEN_HEIGHT - 160, 560)  # ابعاد مربع صفحه
        self.sq_size = self.board_size // 8
        self.start_x = (self.SCREEN_WIDTH - self.board_size) // 2 - 120 # متمایل به چپ برای جا شدن پنل
        self.start_y = (self.SCREEN_HEIGHT - self.board_size) // 2 + 20
        
        # --- منطق و وضعیت بازی ---
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.last_move = None
        self.game_over = False
        self.score_added = False
        self.winner_msg = ""
        self.move_history = []  # ذخیره متنی حرکت‌ها برای نمایش در پنل
        
        self.dragging_piece = None
        self.drag_pos = None
        
        self.dragging_piece = None
        self.drag_pos = None

        # --- فونت‌ها ---
        self.font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 22)
        self.font_move = pygame.font.SysFont("Courier", 18)
        self.font_big = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 40)
        # فونت یونیکد برای مهره‌های شطرنج
        self.piece_font = pygame.font.SysFont("Segoe UI Symbol", int(self.sq_size * 0.75))

        # جدول تبدیل مهره‌ها به کاراکترهای گرافیکی یونیکد (برای Fallback)
        self.unicode_pieces = {
            'R': '♜', 'N': '♞', 'B': '♝', 'Q': '♛', 'K': '♚', 'P': '♟', # مهره‌های سیاه
            'r': '♖', 'n': '♘', 'b': '♗', 'q': '♕', 'k': '♔', 'p': '♙'  # مهره‌های سفید
        }

        # بارگذاری تصاویر مهره‌ها
        self.pieces_images = {}
        self.load_pieces()

    def load_pieces(self):
        # آدرس‌دهی درست با استفاده از تابع resource_path که از main وارد کردیم
        assets_dir = resource_path(os.path.join("games", "chess", "assets", "pieces"))
        pieces = ['wp', 'wn', 'wb', 'wr', 'wq', 'wk', 'bp', 'bn', 'bb', 'br', 'bq', 'bk']
        for p in pieces:
            path = os.path.join(assets_dir, f"{p}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self.pieces_images[p] = pygame.transform.smoothscale(img, (self.sq_size, self.sq_size))

    def get_screen_coords(self, sq):
        col = chess.square_file(sq)
        row = chess.square_rank(sq)
        
        is_flipped = (self.board.turn == chess.BLACK)
        if is_flipped:
            col = 7 - col
            row = 7 - row
            
        x = self.start_x + col * self.sq_size
        y = self.start_y + (7 - row) * self.sq_size
        return x, y

    def get_board_square(self, mx, my):
        col = (mx - self.start_x) // self.sq_size
        row = 7 - ((my - self.start_y) // self.sq_size)
        
        is_flipped = (self.board.turn == chess.BLACK)
        if is_flipped:
            col = 7 - col
            row = 7 - row
            
        if 0 <= col <= 7 and 0 <= row <= 7:
            return chess.square(int(col), int(row))
        return None

    def draw_piece(self, piece, x, y):
        symbol = piece.symbol()
        color_prefix = 'w' if piece.color == chess.WHITE else 'b'
        piece_key = f"{color_prefix}{symbol.lower()}"
        
        if hasattr(self, 'pieces_images') and piece_key in self.pieces_images:
            self.screen.blit(self.pieces_images[piece_key], (x, y))
        else:
            cx = x + self.sq_size // 2
            cy = y + self.sq_size // 2
            char_to_draw = self.unicode_pieces.get(symbol, '')
            p_color = (255, 255, 255) if piece.color == chess.WHITE else (20, 20, 20)
            p_surf = self.piece_font.render(char_to_draw, True, p_color)
            self.screen.blit(p_surf, (cx - p_surf.get_width() // 2, cy - p_surf.get_height() // 2 - 5))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset_game()
                    
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over:
                    # دکمه بازگشت به منو
                    mouse_pos = event.pos
                    back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 100, 160, 45)
                    
                    if back_rect.collidepoint(mouse_pos):
                        self.running = False
                    else:
                        self.reset_game()
                    continue
                
                mx, my = event.pos
                # بررسی اینکه آیا داخل صفحه شطرنج کلیک شده است
                if (self.start_x <= mx <= self.start_x + self.board_size and 
                    self.start_y <= my <= self.start_y + self.board_size):
                    
                    square = self.get_board_square(mx, my)
                    if square is not None:
                        # اگر مهره خودی بود برای درگ اند دراپ انتخابش کن
                        piece = self.board.piece_at(square)
                        if piece and piece.color == self.board.turn:
                            self.dragging_piece = square
                            self.drag_pos = event.pos
                            
                        self.handle_square_click(square)

            elif event.type == pygame.MOUSEMOTION:
                if self.dragging_piece is not None:
                    self.drag_pos = event.pos
                    
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging_piece is not None:
                    mx, my = event.pos
                    if (self.start_x <= mx <= self.start_x + self.board_size and 
                        self.start_y <= my <= self.start_y + self.board_size):
                        target_square = self.get_board_square(mx, my)
                        if target_square is not None and target_square != self.dragging_piece:
                            # شبیه‌سازی کلیک روی خانه مقصد برای انجام حرکت
                            self.selected_square = self.dragging_piece
                            self.handle_square_click(target_square)
                            
                    self.dragging_piece = None

    def handle_square_click(self, square):
        if self.selected_square is None:
            # انتخاب مهره جدید
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.valid_moves = [m.to_square for m in self.board.legal_moves if m.from_square == square]
            return

        # اگر مهره‌ای قبلاً انتخاب شده و روی یکی از خانه‌های مجاز کلیک شود: حرکت انجام شود
        move = chess.Move(self.selected_square, square)
        
        # بررسی ارتقای پیاده (Promotion) به وزیر به صورت خودکار برای سادگی
        pawn_promotion_move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
        
        if pawn_promotion_move in self.board.legal_moves:
            move = pawn_promotion_move

        if move in self.board.legal_moves:
            # ثبت متن سان (SAN) حرکت قبل از اعمال روی صفحه برای پنل راست
            move_san = self.board.san(move)
            self.move_history.append(move_san)
            
            # انجام حرکت
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self.valid_moves = []
            
            # بررسی پایان بازی
            self.check_game_status()
        else:
            # انتخاب مهره جدید
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                # استخراج تمام حرکت‌های مجاز برای این مهره
                self.valid_moves = [m.to_square for m in self.board.legal_moves if m.from_square == square]
            else:
                self.selected_square = None
                self.valid_moves = []

    def check_game_status(self):
        if self.board.is_game_over():
            self.game_over = True
            result = self.board.result()
            
            if result == "1-0":
                self.winner_msg = f"{reshape_persian(self.session.player1_name)} Wins! (White) 🏆"
                if not self.score_added:
                    self.session.scores["player1"] += 1
            elif result == "0-1":
                self.winner_msg = f"{reshape_persian(self.session.player2_name)} Wins! (Black) 🏆"
                if not self.score_added:
                    self.session.scores["player2"] += 1
            else:
                self.winner_msg = "Draw / Stalemate 🤝"
                
            self.score_added = True

    def reset_game(self):
        self.board = chess.Board()
        self.selected_square = None
        self.valid_moves = []
        self.last_move = None
        self.game_over = False
        self.score_added = False
        self.winner_msg = ""
        self.move_history.clear()
        self.move_history.clear()

    def update(self):
        pass

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        # راهنمای کیبورد بالا صفحه
        hint_top = self.font.render("Press 'ESC' to Exit  |  Press 'R' to Restart Chess", True, (150, 150, 150))
        self.screen.blit(hint_top, (20, 20))
        
        # نمایش نوبت بازیکن در بالای صفحه
        if not self.game_over:
            turn_name = reshape_persian(self.session.player1_name) if self.board.turn == chess.WHITE else reshape_persian(self.session.player2_name)
            turn_color = (255, 255, 255) if self.board.turn == chess.WHITE else (150, 150, 150)
            turn_text = f"Turn: {turn_name} ({'White' if self.board.turn == chess.WHITE else 'Black'})"
            txt_surf = self.font.render(turn_text, True, turn_color)
            self.screen.blit(txt_surf, (self.start_x, self.start_y - 40))

        # ۱. رسم صفحات شطرنج
        for row in range(8):
            for col in range(8):
                x = self.start_x + col * self.sq_size
                y = self.start_y + row * self.sq_size
                
                # رنگ پایه‌ای خانه
                base_color = self.LIGHT_SQ if (row + col) % 2 == 0 else self.DARK_SQ
                pygame.draw.rect(self.screen, base_color, (x, y, self.sq_size, self.sq_size))

        # هایلایت آخرین حرکت انجام شده
        if self.last_move:
            for sq in (self.last_move.from_square, self.last_move.to_square):
                hx, hy = self.get_screen_coords(sq)
                pygame.draw.rect(self.screen, self.HIGHLIGHT_COLOR, (hx, hy, self.sq_size, self.sq_size))
                
        # هایلایت مهره انتخاب شده فعلی
        if self.selected_square is not None:
            hx, hy = self.get_screen_coords(self.selected_square)
            pygame.draw.rect(self.screen, self.SELECTED_COLOR, (hx, hy, self.sq_size, self.sq_size))

        # ۲. رسم دایره‌های راهنمای حرکت مجاز
        for sq in self.valid_moves:
            hx, hy = self.get_screen_coords(sq)
            cx = hx + self.sq_size // 2
            cy = hy + self.sq_size // 2
            
            if self.board.piece_at(sq):
                pygame.draw.circle(self.screen, (0, 0, 0, 40), (cx, cy), self.sq_size // 2 - 4, 6)
            else:
                pygame.draw.circle(self.screen, (0, 0, 0, 40), (cx, cy), self.sq_size // 6)

        # ۳. رندر و رسم مهره‌ها روی صفحه
        for sq in chess.SQUARES:
            if sq == self.dragging_piece:
                continue # این مهره را در آخر رسم میکنیم تا روی بقیه قرار بگیرد
                
            piece = self.board.piece_at(sq)
            if piece:
                x, y = self.get_screen_coords(sq)
                self.draw_piece(piece, x, y)
                
        # رسم مهره‌ای که در حال درگ شدن است
        if self.dragging_piece is not None:
            piece = self.board.piece_at(self.dragging_piece)
            if piece and self.drag_pos:
                mx, my = self.drag_pos
                x = mx - self.sq_size // 2
                y = my - self.sq_size // 2
                self.draw_piece(piece, x, y)

        # ۴. رسم پنل لیست حرکت‌ها (Move Log Panel) در سمت راست دسکتاپ
        panel_x = self.start_x + self.board_size + 40
        panel_rect = pygame.Rect(panel_x, self.start_y, 240, self.board_size)
        pygame.draw.rect(self.screen, self.PANEL_COLOR, panel_rect, border_radius=8)
        
        panel_title = self.font.render("LIVE MOVES", True, (150, 152, 148))
        self.screen.blit(panel_title, (panel_x + 20, self.start_y + 15))
        
        # نمایش حداکثر ۱۲ ردیف حرکت آخر بازی به صورت جفت حرکت (سفید و سیاه)
        start_render_idx = max(0, (len(self.move_history) + 1) // 2 - 12)
        for i in range(start_render_idx, (len(self.move_history) + 1) // 2):
            w_idx = i * 2
            b_idx = i * 2 + 1
            
            move_num_str = f"{i + 1}."
            w_move_str = self.move_history[w_idx] if w_idx < len(self.move_history) else ""
            b_move_str = self.move_history[b_idx] if b_idx < len(self.move_history) else ""
            
            row_y = self.start_y + 55 + (i - start_render_idx) * 30
            
            # رندر شماره ردیف، حرکت سفید و حرکت سیاه
            num_surf = self.font_move.render(move_num_str, True, (100, 100, 100))
            self.screen.blit(num_surf, (panel_x + 20, row_y))
            
            w_surf = self.font_move.render(w_move_str, True, (200, 200, 200))
            self.screen.blit(w_surf, (panel_x + 65, row_y))
            
            b_surf = self.font_move.render(b_move_str, True, (150, 150, 150))
            self.screen.blit(b_surf, (panel_x + 155, row_y))

        # ۵. صفحه پاپ‌آپ اتمام مسابقه (کیش و مات / مساوی)
        if self.game_over:
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 220))
            self.screen.blit(overlay, (0, 0))
            
            win_surf = self.font_big.render(self.winner_msg, True, (255, 255, 255))
            self.screen.blit(win_surf, (self.SCREEN_WIDTH // 2 - win_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 - 50))
            
            hint_surf = self.font.render("Click anywhere else to Restart", True, (150, 150, 150))
            self.screen.blit(hint_surf, (self.SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 20))
            
            back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 100, 160, 45)
            pygame.draw.rect(self.screen, (60, 60, 65), back_rect, border_radius=8)
            back_surf = self.font.render("Main Menu", True, (255, 255, 255))
            self.screen.blit(back_surf, (self.SCREEN_WIDTH // 2 - back_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 108))
