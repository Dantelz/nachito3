import pygame
import random
import math

pygame.init()

WIDTH, HEIGHT = 1000, 700
MAP_SIZE = 3000
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (80,80,80)

controls = [
    {"left": pygame.K_a, "right": pygame.K_d},
    {"left": pygame.K_LEFT, "right": pygame.K_RIGHT},
    {"left": pygame.K_j, "right": pygame.K_l},
    {"left": pygame.K_f, "right": pygame.K_h}
]

class Food:
    def __init__(self):
        self.x = random.randint(0, MAP_SIZE)
        self.y = random.randint(0, MAP_SIZE)
        self.size = random.randint(3, 7)
        self.color = [random.randint(100,255) for _ in range(3)]

foods = [Food() for _ in range(600)]  # MUCHOS más puntitos

class Snake:
    def __init__(self, x, y, color, is_ai=False):
        self.body = [(x, y)]
        self.angle = random.uniform(0, 2*math.pi)
        self.speed = 3
        self.length = 20
        self.color = color
        self.is_ai = is_ai
        self.score = 0

    def move(self, keys=None):
        if not self.is_ai:
            if keys:
                if keys["left"]:
                    self.angle -= 0.07
                if keys["right"]:
                    self.angle += 0.07
        else:
            self.angle += random.uniform(-0.05, 0.05)

        x, y = self.body[0]
        x += math.cos(self.angle) * self.speed
        y += math.sin(self.angle) * self.speed

        if x < 0:
            x = MAP_SIZE
        elif x > MAP_SIZE:
            x = 0

        if y < 0:
            y = MAP_SIZE
        elif y > MAP_SIZE:
            y = 0

        self.body.insert(0, (x,y))
        if len(self.body) > self.length:
            self.body.pop()

    def grow(self, amount):
        self.length += amount
        self.score += amount

    def draw(self, surface, cam_x, cam_y):
        for i, (x,y) in enumerate(self.body):
            RADIUS = 6  # tamaño fijo

            pygame.draw.circle(surface, self.color,
                   (int(x - cam_x), int(y - cam_y)),
                   RADIUS)

def draw_food(surface, cam_x, cam_y):
    for food in foods:
        pygame.draw.circle(surface, food.color,
                           (int(food.x - cam_x), int(food.y - cam_y)),
                           food.size)

def check_food(snake):
    global foods
    head = snake.body[0]

    for food in foods[:]:
        if math.hypot(head[0]-food.x, head[1]-food.y) < food.size + 5:
            foods.remove(food)
            foods.append(Food())
            snake.grow(food.size)

def draw_minimap(surface, snakes):
    mini_size = 120
    mini = pygame.Surface((mini_size, mini_size))
    mini.fill((20,20,20))

    scale = mini_size / MAP_SIZE

    # comida
    for food in foods:
        x = int(food.x * scale)
        y = int(food.y * scale)
        pygame.draw.circle(mini, food.color, (x,y), 1)

    # jugadores
    for snake in snakes:
        x = int(snake.body[0][0] * scale)
        y = int(snake.body[0][1] * scale)
        pygame.draw.circle(mini, snake.color, (x,y), 3)

    surface.blit(mini, (surface.get_width()-mini_size-10,
                        surface.get_height()-mini_size-10))

def menu():
    font = pygame.font.SysFont(None, 50)
    while True:
        screen.fill(BLACK)
        text = font.render("Jugadores (1-4)", True, WHITE)
        screen.blit(text, (350, 250))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: return 1
                if event.key == pygame.K_2: return 2
                if event.key == pygame.K_3: return 3
                if event.key == pygame.K_4: return 4

def create_snakes(num_players):
    snakes = []
    colors = [(255,0,0),(0,0,255),(255,255,0),(255,0,255)]

    for i in range(4):
        is_ai = i >= num_players
        snakes.append(Snake(random.randint(0, MAP_SIZE),
                            random.randint(0, MAP_SIZE),
                            colors[i],
                            is_ai))
    return snakes

def check_collisions(snakes):
    for i, snake in enumerate(snakes):
        head = snake.body[0]

        for j, other in enumerate(snakes):
            # podés chocar con cualquiera (incluido vos mismo si querés)
            for segment in other.body[5:]:  # evitamos cabeza inmediata
                if math.hypot(head[0]-segment[0], head[1]-segment[1]) < 6:
                    return i  # devuelve el índice del que murió
    return None

def snake_to_food(snake):
    for x, y in snake.body:
        foods.append(Food())
        foods[-1].x = int(x)
        foods[-1].y = int(y)

def get_viewports(n):
    if n == 1:
        return [(0,0,WIDTH,HEIGHT)]
    elif n == 2:
        return [(0,0,WIDTH//2,HEIGHT),(WIDTH//2,0,WIDTH//2,HEIGHT)]
    elif n == 3:
        return [(0,0,WIDTH//2,HEIGHT//2),(WIDTH//2,0,WIDTH//2,HEIGHT//2),(0,HEIGHT//2,WIDTH,HEIGHT//2)]
    elif n == 4:
        return [
            (0,0,WIDTH//2,HEIGHT//2),
            (WIDTH//2,0,WIDTH//2,HEIGHT//2),
            (0,HEIGHT//2,WIDTH//2,HEIGHT//2),
            (WIDTH//2,HEIGHT//2,WIDTH//2,HEIGHT//2)
        ]

def game():
    num_players = menu()
    snakes = create_snakes(num_players)

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        pressed = pygame.key.get_pressed()

        for i, snake in enumerate(snakes):
            if not snake.is_ai:
                keys = {
                    "left": pressed[controls[i]["left"]],
                    "right": pressed[controls[i]["right"]],
                }
                snake.move(keys)
            else:
                snake.move()

            check_food(snake)
        
        loser = check_collisions(snakes)

        if loser is not None:
            snake_to_food(snakes[loser])
            snakes.pop(loser)

        screen.fill(BLACK)

        viewports = get_viewports(num_players)

        for i in range(num_players):
            vx, vy, vw, vh = viewports[i]
            surface = pygame.Surface((vw, vh))

            snake = snakes[i]
            cam_x = snake.body[0][0] - vw//2
            cam_y = snake.body[0][1] - vh//2

            surface.fill((30,30,30))

            draw_food(surface, cam_x, cam_y)

            for s in snakes:
                s.draw(surface, cam_x, cam_y)

            # minimapa
            draw_minimap(surface, snakes)

            # score
            font = pygame.font.SysFont(None, 25)
            text = font.render(f"P{i+1}: {snake.score}", True, WHITE)
            surface.blit(text, (10,10))

            screen.blit(surface, (vx, vy))

        # separadores de pantalla
        if num_players > 1:
            if num_players >= 2:
                pygame.draw.line(screen, GRAY, (WIDTH//2,0),(WIDTH//2,HEIGHT),3)
            if num_players >= 3:
                pygame.draw.line(screen, GRAY, (0,HEIGHT//2),(WIDTH,HEIGHT//2),3)

        pygame.display.flip()

    pygame.quit()

game()