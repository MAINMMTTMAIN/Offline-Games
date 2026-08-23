import pygame
import random
import math
import sys
import os
import struct

# To import base_game and persian_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path


def _make_sound_from_samples(buf, sample_rate=44100):
    """Convert float samples list (-1..1) to a stereo pygame Sound."""
    try:
        import numpy as np
        packed = bytearray()
        for v in buf:
            vi = max(-32768, min(32767, int(v * 32767)))
            packed += struct.pack('<hh', vi, vi)
        arr = np.frombuffer(bytes(packed), dtype='<i2').reshape(-1, 2)
        return pygame.sndarray.make_sound(arr)
    except Exception:
        return None


def _make_hit_sound():
    """Sharp ping when ball hits paddle - like a solid table-tennis click."""
    sr, dur = 44100, 0.07
    n = int(sr * dur)
    buf = []
    for i in range(n):
        t = i / sr
        p = i / n
        # Short high click + quick decay
        freq = 900 - 300 * p
        env  = math.exp(-25 * p)
        val  = math.sin(2 * math.pi * freq * t) * 0.7 + random.uniform(-0.1, 0.1) * math.exp(-40 * p)
        buf.append(val * env * 0.5)
    return _make_sound_from_samples(buf)


def _make_score_sound():
    """Descending buzz: ball going past paddle / scoring."""
    sr, dur = 44100, 0.40
    n = int(sr * dur)
    buf = []
    for i in range(n):
        t = i / sr
        p = i / n
        env  = math.exp(-4 * p)
        freq = 180 * (1 - 0.75 * p)   # 180 Hz → 45 Hz
        # Mix sawtooth-like wave with noise for a buzzy crash feel
        saw  = 2 * (freq * t - math.floor(freq * t + 0.5))
        noise = random.uniform(-1, 1) * 0.3 * math.exp(-10 * p)
        buf.append((saw * 0.6 + noise) * env * 0.55)
    return _make_sound_from_samples(buf)


def _make_powerup_sound():
    """Ascending chime: picking up a power-up."""
    sr, dur = 44100, 0.20
    n = int(sr * dur)
    buf = []
    for i in range(n):
        t = i / sr
        p = i / n
        # Two harmonics ascending together
        f1 = 500 + 700 * p
        f2 = f1 * 1.5
        env  = math.sin(math.pi * p) * 0.8   # smooth bell envelope
        val  = (math.sin(2 * math.pi * f1 * t) * 0.6 +
                math.sin(2 * math.pi * f2 * t) * 0.4)
        buf.append(val * env * 0.5)
    return _make_sound_from_samples(buf)


class Paddle:
    def __init__(self, x, y, width, height, color):
        self.rect = pygame.Rect(x, y, width, height)
        self.base_height = height
        self.color = color
        self.speed = 7
        self.shield = False

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect, border_radius=5)
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
        # Rally timer: how many frames this ball has been alive (for speed scaling)
        self.rally_frames = 0

    def move(self):
        self.trail.append((self.x, self.y))
        if len(self.trail) > 10:
            self.trail.pop(0)
        self.x += self.speed_x
        self.y += self.speed_y
        self.rally_frames += 1

    def draw(self, screen):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = int(255 * (i / len(self.trail)))
            size  = max(1, int(self.radius * (i / len(self.trail))))
            s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (size, size), size)
            screen.blit(s, (tx - size, ty - size))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), int(self.radius * 0.5))


