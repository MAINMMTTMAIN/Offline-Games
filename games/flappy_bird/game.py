import pygame
import random
import math
import struct
import wave
import os

# To import base_game and persian_utils
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path


class FlappyBird(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.BG_COLOR = (15, 10, 35)
        self.PILLAR_COLOR = (255, 0, 150)
        
        self.P1_COLOR = (0, 255, 255)
        self.P2_COLOR = (255, 200, 0)
        
        self.font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
        self.font_mid = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 32)
        self.font_small = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        
        self.reset_game()
        
    def reset_game(self):
        self.gravity = 0.5
        self.jump_strength = -8
        
        # P1
        self.p1_x = self.width // 3
        self.p1_y = self.height // 2 - 50
        self.p1_vy = 0
        self.p1_alive = True
        self.p1_score = 0
        
        # P2 (or Bot)
        self.p2_x = self.width // 3 - 30
        self.p2_y = self.height // 2 + 50
        self.p2_vy = 0
        self.p2_alive = True
        self.p2_score = 0
            
        self.pillars = []
        self.pillar_width = 70
        self.pillar_gap = 210      # starts wide, decreases over time
        self.pillar_speed = 4.0
        self.spawn_interval = 90  # frames between pillars, decreases over time
        self.spawn_timer = 0
        
        self.state = "PLAY"
        self.winner = None
        
        self.spawn_pillar()

    def spawn_pillar(self):
        # Gap center oscillates (moving pillars effect)
        total_score = self.p1_score + self.p2_score
        # Current gap size (gets tighter every 5 points combined)
        current_gap = max(110, self.pillar_gap - total_score * 2)
        
        margin = 120
        gap_y = random.randint(margin, self.height - margin - current_gap)
        
        self.pillars.append({
            'x': self.width,
            'gap_center': gap_y + current_gap // 2,
            'gap_half': current_gap // 2,
            'top_h': gap_y,
            'bottom_y': gap_y + current_gap,
            'passed_p1': False,
            'passed_p2': False,
            # Oscillation: pillar gap moves up/down sinusoidally
            'osc_speed': random.uniform(0.01, 0.025),
            'osc_phase': random.uniform(0, math.pi * 2),
            'osc_amp': random.randint(15, 45)
        })

    def bot_play(self):
        difficulty = getattr(self.session, 'bot_difficulty', 'medium')
        
        next_pillar = None
        for p in self.pillars:
            if p['x'] + self.pillar_width > self.p2_x:
                next_pillar = p
                break
                
        if next_pillar:
            target_y = next_pillar['top_h'] + (next_pillar['bottom_y'] - next_pillar['top_h']) // 2
            
            if difficulty == 'easy':
                # Weak but not suicidal: ±45px error, jumps 35% of the time when needed
                target_y += random.uniform(-45, 45)
                if self.p2_y > target_y + 20 and random.random() < 0.35:
                    self.jump(2)
            elif difficulty == 'medium':
                target_y += random.uniform(-25, 25)
                if self.p2_y > target_y + 12 and self.p2_vy >= -1:
                    self.jump(2)
            else:
                # Hard: physics look-ahead
                # Cap look-ahead so gravity term doesn't explode
                dist = max(0, next_pillar['x'] - self.p2_x)
                frames = min(45, dist / max(1.0, self.pillar_speed))
                predicted_y = self.p2_y + self.p2_vy * frames + 0.5 * self.gravity * frames ** 2
                # Jump only if prediction says we'll be below centre AND we're not already flying up fast
                if predicted_y > target_y and self.p2_vy > -5:
                    self.jump(2)

    def jump(self, player):
        if player == 1 and self.p1_alive:
            self.p1_vy = self.jump_strength
        elif player == 2 and self.p2_alive:
            self.p2_vy = self.jump_strength

    def update_player(self, px, py, pvy, palive):
        if not palive: return py, pvy, False
        pvy += self.gravity
        py += pvy
        
        crashed = False
        ship_rect = pygame.Rect(px - 12, py - 10, 28, 20)
        
        if py > self.height or py < 0:
            crashed = True
            
        for p in self.pillars:
            top_rect = pygame.Rect(p['x'], 0, self.pillar_width, p['top_h'])
            bottom_rect = pygame.Rect(p['x'], p['bottom_y'], self.pillar_width, self.height - p['bottom_y'])
            if ship_rect.colliderect(top_rect) or ship_rect.colliderect(bottom_rect):
                crashed = True
                break
                
        return py, pvy, crashed

    def update(self):
        if self.state == "GAME_OVER":
            return
            
        is_bot = getattr(self.session, 'is_single_player', False)
        if is_bot and self.p2_alive:
            self.bot_play()
            
        # P1 Physics
        if self.p1_alive:
            self.p1_y, self.p1_vy, crashed1 = self.update_player(self.p1_x, self.p1_y, self.p1_vy, self.p1_alive)
            if crashed1: self.p1_alive = False
            
        # P2 Physics
        if self.p2_alive:
            self.p2_y, self.p2_vy, crashed2 = self.update_player(self.p2_x, self.p2_y, self.p2_vy, self.p2_alive)
            if crashed2: self.p2_alive = False
            
        # Update pillar positions and oscillation
        for p in self.pillars:
            p['x'] -= self.pillar_speed
            p['osc_phase'] += p['osc_speed']
            
            # Compute oscillated gap
            osc = math.sin(p['osc_phase']) * p['osc_amp']
            new_center = p['gap_center'] + osc
            new_center = max(p['gap_half'] + 80, min(self.height - p['gap_half'] - 80, new_center))
            p['top_h'] = int(new_center - p['gap_half'])
            p['bottom_y'] = int(new_center + p['gap_half'])
            
            # Score check
            if self.p1_alive and not p['passed_p1'] and p['x'] + self.pillar_width < self.p1_x:
                p['passed_p1'] = True
                self.p1_score += 1
                
            if self.p2_alive and not p['passed_p2'] and p['x'] + self.pillar_width < self.p2_x:
                p['passed_p2'] = True
                self.p2_score += 1
                
        # Progressive difficulty
        total_score = self.p1_score + self.p2_score
        # Speed increases slowly
        self.pillar_speed = min(10.0, 4.0 + total_score * 0.08)
        # Spawn interval decreases: more pillars over time
        self.spawn_interval = max(50, 90 - total_score * 1)
                
        self.pillars = [p for p in self.pillars if p['x'] + self.pillar_width > 0]
        
        # Spawn new pillars
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_pillar()
            
        # Check game over
        if not self.p1_alive and not self.p2_alive:
            self.state = "GAME_OVER"
            if self.p1_score > self.p2_score:
                self.winner = 1
                self.session.scores["player1"] += 1
            elif self.p2_score > self.p1_score:
                self.winner = 2
                self.session.scores["player2"] += 1
        elif not self.p1_alive:
            self.state = "GAME_OVER"
            self.winner = 2
            self.session.scores["player2"] += 1
        elif not self.p2_alive:
            self.state = "GAME_OVER"
            self.winner = 1
            self.session.scores["player1"] += 1

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE and self.p1_alive:
                    self.jump(1)
                if event.key == pygame.K_RETURN and self.p2_alive:
                    if not getattr(self.session, 'is_single_player', False):
                        self.jump(2)
                if event.key == pygame.K_r and self.state == "GAME_OVER":
                    self.reset_game()

    def draw_ship(self, x, y, vy, color):
        # Thruster flame when falling
        if vy < 0:
            pygame.draw.circle(self.screen, (255, 100, 0), (int(x - 14), int(y + 8)), random.randint(4, 7))
            
        # Body
        pygame.draw.circle(self.screen, color, (int(x), int(y)), 14)
        pygame.draw.circle(self.screen, (255, 255, 255), (int(x), int(y)), 14, 2)
        
        # Eye
        pygame.draw.circle(self.screen, (255, 255, 255), (int(x + 6), int(y - 4)), 5)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(x + 7), int(y - 4)), 2)
        
        # Beak
        beak = [(x + 12, y - 2), (x + 22, y + 2), (x + 12, y + 6)]
        pygame.draw.polygon(self.screen, (255, 200, 0), beak)
        pygame.draw.polygon(self.screen, (255, 255, 255), beak, 1)
        
        # Wing flapping
        wing_y = y + (4 if vy > 0 else -5)
        pygame.draw.ellipse(self.screen, (255, 255, 255), (x - 12, wing_y, 18, 9), 2)

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        # Draw pillars
        for p in self.pillars:
            # Top pillar
            pygame.draw.rect(self.screen, self.PILLAR_COLOR, (p['x'], 0, self.pillar_width, p['top_h']))
            pygame.draw.rect(self.screen, (255, 255, 255), (p['x'], 0, self.pillar_width, p['top_h']), 1)
            # Bottom pillar
            pygame.draw.rect(self.screen, self.PILLAR_COLOR, (p['x'], p['bottom_y'], self.pillar_width, self.height - p['bottom_y']))
            pygame.draw.rect(self.screen, (255, 255, 255), (p['x'], p['bottom_y'], self.pillar_width, self.height - p['bottom_y']), 1)
            # Gap highlight
            pygame.draw.line(self.screen, (255, 100, 200, 80), (p['x'] + self.pillar_width // 2, p['top_h']), (p['x'] + self.pillar_width // 2, p['bottom_y']), 2)
        
        # Draw players
        if self.p1_alive:
            self.draw_ship(self.p1_x, self.p1_y, self.p1_vy, self.P1_COLOR)
        if self.p2_alive:
            self.draw_ship(self.p2_x, self.p2_y, self.p2_vy, self.P2_COLOR)
            
        # Score / HUD
        p1_name = getattr(self.session, 'player1_name', 'P1')
        p2_name = "Bot" if getattr(self.session, 'is_single_player', False) else getattr(self.session, 'player2_name', 'P2')
        
        s1 = self.font_mid.render(f"{reshape_persian(p1_name)}: {self.p1_score}", True, self.P1_COLOR)
        s2 = self.font_mid.render(f"{reshape_persian(p2_name)}: {self.p2_score}", True, self.P2_COLOR)
        self.screen.blit(s1, (20, 10))
        self.screen.blit(s2, (self.width - s2.get_width() - 20, 10))
        
        # Speed indicator
        spd = self.font_small.render(f"Speed: {self.pillar_speed:.1f}x", True, (150, 150, 200))
        self.screen.blit(spd, (self.width // 2 - spd.get_width() // 2, 10))

        # Controls reminder at top
        ctrl_p1 = self.font_small.render("SPACE", True, self.P1_COLOR)
        ctrl_p2 = self.font_small.render("ENTER" if not getattr(self.session, 'is_single_player', False) else "BOT", True, self.P2_COLOR)
        self.screen.blit(ctrl_p1, (20, 40))
        self.screen.blit(ctrl_p2, (self.width - ctrl_p2.get_width() - 20, 40))
        
        if self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            
            if self.winner:
                wname = reshape_persian(p1_name if self.winner == 1 else p2_name)
                wcolor = self.P1_COLOR if self.winner == 1 else self.P2_COLOR
                w_surf = self.font_large.render(f"{wname} Wins!", True, wcolor)
            else:
                w_surf = self.font_large.render("Draw!", True, (255, 215, 0))
                
            self.screen.blit(w_surf, (self.width // 2 - w_surf.get_width() // 2, self.height // 2 - 60))
            r_surf = self.font_mid.render("Press R to Restart | ESC to Quit", True, (200, 200, 255))
            self.screen.blit(r_surf, (self.width // 2 - r_surf.get_width() // 2, self.height // 2 + 20))
