import pygame
import sys
import os
import importlib
from persian_utils import render_persian_text, reshape_persian


def resource_path(relative_path):
    """ پیدا کردن مسیر صحیح فایل‌ها در حالت عادی و حالت exe """
    try:
        # وقتی برنامه به exe تبدیل می‌شود، فایل‌ها در اینجا قرار می‌گیرند
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_base_path():
    """ پیدا کردن مسیر پوشه بازی‌ها در هر دو حالت """
    if getattr(sys, 'frozen', False):
        # اگر فایل exe باشد
        return sys._MEIPASS
    else:
        # اگر در حالت پایتون باشد
        return os.path.dirname(os.path.abspath(__file__))
# مقداردهی اولیه Pygame
pygame.init()


Window_Icon = pygame.image.load(resource_path("myicon.ico"))
pygame.display.set_icon(Window_Icon)

# تنظیمات پنجره اصلی به صورت تمام صفحه (Fullscreen)
infoObject = pygame.display.Info()
SCREEN_WIDTH = infoObject.current_w
SCREEN_HEIGHT = infoObject.current_h

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Arcade Games")
clock = pygame.time.Clock()

# رنگ‌ها (تم سایبرپانک / نئونی)
BG_COLOR = (15, 15, 26)
TEXT_COLOR = (240, 240, 255)
PANEL_COLOR = (25, 25, 40)
ACCENT_COLOR = (0, 240, 255)

