import os
import sys
import pygame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from base_game import BaseGame

class TicTacToe(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session
        pygame.display.set_caption("Tic Tac Toe - Arcade Mode")
        
        self.SCREEN_WIDTH = screen.get_width()
        self.SCREEN_HEIGHT = screen.get_height()
        
        self.BG_COLOR = (10, 10, 18)
        self.GRID_COLOR = (45, 45, 70)
        self.COLOR_X = (255, 40, 100)    
        self.COLOR_O = (0, 245, 180)     
        self.TEXT_COLOR = (220, 220, 240)
        
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.current_player = 1  
        self.winner = None       
        self.game_over = False
        self.score_added = False 
        self.bot_timer = 0
        
        self.font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        self.font_big = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 44)
        
        self.cell_size = 120
        self.grid_width = 3
        self.start_x = (self.SCREEN_WIDTH - (3 * self.cell_size)) // 2
        self.start_y = (self.SCREEN_HEIGHT - (3 * self.cell_size)) // 2

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.running = False
                
            # 🔴 قابلیت خروج و ریستارت وسط بازی دوز
            if event.type == pygame.KEYDOWN: 
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r:
                    self.reset_game()
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over:
                    mouse_pos = event.pos
                    back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 140, 160, 45)
                    
                    if back_rect.collidepoint(mouse_pos):
                        self.running = False  
                    else:
                        self.reset_game()     
                    continue

                mx, my = event.pos
                
                # Block input if single player and it's bot's turn
                if getattr(self.session, 'is_single_player', False) and self.current_player == 2:
                    continue

                if (self.start_x <= mx <= self.start_x + 3 * self.cell_size and 
                    self.start_y <= my <= self.start_y + 3 * self.cell_size):
                    
                    col = (mx - self.start_x) // self.cell_size
                    row = (my - self.start_y) // self.cell_size
                    
                    if self.board[row][col] == 0:
                        self.board[row][col] = self.current_player
                        self.check_winner()
                        if not self.game_over:
                            self.current_player = 3 - self.current_player

    def check_winner(self):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != 0:
                self.winner = self.board[i][0]
                self.game_over = True
                break
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != 0:
                self.winner = self.board[0][i]
                self.game_over = True
                break
                
        if not self.game_over:
            if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
                self.winner = self.board[0][0]
                self.game_over = True
            elif self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
                self.winner = self.board[0][2]
                self.game_over = True
            
        if not self.game_over and all(self.board[r][c] != 0 for r in range(3) for c in range(3)):
            self.winner = "Draw"
            self.game_over = True

        if self.game_over and not self.score_added:
            if self.winner == 1:
                self.session.scores["player1"] += 1
            elif self.winner == 2:
                self.session.scores["player2"] += 1
            self.score_added = True

    def reset_game(self):
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.current_player = 1
        self.winner = None
        self.game_over = False
        self.score_added = False

    def update(self):
        if self.game_over:
            return
            
        if getattr(self.session, 'is_single_player', False) and self.current_player == 2:
            if self.bot_timer == 0:
                self.bot_timer = pygame.time.get_ticks()
            
            if pygame.time.get_ticks() - self.bot_timer > 600: # 600ms delay
                self.make_bot_move()
                self.bot_timer = 0

    def make_bot_move(self):
        empty_cells = [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == 0]
        if not empty_cells:
            return
            
        diff = getattr(self.session, 'bot_difficulty', 'medium')
        move = None
        
        import random
        if diff == "low":
            move = random.choice(empty_cells)
        elif diff == "medium":
            # Check for win or block
            move = self.get_winning_move(2) or self.get_winning_move(1)
            if not move:
                move = random.choice(empty_cells)
        else: # hard - minimax
            move = self.get_best_move_minimax()
            
        if move:
            r, c = move
            self.board[r][c] = 2
            self.check_winner()
            if not self.game_over:
                self.current_player = 1

    def get_winning_move(self, player):
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0:
                    self.board[r][c] = player
                    is_win = self.check_win_condition(player)
                    self.board[r][c] = 0
                    if is_win:
                        return (r, c)
        return None

    def check_win_condition(self, player):
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] == player: return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] == player: return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] == player: return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] == player: return True
        return False
        
    def get_best_move_minimax(self):
        best_score = -float('inf')
        best_move = None
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0:
                    self.board[r][c] = 2
                    score = self.minimax(False)
                    self.board[r][c] = 0
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
        if not best_move:
            empty_cells = [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == 0]
            if empty_cells:
                best_move = empty_cells[0]
        return best_move

    def minimax(self, is_maximizing):
        if self.check_win_condition(2): return 1
        if self.check_win_condition(1): return -1
        
        empty_cells = [(r, c) for r in range(3) for c in range(3) if self.board[r][c] == 0]
        if not empty_cells: return 0
        
        if is_maximizing:
            best_score = -float('inf')
            for r, c in empty_cells:
                self.board[r][c] = 2
                score = self.minimax(False)
                self.board[r][c] = 0
                best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for r, c in empty_cells:
                self.board[r][c] = 1
                score = self.minimax(True)
                self.board[r][c] = 0
                best_score = min(score, best_score)
            return best_score

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        
        hint_top = self.font.render("Press 'ESC' to Exit  |  Press 'R' to Restart Game", True, (100, 100, 120))
        self.screen.blit(hint_top, (20, 20))
        
        if not self.game_over:
            current_name = reshape_persian(self.session.player1_name) if self.current_player == 1 else reshape_persian(self.session.player2_name)
            turn_text = f"Turn: {current_name} ({'X' if self.current_player == 1 else 'O'})"
            color = self.COLOR_X if self.current_player == 1 else self.COLOR_O
            txt_surf = self.font.render(turn_text, True, color)
            self.screen.blit(txt_surf, (self.SCREEN_WIDTH // 2 - txt_surf.get_width() // 2, 30))
        
        for i in range(1, 3):
            pygame.draw.line(self.screen, self.GRID_COLOR, 
                             (self.start_x + i * self.cell_size, self.start_y), 
                             (self.start_x + i * self.cell_size, self.start_y + 3 * self.cell_size), self.grid_width)
            pygame.draw.line(self.screen, self.GRID_COLOR, 
                             (self.start_x, self.start_y + i * self.cell_size), 
                             (self.start_x + 3 * self.cell_size, self.start_y + i * self.cell_size), self.grid_width)
                             
        for row in range(3):
            for col in range(3):
                cx = self.start_x + col * self.cell_size + self.cell_size // 2
                cy = self.start_y + row * self.cell_size + self.cell_size // 2
                offset = 30
                
                if self.board[row][col] == 1:  
                    pygame.draw.line(self.screen, self.COLOR_X, (cx - offset, cy - offset), (cx + offset, cy + offset), 8)
                    pygame.draw.line(self.screen, self.COLOR_X, (cx + offset, cy - offset), (cx - offset, cy + offset), 8)
                elif self.board[row][col] == 2: 
                    pygame.draw.circle(self.screen, self.COLOR_O, (cx, cy), offset, 7)

        if self.game_over:
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            
            if self.winner == "Draw":
                msg = "It's a Draw! 🤝"
                msg_color = (200, 200, 200)
            else:
                winner_name = reshape_persian(self.session.player1_name) if self.winner == 1 else reshape_persian(self.session.player2_name)
                msg = f"{winner_name} Wins! 🎉"
                msg_color = self.COLOR_X if self.winner == 1 else self.COLOR_O
                
            win_surf = self.font_big.render(msg, True, msg_color)
            self.screen.blit(win_surf, (self.SCREEN_WIDTH // 2 - win_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 - 60))
            
            hint_surf = self.font.render("Click anywhere else to Restart", True, (150, 150, 150))
            self.screen.blit(hint_surf, (self.SCREEN_WIDTH // 2 - hint_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 40))
            
            back_rect = pygame.Rect(self.SCREEN_WIDTH // 2 - 80, self.SCREEN_HEIGHT // 2 + 140, 160, 45)
            pygame.draw.rect(self.screen, (40, 40, 60), back_rect, border_radius=8)
            back_surf = self.font.render("Main Menu", True, (255, 255, 255))
            self.screen.blit(back_surf, (self.SCREEN_WIDTH // 2 - back_surf.get_width() // 2, self.SCREEN_HEIGHT // 2 + 148))