def draw_powerup_icon(screen, pu_type, color, cx, cy, size=14):
    if pu_type == 'expand':
        pygame.draw.line(screen, color, (cx, cy - size + 3), (cx, cy + size - 3), 2)
        pygame.draw.polygon(screen, color, [(cx, cy - size), (cx - 4, cy - size + 6), (cx + 4, cy - size + 6)])
        pygame.draw.polygon(screen, color, [(cx, cy + size), (cx - 4, cy + size - 6), (cx + 4, cy + size - 6)])
    elif pu_type == 'shrink':
        pygame.draw.line(screen, color, (cx, cy - size // 2), (cx, cy + size // 2), 2)
        pygame.draw.polygon(screen, color, [(cx, cy - size // 2 + 6), (cx - 4, cy - size // 2), (cx + 4, cy - size // 2)])
        pygame.draw.polygon(screen, color, [(cx, cy + size // 2 - 6), (cx - 4, cy + size // 2), (cx + 4, cy + size // 2)])
    elif pu_type == 'speed':
        pts = [(cx - 4, cy - size), (cx + 2, cy - 2), (cx - 2, cy - 2), (cx + 4, cy + size), (cx - 2, cy + 2), (cx + 2, cy + 2)]
        pygame.draw.polygon(screen, color, pts)
    elif pu_type == 'multi':
        pygame.draw.circle(screen, color, (cx - 6, cy), 5, 2)
        pygame.draw.circle(screen, color, (cx + 6, cy), 5, 2)
    elif pu_type == 'shield':
        pts = [(cx, cy - size), (cx + size - 2, cy - size // 2),
               (cx + size - 2, cy + size // 4), (cx, cy + size),
               (cx - size + 2, cy + size // 4), (cx - size + 2, cy - size // 2)]
        pygame.draw.polygon(screen, color, pts, 2)


class PowerUp:
    TYPES  = ['expand', 'shrink', 'speed', 'multi', 'shield']
    COLORS = {
        'expand': (0, 255, 255),
        'shrink': (255, 0, 100),
        'speed':  (255, 255, 0),
        'multi':  (255, 150, 0),
        'shield': (0, 255, 100)
    }

    def __init__(self, x, y, type):
        self.x      = float(x)
        self.y      = float(y)
        self.radius = 18
        self.type   = type
        self.color  = self.COLORS[type]
        self.timer  = 600
        self.vx     = random.choice([2.5, -2.5]) * random.uniform(0.8, 1.2)
        self.vy     = random.uniform(-1, 1)

    def update(self, height):
        self.x += self.vx
        self.y += self.vy
        if self.y < 20 or self.y > height - 20:
            self.vy *= -1

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius, 2)
        inner_r = int(self.radius * 0.55)
        s = pygame.Surface((inner_r * 2 + 2, inner_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, 80), (inner_r + 1, inner_r + 1), inner_r)
        screen.blit(s, (int(self.x) - inner_r - 1, int(self.y) - inner_r - 1))
        draw_powerup_icon(screen, self.type, self.color, int(self.x), int(self.y), size=10)


class Pong(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width  = screen.get_width()
        self.height = screen.get_height()
        
        self.BG_COLOR  = (10, 10, 25)
        self.ACCENT1   = (0, 255, 255)
        self.ACCENT2   = (255, 0, 255)
        self.BALL_COLOR = (255, 255, 200)
        
        self.font_large    = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
        self.font_mid      = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)
        self.font_small    = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        self.font_countdown = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 120)
        
        self._init_sounds()
        self.reset_game()

    # ── Sounds ──────────────────────────────────────────────────────────────
    def _init_sounds(self):
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.snd_hit     = _make_hit_sound()
            self.snd_score   = _make_score_sound()
            self.snd_powerup = _make_powerup_sound()
        except Exception:
            self.snd_hit = self.snd_score = self.snd_powerup = None

    # ── Reset ────────────────────────────────────────────────────────────────
    def reset_game(self):
        paddle_w, paddle_h = 15, 100
        self.p1 = Paddle(50, self.height // 2 - paddle_h // 2, paddle_w, paddle_h, self.ACCENT1)
        self.p2 = Paddle(self.width - 50 - paddle_w, self.height // 2 - paddle_h // 2, paddle_w, paddle_h, self.ACCENT2)
        
        self.balls    = [Ball(self.width // 2, self.height // 2, 8, self.BALL_COLOR)]
        self.powerups = []
        
        self.score1 = 0
        self.score2 = 0
        self.target_score = 5
        self.game_over = False
        self.winner    = None
        
        self.powerup_timer = 0
        # State: GUIDE → PLAY → COUNTDOWN → PLAY → … → GAME_OVER
        self.state = "GUIDE"
        
        # Countdown state
        self.countdown_val   = 3    # 3, 2, 1
        self.countdown_timer = 0    # frames elapsed in this digit
        self.COUNTDOWN_FRAMES = 60  # 1 second per digit at 60 fps
        
        self.keys = pygame.key.get_pressed()

    # ── Countdown helper ─────────────────────────────────────────────────────
    def _start_countdown(self):
        self.state           = "COUNTDOWN"
        self.countdown_val   = 3
        self.countdown_timer = 0

    # ── Powerup spawning / applying ──────────────────────────────────────────
    def spawn_powerup(self):
        x     = self.width // 2
        y     = random.randint(80, self.height - 80)
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
            new_ball = Ball(self.width // 2, self.height // 2, 8, self.BALL_COLOR)
            new_ball.speed_x = self.balls[0].speed_x * -1
            self.balls.append(new_ball)
        elif ptype == 'shield':
            catcher_p.shield = True
        if self.snd_powerup:
            self.snd_powerup.play()

    # ── Bot AI ───────────────────────────────────────────────────────────────
    def bot_move(self):
        difficulty = getattr(self.session, 'bot_difficulty', 'medium')

        # ── EASY BOT: completely separate logic ──────────────────────────────
        if difficulty == 'easy':
            speed = self.p2.speed * 0.4
            center = self.p2.rect.centery

            # Priority 1: ALWAYS chase the nearest powerup if any exist
            if self.powerups:
                nearest_pu = min(self.powerups, key=lambda pu: abs(pu.y - center))
                target_y = int(nearest_pu.y)
                if center < target_y - 10:
                    self.p2.rect.y += speed
                elif center > target_y + 10:
                    self.p2.rect.y -= speed
                return  # done — powerup takes full attention

            # Priority 2: find ball and move in the WRONG direction
            target_ball_e = None
            for b in self.balls:
                if b.speed_x > 0:
                    target_ball_e = b
                    break
            if target_ball_e:
                ball_y = target_ball_e.y
                # Move AWAY: if ball is in top half, paddle goes to bottom and vice versa
                wrong_target = self.height - ball_y
                if center < wrong_target - 15:
                    self.p2.rect.y += speed
                elif center > wrong_target + 15:
                    self.p2.rect.y -= speed
            return  # easy bot always returns early
        # ── END EASY BOT ─────────────────────────────────────────────────────

        # Find closest ball coming towards p2
        target_ball = None
        min_dist    = 9999
        for b in self.balls:
            if b.speed_x > 0:
                d = self.p2.rect.x - b.x
                if 0 < d < min_dist:
                    min_dist    = d
                    target_ball = b

        if target_ball:
            target_y = target_ball.y
            # Predict ball position at paddle using wall bounces
            if difficulty in ['medium', 'hard']:
                time_to_reach = min_dist / max(0.1, abs(target_ball.speed_x))
                target_y = target_ball.y + target_ball.speed_y * time_to_reach
                while target_y < 0 or target_y > self.height:
                    if target_y < 0:             target_y = -target_y
                    if target_y > self.height:   target_y = 2 * self.height - target_y

            if difficulty == 'medium':      # intermediate
                target_y += random.uniform(-15, 15)
                speed = self.p2.speed * 0.85
            else:                             # hard = strongest
                # Perfect prediction, full speed
                speed = self.p2.speed * 1.15

            center = self.p2.rect.centery
            if center < target_y - 10:
                self.p2.rect.y += speed
            elif center > target_y + 10:
                self.p2.rect.y -= speed

        else:
            # No ball coming: return toward center
            center_y = self.height // 2
            spd = self.p2.speed * 0.5
            if self.p2.rect.centery < center_y - 10:
                self.p2.rect.y += spd
            elif self.p2.rect.centery > center_y + 10:
                self.p2.rect.y -= spd

        # Hard bot ONLY: grab powerups when NO ball is coming toward p2 at all
        # (Ball is always priority #1 - items only when free)
        if difficulty == 'hard' and target_ball is None:
            for pu in self.powerups:
                if pu.vx > 0:
                    pu_dist = self.p2.rect.x - pu.x
                    if 0 < pu_dist < 400:
                        center = self.p2.rect.centery
                        target_pu_y = int(pu.y)
                        spd = self.p2.speed * 1.15
                        if center < target_pu_y - 10:
                            self.p2.rect.y += spd
                        elif center > target_pu_y + 10:
                            self.p2.rect.y -= spd
                        break

    # ── Update ───────────────────────────────────────────────────────────────
    def update(self):
        if self.state == "GUIDE":
            return

        if self.state == "GAME_OVER":
            return

        if self.state == "COUNTDOWN":
            self.countdown_timer += 1
            if self.countdown_timer >= self.COUNTDOWN_FRAMES:
                self.countdown_timer = 0
                self.countdown_val  -= 1
                if self.countdown_val <= 0:
                    # Spawn new ball and resume
                    self.balls.append(Ball(self.width // 2, self.height // 2, 8, self.BALL_COLOR))
                    self.state = "PLAY"
            return

        # ── PLAY state below ─────────────────────────────────────────────────
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

        for pu in self.powerups[:]:
            pu.timer -= 1
            pu.update(self.height)
            if pu.timer <= 0:
                self.powerups.remove(pu)
                continue
            pu_rect = pygame.Rect(int(pu.x) - pu.radius, int(pu.y) - pu.radius, pu.radius * 2, pu.radius * 2)
            if pu_rect.colliderect(self.p1.rect):
                self.apply_powerup(pu.type, self.p1)
                self.powerups.remove(pu)
            elif pu_rect.colliderect(self.p2.rect):
                self.apply_powerup(pu.type, self.p2)
                self.powerups.remove(pu)

        # Ball Logic
        scored = False
        balls_to_remove = []
        for b in self.balls:
            # ── Progressive speed scaling (every 15 frames, +0.5%) ──────────
            if b.rally_frames > 0 and b.rally_frames % 15 == 0:
                max_spd = 15
                factor  = 1.005
                b.speed_x = max(-max_spd, min(max_spd, b.speed_x * factor))
                b.speed_y = max(-max_spd, min(max_spd, b.speed_y * factor))

            b.move()

            # Wall bounce
            if b.y - b.radius <= 0 or b.y + b.radius >= self.height:
                b.speed_y *= -1
                b.y = max(b.radius, min(self.height - b.radius, b.y))

            # Paddle collision
            b_rect = pygame.Rect(b.x - b.radius, b.y - b.radius, b.radius * 2, b.radius * 2)
            hitter = None
            if b_rect.colliderect(self.p1.rect) and b.speed_x < 0:
                b.speed_x *= -1.1
                hitter = self.p1
            elif b_rect.colliderect(self.p2.rect) and b.speed_x > 0:
                b.speed_x *= -1.1
                hitter = self.p2

            if hitter:
                relative_intersect = (hitter.rect.centery - b.y) / (hitter.rect.height / 2)
                b.speed_y = relative_intersect * -b.base_speed
                max_spd = 15
                b.speed_x = max(-max_spd, min(max_spd, b.speed_x))
                b.speed_y = max(-max_spd, min(max_spd, b.speed_y))
                if self.snd_hit:
                    self.snd_hit.play()

            # Score check
            if b.x < 0:
                if self.p1.shield:
                    self.p1.shield = False
                    b.speed_x *= -1
                    b.x = 20
                else:
                    self.score2 += 1
                    balls_to_remove.append(b)
                    scored = True
                    if self.snd_score:
                        self.snd_score.play()
            elif b.x > self.width:
                if self.p2.shield:
                    self.p2.shield = False
                    b.speed_x *= -1
                    b.x = self.width - 20
                else:
                    self.score1 += 1
                    balls_to_remove.append(b)
                    scored = True
                    if self.snd_score:
                        self.snd_score.play()

        for b in balls_to_remove:
            if b in self.balls:
                self.balls.remove(b)

        if len(self.balls) == 0:
            # Restore paddles
            self.p1.rect.height = self.p1.base_height
            self.p2.rect.height = self.p2.base_height
            # Check win condition
            if self.score1 >= self.target_score:
                self.state  = "GAME_OVER"
                self.winner = 1
                self.session.scores["player1"] += 1
            elif self.score2 >= self.target_score:
                self.state  = "GAME_OVER"
                self.winner = 2
                self.session.scores["player2"] += 1
            else:
                # Start countdown before spawning next ball
                self._start_countdown()

    # ── Events ───────────────────────────────────────────────────────────────
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_r and self.state == "GAME_OVER":
                    self.reset_game()
                if self.state == "GUIDE":
                    self.state = "PLAY"

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw_guide(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("PONG", True, (255, 215, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 80))

        is_bot  = getattr(self.session, 'is_single_player', False)
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
            ("EXP icon  →  Expand your paddle",        PowerUp.COLORS['expand']),
            ("SHK icon  →  Shrink enemy paddle",       PowerUp.COLORS['shrink']),
            ("⚡ icon   →  Speed up ball",             PowerUp.COLORS['speed']),
            ("◎◎ icon   →  Multi-ball",               PowerUp.COLORS['multi']),
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

    def _draw_countdown(self):
        """Draw the semi-transparent countdown overlay."""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Fade: bright when digit just changed, fades over the second
        progress = self.countdown_timer / self.COUNTDOWN_FRAMES   # 0..1
        alpha = int(180 * (1 - progress * 0.5))
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

        # Digit scale: grows from 0.5 → 1.0 then shrinks 1.0 → 1.1
        scale = 0.5 + 0.5 * min(1.0, progress * 3)   # quick pop-in
        digit_color = [
            (255, 100, 100),   # 3 → red
            (255, 220, 0),     # 2 → yellow
            (100, 255, 100),   # 1 → green
        ][3 - self.countdown_val]

        # Glow ring
        cx, cy = self.width // 2, self.height // 2
        ring_r = int(90 * scale)
        glow_surf = pygame.Surface((ring_r * 2 + 20, ring_r * 2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*digit_color, 60), (ring_r + 10, ring_r + 10), ring_r + 10)
        pygame.draw.circle(glow_surf, (*digit_color, 120), (ring_r + 10, ring_r + 10), ring_r, 4)
        self.screen.blit(glow_surf, (cx - ring_r - 10, cy - ring_r - 10))

        digit_surf = self.font_countdown.render(str(self.countdown_val), True, digit_color)
        self.screen.blit(digit_surf, (cx - digit_surf.get_width() // 2, cy - digit_surf.get_height() // 2))

        # "Get ready!" label
        lbl = self.font_mid.render("Get ready!", True, (220, 220, 255))
        self.screen.blit(lbl, (cx - lbl.get_width() // 2, cy + 80))

    def draw(self):
        self.screen.fill(self.BG_COLOR)

        # Net
        for y in range(0, self.height, 40):
            pygame.draw.rect(self.screen, (40, 40, 60), (self.width // 2 - 2, y, 4, 20))

        # Scores
        p1_name = self.session.player1_name
        p2_name = self.session.player2_name if not getattr(self.session, 'is_single_player', False) else "Bot"

        s1_surf = self.font_large.render(str(self.score1), True, self.ACCENT1)
        s2_surf = self.font_large.render(str(self.score2), True, self.ACCENT2)
        self.screen.blit(s1_surf, (self.width // 4 - s1_surf.get_width() // 2, 50))
        self.screen.blit(s2_surf, (self.width * 3 // 4 - s2_surf.get_width() // 2, 50))

        n1_surf = self.font_small.render(reshape_persian(p1_name), True, self.ACCENT1)
        n2_surf = self.font_small.render(reshape_persian(p2_name), True, self.ACCENT2)
        self.screen.blit(n1_surf, (20, 20))
        self.screen.blit(n2_surf, (self.width - 20 - n2_surf.get_width(), 20))

        # Controls reminder
        c1 = self.font_small.render("W/S", True, (*self.ACCENT1, 180))
        c2 = self.font_small.render("↑/↓" if not getattr(self.session, 'is_single_player', False) else "BOT", True, (*self.ACCENT2, 180))
        self.screen.blit(c1, (20, self.height - 30))
        self.screen.blit(c2, (self.width - c2.get_width() - 20, self.height - 30))

        # Game objects
        for pu in self.powerups:
            pu.draw(self.screen)
        self.p1.draw(self.screen)
        self.p2.draw(self.screen)
        for b in self.balls:
            b.draw(self.screen)

        if self.state == "GUIDE":
            self._draw_guide()
            return

        if self.state == "COUNTDOWN":
            self._draw_countdown()
            return

        if self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            win_text = f"{reshape_persian(p1_name if self.winner == 1 else p2_name)} Wins!"
            w_surf = self.font_large.render(win_text, True, (255, 215, 0))
            self.screen.blit(w_surf, (self.width // 2 - w_surf.get_width() // 2, self.height // 2 - 60))
            r_surf = self.font_mid.render("Press R to Restart or ESC to Quit", True, (200, 200, 255))
            self.screen.blit(r_surf, (self.width // 2 - r_surf.get_width() // 2, self.height // 2 + 20))
