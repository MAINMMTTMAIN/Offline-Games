import pygame
import random
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path,get_base_path

class MemoryCards(BaseGame):
    """Cyberpunk Memory Cards Game with Turn-Based Multi-player Logic and Dynamic PNG Images."""
    
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width  = screen.get_width()
        self.height = screen.get_height()

        # ── پالت رنگی سایبرپانک و نئونی ───────────────────────────────────
        self.C = {
            "bg":           (10, 10, 20),       
            "card_back":    (25, 30, 56),       
            "card_front":   (35, 40, 75),       
            "card_match":   (15, 15, 25),       
            "border_neon":  (0, 235, 255),      
            "p1":           (0, 235, 255),      
            "p2":           (255, 215, 0),      
            "grid_line":    (45, 52, 84),
            "panel_bg":     (16, 18, 32),
            "text":         (225, 230, 255),
            "text_dim":     (100, 110, 150),
            "wrong":        (255, 0, 100),      
            "correct":      (0, 255, 160)       
        }

        # فونت‌ها
        self.fL  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 46)
        self.fM  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 22)
        self.fS  = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        self.fXS = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 13)

        # دیکشنری نگاشت آیتم‌ها به نام فایل‌های تصویر مربوطه (۱۶ آیتم منحصر به فرد)
        self.item_files = {
            "Computer": "computer.png",
            "Soccer Ball": "soccer_ball.png",
            "Hair Dryer": "hair_dryer.png",
            "ChatGPT Log": "chatgpt.png",
            "Book": "book.png",
            "Socks": "socks.png",
            "Barbie": "barbie.png",
            "Broccoli": "broccoli.png",
            "Phone": "phone.png",
            "Cucumber": "cucumber.png",
            "Mouse (PC)": "pc_mouse.png",
            "Rat (Animal)": "rat.png",
            "Cat": "cat.png",
            "Pen": "pen.png",
            "House": "house.png",
            "Rick": "rick.png"
        }

        self._layout()
        self._load_item_images()
        self.reset_game()

    def _layout(self):
        """تنظیم ابعاد جدول کارت‌ها (تغییر به شبکه ۴ در ۸ برای نمایش دقیق ۳۲ کارت)"""
        W, H = self.width, self.height
        
        self.pnl_w = max(190, int(W * 0.18))
        self.pnl_x = W - self.pnl_w - 20
        self.pnl_y = int(H * 0.07)
        self.pnl_h = int(H * 0.86)

        self.bx = 20
        self.by = int(H * 0.07)
        self.bw = self.pnl_x - 40
        self.bh = int(H * 0.86)

        # تغییر سطر و ستون به ۴ در ۸ برای پوشش کامل ۳۲ کارت
        self.cols = 8
        self.rows = 4
        self.card_w = self.bw // self.cols - 10
        self.card_h = self.bh // self.rows - 10

    def _load_item_images(self):
        """لود کردن تصاویر PNG و تغییر اندازه خودکار متناسب با ابعاد جدید کارت‌ها"""
        self.item_images = {}
        for item_name, file_name in self.item_files.items():
            # مسیر کامل و درست فایل با استفاده از تابع get_base_path
            image_path = os.path.join(get_base_path(), "games", "memory_cards", file_name)
            
            # اصلاح شرط: چک کردن مسیر کامل، نه فقط نام فایل
            if os.path.exists(image_path):
                img = pygame.image.load(image_path).convert_alpha()
                scaled_img = pygame.transform.smoothscale(img, (self.card_w - 16, self.card_h - 16))
                self.item_images[item_name] = scaled_img
            else:
                # اگر فایل پیدا نشد، این بخش اجرا می‌شود (باکس پیش‌فرض)
                fallback = pygame.Surface((self.card_w - 16, self.card_h - 16), pygame.SRCALPHA)
                pygame.draw.rect(fallback, (200, 200, 255, 30), (0, 0, self.card_w - 16, self.card_h - 16), border_radius=4)
                txt = self.fXS.render(item_name[:10], True, (255, 255, 255))
                fallback.blit(txt, ((self.card_w - 16)//2 - txt.get_width()//2, (self.card_h - 16)//2 - txt.get_height()//2))
                self.item_images[item_name] = fallback

    def reset_game(self):
        """راه‌اندازی مجدد بازی با چیدمان فوق‌العاده رندوم و استفاده از تمام ۳۲ کارت"""
        self.cur_p = 1  
        self.p1_score = 0
        self.p2_score = 0
        self.state = "SHOW_ALL"  
        self.message = "Memorize the cards!"
        
        # ساخت ۳۲ کارت (۱۶ جفت کامل)
        cards_pool = list(self.item_files.keys()) + list(self.item_files.keys())
        
        # سیستم رندومایزر پیشرفته برای جلوگیری از تکرار حالت‌های قبلی
        random.seed(time.time_ns()) # مقداردهی اولیه هسته رندوم با نانو ثانیه زمان سیستم
        random.shuffle(cards_pool)   # مخلوط کردن مرحله اول
        random.shuffle(cards_pool)   # مخلوط کردن مرحله دوم برای تنوع حداکثری

        self.cards = []
        idx = 0
        for r in range(self.rows):
            for c in range(self.cols):
                cx = self.bx + c * (self.card_w + 10) + 5
                cy = self.by + r * (self.card_h + 10) + 5
                rect = pygame.Rect(cx, cy, self.card_w, self.card_h)
                
                self.cards.append({
                    "id": idx,
                    "name": cards_pool[idx],
                    "rect": rect,
                    "matched": False,   
                    "flipped": True     
                })
                idx += 1

        self.selected_cards = []  
        self.timer_start = pygame.time.get_ticks()
        self.show_duration = 6000  # ۴ ثانیه فرصت حفظ کردن کارت‌ها
        self.wrong_delay_timer = 0

    def handle_events(self, events):
        super().handle_events(events)
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                elif ev.key == pygame.K_SPACE and self.state == "GAME_OVER":
                    self.reset_game()

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.state != "PLAYING":
                    continue  

                for card in self.cards:
                    if card["rect"].collidepoint(ev.pos) and not card["matched"] and not card["flipped"]:
                        card["flipped"] = True
                        self.selected_cards.append(card)
                        
                        if len(self.selected_cards) == 2:
                            self.state = "WAIT_REVEAL"
                            self.wrong_delay_timer = pygame.time.get_ticks()
                            self._check_match()
                        break

    def _check_match(self):
        c1, c2 = self.selected_cards[0], self.selected_cards[1]
        
        if c1["name"] == c2["name"]:
            c1["matched"] = True
            c2["matched"] = True
            
            if self.cur_p == 1:
                self.p1_score += 1
                
                
            else:
                self.p2_score += 1
                
                
                
            self.message = "Match! Extra turn!"
            self.selected_cards = []
            self.state = "PLAYING"
            
            if all(card["matched"] for card in self.cards):
                if self.p1_score > self.p2_score:
                    self.session.scores["player1"] += 1
                elif self.p1_score < self.p2_score:
                    self.session.scores["player2"] += 1
                self.state = "GAME_OVER"
        else:
            self.message = "Wrong! Switching turn..."

    def update(self):
        now = pygame.time.get_ticks()

        if self.state == "SHOW_ALL":
            if now - self.timer_start > self.show_duration:
                for card in self.cards:
                    card["flipped"] = False
                self.state = "PLAYING"
                self.message = f"{reshape_persian(self.session.player1_name)}'s Turn"

        elif self.state == "WAIT_REVEAL":
            if now - self.wrong_delay_timer > 1200:  
                for card in self.selected_cards:
                    card["flipped"] = False
                self.selected_cards = []
                
                self.cur_p = 2 if self.cur_p == 1 else 1
                p_name = reshape_persian(self.session.player1_name) if self.cur_p == 1 else reshape_persian(self.session.player2_name)
                self.message = f"{p_name}'s Turn"
                self.state = "PLAYING"

    def draw(self):
        self.screen.fill(self.C["bg"])
        
        for card in self.cards:
            rect = card["rect"]
            
            if card["matched"]:
                pygame.draw.rect(self.screen, self.C["card_match"], rect, border_radius=6)
                pygame.draw.rect(self.screen, self.C["grid_line"], rect, 1, border_radius=6)
            elif card["flipped"]:
                border_color = self.C["border_neon"]
                if self.state == "WAIT_REVEAL" and card in self.selected_cards:
                    border_color = self.C["wrong"]
                
                pygame.draw.rect(self.screen, self.C["card_front"], rect, border_radius=6)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=6)
                
                img = self.item_images.get(card["name"])
                if img:
                    ix = rect.centerx - img.get_width() // 2
                    iy = rect.centery - img.get_height() // 2
                    self.screen.blit(img, (ix, iy))
            else:
                pygame.draw.rect(self.screen, self.C["card_back"], rect, border_radius=6)
                pygame.draw.rect(self.screen, self.C["grid_line"], rect, 1, border_radius=6)
                q_surf = self.fM.render("?", True, self.C["text_dim"])
                self.screen.blit(q_surf, (rect.centerx - q_surf.get_width()//2, rect.centery - q_surf.get_height()//2))

        self._draw_panel()

        if self.state == "GAME_OVER":
            self._draw_gameover()

    def _draw_panel(self):
        px, py, pw, ph = self.pnl_x, self.pnl_y, self.pnl_w, self.pnl_h
        active_color = self.C["p1"] if self.cur_p == 1 else self.C["p2"]

        pygame.draw.rect(self.screen, self.C["panel_bg"], (px, py, pw, ph), border_radius=12)
        pygame.draw.rect(self.screen, active_color if self.state != "GAME_OVER" else self.C["border_neon"], (px, py, pw, ph), 2, border_radius=12)

        cy = py + 20
        def blit_center(surf):
            nonlocal cy
            self.screen.blit(surf, (px + pw // 2 - surf.get_width() // 2, cy))
            cy += surf.get_height() + 10

        blit_center(self.fS.render("MATCH SCORE", True, self.C["text_dim"]))
        blit_center(render_persian_text(self.fM, f"{self.session.player1_name[:10]}: {self.p1_score}", self.C["p1"]))
        blit_center(render_persian_text(self.fM, f"{self.session.player2_name[:10]}: {self.p2_score}", self.C["p2"]))
        
        cy += 15
        pygame.draw.line(self.screen, self.C["grid_line"], (px + 15, cy), (px + pw - 15, cy), 1)
        cy += 20

        if self.state != "GAME_OVER":
            blit_center(self.fXS.render("ACTIVE PLAYER", True, self.C["text_dim"]))
            active_name = reshape_persian(self.session.player1_name) if self.cur_p == 1 else reshape_persian(self.session.player2_name)
            blit_center(render_persian_text(self.fM, reshape_persian(active_name[:12]), active_color))

        cy += 20
        if self.message:
            msg_color = self.C["correct"] if "Match" in self.message else (self.C["wrong"] if "Wrong" in self.message else self.C["text"])
            msg_surf = self.fXS.render(self.message, True, msg_color)
            blit_center(msg_surf)

        exit_surf = self.fXS.render("ESC: Menu", True, self.C["text_dim"])
        self.screen.blit(exit_surf, (px + pw//2 - exit_surf.get_width()//2, py + ph - 35))

    def _draw_gameover(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        if self.p1_score > self.p2_score:
            winner_text = f"{reshape_persian(self.session.player1_name)} Wins!"
            win_color = self.C["p1"]
        elif self.p2_score > self.p1_score:
            winner_text = f"{reshape_persian(self.session.player2_name)} Wins!"
            win_color = self.C["p2"]
        else:
            winner_text = "It's a Draw!"
            win_color = self.C["text"]

        cy = self.height // 2 - 80
        t1 = self.fL.render("GAME OVER", True, (255, 50, 50))
        t2 = self.fL.render(winner_text, True, win_color)
        t3 = self.fM.render("Press SPACE to Play Again", True, self.C["text_dim"])

        self.screen.blit(t1, (self.width // 2 - t1.get_width() // 2, cy)); cy += 70
        self.screen.blit(t2, (self.width // 2 - t2.get_width() // 2, cy)); cy += 75
        self.screen.blit(t3, (self.width // 2 - t3.get_width() // 2, cy))
    