# سیستم مدیریت امتیازات و نام بازیکنان
class GameSession:
    def __init__(self):
        self.player1_name = "Player 1"
        self.player2_name = "Player 2"
        self.scores = {
            "player1": 0,
            "player2": 0
        }
        self.is_single_player = False
        self.bot_difficulty = "medium"

    def get_player_names(self):
        """ منوی ورود نام بازیکنان در ابتدای بازی """
        font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 24)
        input_font = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 20)
        
        p1_text = ""
        p2_text = ""
        active_input = 1
        is_single_player = False
        bot_difficulty = "Medium"
        
        getting_names = True
        while getting_names:
            screen.fill(BG_COLOR)
            
            # راهنما
            title_surf = font.render("🎮 Game Setup", True, ACCENT_COLOR)
            screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 280))
            
            # انتخاب حالت بازی
            mode_label = font.render("Game Mode:", True, TEXT_COLOR)
            screen.blit(mode_label, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 210))
            
            mode1_btn = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 215, 160, 40)
            pygame.draw.rect(screen, ACCENT_COLOR if is_single_player else PANEL_COLOR, mode1_btn, border_radius=8)
            pygame.draw.rect(screen, ACCENT_COLOR, mode1_btn, width=2, border_radius=8)
            m1_surf = input_font.render("1 Player (Bot)", True, BG_COLOR if is_single_player else ACCENT_COLOR)
            screen.blit(m1_surf, (mode1_btn.centerx - m1_surf.get_width()//2, mode1_btn.centery - m1_surf.get_height()//2))

            mode2_btn = pygame.Rect(SCREEN_WIDTH // 2 + 80, SCREEN_HEIGHT // 2 - 215, 160, 40)
            pygame.draw.rect(screen, ACCENT_COLOR if not is_single_player else PANEL_COLOR, mode2_btn, border_radius=8)
            pygame.draw.rect(screen, ACCENT_COLOR, mode2_btn, width=2, border_radius=8)
            m2_surf = input_font.render("2 Players", True, BG_COLOR if not is_single_player else ACCENT_COLOR)
            screen.blit(m2_surf, (mode2_btn.centerx - m2_surf.get_width()//2, mode2_btn.centery - m2_surf.get_height()//2))

            diff_btns = []
            if is_single_player:
                # انتخاب سختی
                diff_label = font.render("Bot Difficulty:", True, TEXT_COLOR)
                screen.blit(diff_label, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 150))
                
                diffs = ["Low", "Medium", "Hard"]
                for i, d in enumerate(diffs):
                    btn = pygame.Rect(SCREEN_WIDTH // 2 - 100 + i * 115, SCREEN_HEIGHT // 2 - 155, 100, 40)
                    pygame.draw.rect(screen, ACCENT_COLOR if bot_difficulty == d else PANEL_COLOR, btn, border_radius=8)
                    pygame.draw.rect(screen, ACCENT_COLOR, btn, width=2, border_radius=8)
                    dsurf = input_font.render(d, True, BG_COLOR if bot_difficulty == d else ACCENT_COLOR)
                    screen.blit(dsurf, (btn.centerx - dsurf.get_width()//2, btn.centery - dsurf.get_height()//2))
                    diff_btns.append((btn, d))
            
            # باکس بازیکن اول
            p1_label = font.render("Player 1 Name:" if not is_single_player else "Your Name:", True, TEXT_COLOR)
            screen.blit(p1_label, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 80))
            p1_box = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 40, 500, 45)
            pygame.draw.rect(screen, PANEL_COLOR if active_input != 1 else ACCENT_COLOR, p1_box, border_radius=8, width=2 if active_input != 1 else 3)
            p1_to_show = p1_text + ("|" if active_input == 1 and pygame.time.get_ticks() % 1000 < 500 else "")
            p1_surf = render_persian_text(input_font, p1_to_show, TEXT_COLOR)
            screen.blit(p1_surf, (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 - 30))
            
            if not is_single_player:
                # باکس بازیکن دوم
                p2_label = font.render("Player 2 Name:", True, TEXT_COLOR)
                screen.blit(p2_label, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 40))
                p2_box = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 + 80, 500, 45)
                pygame.draw.rect(screen, PANEL_COLOR if active_input != 2 else ACCENT_COLOR, p2_box, border_radius=8, width=2 if active_input != 2 else 3)
                p2_to_show = p2_text + ("|" if active_input == 2 and pygame.time.get_ticks() % 1000 < 500 else "")
                p2_surf = render_persian_text(input_font, p2_to_show, TEXT_COLOR)
                screen.blit(p2_surf, (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 + 90))
            else:
                p2_box = pygame.Rect(0, 0, 0, 0)
            
            # دکمه تایید
            btn_box = pygame.Rect(SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 + 160, 160, 50)
            pygame.draw.rect(screen, PANEL_COLOR, btn_box, border_radius=10)
            pygame.draw.rect(screen, ACCENT_COLOR, btn_box, width=2, border_radius=10)
            btn_surf = font.render("START", True, ACCENT_COLOR)
            screen.blit(btn_surf, (SCREEN_WIDTH // 2 - btn_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 170))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if mode1_btn.collidepoint(event.pos):
                        is_single_player = True
                        active_input = 1
                    elif mode2_btn.collidepoint(event.pos):
                        is_single_player = False
                        
                    if is_single_player:
                        for btn, d in diff_btns:
                            if btn.collidepoint(event.pos):
                                bot_difficulty = d
                                
                    if p1_box.collidepoint(event.pos):
                        active_input = 1
                    elif not is_single_player and p2_box.collidepoint(event.pos):
                        active_input = 2
                    elif btn_box.collidepoint(event.pos):
                        getting_names = False
                        
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if not is_single_player and active_input == 1:
                            active_input = 2
                        else:
                            getting_names = False
                    elif event.key == pygame.K_TAB:
                        if not is_single_player:
                            active_input = 2 if active_input == 1 else 1
                    elif event.key == pygame.K_BACKSPACE:
                        if active_input == 1:
                            p1_text = p1_text[:-1]
                        elif not is_single_player:
                            p2_text = p2_text[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    else:
                        if event.unicode and ord(event.unicode) >= 32:
                            if len(p1_text) < 15 and active_input == 1:
                                p1_text += event.unicode
                            elif not is_single_player and len(p2_text) < 15 and active_input == 2:
                                p2_text += event.unicode
            
            pygame.display.flip()
            clock.tick(30)
            
        if p1_text.strip(): self.player1_name = p1_text.strip()
        if is_single_player:
            self.player2_name = f"Bot ({bot_difficulty})"
            self.is_single_player = True
            self.bot_difficulty = bot_difficulty.lower()
        else:
            if p2_text.strip(): self.player2_name = p2_text.strip()
            self.is_single_player = False


class ArcadeMenu:
    def __init__(self, session, screen):
        self.session = session
        self.screen = screen
        self.games_dir = os.path.join(get_base_path(), "games")
        self.error_msg = ""
        self.error_timer = 0
        self.scroll_y = 0
        self.discover_games()
        self.load_assets()

    def discover_games(self):
        self.available_games = []
        if not os.path.exists(self.games_dir):
            return

        for folder in os.listdir(self.games_dir):
            folder_path = os.path.join(self.games_dir, folder)
            if os.path.isdir(folder_path) and not folder.startswith("__"):
                game_file = os.path.join(folder_path, "game.py")
                if os.path.exists(game_file):
                    # اصلاح دقیق آدرس آیکون
                    icon_path = os.path.join(folder_path, "icon.png")
                    
                    self.available_games.append({
                        "id": folder,
                        "title": folder.replace("_", " ").title(),
                        "icon_path": icon_path if os.path.exists(icon_path) else None
                    })

    def load_assets(self):
        self.font_title = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 36)
        self.font_game = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 16)
        self.font_score = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 18)
        
        for game in self.available_games:
            # ساخت مسیر دقیق با get_base_path
            # در exe این مسیر به داخل MEIPASS اشاره می‌کند
            full_icon_path = os.path.join(get_base_path(), "games", game['id'], "icon.png")

            try:
                if os.path.exists(full_icon_path):
                    img = pygame.image.load(full_icon_path).convert_alpha()
                    game["icon_img"] = pygame.transform.scale(img, (90, 90))
                else:
                    game["icon_img"] = self._get_fallback_icon()
            except:
                game["icon_img"] = self._get_fallback_icon()
        

    def _get_fallback_icon(self):
        fallback = pygame.Surface((90, 90))
        fallback.fill(ACCENT_COLOR)
        return fallback
    
    def draw_menu(self):
        screen.fill(BG_COLOR)
        
        # Calculate max scrolling
        cols = 4
        max_rows = (len(self.available_games) + cols - 1) // cols
        gap_x, gap_y = 170, 200
        content_height = max_rows * gap_y + 60 # Added 60 for the footer
        max_scroll = min(0, SCREEN_HEIGHT - 240 - content_height - 50)
        self.scroll_y = max(max_scroll, min(0, self.scroll_y))
        
        # چیدمان شبکه ای آیکون‌ها بر اساس مانیتور تمام صفحه
        start_x = (SCREEN_WIDTH - (4 * 160)) // 2  
        start_y = 240 + self.scroll_y
        
        for index, game in enumerate(self.available_games):
            col = index % cols
            row = index // cols
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            
            game["rect"] = pygame.Rect(x, y, 110, 130)
            
            mouse_pos = pygame.mouse.get_pos()
            if game["rect"].collidepoint(mouse_pos):
                pygame.draw.rect(screen, PANEL_COLOR, game["rect"].inflate(15, 15), border_radius=12)
                pygame.draw.rect(screen, ACCENT_COLOR, game["rect"].inflate(15, 15), width=2, border_radius=12)
            else:
                pygame.draw.rect(screen, PANEL_COLOR, game["rect"].inflate(10, 10), border_radius=10)
            
            screen.blit(game["icon_img"], (x + 10, y + 10))
            text_surf = self.font_game.render(game["title"], True, TEXT_COLOR)
            screen.blit(text_surf, (x + 55 - text_surf.get_width() // 2, y + 110))
            
        # Draw Footer
        footer_y = start_y + max_rows * gap_y + 20
        footer_surf = self.font_game.render("Made with love by MMTT", True, ACCENT_COLOR)
        screen.blit(footer_surf, (SCREEN_WIDTH // 2 - footer_surf.get_width() // 2, footer_y))
            
        # Draw Top Bar Background to hide scrolled icons
        pygame.draw.rect(screen, BG_COLOR, (0, 0, SCREEN_WIDTH, 180))
        
        # رسم هدر منو در وسط صفحه تمام صفحه
        title_surf = self.font_title.render("🎮 OFFLINE ARCADE HUB", True, ACCENT_COLOR)
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 40))
        
        # تابلوی امتیازات ریسپانسیو
        score_box = pygame.Rect(100, 110, SCREEN_WIDTH - 200, 50)
        pygame.draw.rect(screen, PANEL_COLOR, score_box, border_radius=8)
        
        p1_name_display = reshape_persian(self.session.player1_name)
        p2_name_display = reshape_persian(self.session.player2_name)
        scores_text = f"SCOREBOARD  |  {reshape_persian(p1_name_display)}: {self.session.scores['player1']}   VS   {reshape_persian(p2_name_display)}: {self.session.scores['player2']}"
        score_surf = render_persian_text(self.font_score, scores_text, TEXT_COLOR)
        screen.blit(score_surf, (SCREEN_WIDTH // 2 - score_surf.get_width() // 2, 122))
        
        # Mode toggle button
        self.mode_btn_rect = pygame.Rect(SCREEN_WIDTH - 460, 115, 160, 40)
        mouse_pos = pygame.mouse.get_pos()
        hovering_mode = self.mode_btn_rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, ACCENT_COLOR if hovering_mode else PANEL_COLOR, self.mode_btn_rect, border_radius=8)
        pygame.draw.rect(screen, ACCENT_COLOR, self.mode_btn_rect, 2, border_radius=8)
        mode_str = "1 Player" if getattr(self.session, 'is_single_player', False) else "2 Players"
        mode_text = self.font_score.render(f"Mode: {mode_str}", True, BG_COLOR if hovering_mode else ACCENT_COLOR)
        screen.blit(mode_text, (self.mode_btn_rect.centerx - mode_text.get_width() // 2, self.mode_btn_rect.centery - mode_text.get_height() // 2))

        if getattr(self.session, 'is_single_player', False):
            self.diff_btn_rect = pygame.Rect(SCREEN_WIDTH - 280, 115, 160, 40)
            hovering = self.diff_btn_rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, ACCENT_COLOR if hovering else PANEL_COLOR, self.diff_btn_rect, border_radius=8)
            pygame.draw.rect(screen, ACCENT_COLOR, self.diff_btn_rect, 2, border_radius=8)
            diff_text = self.font_score.render(f"Bot Level: {self.session.bot_difficulty.upper()}", True, BG_COLOR if hovering else ACCENT_COLOR)
            screen.blit(diff_text, (self.diff_btn_rect.centerx - diff_text.get_width() // 2, self.diff_btn_rect.centery - diff_text.get_height() // 2))
        
        if self.error_msg and pygame.time.get_ticks() < self.error_timer:
            msg_surf = render_persian_text(self.font_title, reshape_persian(self.error_msg), (255, 50, 50))
            screen.blit(msg_surf, (SCREEN_WIDTH // 2 - msg_surf.get_width() // 2, SCREEN_HEIGHT - 100))
        elif self.error_msg and pygame.time.get_ticks() >= self.error_timer:
            self.error_msg = ""

    def launch_game(self, game_id):
        supported_single_player = ["tic_tac_toe", "dots_and_boxes", "chess", "snake_duel", "backgammon", "pacman_duel", "bomberman", "connect_four", "billiards", "pong", "flappy_bird"]
        if getattr(self.session, 'is_single_player', False) and game_id not in supported_single_player:
            self.error_msg = "This game doesn't have bot"
            self.error_timer = pygame.time.get_ticks() + 3000
            return
            
        try:
            active_game = None
            
            # ایمپورت کردن فقط در لحظه کلیک (Lazy Import)
            if game_id == "memory_cards":
                from games.memory_cards import game as memory_cards_game
                active_game = memory_cards_game.MemoryCards(self.screen, self.session)
                
            elif game_id == "chess":
                from games.chess import game as chess_game
                active_game = chess_game.Chess(self.screen, self.session)
                
            elif game_id == "backgammon":
                from games.backgammon import game as backgammon_game
                active_game = backgammon_game.Backgammon(self.screen, self.session)
                
            elif game_id == "dots_and_boxes":
                 from games.dots_and_boxes import game as dots_and_boxes_game
                 active_game = dots_and_boxes_game.DotsAndBoxes(self.screen, self.session)
                 
            elif game_id == "minesweeper":
                 from games.minesweeper import game as minesweeper_game
                 active_game = minesweeper_game.Minesweeper(self.screen, self.session)
                 
            elif game_id == "snake_duel":
                 from games.snake_duel import game as snake_duel_game
                 active_game = snake_duel_game.SnakeDuel(self.screen, self.session)
                 
            elif game_id == "SnakeLadders":
                 from games.SnakeLadders import game as SnakeLadders_game
                 active_game = SnakeLadders_game.Snakeladders(self.screen, self.session)
                 
            elif game_id == "tic_tac_toe":
                 from games.tic_tac_toe import game as tic_tac_toe_game
                 active_game = tic_tac_toe_game.TicTacToe(self.screen, self.session)
            
            elif game_id == "battleship":
                 from games.battleship import game as battleship_game
                 active_game = battleship_game.Battleship(self.screen, self.session)
                 
            elif game_id == "pacman_duel":
                 from games.pacman_duel import game as pacman_duel_game
                 active_game = pacman_duel_game.PacmanDuel(self.screen, self.session)
                 
            elif game_id == "bomberman":
                 from games.bomberman import game as bomberman_game
                 active_game = bomberman_game.Bomberman(self.screen, self.session)
                 
            elif game_id == "connect_four":
                 from games.connect_four import game as connect_four_game
                 active_game = connect_four_game.ConnectFour(self.screen, self.session)
                 
            elif game_id == "lumberjack_battle":
                 from games.lumberjack_battle import game as lumberjack_battle_game
                 active_game = lumberjack_battle_game.LumberjackBattle(self.screen, self.session)

            elif game_id == "typing_race":
                 from games.typing_race import game as typing_race_game
                 active_game = typing_race_game.TypingRace(self.screen, self.session)
                 
            elif game_id == "billiards":
                 from games.billiards import game as billiards_game
                 active_game = billiards_game.Billiards(self.screen, self.session)
                 
            elif game_id == "pong":
                 from games.pong import game as pong_game
                 active_game = pong_game.Pong(self.screen, self.session)
                 
            elif game_id == "flappy_bird":
                 from games.flappy_bird import game as flappy_bird_game
                 active_game = flappy_bird_game.FlappyBird(self.screen, self.session)
            
            # اگر بازی لود شد، حلقه اجرای بازی را شروع کن
            if active_game:
                game_clock = pygame.time.Clock()
                while active_game.running:
                    events = pygame.event.get()
                    for event in events:
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                    
                    active_game.handle_events(events)
                    active_game.update()
                    active_game.draw()
                    
                    pygame.display.flip()
                    game_clock.tick(60)
            
            # بعد از خروج از بازی، عنوان پنجره را برگردان
            pygame.display.set_caption("Arcade Games")

        except Exception as e:
            print(f"خطا در اجرای بازی {game_id}: {e}")

def show_welcome_screen(screen):
    import random
    import math
    import os
    font_large = pygame.font.Font(resource_path("Vazirmatn-VariableFont_wght.ttf"), 64)
    
    try:
        pygame.mixer.init()
        bg_music_path = resource_path(os.path.join("games", "pacman_duel", "pacman_sounds", "intermission.wav"))
        if os.path.exists(bg_music_path):
            pygame.mixer.music.load(bg_music_path)
            pygame.mixer.music.play(-1) # Loop indefinitely
    except:
        pass
        
    start_time = pygame.time.get_ticks()
    duration = 15000  # 15 seconds
    
    clock = pygame.time.Clock()
    
    # Load all available game icons
    games_dir = os.path.join(get_base_path(), "games")
    icon_surfaces = []
    if os.path.exists(games_dir):
        for folder in os.listdir(games_dir):
            folder_path = os.path.join(games_dir, folder)
            if os.path.isdir(folder_path) and not folder.startswith("__"):
                icon_path = os.path.join(folder_path, "icon.png")
                if os.path.exists(icon_path):
                    try:
                        img = pygame.image.load(icon_path).convert_alpha()
                        icon_surfaces.append(img)
                    except: pass
                    
    floating_icons = []
    if icon_surfaces:
        for _ in range(20):
            img = random.choice(icon_surfaces)
            size = random.randint(40, 100)
            scaled = pygame.transform.scale(img, (size, size))
            scaled.set_alpha(random.randint(100, 200))
            floating_icons.append({
                'surf': scaled,
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'speed': random.uniform(0.5, 3.0),
                'size': size
            })
            
    # Particle system for cyberpunk background
    particles = []
    for _ in range(100):
        particles.append({
            'x': random.randint(0, SCREEN_WIDTH),
            'y': random.randint(0, SCREEN_HEIGHT),
            'speed': random.uniform(0.5, 2.0),
            'radius': random.randint(1, 4),
            'color': random.choice([ACCENT_COLOR, (255, 0, 255), (0, 255, 255)])
        })
        
    grid_offset_y = 0
    
    running = True
    while running:
        current_time = pygame.time.get_ticks()
        if current_time - start_time > duration:
            break
            
        screen.fill(BG_COLOR)
        
        # Moving Grid Background
        grid_offset_y = (grid_offset_y + 1) % 40
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(screen, (20, 20, 40), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT + 40, 40):
            pygame.draw.line(screen, (20, 20, 40), (0, y - grid_offset_y), (SCREEN_WIDTH, y - grid_offset_y), 1)
        
        # Update and draw particles
        for p in particles:
            p['y'] -= p['speed']
            if p['y'] < 0:
                p['y'] = SCREEN_HEIGHT
                p['x'] = random.randint(0, SCREEN_WIDTH)
            pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), p['radius'])
            
        # Update and draw floating icons
        for icon in floating_icons:
            icon['y'] -= icon['speed']
            if icon['y'] < -icon['size']:
                icon['y'] = SCREEN_HEIGHT
                icon['x'] = random.randint(0, SCREEN_WIDTH)
            screen.blit(icon['surf'], (int(icon['x']), int(icon['y'])))
        
        # Draw Title
        title_surf = font_large.render("Arcade Games", True, ACCENT_COLOR)
        screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        
        # Draw Progress Bar
        progress = (current_time - start_time) / duration
        bar_width = 400
        bar_height = 10
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + 50
        pygame.draw.rect(screen, PANEL_COLOR, (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        pygame.draw.rect(screen, ACCENT_COLOR, (bar_x, bar_y, bar_width * progress, bar_height), border_radius=5)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
        pygame.display.flip()
        clock.tick(60)
        
    try:
        pygame.mixer.music.stop()
    except:
        pass

def main():
    session = GameSession()
    show_welcome_screen(screen)
    session.get_player_names()
    
    menu = ArcadeMenu(session,screen)
    
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # زدن دکمه اسکیپ در منو برنامه را می‌بندد
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_UP:
                    menu.scroll_y += 50
                elif event.key == pygame.K_DOWN:
                    menu.scroll_y -= 50
                    
            if event.type == pygame.MOUSEWHEEL:
                menu.scroll_y += event.y * 30
                
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if hasattr(menu, 'mode_btn_rect') and menu.mode_btn_rect.collidepoint(event.pos):
                    session.is_single_player = not session.is_single_player
                    if session.is_single_player:
                        session.player2_name = f"Bot ({session.bot_difficulty.capitalize()})"
                    else:
                        session.player2_name = "Player 2"
                elif getattr(session, 'is_single_player', False) and hasattr(menu, 'diff_btn_rect') and menu.diff_btn_rect.collidepoint(event.pos):
                    diffs = ["low", "medium", "hard"]
                    idx = diffs.index(session.bot_difficulty)
                    session.bot_difficulty = diffs[(idx + 1) % len(diffs)]
                    session.player2_name = f"Bot ({session.bot_difficulty.capitalize()})"
                else:
                    for game in menu.available_games:
                        if "rect" in game and game["rect"].collidepoint(event.pos):
                            menu.launch_game(game["id"])
        
        menu.draw_menu()
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    main()
