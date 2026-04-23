import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
MAP_SIZE = 12000
FPS = 90
MIN_BOTS = 20

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Slither.io Local")
clock = pygame.time.Clock()


WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GRAY    = (80,  80,  80)
DARK    = (15,  15,  25)
ACCENT  = (0,   220, 180)


PALETTE = [
    (220,  50,  50),   # rojo
    ( 50, 120, 255),   # azul
    (255, 210,  30),   # amarillo
    (220,  50, 220),   # magenta
    ( 50, 220,  80),   # verde
    (255, 130,  20),   # naranja
    ( 80, 220, 255),   # celeste
    (200, 255,  80),   # lima
]

PALETTE_NAMES = [
    "Rojo", "Azul", "Amarillo", "Magenta",
    "Verde", "Naranja", "Celeste", "Lima"
]

BOT_COLORS = [
    (160, 80,  80), (80, 80, 160), (80, 160, 80), (160, 160, 80),
    (160, 80, 160), (80, 160, 160),(200, 120, 60), (120, 200, 60),
    (60, 120, 200), (200, 60, 120),
]

controls = [
    {"left": pygame.K_a, "right": pygame.K_d, "boost": pygame.K_w},
    {"left": pygame.K_LEFT, "right": pygame.K_RIGHT, "boost": pygame.K_UP},
    {"left": pygame.K_j, "right": pygame.K_l, "boost": pygame.K_i},
    {"left": pygame.K_f, "right": pygame.K_h, "boost": pygame.K_t},
]

BOT_PREFIXES = ["Zar","Nyx","Vel","Dro","Kex","Mur","Siv","Tog","Brix","Phal","Quen","Arlo","Vex","Kro","Snak"]
BOT_SUFFIXES = ["ius","ox","ek","ara","on","ax","ix","oth","en","ak","uz","yr","el","an","or"]

def random_bot_name():
    return random.choice(BOT_PREFIXES) + random.choice(BOT_SUFFIXES)

class Food:
    def __init__(self):
        self.respawn()

    def respawn(self):
        self.x         = random.randint(0, MAP_SIZE)
        self.y         = random.randint(0, MAP_SIZE)
        self.size      = random.randint(3, 8)
        self.color     = [random.randint(120, 255) for _ in range(3)]
        self.phase     = random.uniform(0, 2 * math.pi)
        self.speed_osc = random.uniform(0.04, 0.10)
        self.float_r   = random.uniform(0.8, 1.8)

foods = [Food() for _ in range(1500)]

