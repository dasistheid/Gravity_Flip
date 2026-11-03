"""
Gravity Flip — 2D платформер с переворотом гравитации

"""

import pygame
import sys
import random

# ==================== НАСТРОЙКИ ====================
WIDTH, HEIGHT = 1000, 600
FPS = 60
TITLE = "Gravity Flip"
LEVEL_WIDTH = 3500          # ширина уровня

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (70, 130, 255)
LIGHT_BLUE = (120, 180, 255)
GREEN = (50, 200, 100)
RED = (220, 60, 60)
ORANGE = (255, 140, 40)
YELLOW = (255, 220, 50)
CYAN = (50, 220, 220)
DARK = (20, 20, 30)
PLATFORM_COLOR = (60, 70, 90)
PLATFORM_BORDER = (100, 120, 150)

# ==================== КЛАССЫ ====================

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 32
        self.height = 42
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Важно: facing_right должен быть ДО вызова _draw_player
        self.facing_right = True
        self._draw_player()
        self.rect = self.image.get_rect(topleft=(x, y))

        # Физика
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 4.0              # чуть медленнее
        self.jump_power = -13
        self.gravity = 0.55
        self.gravity_dir = 1          # 1 = вниз, -1 = вверх

        # Состояния
        self.on_ground = False
        self.jumps_left = 2
        self.max_jumps = 2

        # Гравитация
        self.gravity_charges = 3
        self.max_gravity_charges = 3
        self.flip_cooldown = 0

        # Жизни и очки
        self.lives = 3
        self.score = 0
        self.combo = 0
        self.combo_timer = 0

        # Неуязвимость после урона
        self.invincible = 0

    def _draw_player(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, BLUE, (4, 8, 24, 28), border_radius=6)
        pygame.draw.circle(self.image, LIGHT_BLUE, (16, 10), 10)
        eye_offset = 3 if self.facing_right else -3
        pygame.draw.circle(self.image, WHITE, (16 + eye_offset, 9), 3)
        pygame.draw.circle(self.image, BLACK, (16 + eye_offset + 1, 9), 1)
        pygame.draw.rect(self.image, (40, 80, 180), (6, 34, 8, 8), border_radius=2)
        pygame.draw.rect(self.image, (40, 80, 180), (18, 34, 8, 8), border_radius=2)

    def flip_gravity(self):
        if self.gravity_charges > 0 and self.flip_cooldown <= 0:
            self.gravity_dir *= -1
            self.gravity_charges -= 1
            self.flip_cooldown = 20
            self.vel_y = 0
            self.jumps_left = self.max_jumps
            return True
        return False

    def jump(self):
        if self.jumps_left > 0:
            self.vel_y = self.jump_power * self.gravity_dir
            self.jumps_left -= 1
            self.on_ground = False

    def take_damage(self):
        if self.invincible <= 0:
            self.lives -= 1
            self.invincible = 90
            self.combo = 0
            return True
        return False

    def add_score(self, points):
        self.combo += 1
        self.combo_timer = 120
        multiplier = min(1 + self.combo // 3, 5)
        self.score += points * multiplier

    def update(self, platforms, enemies, coins, crystals):
        keys = pygame.key.get_pressed()

        # Горизонтальное движение
        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True

        # Гравитация
        self.vel_y += self.gravity * self.gravity_dir

        max_fall = 14
        if self.gravity_dir == 1:
            self.vel_y = min(self.vel_y, max_fall)
        else:
            self.vel_y = max(self.vel_y, -max_fall)

        # Перемещение по X
        self.rect.x += int(self.vel_x)
        self._collide_platforms(platforms, "x")

        # Не даём уйти левее начала уровня
        if self.rect.left < 0:
            self.rect.left = 0

        # Перемещение по Y
        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self._collide_platforms(platforms, "y")

        # Падение за пределы уровня
        if self.rect.top > HEIGHT + 80 or self.rect.bottom < -80:
            self.take_damage()
            self.rect.topleft = (max(60, self.rect.x - 150), 400)
            self.vel_y = 0
            self.gravity_dir = 1

        # Таймеры
        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        # Столкновения с врагами
        for enemy in list(enemies):
            if self.rect.colliderect(enemy.rect) and self.invincible <= 0:
                if not enemy.spiked and self._can_stomp(enemy):
                    enemy.kill()
                    self.vel_y = self.jump_power * self.gravity_dir * 0.7
                    self.add_score(50)
                else:
                    self.take_damage()

        # Сбор монет
        for coin in pygame.sprite.spritecollide(self, coins, True):
            self.add_score(10)

        # Сбор кристаллов
        for crystal in pygame.sprite.spritecollide(self, crystals, True):
            self.gravity_charges = min(self.gravity_charges + 1, self.max_gravity_charges)
            self.add_score(25)

        # Перерисовка
        self._draw_player()
        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            self.image.set_alpha(120)
        else:
            self.image.set_alpha(255)

    def _can_stomp(self, enemy):
        if self.gravity_dir == 1:
            return self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 12
        else:
            return self.vel_y < 0 and self.rect.top > enemy.rect.centery - 12

    def _collide_platforms(self, platforms, direction):
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if direction == "x":
                    if self.vel_x > 0:
                        self.rect.right = platform.rect.left
                    elif self.vel_x < 0:
                        self.rect.left = platform.rect.right
                elif direction == "y":
                    if self.gravity_dir == 1:
                        if self.vel_y > 0:
                            self.rect.bottom = platform.rect.top
                            self.vel_y = 0
                            self.on_ground = True
                            self.jumps_left = self.max_jumps
                        elif self.vel_y < 0:
                            self.rect.top = platform.rect.bottom
                            self.vel_y = 0
                    else:
                        if self.vel_y < 0:
                            self.rect.top = platform.rect.bottom
                            self.vel_y = 0
                            self.on_ground = True
                            self.jumps_left = self.max_jumps
                        elif self.vel_y > 0:
                            self.rect.bottom = platform.rect.top
                            self.vel_y = 0


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, moving=False, move_range=0, move_speed=2, axis="x"):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(PLATFORM_COLOR)
        pygame.draw.rect(self.image, PLATFORM_BORDER, (0, 0, w, h), 3, border_radius=4)
        pygame.draw.rect(self.image, (80, 90, 120), (3, 3, w-6, h-6), border_radius=3)
        self.rect = self.image.get_rect(topleft=(x, y))

        self.moving = moving
        self.start_x = x
        self.start_y = y
        self.move_range = move_range
        self.move_speed = move_speed
        self.axis = axis
        self.direction = 1

    def update(self):
        if not self.moving:
            return
        if self.axis == "x":
            self.rect.x += self.move_speed * self.direction
            if abs(self.rect.x - self.start_x) >= self.move_range:
                self.direction *= -1
        else:
            self.rect.y += self.move_speed * self.direction
            if abs(self.rect.y - self.start_y) >= self.move_range:
                self.direction *= -1


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, spiked=False, patrol_range=80):
        super().__init__()
        self.spiked = spiked
        self.image = pygame.Surface((36, 30), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.start_x = x
        self.patrol_range = patrol_range
        self.speed = 1.6 if not spiked else 1.1
        self.direction = 1

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        color = RED if self.spiked else ORANGE
        pygame.draw.ellipse(self.image, color, (0, 4, 36, 26))
        pygame.draw.circle(self.image, WHITE, (12, 14), 5)
        pygame.draw.circle(self.image, WHITE, (24, 14), 5)
        pygame.draw.circle(self.image, BLACK, (13, 14), 2)
        pygame.draw.circle(self.image, BLACK, (25, 14), 2)
        if self.spiked:
            for i in range(5):
                sx = 4 + i * 7
                pygame.draw.polygon(self.image, (180, 40, 40),
                                    [(sx, 8), (sx + 3, 0), (sx + 6, 8)])

    def update(self, platforms):
        self.rect.x += self.speed * self.direction
        if abs(self.rect.x - self.start_x) >= self.patrol_range:
            self.direction *= -1

        # Не падаем с платформ
        self.rect.y += 3
        on_platform = any(self.rect.colliderect(p.rect) for p in platforms)
        self.rect.y -= 3
        if not on_platform:
            self.direction *= -1


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (9, 9), 9)
        pygame.draw.circle(self.image, (255, 240, 150), (9, 9), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        self.bob = 0.0

    def update(self):
        self.bob += 0.12
        self.rect.y = self.start_y + int(4 * pygame.math.Vector2(1, 0).rotate(self.bob * 40).y)


class Crystal(pygame.sprite.Sprite):
    """Кристалл гравитации — покачивается как монеты"""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((22, 28), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, CYAN, [(11, 0), (22, 14), (11, 28), (0, 14)])
        pygame.draw.polygon(self.image, (150, 255, 255), [(11, 4), (18, 14), (11, 24), (4, 14)])
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        self.bob = 0.0

    def update(self):
        self.bob += 0.10
        self.rect.y = self.start_y + int(5 * pygame.math.Vector2(1, 0).rotate(self.bob * 35).y)


class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((36, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (180, 180, 180), (14, 0, 8, 60))
        pygame.draw.polygon(self.image, GREEN, [(22, 4), (36, 16), (22, 28)])
        self.rect = self.image.get_rect(bottomleft=(x, y))


# ==================== ПРОЦЕДУРНАЯ ГЕНЕРАЦИЯ УРОВНЯ ====================

def create_level():
    """
    Процедурная генерация горизонтального уровня.
    Каждый раз создаётся новая раскладка.
    """
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    crystals = pygame.sprite.Group()

    # Пол на всю длину уровня
    platforms.add(Platform(0, 550, LEVEL_WIDTH, 50))

    # Генерация основных платформ
    x = 180
    last_y = 460

    while x < LEVEL_WIDTH - 250:
        # Случайная высота относительно предыдущей
        y = last_y + random.randint(-90, 70)
        y = max(180, min(480, y))

        width = random.randint(110, 180)
        platforms.add(Platform(x, y, width, 20))

        # Иногда движущаяся платформа
        if random.random() < 0.22:
            move_axis = random.choice(["x", "y"])
            move_range = random.randint(60, 120)
            move_speed = random.uniform(1.4, 2.4)
            platforms.add(Platform(
                x + random.randint(20, 40),
                y - random.randint(40, 80),
                random.randint(80, 110),
                18,
                moving=True,
                move_range=move_range,
                move_speed=move_speed,
                axis=move_axis
            ))

        # Враги
        if random.random() < 0.55 and width > 120:
            enemy_x = x + random.randint(20, width - 50)
            spiked = random.random() < 0.35
            patrol = random.randint(35, 60)
            enemies.add(Enemy(enemy_x, y - 30, spiked=spiked, patrol_range=patrol))

        # Монеты
        num_coins = random.randint(1, 3)
        for i in range(num_coins):
            coin_x = x + 25 + i * 35
            if coin_x < x + width - 15:
                coins.add(Coin(coin_x, y - 35))

        # Кристалл (реже)
        if random.random() < 0.18:
            crystals.add(Crystal(x + width // 2, y - 50))

        last_y = y
        x += width + random.randint(70, 140)

    # Финиш
    goal = Goal(LEVEL_WIDTH - 130, 400)
    platforms.add(Platform(LEVEL_WIDTH - 280, 420, 160, 20))

    return platforms, enemies, coins, crystals, goal


# ==================== ОТРИСОВКА UI ====================

def draw_ui(screen, player, font, small_font):
    s = pygame.Surface((WIDTH, 48), pygame.SRCALPHA)
    s.fill((0, 0, 0, 160))
    screen.blit(s, (0, 0))

    score_text = font.render(f"Очки: {player.score}", True, WHITE)
    screen.blit(score_text, (20, 10))

    if player.combo >= 3:
        combo_text = font.render(f"Комбо x{min(1 + player.combo // 3, 5)}!", True, YELLOW)
        screen.blit(combo_text, (200, 10))

    lives_text = font.render(f"Жизни: {player.lives}", True, RED if player.lives <= 1 else WHITE)
    screen.blit(lives_text, (400, 10))

    grav_text = font.render(f"Гравитация: {player.gravity_charges}/{player.max_gravity_charges}", True, CYAN)
    screen.blit(grav_text, (580, 10))

    hint = small_font.render("A/D — ходьба  |  Пробел — прыжок  |  G — переворот гравитации", True, (160, 160, 180))
    screen.blit(hint, (20, HEIGHT - 28))


def draw_text_center(screen, text, font, color, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    screen.blit(surf, rect)


# ==================== ГЛАВНЫЙ ЦИКЛ ====================

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("segoeui", 28)
    big_font = pygame.font.SysFont("segoeui", 56)
    small_font = pygame.font.SysFont("segoeui", 18)

    state = "menu"
    camera_x = 0.0

    player = None
    platforms = enemies = coins = crystals = None
    goal = None

    def start_game():
        nonlocal player, platforms, enemies, coins, crystals, goal, state, camera_x
        player = Player(80, 480)
        platforms, enemies, coins, crystals, goal = create_level()
        camera_x = 0.0
        state = "playing"

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if state == "menu" and event.key == pygame.K_RETURN:
                    start_game()

                elif state == "playing":
                    if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        player.jump()
                    if event.key == pygame.K_g:
                        player.flip_gravity()

                elif state in ("win", "lose"):
                    if event.key == pygame.K_RETURN:
                        start_game()
                    if event.key == pygame.K_ESCAPE:
                        state = "menu"

        if state == "playing":
            platforms.update()
            enemies.update(platforms)
            coins.update()
            crystals.update()
            player.update(platforms, enemies, coins, crystals)

            # ===== КАМЕРА (только вправо) =====
            target = player.rect.centerx - WIDTH // 3
            if target > camera_x:
                camera_x += (target - camera_x) * 0.08

            camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))

            if player.rect.colliderect(goal.rect):
                state = "win"
            if player.lives <= 0:
                state = "lose"

        # ===== ОТРИСОВКА =====
        screen.fill(DARK)

        if state == "menu":
            draw_text_center(screen, "GRAVITY FLIP", big_font, CYAN, 180)
            draw_text_center(screen, "Платформер с переворотом гравитации", font, WHITE, 260)
            draw_text_center(screen, "Нажми ENTER чтобы начать", font, YELLOW, 360)
            draw_text_center(screen, "A/D — движение   Пробел — прыжок   G — гравитация", small_font, (150, 150, 170), 450)
            draw_text_center(screen, "Каждый уровень генерируется заново!", small_font, (150, 150, 170), 480)

        elif state == "playing":
            # Рисуем всё с учётом камеры
            for platform in platforms:
                screen.blit(platform.image, (platform.rect.x - camera_x, platform.rect.y))

            for coin in coins:
                screen.blit(coin.image, (coin.rect.x - camera_x, coin.rect.y))

            for crystal in crystals:
                screen.blit(crystal.image, (crystal.rect.x - camera_x, crystal.rect.y))

            for enemy in enemies:
                screen.blit(enemy.image, (enemy.rect.x - camera_x, enemy.rect.y))

            screen.blit(goal.image, (goal.rect.x - camera_x, goal.rect.y))
            screen.blit(player.image, (player.rect.x - camera_x, player.rect.y))

            # Индикатор гравитации
            if player.gravity_dir == -1:
                pygame.draw.polygon(screen, CYAN, [(WIDTH - 40, 70), (WIDTH - 20, 70), (WIDTH - 30, 50)])
            else:
                pygame.draw.polygon(screen, CYAN, [(WIDTH - 40, 50), (WIDTH - 20, 50), (WIDTH - 30, 70)])

            draw_ui(screen, player, font, small_font)

        elif state == "win":
            draw_text_center(screen, "ПОБЕДА!", big_font, GREEN, 200)
            draw_text_center(screen, f"Твой счёт: {player.score}", font, WHITE, 290)
            draw_text_center(screen, "ENTER — играть снова    ESC — в меню", font, YELLOW, 380)

        elif state == "lose":
            draw_text_center(screen, "ПОРАЖЕНИЕ", big_font, RED, 200)
            draw_text_center(screen, f"Счёт: {player.score}", font, WHITE, 290)
            draw_text_center(screen, "ENTER — попробовать снова    ESC — в меню", font, YELLOW, 380)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()