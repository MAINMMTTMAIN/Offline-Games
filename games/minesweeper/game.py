import pygame
import random
import time
from base_game import BaseGame
from persian_utils import render_persian_text, reshape_persian
from main import resource_path

class Minesweeper(BaseGame):
    def __init__(self, screen, session):
        super().__init__(screen)
        self.session = session

        self.width = screen.get_width()
        self.height = screen.get_height()

        # Difficulty: Intermediate
        self.cols = 16
        self.rows = 16
        self.total_mines = 40

        # Calculate tile size and offsets to center the grid
        # Max screen height usage ~70% to leave room for top bar and bottom score
        max_grid_height = int(self.height * 0.70)
        self.tile_size = min(max_grid_height // self.rows, self.width // (self.cols + 4))

        self.grid_width = self.cols * self.tile_size
        self.grid_height = self.rows * self.tile_size

        self.offset_x = (self.width - self.grid_width) // 2
        self.offset_y = (self.height - self.grid_height) // 2 + 10

        self.font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 54 )
        self.font_medium = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 28 )
        self.font_small_ui = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20 )

        # Adjust tile font size based on tile size
        font_s = max(12, int(self.tile_size * 0.6))
        self.font_small = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), font_s)

        self.colors = {
            "bg": (15, 15, 26),
            "panel": (25, 25, 40),
            "hidden": (45, 45, 65),
            "hover": (70, 70, 95),
            "revealed": (20, 20, 32),
            "border_p1": (50, 255, 50),    # Green for P1
            "border_p2": (50, 150, 255),   # Blue for P2
            "border_neutral": (0, 240, 255),
            "flag_p1": (50, 255, 50),
            "flag_p2": (50, 150, 255),
            "mine": (255, 50, 50),
            "mine_bg": (120, 30, 30),
            "mine_hit_bg": (200, 50, 50),
            "text": (240, 240, 255),
            1: (0, 240, 255),
            2: (50, 255, 50),
            3: (255, 50, 50),
            4: (180, 50, 255),
            5: (255, 215, 0),
            6: (255, 140, 0),
            7: (255, 105, 180),
            8: (255, 255, 255)
        }

        self.reset_game()

    def reset_game(self):
        self.state = "START"  # START, PLAYING, GAME_OVER, WON
        self.first_click = True
        self.start_time = 0
        self.end_time = 0

        # Two-player state
        self.current_player = 1   # 1 or 2
        self.score_p1 = 0
        self.score_p2 = 0
        self.last_hit_mine = False  # Flash effect when mine is hit
        self.mine_hit_pos = None
        self.winner_msg = ""

        # grid: -1 = mine, 0 = empty, 1-8 = adjacent mines
        self.grid = [[0 for _ in range(self.rows)] for _ in range(self.cols)]

        # states: "hidden", "revealed", "flagged_p1", "flagged_p2"
        self.states = [["hidden" for _ in range(self.rows)] for _ in range(self.cols)]

    def place_mines(self, safe_x, safe_y):
        mines_placed = 0
        while mines_placed < self.total_mines:
            x = random.randint(0, self.cols - 1)
            y = random.randint(0, self.rows - 1)
            if self.grid[x][y] != -1 and not (abs(x - safe_x) <= 1 and abs(y - safe_y) <= 1):
                self.grid[x][y] = -1
                mines_placed += 1

        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[x][y] == -1:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows:
                            if self.grid[nx][ny] == -1:
                                count += 1
                self.grid[x][y] = count

    def reveal(self, x, y):
        """Returns number of safe tiles revealed."""
        if not (0 <= x < self.cols and 0 <= y < self.rows):
            return 0
        if self.states[x][y] != "hidden":
            return 0

        self.states[x][y] = "revealed"

        if self.grid[x][y] == -1:
            # Mine hit! -10 penalty for current player, then switch
            self.mine_hit_pos = (x, y)
            self.last_hit_mine = True
            if self.current_player == 1:
                self.score_p1 -= 10
            else:
                self.score_p2 -= 10
            self.switch_player()
            self.check_win()
            return 0

        count = 1
        if self.grid[x][y] == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        count += self.reveal(x + dx, y + dy)

        return count

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def toggle_flag(self, x, y):
        if self.states[x][y] == "hidden":
            self.states[x][y] = f"flagged_p{self.current_player}"
        elif self.states[x][y] in ("flagged_p1", "flagged_p2"):
            self.states[x][y] = "hidden"

    def check_win(self):
        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[x][y] != -1 and self.states[x][y] not in ("revealed",):
                    return
        self.game_over()

    def game_over(self):
        self.state = "GAME_OVER"
        self.end_time = time.time()

        # Determine winner
        if self.score_p1 > self.score_p2:
            self.winner_msg = f"{reshape_persian(self.session.player1_name)} Wins!"
            self.session.scores["player1"] += 1
        elif self.score_p2 > self.score_p1:
            self.winner_msg = f"{reshape_persian(self.session.player2_name)} Wins!"
            self.session.scores["player2"] += 1
        else:
            self.winner_msg = "It's a Draw!"

        # Reveal all mines
        for x in range(self.cols):
            for y in range(self.rows):
                if self.grid[x][y] == -1 and self.states[x][y] == "hidden":
                    self.states[x][y] = "revealed"

    def handle_events(self, events):
        super().handle_events(events)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == "GAME_OVER" and event.key == pygame.K_SPACE:
                    self.reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == "GAME_OVER":
                    return
                if self.state == "START":
                    # Start on first click
                    pass

                mouse_x, mouse_y = event.pos
                grid_x = (mouse_x - self.offset_x) // self.tile_size
                grid_y = (mouse_y - self.offset_y) // self.tile_size

                if 0 <= grid_x < self.cols and 0 <= grid_y < self.rows:
                    if event.button == 1:  # Left click - reveal
                        if self.first_click:
                            self.place_mines(grid_x, grid_y)
                            self.first_click = False
                            self.start_time = time.time()
                            self.state = "PLAYING"

                        self.last_hit_mine = False
                        self.mine_hit_pos = None

                        tiles_revealed = self.reveal(grid_x, grid_y)
                        # Add score to current player BEFORE possibly switching
                        # (switch_player is called inside reveal if mine hit)
                        if tiles_revealed > 0:
                            if self.current_player == 1:
                                self.score_p1 += tiles_revealed
                            else:
                                self.score_p2 += tiles_revealed
                            # Revealing safe tiles → keep your turn (don't switch)
                            # Check win after scoring
                            self.check_win()

                    elif event.button == 3:  # Right click - flag
                        if not self.first_click and self.state == "PLAYING":
                            if self.states[grid_x][grid_y] in ("hidden", "flagged_p1", "flagged_p2"):
                                self.toggle_flag(grid_x, grid_y)

    def draw(self):
        self.screen.fill(self.colors["bg"])

        p1_color = self.colors["border_p1"]
        p2_color = self.colors["border_p2"]
        active_color = p1_color if self.current_player == 1 else p2_color

        # ── Top Score Panel ──────────────────────────────────────────────
        panel_h = 70
        panel_y = self.offset_y - panel_h - 15
        panel_w = self.grid_width
        panel_x = self.offset_x

        # P1 score box
        p1_box = pygame.Rect(panel_x, panel_y, panel_w // 2 - 5, panel_h)
        pygame.draw.rect(self.screen, self.colors["panel"], p1_box, border_radius=10)
        border_w = 3 if self.current_player == 1 and self.state == "PLAYING" else 1
        pygame.draw.rect(self.screen, p1_color, p1_box, width=border_w, border_radius=10)

        p1_name_surf = self.font_small_ui.render(reshape_persian(self.session.player1_name), True, p1_color)
        p1_score_surf = self.font_medium.render(str(self.score_p1), True, p1_color)
        self.screen.blit(p1_name_surf, (p1_box.x + 10, p1_box.y + 8))
        self.screen.blit(p1_score_surf, (p1_box.x + 10, p1_box.y + 33))

        if self.current_player == 1 and self.state == "PLAYING":
            turn_surf = self.font_small_ui.render("▶ YOUR TURN", True, p1_color)
            self.screen.blit(turn_surf, (p1_box.right - turn_surf.get_width() - 10, p1_box.y + 8))

        # P2 score box
        p2_box = pygame.Rect(panel_x + panel_w // 2 + 5, panel_y, panel_w // 2 - 5, panel_h)
        pygame.draw.rect(self.screen, self.colors["panel"], p2_box, border_radius=10)
        border_w = 3 if self.current_player == 2 and self.state == "PLAYING" else 1
        pygame.draw.rect(self.screen, p2_color, p2_box, width=border_w, border_radius=10)

        p2_name_surf = self.font_small_ui.render(reshape_persian(self.session.player2_name), True, p2_color)
        p2_score_surf = self.font_medium.render(str(self.score_p2), True, p2_color)
        self.screen.blit(p2_name_surf, (p2_box.x + 10, p2_box.y + 8))
        self.screen.blit(p2_score_surf, (p2_box.x + 10, p2_box.y + 33))

        if self.current_player == 2 and self.state == "PLAYING":
            turn_surf = self.font_small_ui.render("▶ YOUR TURN", True, p2_color)
            self.screen.blit(turn_surf, (p2_box.right - turn_surf.get_width() - 10, p2_box.y + 8))

        # ── Timer & Mine Counter (center of top panel area) ──────────────
        current_time = 0
        if self.state == "PLAYING":
            current_time = int(time.time() - self.start_time)
        elif self.state == "GAME_OVER":
            current_time = int(self.end_time - self.start_time)

        # Count remaining (unrevealed) mines
        remaining_mines = sum(
            1 for x in range(self.cols)
            for y in range(self.rows)
            if self.grid[x][y] == -1 and self.states[x][y] != "revealed"
        ) if not self.first_click else self.total_mines

        time_surf = self.font_small_ui.render(f"⏱ {current_time}s", True, self.colors["text"])
        mine_surf = self.font_small_ui.render(f"💣 {remaining_mines}", True, self.colors["mine"])
        center_x = self.width // 2
        self.screen.blit(time_surf, (center_x - time_surf.get_width() // 2, panel_y + 8))
        self.screen.blit(mine_surf, (center_x - mine_surf.get_width() // 2, panel_y + 38))

        # ── Game Border ────────────────────────────────────────────────────
        border_rect = pygame.Rect(
            self.offset_x - 4, self.offset_y - 4,
            self.grid_width + 8, self.grid_height + 8
        )
        pygame.draw.rect(self.screen, active_color if self.state == "PLAYING" else self.colors["border_neutral"],
                         border_rect, width=3, border_radius=4)

        # ── Grid ──────────────────────────────────────────────────────────
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_x = (mouse_x - self.offset_x) // self.tile_size
        hover_y = (mouse_y - self.offset_y) // self.tile_size

        for x in range(self.cols):
            for y in range(self.rows):
                rect = pygame.Rect(
                    self.offset_x + x * self.tile_size,
                    self.offset_y + y * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )

                state = self.states[x][y]
                val = self.grid[x][y]

                if state == "hidden":
                    is_hover = (x == hover_x and y == hover_y and self.state in ("START", "PLAYING"))
                    color = self.colors["hover"] if is_hover else self.colors["hidden"]
                    pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=4)

                elif state in ("flagged_p1", "flagged_p2"):
                    pygame.draw.rect(self.screen, self.colors["hidden"], rect.inflate(-2, -2), border_radius=4)
                    flag_color = p1_color if state == "flagged_p1" else p2_color
                    flag_surf = self.font_small.render("F", True, flag_color)
                    self.screen.blit(flag_surf, (rect.centerx - flag_surf.get_width() // 2,
                                                  rect.centery - flag_surf.get_height() // 2))

                elif state == "revealed":
                    is_mine_hit = (self.mine_hit_pos == (x, y))
                    if val == -1:
                        bg = self.colors["mine_hit_bg"] if is_mine_hit else self.colors["mine_bg"]
                        pygame.draw.rect(self.screen, bg, rect.inflate(-2, -2), border_radius=4)
                        mine_surf = self.font_small.render("*", True, (255, 200, 200) if is_mine_hit else (0, 0, 0))
                        self.screen.blit(mine_surf, (rect.centerx - mine_surf.get_width() // 2,
                                                      rect.centery - mine_surf.get_height() // 2 + 5))
                    else:
                        pygame.draw.rect(self.screen, self.colors["revealed"], rect.inflate(-2, -2))
                        pygame.draw.rect(self.screen, self.colors["panel"], rect, width=1)
                        if val > 0:
                            num_surf = self.font_small.render(str(val), True, self.colors.get(val, self.colors["text"]))
                            self.screen.blit(num_surf, (rect.centerx - num_surf.get_width() // 2,
                                                         rect.centery - num_surf.get_height() // 2))

        # ── START overlay ─────────────────────────────────────────────────
        if self.state == "START":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 170))
            self.screen.blit(overlay, (0, 0))

            title_surf = self.font_large.render("MINESWEEPER DUEL", True, self.colors["border_neutral"])
            sub_surf = self.font_medium.render("Click any tile to start!", True, self.colors["text"])
            rule1 = self.font_small_ui.render("✔ Reveal safe tiles → score points & keep your turn", True, (200, 200, 220))
            text4 = reshape_persian("✔ کاشی‌های امن را رو کنید → امتیاز بگیرید و نوبت خود را حفظ کنید")
            rule4 = self.font_small_ui.render(text4, True, (200, 200, 220))
            rule2 = self.font_small_ui.render("💣 Hit a mine → turn passes to opponent", True, (200, 200, 220))
            rule5 = self.font_small_ui.render(reshape_persian("💣 به مین برخورد کنی → نوبتت میره برای حریف "), True, (200, 200, 220))
            rule3 = self.font_small_ui.render("🏆 Most tiles revealed when all safe tiles are gone → WIN!", True, (200, 200, 220))
            rule6 = self.font_small_ui.render(reshape_persian("وقتی تمام کاشی های امن رو بشود کسی که بیشترین امتیاز رو گرفته باشه برندس"), True, (200, 200, 220))
            p1_lbl = self.font_medium.render(f"{reshape_persian(self.session.player1_name)} (Green)", True, p1_color)
            p2_lbl = self.font_medium.render(f"{reshape_persian(self.session.player2_name)} (Blue)", True, p2_color)
            vs_lbl = self.font_medium.render("VS", True, (255, 215, 0))

            cy = self.height // 2 - 130
            self.screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, cy))
            cy += 70
            self.screen.blit(p1_lbl, (self.width // 2 - p1_lbl.get_width() - 20, cy))
            self.screen.blit(vs_lbl, (self.width // 2 - vs_lbl.get_width() // 2, cy))
            self.screen.blit(p2_lbl, (self.width // 2 + 20, cy))
            cy += 60
            self.screen.blit(sub_surf, (self.width // 2 - sub_surf.get_width() // 2, cy))
            cy += 45
            self.screen.blit(rule1, (self.width // 2 - rule1.get_width() // 2, cy))
            cy += 30
            self.screen.blit(rule2, (self.width // 2 - rule2.get_width() // 2, cy))
            cy += 30
            self.screen.blit(rule3, (self.width // 2 - rule3.get_width() // 2, cy))
            cy += 30
            self.screen.blit(rule4, (self.width // 2 - rule4.get_width() // 2, cy))
            cy += 30
            self.screen.blit(rule5, (self.width // 2 - rule5.get_width() // 2, cy))
            cy += 30
            self.screen.blit(rule6, (self.width // 2 - rule6.get_width() // 2, cy))
        # ── GAME OVER overlay ──────────────────────────────────────────────
        elif self.state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            winner_color = (255, 215, 0)
            title_surf = self.font_large.render("GAME OVER", True, (255, 50, 50))
            winner_surf = self.font_large.render(self.winner_msg, True, winner_color)
            score_surf = self.font_medium.render(
                f"{reshape_persian(self.session.player1_name)}: {self.score_p1}  |  {reshape_persian(self.session.player2_name)}: {self.score_p2}",
                True, self.colors["text"]
            )
            inst_surf = self.font_small_ui.render("Press SPACE to Play Again  |  ESC to Menu", True, self.colors["text"])

            cy = self.height // 2 - 110
            self.screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, cy))
            cy += 75
            self.screen.blit(winner_surf, (self.width // 2 - winner_surf.get_width() // 2, cy))
            cy += 65
            self.screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, cy))
            cy += 50
            self.screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, cy))
