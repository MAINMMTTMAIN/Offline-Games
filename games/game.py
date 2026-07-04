import os
import sys
import pygame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path

# اضافه کردن مسیر پوشه اصلی پروژه به پایتون برای حل مشکل Import کلاس پایه
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame

class DotsAndBoxes(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session  # ذخیره سیستم امتیازات و نام بازیکنان
        pygame.display.set_caption("Dots and Boxes - Arcade Mode")
        
        # دریافت ابعاد مانیتور به صورت پویا برای وسط‌چین کردن نقشه بازی
        self.SCREEN_WIDTH = screen.get_width()
        self.SCREEN_HEIGHT = screen.get_height()
        
        # --- رنگ‌ها (تم نئونی سایبرپانک) ---
        self.BG_COLOR = (12, 12, 22)
        self.DOT_COLOR = (240, 240, 255)
        self.LINE_HOVER_COLOR = (50, 50, 80)
        self.COLOR_P1 = (255, 40, 100)    # صورتی نئون (بازیکن اول)
        self.COLOR_P2 = (0, 245, 180)     # سبز فسفری نئون (بازیکن دوم)
        self.TEXT_COLOR = (220, 220, 240)
        
        # --- تنظیمات جدول بازی (یک جدول ۴ در ۴ از نقطه‌ها که ۹ باکس ایجاد می‌کند) ---
        self.GRID_SIZE = 8
        self.cell_size = 100
        self.start_x = (self.SCREEN_WIDTH - ((self.GRID_SIZE - 1) * self.cell_size)) // 2
        self.start_y = (self.SCREEN_HEIGHT - ((self.GRID_SIZE - 1) * self.cell_size)) // 2
        self.dot_radius = 8
        self.line_thickness = 6
        
        # --- وضعیت‌های بازی ---
        self.current_player = 1  # 1 = بازیکن اول، 2 = بازیکن دوم
        self.game_over = False
        self.score_added = False
        
        # ذخیره خطوط کشیده شده: (نوع خط 'h' یا 'v', ردیف, ستون) -> شماره بازیکن
        self.lines = {} 
        # ذخیره باکس‌های تصاحب شده: (ردیف, ستون) -> شماره بازیکن
        self.boxes = {}
        
        # شمارش تعداد باکس‌های برده شده هر بازیکن در این راند
        self.p1_boxes_count = 0
        self.p2_boxes_count = 0
        self.winner = None

        # --- تنظیمات فونت ---
        self.font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        self.font_big = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 44)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                
            # قابلیت خروج و ریستارت در وسط بازی با کیبورد
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # برگشت به منوی اصلی با زدن دکمه ESC
                    self.running = False
                elif event.key == pygame.K_r:       # ریستارت کردن بازی با زدن دکمه R
                    self.reset_game()
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over:
                    mouse_pos = event.pos
                    # دکمه منوی اصلی هماهنگ با مرکز مانیتور
                    back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 140, 160, 45)
                    
                    if back_rect.collidepoint(mouse_pos):
                        self.running = False  # برگشت به منوی اصلی هاب
                    else:
                        self.reset_game()     # شروع مجدد بازی
                    continue

                # پیدا کردن خطی که به کلیک موس نزدیک است
                mx, my = event.pos
                clicked_line = self.get_closest_line(mx, my)
                
                if clicked_line and clicked_line not in self.lines:
                    # ثبت خط برای بازیکن فعلی
                    self.lines[clicked_line] = self.current_player
                    
                    # بررسی اینکه آیا با این خط باکسی کامل شده است یا خیر
                    boxes_completed = self.check_new_boxes()
                    
                    if boxes_completed > 0:
                        # اگر باکسی کامل شد، امتیاز بازیکن اضافه می‌شود
                        if self.current_player == 1:
                            self.p1_boxes_count += boxes_completed
                        else:
                            self.p2_boxes_count += boxes_completed
                            
                        # بررسی شرط پایان بازی (کامل شدن تمام ۹ باکس زمین)
                        if len(self.boxes) == (self.GRID_SIZE - 1) * (self.GRID_SIZE - 1):
                            self.game_over = True
                            self.calculate_winner()
                    else:
                        # اگر باکسی کامل نشد، نوبت عوض می‌شود
                        self.current_player = 3 - self.current_player

    def get_closest_line(self, mx, my):
        """ پیدا کردن نزدیک‌ترین خط افقی یا عمودی به موقعیت کلیک موس """
        threshold = 15  # میزان حساسیت کلیک نزدیک خط
        
        # بررسی خطوط افقی
        for r in range(self.GRID_SIZE):
            for c in range(self.GRID_SIZE - 1):
                lx = self.start_x + c * self.cell_size
                ly = self.start_y + r * self.cell_size
                rect = pygame.Rect(lx, ly - threshold, self.cell_size, threshold * 2)
                if rect.collidepoint(mx, my):
                    return ('h', r, c)
                    
        # بررسی خطوط عمودی
        for r in range(self.GRID_SIZE - 1):
            for c in range(self.GRID_SIZE):
                lx = self.start_x + c * self.cell_size
                ly = self.start_y + r * self.cell_size
                rect = pygame.Rect(lx - threshold, ly, threshold * 2, self.cell_size)
                if rect.collidepoint(mx, my):
                    return ('v', r, c)
        return None

    def check_new_boxes(self):
        """ بررسی تمام باکس‌ها برای پیدا کردن باکس‌های تازه کامل شده """
        new_boxes_found = 0
        for r in range(self.GRID_SIZE - 1):
            for c in range(self.GRID_SIZE - 1):
                if (r, c) not in self.boxes:
                    # یک باکس زمانی کامل است که هر ۴ خط آن رسم شده باشد
                    top = ('h', r, c)
                    bottom = ('h', r + 1, c)
                    left = ('v', r, c)
                    right = ('v', r, c + 1)
                    
                    if top in self.lines and bottom in self.lines and left in self.lines and right in self.lines:
                        self.boxes[(r, c)] = self.current_player
                        new_boxes_found += 1
        return new_boxes_found

    def calculate_winner(self):
        """ مشخص کردن برنده نهایی راند (فقط زمانی که بازی کاملاً به پایان رسیده) """
        if self.p1_boxes_count > self.p2_boxes_count:
            self.winner = 1
        elif self.p2_boxes_count > self.p1_boxes_count:
            self.winner = 2
        else:
            self.winner = "Draw"

        # ثبت و افزایش امتیاز در سشن اصلی پروژه
        if not self.score_added:
            if self.winner == 1:
                self.session.scores["player1"] += 1
            elif self.winner == 2:
                self.session.scores["player2"] += 1
            self.score_added = True

    def reset_game(self):
        self.lines.clear()
        self.boxes.clear()
        self.p1_boxes_count = 0
        self.p2_boxes_count = 0
        self.current_player = 1
        self.winner = None
        self.game_over = False
        self.score_added = False

    def update(self):
        pass

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        # نوار بالایی راهنمای کلیدهای کیبورد
        hint_top = self.font.render("Press 'ESC' to Exit  |  Press 'R' to Restart Game", True, (100, 100, 120))
        self.screen.blit(hint_top, (20, 20))
        
        # ۱. نمایش نوبت بازیکنان در بالای صفحه
        if not self.game_over:
            current_name = reshape_persian(self.session.player1_name) if self.current_player == 1 else reshape_persian(self.session.player2_name)
            turn_text = f"Turn: {current_name} ({'Pink' if self.current_player == 1 else 'Green'})"
            color = self.COLOR_P1 if self.current_player == 1 else self.COLOR_P2
            txt_surf = self.font.render(turn_text, True, color)
            self.screen.blit(txt_surf, (self.SCREEN_WIDTH // 2 - txt_surf.get_width() // 2, 30))
            
        # نمایش تعداد باکس‌های تصاحب شده زنده هر بازیکن در زمین
        stats_text = f"{reshape_persian(self.session.player1_name)}: {self.p1_boxes_count} Box(es)  |  {reshape_persian(self.session.player2_name)}: {self.p2_boxes_count} Box(es)"
        stats_surf = self.font.render(stats_text, True, self.TEXT_COLOR)
        self.screen.blit(stats_surf, (self.SCREEN_WIDTH // 2 - stats_surf.get_width() // 2, 60))

        # ۲. رنگ‌آمیزی داخل باکس‌های تصاحب شده
        for (r, c), player_id in self.boxes.items():
            bx = self.start_x + c * self.cell_size + self.line_thickness // 2
            by = self.start_y + r * self.cell_size + self.line_thickness // 2
            box_rect = pygame.Rect(bx, by, self.cell_size - self.line_thickness, self.cell_size - self.line_thickness)
            
            color = (60, 15, 30) if player_id == 1 else (10, 50, 40)
            pygame.draw.rect(self.screen, color, box_rect)

        # ۳. رسم خطوط هاور (پیش‌نمایش قبل از کلیک)
        mx, my = pygame.mouse.get_pos()
        closest = self.get_closest_line(mx, my)
        if closest and closest not in self.lines and not self.game_over:
            l_type, r, c = closest
            lx = self.start_x + c * self.cell_size
            ly = self.start_y + r * self.cell_size
            if l_type == 'h':
                pygame.draw.line(self.screen, self.LINE_HOVER_COLOR, (lx, ly), (lx + self.cell_size, ly), self.line_thickness)
            else:
                pygame.draw.line(self.screen, self.LINE_HOVER_COLOR, (lx, ly), (lx, ly + self.cell_size), self.line_thickness)

        # ۴. رسم خطوط اصلی کشیده شده توسط بازیکنان
        for (l_type, r, c), player_id in self.lines.items():
            color = self.COLOR_P1 if player_id == 1 else self.COLOR_P2
            lx = self.start_x + c * self.cell_size
            ly = self.start_y + r * self.cell_size
            if l_type == 'h':
                pygame.draw.line(self.screen, color, (lx, ly), (lx + self.cell_size, ly), self.line_thickness)
            else:
                pygame.draw.line(self.screen, color, (lx, ly), (lx, ly + self.cell_size), self.line_thickness)

        # ۵. رسم نقطه‌های شبکه بازی
        for r in range(self.GRID_SIZE):
            for c in range(self.GRID_SIZE):
                nx = self.start_x + c * self.cell_size
                ny = self.start_y + r * self.cell_size
                pygame.draw.circle(self.screen, self.DOT_COLOR, (nx, ny), self.dot_radius)

        # ۶. صفحه نمایش پایان بازی و برنده راند
        if self.game_over:
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 210))
            self.screen.blit(overlay, (0, 0))
            
            if self.winner == "Draw":
                msg = "It's a Tie Game! 🤝"
                msg_color = (200, 200, 200)
            else:
                winner_name = reshape_persian(self.session.player1_name) if self.winner == 1 else reshape_persian(self.session.player2_name)
                msg = f"{winner_name} Wins Dots & Boxes! 🎉"
                msg_color = self.COLOR_P1 if self.winner == 1 else self.COLOR_P2
                
            win_surf = self.font_big.render(msg, True, msg_color)
            self.screen.blit(win_surf, (self.SCREEN_WIDTH // 2 - win_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 - 60))
            
            hint_surf = self.font.render("Click anywhere else to Restart", True, (150, 150, 150))
            self.screen.blit(hint_surf, (self.SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 40))
            
            # دکمه برگشت به منوی اصلی هاب
            back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 140, 160, 45)
            pygame.draw.rect(self.screen, (40, 40, 60), back_rect, border_radius=8)
            back_surf = self.font.render("Main Menu", True, (255, 255, 255))
            self.screen.blit(back_surf, (self.SCREEN_WIDTH // 2 - back_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 148))