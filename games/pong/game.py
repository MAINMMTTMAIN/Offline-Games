import pygame
import random
import math
import sys
import os

# To import base_game and persian_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path


class Paddle:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.base_height = height
        self.color = color
        self.speed = 7
        self.shield = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
        # Glow effect
        glow = pygame.Surface((self.rect.width + 10, self.rect.height + 10), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*self.color, 60), glow.get_rect(), border_radius=8)
        screen.blit(glow, (self.rect.x - 5, self.rect.y - 5))
        
        if self.shield:
            pygame.draw.rect(screen, (0, 255, 100), (self.rect.x - 10, self.rect.y - 5, self.rect.width + 20, self.rect.height + 10), 2, border_radius=8)


class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.base_speed = 6
        self.speed_x = self.base_speed * random.choice((1, -1))
        self.speed_y = self.base_speed * random.choice((1, -1))
        self.trail = []

    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.speed_x
        self.y += self.speed_y

    def draw(self, screen):
        # Draw trail
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            size = max(1, int(self.radius * (i / len(self.trail))))
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
            screen.blit(s, (tx - size, ty - size))
            
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        # Core glow
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), int(self.radius*0.5))


def draw_powerup_icon(screen, pu_type, color, cx, cy, size=14):
    """Draw a geometric icon representing the powerup type."""
    if pu_type == 'expand':
        # Two arrows pointing outward (↑↓)
        pygame.draw.line(screen, color, (cx, cy - size + 3), (cx, cy + size - 3), 2)
        pygame.draw.polygon(screen, color, [(cx, cy - size), (cx - 4, cy - size + 6), (cx + 4, cy - size + 6)])
        pygame.draw.polygon(screen, color, [(cx, cy + size), (cx - 4, cy + size - 6), (cx + 4, cy + size - 6)])
    elif pu_type == 'shrink':
        # Two arrows pointing inward (↓↑)
        pygame.draw.line(screen, color, (cx, cy - size // 2), (cx, cy + size // 2), 2)
        pygame.draw.polygon(screen, color, [(cx, cy - size // 2 + 6), (cx - 4, cy - size // 2), (cx + 4, cy - size // 2)])
        pygame.draw.polygon(screen, color, [(cx, cy + size // 2 - 6), (cx - 4, cy + size // 2), (cx + 4, cy + size // 2)])
    elif pu_type == 'speed':
        # Lightning bolt
        pts = [(cx - 4, cy - size), (cx + 2, cy - 2), (cx - 2, cy - 2), (cx + 4, cy + size), (cx - 2, cy + 2), (cx + 2, cy + 2)]
        pygame.draw.polygon(screen, color, pts)
    elif pu_type == 'multi':
        # Two small circles (double ball)
        pygame.draw.circle(screen, color, (cx - 6, cy), 5, 2)
        pygame.draw.circle(screen, color, (cx + 6, cy), 5, 2)
    elif pu_type == 'shield':
        # Shield shape
        pts = [(cx, cy - size), (cx + size - 2, cy - size // 2),
               (cx + size - 2, cy + size // 4), (cx, cy + size), (cx - size + 2, cy + size // 4), (cx - size + 2, cy - size // 2)]
        pygame.draw.polygon(screen, color, pts, 2)


class PowerUp:
    TYPES = ['expand', 'shrink', 'speed', 'multi', 'shield']
    COLORS = {
        'expand': (0, 255, 255),    # Cyan
        'shrink': (255, 0, 100),    # Hot Pink
        'speed': (255, 255, 0),     # Yellow
        'multi': (255, 150, 0),     # Orange
        'shield': (0, 255, 100)     # Neon Green
    }

    def __init__(self, x, y, type):
        self.x = float(x)
        self.y = float(y)
        self.radius = 18
        self.type = type
        self.color = self.COLORS[type]
        self.timer = 600  # 10 seconds alive
        self.vx = random.choice([2.5, -2.5]) * random.uniform(0.8, 1.2)
        self.vy = random.uniform(-1, 1)

    def update(self, height):
        self.x += self.vx
        self.y += self.vy
        if self.y < 20 or self.y > height - 20:
            self.vy *= -1

    def draw(self, screen):
        # Outer ring
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, 2)
        # Pulsing inner fill
        inner_r = int(self.radius * 0.55)
        s = pygame.Surface((inner_r * 2 + 2, inner_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 80), (inner_r + 1, inner_r + 1), inner_r)
        screen.blit(s, (int(self.x) - inner_r - 1, int(self.y) - inner_r - 1))
        # Icon
        draw_powerup_icon(screen, self.type, self.color, int(self.x), int(self.y), size=10)


class Pong(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.BG_COLOR = (10, 10, 25)
        self.ACCENT1 = (0, 255, 255)
        self.ACCENT2 = (255, 0, 255)
        self.BALL_COLOR = (255, 255, 200)
        
        self.font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
        self.font_mid = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)
        self.font_small = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        
        self.reset_game()

    def reset_game(self):
        paddle_w, paddle_h = 15, 100
        self.p1 = Paddle(50, self.height//2 - paddle_h//2, paddle_w, paddle_h, self.ACCENT1)
        self.p2 = Paddle(self.width - 50 - paddle_w, self.height//2 - paddle_h//2, paddle_w, paddle_h, self.ACCENT2)
        
        self.balls = [Ball(self.width//2, self.height//2, 8, self.BALL_COLOR)]
        self.powerups = []
        
        self.score1 = 0
        self.score2 = 0
        self.target_score = 5
        self.game_over = False
        self.winner = None
        
        self.powerup_timer = 0
        # State: GUIDE -> PLAY -> GAME_OVER
        self.state = "GUIDE"
        
        self.keys = pygame.key.get_pressed()

    def spawn_powerup(self):
        x = self.width // 2  # Always spawns center
        y = random.randint(80, self.height - 80)
        ptype = random.choice(PowerUp.TYPES)
        self.powerups.append(PowerUp(x, y, ptype))

    def apply_powerup(self, ptype, catcher_p):
        other_p = self.p2 if catcher_p == self.p1 else self.p1
        if ptype == 'expand':
            catcher_p.rect.height = int(catcher_p.base_height * 1.5)
        elif ptype == 'shrink':
            other_p.rect.height = int(other_p.base_height * 0.5)
        elif ptype == 'speed':
            for b in self.balls:
                b.speed_x *= 1.5
                b.speed_y *= 1.5
        elif ptype == 'multi':
            new_ball = Ball(self.width//2, self.height//2, 8, self.BALL_COLOR)
            new_ball.speed_x = self.balls[0].speed_x * -1
            self.balls.append(new_ball)
        elif ptype == 'shield':
            catcher_p.shield = True

    def bot_move(self):
        difficulty = getattr(self.session, 'bot_difficulty', 'medium')
        
        # Find closest ball coming towards p2
        target_ball = None
        min_dist = 9999
        for b in self.balls:
            if b.speed_x > 0:
                d = self.p2.rect.x - b.x
                if 0 < d < min_dist:
                    min_dist = d
                    target_ball = b

        if target_ball:
            target_y = target_ball.y
            # Predict position at paddle
            if difficulty in ['medium', 'easy']:  # easy is now the strong bot
                time_to_reach = min_dist / max(0.1, abs(target_ball.speed_x))
                target_y = target_ball.y + target_ball.speed_y * time_to_reach
                while target_y < 0 or target_y > self.height:
                    if target_y < 0: target_y = -target_y
                    if target_y > self.height: target_y = 2*self.height - target_y

            if difficulty == 'easy':      # strongest
                speed = self.p2.speed * 1.15
            elif difficulty == 'medium':
                target_y += random.uniform(-15, 15)
                speed = self.p2.speed * 0.85
            else:                          # hard = weakest
                target_y += random.uniform(-80, 80)
                speed = self.p2.speed * 0.45

            center = self.p2.rect.centery
            if center < target_y - 10:
                self.p2.rect.y += speed
            elif center > target_y + 10:
                self.p2.rect.y -= speed

        else:
            # No ball coming: easy returns to center, hard stays put
            center_y = self.height // 2
            if difficulty == 'hard':
                pass
            else:
                if self.p2.rect.centery < center_y - 10:
                    self.p2.rect.y += self.p2.speed * 0.5
                elif self.p2.rect.centery > center_y + 10:
                    self.p2.rect.y -= self.p2.speed * 0.5

        # Easy bot ONLY: also try to collect powerups if ball is far
        if difficulty == 'easy' and min_dist > 250:
            for pu in self.powerups:
                if pu.vx > 0:
                    pu_dist = self.p2.rect.x - pu.x
                    if 0 < pu_dist < min_dist:
                        center = self.p2.rect.centery
                        target_pu_y = int(pu.y)
                        spd = self.p2.speed * 1.15
                        if center < target_pu_y - 10:
                            self.p2.rect.y += spd
                        elif center > target_pu_y + 10:
                            self.p2.rect.y -= spd
                        break

    def update(self):
        if self.state == "GUIDE":
            return  # Wait for keypress
            
        if self.state == "GAME_OVER":
            return
            
        self.keys = pygame.key.get_pressed()
        
        # Player 1 Move
        if self.keys[pygame.K_w] and self.p1.rect.top > 0:
            self.p1.rect.y -= self.p1.speed
        if self.keys[pygame.K_s] and self.p1.rect.bottom < self.height:
            self.p1.rect.y += self.p1.speed
            
        # Player 2 Move
        if getattr(self.session, 'is_single_player', False):
            self.bot_move()
        else:
            if self.keys[pygame.K_UP] and self.p2.rect.top > 0:
                self.p2.rect.y -= self.p2.speed
            if self.keys[pygame.K_DOWN] and self.p2.rect.bottom < self.height:
                self.p2.rect.y += self.p2.speed
                
        # Clamping
        self.p1.rect.y = max(0, min(self.height - self.p1.rect.height, self.p1.rect.y))
        self.p2.rect.y = max(0, min(self.height - self.p2.rect.height, self.p2.rect.y))

        # Powerups logic
        self.powerup_timer += 1
        if self.powerup_timer > 600:
            self.powerup_timer = 0
            if random.random() < 0.6:
                self.spawn_powerup()
                
        # Update and expire powerups
        for pu in self.powerups[:]:
            pu.timer -= 1
            pu.update(self.height)
            if pu.timer <= 0:
                self.powerups.remove(pu)
                continue
            # Paddle catches powerup (not ball)
            pu_rect = pygame.Rect(int(pu.x) - pu.radius, int(pu.y) - pu.radius, pu.radius * 2, pu.radius * 2)
            if pu_rect.colliderect(self.p1.rect):
                self.apply_powerup(pu.type, self.p1)
                self.powerups.remove(pu)
            elif pu_rect.colliderect(self.p2.rect):
                self.apply_powerup(pu.type, self.p2)
                self.powerups.remove(pu)

        # Ball Logic
        balls_to_remove = []
        for b in self.balls:
            b.move()
            
            # Wall bounce
            if b.y - b.radius <= 0 or b.y + b.radius >= self.height:
                b.speed_y *= -1
                b.y = max(b.radius, min(self.height - b.radius, b.y))
                
            # Paddle collision
            b_rect = pygame.Rect(b.x - b.radius, b.y - b.radius, b.radius*2, b.radius*2)
            
            hitter = None
            if b_rect.colliderect(self.p1.rect) and b.speed_x < 0:
                b.speed_x *= -1.1
                hitter = self.p1
            elif b_rect.colliderect(self.p2.rect) and b.speed_x > 0:
                b.speed_x *= -1.1
                hitter = self.p2
                
            if hitter:
                # English effect
                relative_intersect = (hitter.rect.centery - b.y) / (hitter.rect.height / 2)
                b.speed_y = relative_intersect * -b.base_speed
                # Limit speed
                max_spd = 15
                b.speed_x = max(-max_spd, min(max_spd, b.speed_x))
                b.speed_y = max(-max_spd, min(max_spd, b.speed_y))

            # Score check
            if b.x < 0:
                if self.p1.shield:
                    self.p1.shield = False
                    b.speed_x *= -1
                    b.x = 20
                else:
                    self.score2 += 1
                    balls_to_remove.append(b)
            elif b.x > self.width:
                if self.p2.shield:
                    self.p2.shield = False
                    b.speed_x *= -1
                    b.x = self.width - 20
                else:
                    self.score1 += 1
                    balls_to_remove.append(b)
                    
        for b in balls_to_remove:
            if b in self.balls:
                self.balls.remove(b)
                
        if len(self.balls) == 0:
            # Restore paddles
            self.p1.rect.height = self.p1.base_height
            self.p2.rect.height = self.p2.base_height
            # Check win
            if self.score1 >= self.target_score:
                self.state = "GAME_OVER"
                self.winner = 1
                self.session.scores["player1"] += 1
            elif self.score2 >= self.target_score:
                self.state = "GAME_OVER"
                self.winner = 2
                self.session.scores["player2"] += 1
            else:
                self.balls.append(Ball(self.width//2, self.height//2, 8, self.BALL_COLOR))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_r and self.state == "GAME_OVER":
                    self.reset_game()
                # Dismiss guide screen on any key
                if self.state == "GUIDE":
                    self.state = "PLAY"

    def _draw_guide(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))
        
        title = self.font_large.render("PONG", True, (255, 215, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))
        
        is_bot = getattr(self.session, 'is_single_player', False)
        p2_label = "Bot (AI)" if is_bot else reshape_persian(getattr(self.session, 'player2_name', 'P2'))
        p1_label = reshape_persian(getattr(self.session, 'player1_name', 'P1'))
        
        lines = [
            ("Controls", (255, 255, 255)),
            (f"{p1_label}  →  W / S", self.ACCENT1),
            (f"{p2_label}  →  Up and Down Arrow Keys" if not is_bot else f"{p2_label}  →  AI controlled", self.ACCENT2),
            ("", (255, 255, 255)),
            ("Power-ups", (255, 255, 255)),
        ]
        powerup_info = [
            ("EXP icon  →  Expand your paddle", PowerUp.COLORS['expand']),
            ("SHK icon  →  Shrink enemy paddle", PowerUp.COLORS['shrink']),
            ("⚡ icon   →  Speed up ball", PowerUp.COLORS['speed']),
            ("◎◎ icon   →  Multi-ball", PowerUp.COLORS['multi']),
            ("⛉ icon   →  Shield (ball bounces back)", PowerUp.COLORS['shield']),
        ]
        
        y = 190
        for text, color in lines:
            if text:
                surf = self.font_mid.render(text, True, color)
                self.screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))
            y += 45
            
        y += 5
        for text, color in powerup_info:
            surf = self.font_small.render(text, True, color)
            self.screen.blit(surf, (self.width // 2 - surf.get_width() // 2, y))
            y += 32
        
        prompt = self.font_mid.render("Press any key to start!", True, (255, 215, 0))
        self.screen.blit(prompt, (self.width // 2 - prompt.get_width() // 2, self.height - 80))

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        # Draw net
        for y in range(0, self.height, 40):
            pygame.draw.rect(self.screen, (40, 40, 60), (self.width//2 - 2, y, 4, 20))
            
        # Draw scores
        p1_name = self.session.player1_name
        p2_name = self.session.player2_name if not getattr(self.session, 'is_single_player', False) else "Bot"
        
        s1_surf = self.font_large.render(str(self.score1), True, self.ACCENT1)
        s2_surf = self.font_large.render(str(self.score2), True, self.ACCENT2)
        
        self.screen.blit(s1_surf, (self.width//4 - s1_surf.get_width()//2, 50))
        self.screen.blit(s2_surf, (self.width*3//4 - s2_surf.get_width()//2, 50))
        
        n1_surf = self.font_small.render(reshape_persian(p1_name), True, self.ACCENT1)
        n2_surf = self.font_small.render(reshape_persian(p2_name), True, self.ACCENT2)
        self.screen.blit(n1_surf, (20, 20))
        self.screen.blit(n2_surf, (self.width - 20 - n2_surf.get_width(), 20))

        # Controls reminder
        c1 = self.font_small.render("W/S", True, (*self.ACCENT1, 180))
        c2 = self.font_small.render("↑/↓" if not getattr(self.session, 'is_single_player', False) else "BOT", True, (*self.ACCENT2, 180))
        self.screen.blit(c1, (20, self.height - 30))
        self.screen.blit(c2, (self.width - c2.get_width() - 20, self.height - 30))

        # Game Objects
        for pu in self.powerups:
            pu.draw(self.screen)
            
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        
        for b in self.balls:
            b.draw(self.screen)
            
        if self.state == "GUIDE":
            self._draw_guide()
            return
            
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            win_text = f"{reshape_persian(p1_name if self.winner == 1 else p2_name)} Wins!"
            w_surf = self.font_large.render(win_text, True, (255, 215, 0))
            self.screen.blit(w_surf, (self.width//2 - w_surf.get_width()//2, self.height//2 - 60))
            
            r_surf = self.font_mid.render("Press R to Restart or ESC to Quit", True, (200, 200, 255))
            self.screen.blit(r_surf, (self.width//2 - r_surf.get_width()//2, self.height//2 + 20))