class Snake:
    def __init__(self, x, y, color, is_ai=False, player_index=0, name=None):
        self.body         = [(x, y)]
        self.angle        = random.uniform(0, 2 * math.pi)
        self.speed        = 3
        self.length       = 20
        self.color        = color
        self.is_ai        = is_ai
        self.player_index = player_index
        self.score        = 0
        self.alive        = True
        self.name         = name or (random_bot_name() if is_ai else f"P{player_index+1}")
        self.boost_timer = 0   # acumula frames de boost

        # IA: objetivo actual
        self._ai_target   = None
        self._ai_timer    = 0

    def move(self, keys=None):
        if not self.is_ai:
            if keys:
                if keys["left"]:
                    self.angle -= 0.07
                if keys["right"]:
                    self.angle += 0.07
                current_speed = 6 if keys["boost"] and self.score > 0 else self.speed
        else:
            self._ai_move()
            current_speed = self.speed

        hx, hy = self.body[0]
        hx += math.cos(self.angle) * current_speed
        hy += math.sin(self.angle) * current_speed

        # wrap
        hx %= MAP_SIZE
        hy %= MAP_SIZE

        self.body.insert(0, (hx, hy))
        if len(self.body) > self.length:
            self.body.pop()

    def _ai_move(self):
        
        self._ai_timer -= 1
        hx, hy = self.body[0]

        if self._ai_timer <= 0 or self._ai_target is None:
            # elegir la comida más cercana en un radio
            best   = None
            best_d = float("inf")
            for f in random.sample(foods, min(20, len(foods))):
                d = math.hypot(hx - f.x, hy - f.y)
                if d < best_d:
                    best_d = d
                    best   = f
            self._ai_target = best
            self._ai_timer  = 20    

        if self._ai_target:
            tx, ty    = self._ai_target.x, self._ai_target.y
            desired   = math.atan2(ty - hy, tx - hx)
            diff      = (desired - self.angle + math.pi) % (2 * math.pi) - math.pi
            turn      = max(-0.08, min(0.08, diff))
            self.angle += turn
        else:
            self.angle += random.uniform(-0.05, 0.05)

    def grow(self, amount):
        self.length += amount
        self.score  += amount

    def draw(self, surface, cam_x, cam_y, boosting=False):
        n = len(self.body)

        for idx, (x, y) in enumerate(self.body):
            base_r = 5 + min(self.length // 60, 5)
            r      = base_r if idx > 0 else base_r + 2

            fade  = 0.5 + 0.5 * (1 - idx / max(n, 1))
            color = tuple(int(c * fade) for c in self.color)

            sx = int(x - cam_x)
            sy = int(y - cam_y)
            pygame.draw.circle(surface, color, (sx, sy), r)

            # luz que pulsa en todo el cuerpo a la vez
            if boosting:
                pulse = 0.5 + 0.5 * math.sin(GAME_TICK * 0.18)
                if pulse > 0.1:
                    glow_r = r + 4
                    glow_a = int(pulse * 160)
                    glow_c = tuple(min(255, int(c + 100 * pulse)) for c in self.color)
                    gs = pygame.Surface((glow_r * 2 + 1, glow_r * 2 + 1), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (*glow_c, glow_a), (glow_r, glow_r), glow_r)
                    surface.blit(gs, (sx - glow_r, sy - glow_r))

        # ojos
        hx = int(self.body[0][0] - cam_x)
        hy = int(self.body[0][1] - cam_y)
        eye_r  = max(2, base_r // 2)
        offset = base_r - 1
        ex1 = hx + int(math.cos(self.angle - 0.6) * offset)
        ey1 = hy + int(math.sin(self.angle - 0.6) * offset)
        ex2 = hx + int(math.cos(self.angle + 0.6) * offset)
        ey2 = hy + int(math.sin(self.angle + 0.6) * offset)
        pygame.draw.circle(surface, WHITE, (ex1, ey1), eye_r)
        pygame.draw.circle(surface, WHITE, (ex2, ey2), eye_r)
        pygame.draw.circle(surface, BLACK, (ex1, ey1), max(1, eye_r - 1))
        pygame.draw.circle(surface, BLACK, (ex2, ey2), max(1, eye_r - 1))


GAME_TICK = 0

def draw_food(surface, cam_x, cam_y):
    for food in foods:
        t      = GAME_TICK * food.speed_osc + food.phase
        fx     = food.x + math.sin(t) * food.float_r
        fy     = food.y + math.cos(t * 0.7) * food.float_r
        sx     = int(fx - cam_x)
        sy     = int(fy - cam_y)

        # pulso de brillo: sube y baja suavemente
        bright = 0.4 + 0.6 * (0.5 + 0.5 * math.sin(t * 1.3))

        # halo exterior grande, muy transparente
        for halo_r, alpha in [(food.size + 6, 35), (food.size + 3, 65)]:
            halo_c = tuple(min(255, int(c * bright)) for c in food.color)
            hs = pygame.Surface((halo_r * 2 + 1, halo_r * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(hs, (*halo_c, alpha), (halo_r, halo_r), halo_r)
            surface.blit(hs, (sx - halo_r, sy - halo_r))

        # núcleo: solo un círculo pequeño de luz, sin relleno sólido
        core_r = max(2, int(food.size * 0.5 * bright))
        core_c = tuple(min(255, int(c * bright + 80)) for c in food.color)
        core_s = pygame.Surface((core_r * 2 + 1, core_r * 2 + 1), pygame.SRCALPHA)
        pygame.draw.circle(core_s, (*core_c, 200), (core_r, core_r), core_r)
        surface.blit(core_s, (sx - core_r, sy - core_r))

def check_food(snake):
    head = snake.body[0]
    for food in foods:
        if math.hypot(head[0] - food.x, head[1] - food.y) < food.size + 6:
            food.respawn()
            snake.grow(food.size)

def draw_minimap(surface, snakes):
    mini_size = 160
    mini = pygame.Surface((mini_size, mini_size), pygame.SRCALPHA)
    mini.fill((10, 10, 20, 200))
    pygame.draw.rect(mini, ACCENT, (0, 0, mini_size, mini_size), 1)

    scale = mini_size / MAP_SIZE

    for food in random.sample(foods, min(100, len(foods))):
        x = int(food.x * scale)
        y = int(food.y * scale)
        pygame.draw.circle(mini, food.color, (x, y), 1)

    for snake in snakes:
        x = int(snake.body[0][0] * scale)
        y = int(snake.body[0][1] * scale)
        r = 4 if not snake.is_ai else 2
        pygame.draw.circle(mini, snake.color, (x, y), r)

    surface.blit(mini, (surface.get_width() - mini_size - 8,
                         surface.get_height() - mini_size - 8))

def draw_grid(surface, cam_x, cam_y):
    GRID = 200
    color = (35, 35, 50)
    sx = int(cam_x) % GRID
    sy = int(cam_y) % GRID
    w, h = surface.get_size()
    for gx in range(-GRID, w + GRID, GRID):
        pygame.draw.line(surface, color, (gx - sx, 0), (gx - sx, h))
    for gy in range(-GRID, h + GRID, GRID):
        pygame.draw.line(surface, color, (0, gy - sy), (w, gy - sy))


def check_collisions(snakes):
    dead = []
    for i, snake in enumerate(snakes):
        head = snake.body[0]
        for j, other in enumerate(snakes):
            if i == j: continue  # No self-collision
            for segment in other.body:
                if math.hypot(head[0] - segment[0], head[1] - segment[1]) < 7:
                    dead.append(i)
                    break
            if i in dead:
                break
    return list(set(dead))

def snake_to_food(snake):
    for x, y in snake.body[::3]:   # cada 3 segmentos para no saturar
        f = Food()
        f.x, f.y = int(x), int(y)
        foods.append(f)

def replenish_bots(snakes):
    bot_count = sum(1 for s in snakes if s.is_ai)
    for _ in range(MIN_BOTS - bot_count):
        color = random.choice(BOT_COLORS)
        s = Snake(
            random.randint(0, MAP_SIZE),
            random.randint(0, MAP_SIZE),
            color,
            is_ai=True,
            player_index=99,
        )
        snakes.append(s)


def get_viewports(n):
    if n <= 0:
        return []
    if n == 1:
        return [(0, 0, WIDTH, HEIGHT)]
    if n == 2:
        return [(0, 0, WIDTH // 2, HEIGHT), (WIDTH // 2, 0, WIDTH // 2, HEIGHT)]
    if n == 3:
        return [
            (0, 0, WIDTH // 2, HEIGHT // 2),
            (WIDTH // 2, 0, WIDTH // 2, HEIGHT // 2),
            (0, HEIGHT // 2, WIDTH, HEIGHT // 2),
        ]
    return [
        (0,         0,          WIDTH // 2, HEIGHT // 2),
        (WIDTH // 2, 0,         WIDTH // 2, HEIGHT // 2),
        (0,         HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
        (WIDTH // 2, HEIGHT // 2, WIDTH // 2, HEIGHT // 2),
    ]


def draw_starfield(surface, stars, t):
    for (sx, sy, sr, speed) in stars:
        ny = (sy + speed * t * 0.02) % HEIGHT
        alpha = int(80 + 120 * abs(math.sin(t * 0.01 + sx)))
        color  = (alpha, alpha, alpha)
        pygame.draw.circle(surface, color, (sx, int(ny)), sr)

def menu():
    try:
        title_font  = pygame.font.SysFont("couriernew", 62, bold=True)
        sub_font    = pygame.font.SysFont("couriernew", 22)
        label_font  = pygame.font.SysFont("couriernew", 18)
    except Exception:
        title_font  = pygame.font.SysFont(None, 62)
        sub_font    = pygame.font.SysFont(None, 22)
        label_font  = pygame.font.SysFont(None, 18)

    # estrellas de fondo
    stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT),
              random.randint(1, 2), random.uniform(0.3, 1.5)) for _ in range(180)]

    num_players    = 1
    player_colors  = [0, 1, 2, 3]   
    selected_slot  = 0               
    t              = 0

    
    BLOCK_W, BLOCK_H = 200, 110
    gap   = 20
    total = num_players * BLOCK_W + (num_players - 1) * gap
    

    running = True
    while running:
        t += 1
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: num_players = 1
                if event.key == pygame.K_2: num_players = 2
                if event.key == pygame.K_3: num_players = 3
                if event.key == pygame.K_4: num_players = 4

                # navegar slots con TAB
                if event.key == pygame.K_TAB:
                    selected_slot = (selected_slot + 1) % num_players

                # cambiar color del slot seleccionado
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    player_colors[selected_slot] = (player_colors[selected_slot] - 1) % len(PALETTE)
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    player_colors[selected_slot] = (player_colors[selected_slot] + 1) % len(PALETTE)

                # iniciar juego
                if event.key == pygame.K_RETURN:
                    chosen = [PALETTE[player_colors[i]] for i in range(num_players)]
                    return num_players, chosen

        # ── fondo ────────────────────────────────────────────────
        screen.fill(DARK)
        draw_starfield(screen, stars, t)

        # línea decorativa superior
        pygame.draw.line(screen, ACCENT, (60, 90), (WIDTH - 60, 90), 1)
        pygame.draw.line(screen, ACCENT, (60, 92), (WIDTH - 60, 92), 1)

        # título
        pulse = int(200 + 55 * math.sin(t * 0.04))
        title_color = (0, pulse, int(pulse * 0.8))
        title_surf  = title_font.render("SLITHER  LOCAL", True, title_color)
        screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 55)))

        # instrucciones superiores
        instr = sub_font.render("Presioná  1 · 2 · 3 · 4  para elegir jugadores", True, (140, 200, 180))
        screen.blit(instr, instr.get_rect(center=(WIDTH // 2, 120)))

        # ── bloques de jugador ───────────────────────────────────
        total_w = num_players * BLOCK_W + (num_players - 1) * gap
        start_x = (WIDTH - total_w) // 2
        block_y  = 175

        for i in range(num_players):
            bx = start_x + i * (BLOCK_W + gap)
            is_sel = (i == selected_slot)

            border_col = ACCENT if is_sel else (50, 70, 80)
            bg_col     = (20, 30, 40) if is_sel else (12, 18, 25)
            pygame.draw.rect(screen, bg_col,    (bx, block_y, BLOCK_W, BLOCK_H), border_radius=8)
            pygame.draw.rect(screen, border_col,(bx, block_y, BLOCK_W, BLOCK_H), 2, border_radius=8)

            # etiqueta jugador
            p_label = label_font.render(f"JUGADOR  {i+1}", True, ACCENT if is_sel else GRAY)
            screen.blit(p_label, p_label.get_rect(center=(bx + BLOCK_W // 2, block_y + 20)))

            # muestra de color
            swatch_rect = pygame.Rect(bx + BLOCK_W // 2 - 22, block_y + 38, 44, 28)
            pygame.draw.rect(screen, PALETTE[player_colors[i]], swatch_rect, border_radius=5)
            pygame.draw.rect(screen, WHITE, swatch_rect, 1, border_radius=5)

            # nombre del color
            c_name = label_font.render(PALETTE_NAMES[player_colors[i]], True, WHITE)
            screen.blit(c_name, c_name.get_rect(center=(bx + BLOCK_W // 2, block_y + 80)))

            # flechas si está seleccionado
            if is_sel:
                arr = label_font.render("◄          ►", True, ACCENT)
                screen.blit(arr, arr.get_rect(center=(bx + BLOCK_W // 2, block_y + 80)))

        
        y_hint = block_y + BLOCK_H + 30
        hints = [
            "TAB  →  cambiar slot seleccionado",
            "◄  ►  /  A  D  →  cambiar color del slot",
            "ENTER  →  ¡Jugar!",
        ]
        for idx, h in enumerate(hints):
            hs = label_font.render(h, True, (100, 160, 140))
            screen.blit(hs, hs.get_rect(center=(WIDTH // 2, y_hint + idx * 26)))

        # controles de cada jugador
        ctrl_labels = ["A / D", "← / →", "J / L", "F / H"]
        y_ctrl = y_hint + len(hints) * 26 + 20
        ctrl_title = label_font.render("Controles:", True, (80, 120, 100))
        screen.blit(ctrl_title, ctrl_title.get_rect(center=(WIDTH // 2, y_ctrl)))
        for i in range(num_players):
            cl = label_font.render(f"P{i+1}: {ctrl_labels[i]}", True, PALETTE[player_colors[i]])
            screen.blit(cl, cl.get_rect(center=(WIDTH // 2 + (i - num_players // 2) * 130 + (30 if num_players % 2 == 0 else 0), y_ctrl + 24)))

        
        pygame.draw.line(screen, ACCENT, (60, HEIGHT - 30), (WIDTH - 60, HEIGHT - 30), 1)

        pygame.display.flip()

    return 1, [PALETTE[0]]


def draw_border_warning(surface, cam_x, cam_y, t):
    WARNING_DIST = 300
    w, h = surface.get_size()

    overlay = pygame.Surface((w, h), pygame.SRCALPHA)

    left   = -cam_x
    right  = MAP_SIZE - cam_x
    top    = -cam_y
    bottom = MAP_SIZE - cam_y

    pulse = 0.5 + 0.5 * math.sin(t * 0.05)

    # Draw red alarm outside the map
    if cam_x < 0:
        alpha = int(150 * pulse)
        alpha = max(0, min(255, alpha))
        overlay.fill((255, 0, 0, alpha), pygame.Rect(0, 0, -cam_x, h))
    if cam_y < 0:
        alpha = int(150 * pulse)
        alpha = max(0, min(255, alpha))
        overlay.fill((255, 0, 0, alpha), pygame.Rect(0, 0, w, -cam_y))
    if cam_x > MAP_SIZE - w:
        alpha = int(150 * pulse)
        alpha = max(0, min(255, alpha))
        overlay.fill((255, 0, 0, alpha), pygame.Rect(MAP_SIZE - cam_x, 0, w - (MAP_SIZE - cam_x), h))
    if cam_y > MAP_SIZE - h:
        alpha = int(150 * pulse)
        alpha = max(0, min(255, alpha))
        overlay.fill((255, 0, 0, alpha), pygame.Rect(0, MAP_SIZE - cam_y, w, h - (MAP_SIZE - cam_y)))

    surface.blit(overlay, (0, 0))


def show_gameover(winner_color, winner_idx):
    try:
        big   = pygame.font.SysFont("couriernew", 54, bold=True)
        small = pygame.font.SysFont("couriernew", 24)
    except Exception:
        big   = pygame.font.SysFont(None, 54)
        small = pygame.font.SysFont(None, 24)

    t = 0
    while True:
        t += 1
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    return "quit"

        screen.fill(DARK)
        pulse = int(180 + 75 * math.sin(t * 0.05))
        wc    = tuple(min(255, int(c * pulse / 255)) for c in winner_color)

        w_txt = big.render(f"¡GANÓ  JUGADOR  {winner_idx + 1}!", True, wc)
        screen.blit(w_txt, w_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        r_txt = small.render("ENTER  →  Reiniciar     ESC  →  Salir", True, (120, 180, 160))
        screen.blit(r_txt, r_txt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30)))
        pygame.display.flip()


def create_snakes(num_players, player_colors):
    snakes = []
    for i in range(num_players):
        s = Snake(
            random.randint(200, MAP_SIZE - 200),
            random.randint(200, MAP_SIZE - 200),
            player_colors[i],
            is_ai=False,
            player_index=i,
        )
        snakes.append(s)

    # bots iniciales
    for _ in range(MIN_BOTS):
        color = random.choice(BOT_COLORS)
        s = Snake(
            random.randint(0, MAP_SIZE),
            random.randint(0, MAP_SIZE),
            color,
            is_ai=True,
            player_index=99,
        )
        snakes.append(s)

    return snakes

def draw_leaderboard(surface, snakes):
    try:
        lb_font  = pygame.font.SysFont("couriernew", 16, bold=True)
        ttl_font = pygame.font.SysFont("couriernew", 17, bold=True)
    except Exception:
        lb_font  = pygame.font.SysFont(None, 16)
        ttl_font = pygame.font.SysFont(None, 17)

    TOP      = 5
    W, ROW_H = 200, 22
    PAD      = 8
    top5     = sorted(snakes, key=lambda s: s.score, reverse=True)[:TOP]
    total_h  = PAD + 24 + TOP * ROW_H + PAD

    bg = pygame.Surface((W, total_h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    x0 = surface.get_width() - W - 10
    y0 = 10
    surface.blit(bg, (x0, y0))
    pygame.draw.rect(surface, ACCENT, (x0, y0, W, total_h), 1, border_radius=4)

    title = ttl_font.render("▶  TOP  5", True, ACCENT)
    surface.blit(title, (x0 + PAD, y0 + PAD))

    for rank, s in enumerate(top5):
        ry = y0 + PAD + 24 + rank * ROW_H
        if not s.is_ai:
            hl = pygame.Surface((W - 2, ROW_H - 2), pygame.SRCALPHA)
            hl.fill((255, 255, 255, 18))
            surface.blit(hl, (x0 + 1, ry))
        pygame.draw.circle(surface, s.color, (x0 + PAD + 6, ry + ROW_H // 2), 5)
        label = lb_font.render(f"{rank+1}.  {s.name}", True, s.color)
        surface.blit(label, (x0 + PAD + 16, ry + 3))
        sc_txt = lb_font.render(f"{s.score}", True, WHITE)
        surface.blit(sc_txt, (x0 + W - sc_txt.get_width() - PAD, ry + 3))

def game():
    global foods
    num_players, player_colors = menu()

    while True:
        foods   = [Food() for _ in range(1200)]
        snakes  = create_snakes(num_players, player_colors)
        dead_scores = {}   # player_index -> score al morir
        t = 0

        running = True
        while running:
            clock.tick(FPS)
            global GAME_TICK
            GAME_TICK += 1
            t += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); return

            pressed = pygame.key.get_pressed()

            # mover todas
            for i, snake in enumerate(snakes):
                if not snake.is_ai:
                    keys = {
                        "left":  pressed[controls[snake.player_index]["left"]],
                        "right": pressed[controls[snake.player_index]["right"]],
                        "boost": pressed[controls[snake.player_index]["boost"]],
                    }
                    snake.move(keys)

                    # costo del boost: 1 punto por segundo (60 frames)
                    if keys["boost"] and snake.score > 0 and snake.length > 5:
                        snake.boost_timer += 1
                        if snake.boost_timer >= 60:
                            snake.boost_timer = 0
                            snake.length = max(5, snake.length - 2)
                            snake.score  = max(0, snake.score  - 2)
                    else:
                        snake.boost_timer = 0
                else:
                    snake.move()
                check_food(snake)

            # colisiones (podría haber múltiples muertos simultáneos)
            dead_indices = check_collisions(snakes)
            for di in sorted(dead_indices, reverse=True):
                dead_snake = snakes[di]
                if not dead_snake.is_ai:
                    dead_scores[dead_snake.player_index] = dead_snake.score
                snake_to_food(dead_snake)
                snakes.pop(di)

            # reponer bots
            replenish_bots(snakes)

            # verificar fin de partida
            human_snakes = [s for s in snakes if not s.is_ai]
            if num_players > 1 and len(human_snakes) <= 1:
                # queda un ganador (o ninguno)
                if human_snakes:
                    winner = human_snakes[0]
                    action = show_gameover(winner.color, winner.player_index)
                else:
                    action = show_gameover(GRAY, 0)
                if action == "restart":
                    break   # rompe el inner loop → reinicia
                else:
                    return

            # ── render ──────────────────────────────────────────
            human_snakes = [s for s in snakes if not s.is_ai]
            if not human_snakes:
                break

            viewports = get_viewports(len(human_snakes))
            screen.fill(BLACK)

            for draw_i, snake in enumerate(human_snakes):
                vx, vy, vw, vh = viewports[draw_i]
                surface = pygame.Surface((vw, vh))

                cam_x = snake.body[0][0] - vw // 2
                cam_y = snake.body[0][1] - vh // 2

                surface.fill((18, 18, 28))
                draw_grid(surface, cam_x, cam_y)
                draw_food(surface, cam_x, cam_y)
                draw_border_warning(surface, cam_x, cam_y, t)

                for s in snakes:
                    is_boosting = (not s.is_ai and
                        pressed[controls[s.player_index]["boost"]])
                    s.draw(surface, cam_x, cam_y, boosting=is_boosting) 

                draw_minimap(surface, snakes)

                # HUD score
                try:
                    hud_font = pygame.font.SysFont("couriernew", 20, bold=True)
                except Exception:
                    hud_font = pygame.font.SysFont(None, 20)

                score_bg = pygame.Surface((160, 28), pygame.SRCALPHA)
                score_bg.fill((0, 0, 0, 140))
                surface.blit(score_bg, (6, 6))
                score_txt = hud_font.render(f"P{snake.player_index+1}  ·  {snake.score} pts", True, snake.color)
                surface.blit(score_txt, (10, 8))

                screen.blit(surface, (vx, vy))

            # separadores
            alive_count = len(human_snakes)
            sep_color = (60, 80, 80)

            if alive_count == 2:
                # división izquierda/derecha
                pygame.draw.line(screen, sep_color, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)

            elif alive_count == 3:
                # línea horizontal (arriba/abajo)
                pygame.draw.line(screen, sep_color, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 2)

                # línea vertical SOLO en la parte de arriba
                pygame.draw.line(screen, sep_color, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT // 2), 2)

            elif alive_count == 4:
                # cruz completa
                pygame.draw.line(screen, sep_color, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)
                pygame.draw.line(screen, sep_color, (0, HEIGHT // 2), (WIDTH, HEIGHT // 2), 2)

            draw_leaderboard(screen, snakes)
            pygame.display.flip()

        # si llegó acá por restart → volver al menú
        num_players, player_colors = menu()

game()