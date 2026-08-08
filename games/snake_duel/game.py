import pygame
import random
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path

class SnakeDuel(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.block_size = 28
        
        # Calculate grid boundaries based on full screen to leave a margin
        self.margin = 50
        self.grid_width = (self.width - 2 * self.margin) // self.block_size
        self.grid_height = (self.height - 2 * self.margin) // self.block_size
        
        self.game_area_width = self.grid_width * self.block_size
        self.game_area_height = self.grid_height * self.block_size
        
        self.offset_x = (self.width - self.game_area_width) // 2
        self.offset_y = (self.height - self.game_area_height) // 2

        self.state = "START" # START, PLAYING, GAME_OVER
        self.font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
        self.font_small = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 28)
        
        self.winner_msg = ""
        
        # Colors
        self.color_bg = (15, 15, 26)
        self.color_wall = (40, 40, 60)
        self.color_p1 = (50, 255, 50) # Green (Player 1)
        self.color_p2 = (50, 150, 255) # Blue (Player 2)
        self.color_food = (255, 50, 50) # Red
        self.color_text = (240, 240, 255)
        
        # Audio
        self.eat_sound = None
        self.crash_sound = None
        try:
            import os
            pygame.mixer.init()
            base = os.path.dirname(os.path.abspath(__file__))
            eat_path = os.path.join(base, "sounds", "crunch.wav")
            crash_path = os.path.join(base, "sounds", "thud.wav")
            if os.path.exists(eat_path):
                self.eat_sound = pygame.mixer.Sound(eat_path)
            if os.path.exists(crash_path):
                self.crash_sound = pygame.mixer.Sound(crash_path)
        except Exception as e:
            print(f"Error loading sounds: {e}")

        self.reset_game()

    def reset_game(self):
        self.move_delay = 120 # milliseconds per step
        self.last_move_time = pygame.time.get_ticks()
        
        # Initial positions
        # P1 (Right side, moves left)
        start_x1 = self.grid_width - 6
        start_y1 = self.grid_height // 2
        self.snake1 = [(start_x1, start_y1), (start_x1+1, start_y1), (start_x1+2, start_y1)]
        self.dir1 = (-1, 0)
        self.next_dir1 = (-1, 0)
        
        # P2 (Left side, moves right)
        start_x2 = 5
        start_y2 = self.grid_height // 2
        self.snake2 = [(start_x2, start_y2), (start_x2-1, start_y2), (start_x2-2, start_y2)]
        self.dir2 = (1, 0)
        self.next_dir2 = (1, 0)
        
        self.food = self.spawn_food()

    def spawn_food(self):
        while True:
            fx = random.randint(0, self.grid_width - 1)
            fy = random.randint(0, self.grid_height - 1)
            if (fx, fy) not in self.snake1 and (fx, fy) not in self.snake2:
                return (fx, fy)

    def handle_events(self, events):
        super().handle_events(events)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if self.state == "START":
                    if event.key == pygame.K_SPACE:
                        self.state = "PLAYING"
                        self.last_move_time = pygame.time.get_ticks()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.state == "GAME_OVER":
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        # Allow restart
                        self.reset_game()
                        self.state = "PLAYING"
                elif self.state == "PAUSED":
                    if event.key == pygame.K_SPACE:
                        self.state = "PLAYING"
                        self.last_move_time = pygame.time.get_ticks()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif self.state == "PLAYING":
                    if event.key == pygame.K_SPACE:
                        self.state = "PAUSED"
                        
                    # P1 controls (Arrows)
                    if event.key == pygame.K_UP and self.dir1 != (0, 1):
                        self.next_dir1 = (0, -1)
                    elif event.key == pygame.K_DOWN and self.dir1 != (0, -1):
                        self.next_dir1 = (0, 1)
                    elif event.key == pygame.K_LEFT and self.dir1 != (1, 0):
                        self.next_dir1 = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.dir1 != (-1, 0):
                        self.next_dir1 = (1, 0)
                        
                    # P2 controls (WASD)
                    if event.key == pygame.K_w and self.dir2 != (0, 1):
                        self.next_dir2 = (0, -1)
                    elif event.key == pygame.K_s and self.dir2 != (0, -1):
                        self.next_dir2 = (0, 1)
                    elif event.key == pygame.K_a and self.dir2 != (1, 0):
                        self.next_dir2 = (-1, 0)
                    elif event.key == pygame.K_d and self.dir2 != (-1, 0):
                        self.next_dir2 = (1, 0)

    def get_snake_bot_move(self):
        diff = getattr(self.session, 'bot_difficulty', 'medium')
        head = self.snake2[0]
        food = self.food
        
        possible_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        # Filter reverse direction
        possible_dirs = [d for d in possible_dirs if d != (-self.dir2[0], -self.dir2[1])]
        
        import random
        
        def is_safe(x, y):
            if x < 0 or x >= self.grid_width or y < 0 or y >= self.grid_height: return False
            if (x, y) in self.snake1: return False
            if (x, y) in self.snake2[:-1]: return False
            return True
            
        safe_dirs = []
        for d in possible_dirs:
            if is_safe(head[0] + d[0], head[1] + d[1]):
                safe_dirs.append(d)
                
        if diff == "low":
            # Just go towards food, maybe randomly die
            dx = food[0] - head[0]
            dy = food[1] - head[1]
            best_dir = None
            if abs(dx) > abs(dy):
                best_dir = (1 if dx > 0 else -1, 0)
            else:
                best_dir = (0, 1 if dy > 0 else -1)
            
            if best_dir in possible_dirs:
                if random.random() > 0.1: # 90% chance to go towards food
                    return best_dir
            return possible_dirs[0] if possible_dirs else self.dir2
            
        elif diff == "medium":
            if not safe_dirs:
                return possible_dirs[0] if possible_dirs else self.dir2
            
            # Go towards food but only if safe
            best_dir = safe_dirs[0]
            min_dist = float('inf')
            for d in safe_dirs:
                nx, ny = head[0] + d[0], head[1] + d[1]
                dist = abs(nx - food[0]) + abs(ny - food[1])
                if dist < min_dist:
                    min_dist = dist
                    best_dir = d
            return best_dir
            
        else: # hard
            if not safe_dirs:
                return possible_dirs[0] if possible_dirs else self.dir2
                
            # BFS to find food
            from collections import deque
            queue = deque([(head, [])])
            visited = set([head])
            
            path_found = None
            
            while queue:
                curr, path = queue.popleft()
                if curr == food:
                    path_found = path
                    break
                    
                for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    nx, ny = curr[0] + d[0], curr[1] + d[1]
                    if is_safe(nx, ny) and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append(((nx, ny), path + [d]))
                        
            if path_found and path_found[0] in safe_dirs:
                return path_found[0]
            else:
                # Survival mode
                best_dir = safe_dirs[0]
                max_space = -1
                for d in safe_dirs:
                    space = self.flood_fill(head[0] + d[0], head[1] + d[1])
                    if space > max_space:
                        max_space = space
                        best_dir = d
                return best_dir

    def flood_fill(self, sx, sy):
        from collections import deque
        queue = deque([(sx, sy)])
        visited = set([(sx, sy)])
        space = 0
        while queue and space < 100:
            curr = queue.popleft()
            space += 1
            for d in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = curr[0] + d[0], curr[1] + d[1]
                if nx >= 0 and nx < self.grid_width and ny >= 0 and ny < self.grid_height:
                    if (nx, ny) not in visited and (nx, ny) not in self.snake1 and (nx, ny) not in self.snake2[:-1]:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        return space

    def update(self):
        if self.state != "PLAYING":
            return
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time > self.move_delay:
            self.last_move_time = current_time
            
            if getattr(self.session, 'is_single_player', False):
                self.next_dir2 = self.get_snake_bot_move()
            
            self.dir1 = self.next_dir1
            self.dir2 = self.next_dir2
            
            # Calculate new heads
            head1 = (self.snake1[0][0] + self.dir1[0], self.snake1[0][1] + self.dir1[1])
            head2 = (self.snake2[0][0] + self.dir2[0], self.snake2[0][1] + self.dir2[1])
            
            p1_dead = False
            p2_dead = False

            # Check Wall Collisions
            if head1[0] < 0 or head1[0] >= self.grid_width or head1[1] < 0 or head1[1] >= self.grid_height:
                p1_dead = True
            if head2[0] < 0 or head2[0] >= self.grid_width or head2[1] < 0 or head2[1] >= self.grid_height:
                p2_dead = True

            # Check Head to Head Collision
            if head1 == head2:
                p1_dead = True
                p2_dead = True

            # Check Self Collisions
            if head1 in self.snake1[:-1]:
                p1_dead = True
            if head2 in self.snake2[:-1]:
                p2_dead = True

            # Check Cross Collisions
            if head1 in self.snake2:
                p1_dead = True
            if head2 in self.snake1:
                p2_dead = True
                
            if p1_dead and p2_dead:
                if self.crash_sound: self.crash_sound.play()
                self.game_over("Draw!")
                return
            elif p1_dead:
                if self.crash_sound: self.crash_sound.play()
                self.session.scores["player2"] += 1
                self.game_over(f"{reshape_persian(self.session.player2_name)} Wins!")
                return
            elif p2_dead:
                if self.crash_sound: self.crash_sound.play()
                self.session.scores["player1"] += 1
                self.game_over(f"{reshape_persian(self.session.player1_name)} Wins!")
                return
                
            # Move snakes
            self.snake1.insert(0, head1)
            self.snake2.insert(0, head2)
            
            # Check food
            ate1 = (head1 == self.food)
            ate2 = (head2 == self.food)
            
            if ate1 or ate2:
                if self.eat_sound: self.eat_sound.play()
                self.food = self.spawn_food()
                # Speed up slightly
                self.move_delay = max(40, int(self.move_delay * 0.98))
            
            if not ate1:
                self.snake1.pop()
            if not ate2:
                self.snake2.pop()

    def game_over(self, msg):
        self.state = "GAME_OVER"
        self.winner_msg = msg

    def get_rect(self, x, y):
        return pygame.Rect(
            self.offset_x + x * self.block_size,
            self.offset_y + y * self.block_size,
            self.block_size,
            self.block_size
        )

    def draw(self):
        self.screen.fill(self.color_bg)
        
        # Draw Walls (border)
        border_rect = pygame.Rect(
            self.offset_x - 5,
            self.offset_y - 5,
            self.game_area_width + 10,
            self.game_area_height + 10
        )
        pygame.draw.rect(self.screen, self.color_wall, border_rect, width=5)
        
        # Draw Food (Realistic Apple)
        food_rect = self.get_rect(self.food[0], self.food[1])
        center = food_rect.center
        radius = self.block_size // 2 - 2
        # Apple body
        pygame.draw.circle(self.screen, self.color_food, center, radius)
        # Highlight
        pygame.draw.circle(self.screen, (255, 100, 100), (center[0] - radius//3, center[1] - radius//3), radius//3)
        # Stem
        pygame.draw.rect(self.screen, (101, 67, 33), (center[0] - 1, center[1] - radius - 3, 3, 5))
        # Leaf
        pygame.draw.ellipse(self.screen, (34, 139, 34), (center[0] + 1, center[1] - radius - 4, 6, 4))
        
        import math
        def draw_snake(snake, base_color, head_color, direction):
            # --- PASS 1: Draw body (skip index 0 = head) ---
            for i, segment in enumerate(snake):
                if i == 0:
                    continue
                seg_rect = self.get_rect(segment[0], segment[1])
                seg_center = seg_rect.center
                seg_radius = self.block_size // 2 - 1
                
                scale = max(0.5, 1.0 - (i / max(10, len(snake))))
                current_radius = int(seg_radius * scale)
                pygame.draw.circle(self.screen, base_color, seg_center, current_radius)
                
                prev_seg = snake[i-1]
                if abs(prev_seg[0] - segment[0]) + abs(prev_seg[1] - segment[1]) == 1:
                    prev_rect = self.get_rect(prev_seg[0], prev_seg[1])
                    prev_center = prev_rect.center
                    pygame.draw.line(self.screen, base_color, prev_center, seg_center, current_radius * 2)
                    
            # --- PASS 2: Draw head on top ---
            if not snake:
                return
            segment = snake[0]
            seg_rect = self.get_rect(segment[0], segment[1])
            seg_center = seg_rect.center
            seg_radius = self.block_size // 2 - 1

            dist_to_food = abs(segment[0] - self.food[0]) + abs(segment[1] - self.food[1])
            is_open = dist_to_food <= 3
            
            angle = 0
            if direction == (1, 0): angle = 0
            elif direction == (0, -1): angle = 90
            elif direction == (-1, 0): angle = 180
            elif direction == (0, 1): angle = 270
            
            surf_size = seg_radius * 6
            head_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center_h = (surf_size//2, surf_size//2)
            
            # Draw head base (ellipse)
            head_rect = pygame.Rect(center_h[0]-seg_radius*1.2, center_h[1]-seg_radius*1.2, seg_radius*2.4, seg_radius*2.4)
            pygame.draw.ellipse(head_surf, head_color, head_rect)
            
            if is_open:
                # Open mouth (human-like)
                mouth_rect = pygame.Rect(center_h[0], center_h[1]-seg_radius*0.6, seg_radius, seg_radius*1.2)
                pygame.draw.ellipse(head_surf, (50,0,0), mouth_rect)
                pygame.draw.ellipse(head_surf, (255,100,100), mouth_rect, 2)
                # Upper Teeth
                pygame.draw.rect(head_surf, (255,255,255), (int(center_h[0]+seg_radius*0.4), int(center_h[1]-seg_radius*0.5), int(seg_radius*0.4), int(seg_radius*0.3)))
                # Lower Teeth
                pygame.draw.rect(head_surf, (255,255,255), (int(center_h[0]+seg_radius*0.4), int(center_h[1]+seg_radius*0.2), int(seg_radius*0.4), int(seg_radius*0.3)))
            else:
                # Closed mouth
                mouth_rect = pygame.Rect(int(center_h[0]+seg_radius*0.5), int(center_h[1]-seg_radius*0.4), 4, int(seg_radius*0.8))
                pygame.draw.ellipse(head_surf, (255,100,100), mouth_rect)
                # Tongue
                t_x = int(center_h[0] + seg_radius*0.8)
                t_y = int(center_h[1])
                pygame.draw.line(head_surf, (255,50,50), (t_x, t_y), (t_x+10, t_y), 2)
                pygame.draw.line(head_surf, (255,50,50), (t_x+10, t_y), (t_x+14, t_y-4), 2)
                pygame.draw.line(head_surf, (255,50,50), (t_x+10, t_y), (t_x+14, t_y+4), 2)
                
            # BIG Eyes (drawn last so always on top)
            eye1 = (int(center_h[0]-seg_radius*0.2), int(center_h[1]-seg_radius*0.55))
            eye2 = (int(center_h[0]-seg_radius*0.2), int(center_h[1]+seg_radius*0.55))
            # pygame.draw.circle(head_surf, (255,255,255), eye1, 5)
            # pygame.draw.circle(head_surf, (255,255,255), eye2, 5)
            pygame.draw.circle(head_surf, (30,30,30), (eye1[0]+2, eye1[1]), 3)
            pygame.draw.circle(head_surf, (30,30,30), (eye2[0]+2, eye2[1]), 3)
            # Eye shine
            pygame.draw.circle(head_surf, (255,255,255), (eye1[0]+3, eye1[1]-2), 2)
            pygame.draw.circle(head_surf, (255,255,255), (eye2[0]+3, eye2[1]-2), 2)
            
            rotated_head = pygame.transform.rotate(head_surf, angle)
            self.screen.blit(rotated_head, (seg_center[0] - rotated_head.get_width()//2, seg_center[1] - rotated_head.get_height()//2))

        # Draw Snake 1 (Green)
        draw_snake(self.snake1, (30, 200, 30), self.color_p1, self.dir1)
            
        # Draw Snake 2 (Blue)
        draw_snake(self.snake2, (30, 120, 200), self.color_p2, self.dir2)
            
        # UI Overlay
        if self.state == "START":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            title_surf = self.font_large.render("SNAKE DUEL", True, (0, 240, 255))
            inst_surf = self.font_small.render("Press SPACE to Start", True, self.color_text)
            
            p1_inst = self.font_small.render(f"{reshape_persian(self.session.player1_name)}: Use Arrow keys", True, self.color_p1)
            p2_inst = self.font_small.render(f"{reshape_persian(self.session.player2_name)}: Use WASD", True, self.color_p2)
            
            self.screen.blit(title_surf, (self.width//2 - title_surf.get_width()//2, self.height//2 - 100))
            self.screen.blit(inst_surf, (self.width//2 - inst_surf.get_width()//2, self.height//2 + 20))
            self.screen.blit(p2_inst, (self.width//4 - p2_inst.get_width()//2, self.height//2 + 80))
            self.screen.blit(p1_inst, (3*self.width//4 - p1_inst.get_width()//2, self.height//2 + 80))
            
        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            over_surf = self.font_large.render("GAME OVER", True, (255, 50, 50))
            winner_surf = self.font_small.render(self.winner_msg, True, (255, 215, 0))
            inst_surf = self.font_small.render("Press SPACE to Play Again | ESC to Main Menu", True, self.color_text)
            
            self.screen.blit(over_surf, (self.width//2 - over_surf.get_width()//2, self.height//2 - 100))
            self.screen.blit(winner_surf, (self.width//2 - winner_surf.get_width()//2, self.height//2 - 20))
            self.screen.blit(inst_surf, (self.width//2 - inst_surf.get_width()//2, self.height//2 + 50))
            
        elif self.state == "PAUSED":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            paused_surf = self.font_large.render("PAUSED", True, (255, 255, 0))
            inst_surf = self.font_small.render("Press SPACE to Resume", True, self.color_text)
            
            self.screen.blit(paused_surf, (self.width//2 - paused_surf.get_width()//2, self.height//2 - 50))
            self.screen.blit(inst_surf, (self.width//2 - inst_surf.get_width()//2, self.height//2 + 30))

