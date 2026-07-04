def __init__(self, screen):
        super().__init__(screen)
        pygame.display.set_caption("Tic Tac Toe - Arcade Mode")
        
        # --- رنگ‌های اختصاصی بازی دوز (تم نئونی) ---
        self.BG_COLOR = (10, 10, 18)
        self.GRID_COLOR = (45, 45, 70)
        self.COLOR_X = (255, 40, 100)    # صورتی نئون
        self.COLOR_O = (0, 245, 180)     # سبز فسفری نئون
        self.TEXT_COLOR = (220, 220, 240)
        
        # --- منطق بازی ---
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.current_player = 1  # 1 = X, 2 = O
        self.winner = None       # 1, 2, or 'Draw'
        self.game_over = False
        
        # --- تنظیمات فونت ---
        self.font = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_big = pygame.font.SysFont("Segoe UI", 48, bold=True)
        
        # --- محاسبه ابعاد جدول وسط صفحه ---
        self.cell_size = 120
        self.grid_width = 3
        self.start_x = (800 - (3 * self.cell_size)) // 2
        self.start_y = (600 - (3 * self.cell_size)) // 2
