import pygame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path
class BaseGame:
    def __init__(self, screen):
        self.screen = screen
        self.running = True
        # فونت عمومی برای بازی‌ها
        self.font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 24)

    def draw_persian_text(self, text, color, pos, font=None):
        """متد کمکی برای رندر متن فارسی در هر بازی"""
        f = font if font else self.font
        surf = render_persian_text(f, text, color)
        self.screen.blit(surf, pos)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        pass

    def draw(self):
        pass