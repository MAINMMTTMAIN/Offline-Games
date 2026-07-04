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
        
        self.block_size = 25
        
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

    def update(self):
        if self.state != "PLAYING":
            return
            
        current_time = pygame.time.get_ticks()
        if current_time - self.last_move_time > self.move_delay:
            self.last_move_time = current_time
            
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
                self.game_over("Draw!")
                return
            elif p1_dead:
                self.session.scores["player2"] += 1
                self.game_over(f"{reshape_persian(self.session.player2_name)} Wins!")
                return
            elif p2_dead:
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
        
        # Draw Food
        pygame.draw.rect(self.screen, self.color_food, self.get_rect(self.food[0], self.food[1]).inflate(-2, -2), border_radius=4)
        
        # Draw Snake 1 (Green)
        for i, segment in enumerate(self.snake1):
            color = self.color_p1 if i == 0 else (30, 200, 30)
            pygame.draw.rect(self.screen, color, self.get_rect(segment[0], segment[1]).inflate(-1, -1), border_radius=2)
            
        # Draw Snake 2 (Blue)
        for i, segment in enumerate(self.snake2):
            color = self.color_p2 if i == 0 else (30, 120, 200)
            pygame.draw.rect(self.screen, color, self.get_rect(segment[0], segment[1]).inflate(-1, -1), border_radius=2)
            
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

