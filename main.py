import pygame
import sys
import random
import math

WIDTH, HEIGHT = 1000, 600
FPS = 60
TITLE = "Gravity Flip"
LEVEL_WIDTH = 3800

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (50, 150, 255)
LIGHT_BLUE = (150, 220, 255)
GREEN = (50, 220, 120)
RED = (255, 70, 90)
ORANGE = (255, 160, 50)
YELLOW = (255, 230, 80)
CYAN = (60, 240, 240)
DARK_BG = (10, 10, 20)
GRID_COLOR = (25, 25, 45)
PLATFORM_COLOR = (40, 45, 60)
PLATFORM_BORDER = (70, 80, 110)
PLATFORM_NEON = (80, 200, 255)
PURPLE = (180, 100, 255)

particles = []
stars = []


def init_stars():
    global stars
    stars = []
    for _ in range(250):
        stars.append({
            'x': random.randint(0, WIDTH),
            'y': random.randint(0, HEIGHT),
            'size': random.uniform(0.5, 2.5),
            'parallax': random.uniform(0.1, 0.4),
            'twinkle_speed': random.uniform(0.05, 0.15),
            'twinkle_offset': random.uniform(0, math.pi * 2)
        })


def spawn_particles(x, y, color, count=10, speed=4, size_range=(2, 5)):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(1, speed)
        particles.append({
            'x': x, 'y': y,
            'vx': math.cos(angle) * spd,
            'vy': math.sin(angle) * spd,
            'life': 1.0,
            'decay': random.uniform(0.02, 0.05),
            'color': color,
            'size': random.randint(size_range[0], size_range[1])
        })


def update_and_draw_particles(surface, camera_x):
    for p in particles[:]:
        p['x'] += p['vx']
        p['y'] += p['vy']
        p['vy'] += 0.1
        p['life'] -= p['decay']

        if p['life'] <= 0:
            particles.remove(p)
            continue

        alpha = int(255 * p['life'])
        size = max(1, int(p['size'] * p['life']))

        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (*p['color'], alpha), (size, size), size)
        surface.blit(surf, (int(p['x'] - camera_x - size), int(p['y'] - size)))


def draw_glow(surface, center, radius, color, intensity=1.0, camera_x=0):
    glow_size = int(radius * 4)
    glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
    glow_center = glow_size // 2

    for i in range(6):
        r = radius + (i * radius // 2)
        alpha = int((60 - (i * 10)) * intensity)
        if alpha > 0:
            pygame.draw.circle(glow_surf, (*color, alpha), (glow_center, glow_center), r)

    surface.blit(glow_surf, (int(center[0] - camera_x - glow_center), int(center[1] - glow_center)))


def draw_background(screen, camera_x, time):
    screen.fill(DARK_BG)

    # 1. Мерцающие звёзды с параллаксом
    for star in stars:
        sx = (star['x'] - camera_x * star['parallax']) % WIDTH
        if sx < 0: sx += WIDTH

        # Вычисляем альфа-канал с защитой от отрицательных значений
        alpha = int(100 + 155 * math.sin(time * star['twinkle_speed'] + star['twinkle_offset']))
        alpha = max(0, min(255, alpha))

        # Размер звезды (минимум 1)
        size = max(1, int(star['size']))

        # Создаём поверхность с поддержкой прозрачности
        surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)

        # Рисуем круг с гарантированно корректными значениями
        color = (255, 255, 255, int(alpha))
        center = (size, size)

        pygame.draw.circle(surf, color, center, size)
        screen.blit(surf, (int(sx), int(star['y'])))

    # 2. Сетка на заднем плане
    offset = int(camera_x * 0.5) % 50
    for x in range(-offset, WIDTH, 50):
        pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, 50):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (WIDTH, y))


def draw_text_center(screen, text, font, color, y, glow=False, intensity=0.3):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    if glow:
        draw_glow(screen, rect.center, 120, color, intensity, camera_x=0)
    screen.blit(surf, rect)


def draw_menu_screen(screen, time):
    draw_background(screen, 0, time)

    # Декоративное вращающееся неоновое кольцо
    ring_radius = 130
    ring_surf = pygame.Surface((ring_radius * 2, ring_radius * 2), pygame.SRCALPHA)
    center = ring_radius
    for i in range(0, 360, 12):
        angle = math.radians(i + time * 0.8)
        x1 = center + math.cos(angle) * (ring_radius - 12)
        y1 = center + math.sin(angle) * (ring_radius - 12)
        x2 = center + math.cos(angle) * (ring_radius + 12)
        y2 = center + math.sin(angle) * (ring_radius + 12)
        color = CYAN if i % 24 == 0 else (100, 100, 255, 150)
        pygame.draw.line(ring_surf, color, (x1, y1), (x2, y2), 4)
    screen.blit(ring_surf, (WIDTH // 2 - ring_radius, 170 - ring_radius))

    draw_text_center(screen, "GRAVITY FLIP", pygame.font.SysFont("segoeui", 72), CYAN, 170, glow=True, intensity=0.6)
    draw_text_center(screen, "Неоновый платформер с физикой", pygame.font.SysFont("segoeui", 28), WHITE, 260)

    pulse = 0.6 + 0.4 * math.sin(time * 0.1)
    draw_text_center(screen, "Нажми ENTER чтобы начать", pygame.font.SysFont("segoeui", 32), YELLOW, 370, glow=True,
                     intensity=pulse)

    draw_text_center(screen, "A/D — движение  |  ПРОБЕЛ — прыжок  |  G — гравитация",
                     pygame.font.SysFont("segoeui", 20), (150, 150, 170), 460)
    draw_text_center(screen, "Исследуй процедурно-генерируемые уровни", pygame.font.SysFont("segoeui", 20),
                     (150, 150, 170), 490)


def draw_game_over_screen(screen, player, level, time, camera_x):
    draw_background(screen, camera_x, time)

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 10, 20, 220))
    screen.blit(overlay, (0, 0))

    draw_glow(screen, (WIDTH // 2, 180), 150, RED, 0.5, camera_x=0)
    draw_text_center(screen, "GAME OVER", pygame.font.SysFont("segoeui", 72), RED, 180, glow=True, intensity=0.6)

    # Стильная панель статистики
    box_w, box_h = 420, 150
    box_x, box_y = WIDTH // 2 - box_w // 2, 250
    box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box_surf.fill((20, 20, 35, 230))
    pygame.draw.rect(box_surf, RED, (0, 0, box_w, box_h), 3, border_radius=10)
    pygame.draw.rect(box_surf, (40, 40, 60, 100), (3, 3, box_w - 6, box_h - 6), border_radius=8)
    screen.blit(box_surf, (box_x, box_y))

    draw_text_center(screen, f"Итоговый счёт: {player.score}", pygame.font.SysFont("segoeui", 32), WHITE, 290)
    draw_text_center(screen, f"Достигнутый уровень: {level}", pygame.font.SysFont("segoeui", 28), YELLOW, 340)

    pulse = 0.6 + 0.4 * math.sin(time * 0.1)
    draw_text_center(screen, "Нажми ENTER, чтобы начать заново", pygame.font.SysFont("segoeui", 28), CYAN, 460,
                     glow=True, intensity=pulse)


def draw_ui(screen, player, font, small_font, level, time):
    # Верхняя панель
    panel_height = 50
    s = pygame.Surface((WIDTH, panel_height), pygame.SRCALPHA)
    s.fill((10, 10, 20, 210))
    screen.blit(s, (0, 0))

    # Неоновые границы панели
    pygame.draw.line(screen, CYAN, (0, panel_height), (WIDTH, panel_height), 2)
    pygame.draw.line(screen, (30, 30, 50), (0, 0), (WIDTH, 0), 1)

    # Нижняя панель подсказок
    s_bottom = pygame.Surface((WIDTH, 35), pygame.SRCALPHA)
    s_bottom.fill((10, 10, 20, 190))
    screen.blit(s_bottom, (0, HEIGHT - 35))
    pygame.draw.line(screen, CYAN, (0, HEIGHT - 35), (WIDTH, HEIGHT - 35), 2)

    # Вспомогательная функция для отрисовки статистики с иконкой
    def draw_stat(text, x, color, icon_color):
        surf = font.render(text, True, color)
        screen.blit(surf, (x, 13))
        if icon_color:
            pygame.draw.rect(screen, icon_color, (x - 22, 18, 14, 14), border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255, 100), (x - 22, 18, 14, 14), 1, border_radius=4)

    draw_stat(f"Очки: {player.score}", 30, WHITE, YELLOW)

    if player.combo >= 3:
        combo_multiplier = min(1 + player.combo // 3, 5)
        combo_text = font.render(f"Комбо x{combo_multiplier}!", True, YELLOW)
        draw_glow(screen, (230, 25), 40, YELLOW, 0.6, camera_x=0)
        screen.blit(combo_text, (210, 13))

    draw_stat(f"Жизни: {player.lives}/{player.max_lives}", 420, RED if player.lives <= 1 else WHITE, RED)
    draw_stat(f"Гравитация: {player.gravity_charges}/{player.max_gravity_charges}", 640, CYAN, CYAN)
    draw_stat(f"Уровень: {level}", 860, YELLOW, PURPLE)

    hint = small_font.render("A/D — движение  |  ПРОБЕЛ — прыжок  |  G — переворот гравитации", True, (150, 150, 170))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 25))


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 32
        self.height = 42
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.facing_right = True

        self.anim_timer = 0
        self.vel_x = 0

        self._draw_player()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.vel_y = 0
        self.speed = 4.0
        self.jump_power = -13
        self.gravity = 0.55
        self.gravity_dir = 1

        self.on_ground = False
        self.jumps_left = 2
        self.max_jumps = 2

        self.gravity_charges = 3
        self.max_gravity_charges = 3
        self.flip_cooldown = 0

        self.lives = 3
        self.max_lives = 5
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.invincible = 0

        self.on_moving_platform = None
        self.dying = False
        self.death_timer = 0
        self.death_duration = 45

    def _draw_player(self):
        self.image.fill((0, 0, 0, 0))
        pygame.draw.rect(self.image, (30, 60, 120), (4, 8, 24, 28), border_radius=8)
        pygame.draw.rect(self.image, BLUE, (6, 10, 20, 24), border_radius=6)

        pulse = int(10 + 5 * math.sin(self.anim_timer * 0.2))
        pygame.draw.circle(self.image, LIGHT_BLUE, (16, 18), pulse)
        pygame.draw.circle(self.image, WHITE, (16, 18), 4)

        eye_offset = 4 if self.facing_right else -4
        pygame.draw.ellipse(self.image, WHITE, (10 + eye_offset, 14, 12, 8))
        pygame.draw.circle(self.image, BLACK, (12 + eye_offset + (2 if self.facing_right else -2), 18), 3)

        leg_offset = 2 if self.vel_x != 0 and int(self.anim_timer * 0.5) % 2 == 0 else 0
        pygame.draw.rect(self.image, (40, 80, 180), (6, 34, 8, 8 + leg_offset), border_radius=3)
        pygame.draw.rect(self.image, (40, 80, 180), (18, 34, 8, 8 - leg_offset), border_radius=3)

    def flip_gravity(self):
        if not self.dying and self.gravity_charges > 0 and self.flip_cooldown <= 0:
            self.gravity_dir *= -1
            self.gravity_charges -= 1
            self.flip_cooldown = 20
            self.vel_y = 0
            self.jumps_left = self.max_jumps
            self.on_moving_platform = None
            spawn_particles(self.rect.centerx, self.rect.centery, CYAN, count=15, speed=5)
            return True
        return False

    def jump(self):
        if not self.dying and self.jumps_left > 0:
            self.vel_y = self.jump_power * self.gravity_dir
            self.jumps_left -= 1
            self.on_ground = False
            self.on_moving_platform = None
            spawn_particles(self.rect.centerx, self.rect.bottom if self.gravity_dir == 1 else self.rect.top,
                            (200, 200, 200), count=5, speed=2, size_range=(1, 3))

    def take_damage(self):
        if self.invincible > 0 or self.dying:
            return
        self.lives -= 1
        self.combo = 0
        if self.lives <= 0:
            self.dying = True
            self.death_timer = self.death_duration
            self.vel_x = 0
            self.vel_y = -4 * self.gravity_dir
            self.on_moving_platform = None
            spawn_particles(self.rect.centerx, self.rect.centery, BLUE, count=30, speed=6)
        else:
            self.invincible = 90
            spawn_particles(self.rect.centerx, self.rect.centery, RED, count=10, speed=3)

    def update_death(self):
        if not self.dying:
            return False
        self.vel_y += 0.3 * self.gravity_dir
        self.rect.y += int(self.vel_y)
        self.death_timer -= 1
        if self.death_timer % 3 == 0:
            spawn_particles(self.rect.centerx, self.rect.centery, BLUE, count=2, speed=1)
        return self.death_timer <= 0

    def get_death_image(self):
        progress = self.death_timer / self.death_duration
        angle = (1 - progress) * 540 * self.gravity_dir
        image = pygame.transform.rotate(self.image, angle)
        image.set_alpha(max(0, int(255 * progress)))
        return image

    def respawn(self, platforms):
        self.dying = False
        self.death_timer = 0
        self.gravity_dir = 1
        self.vel_x = 0
        self.vel_y = 0
        self.invincible = 90
        self.jumps_left = self.max_jumps

        if self.lives <= 0:
            self.lives = 3
            self.score = max(0, self.score - 100)
            self.gravity_charges = self.max_gravity_charges
            self.rect.topleft = (100, 458)
            self.on_ground = False
            return

        self._respawn_on_nearest_platform(platforms)

    def _respawn_on_nearest_platform(self, platforms):
        player_cx = self.rect.centerx
        best_plat = None
        best_score = float('inf')

        for p in platforms:
            dx = abs(p.rect.centerx - player_cx)
            if dx > 500: continue
            dy = abs(p.rect.centery - self.rect.centery)
            score = dx + dy * 0.5
            if score < best_score:
                best_score = score
                best_plat = p

        if best_plat:
            self.rect.midbottom = (best_plat.rect.centerx, best_plat.rect.top - 2) if self.gravity_dir == 1 else (
                best_plat.rect.centerx, best_plat.rect.bottom + 2)
            self.on_ground = True
            self.jumps_left = self.max_jumps
        else:
            self.rect.topleft = (100, 458)
            self.on_ground = False

    def add_score(self, points):
        self.combo += 1
        self.combo_timer = 120
        multiplier = min(1 + self.combo // 3, 5)
        self.score += points * multiplier

    def update(self, platforms, enemies, coins, crystals, hearts, camera_x):
        if self.dying:
            return

        self.anim_timer += 1
        keys = pygame.key.get_pressed()
        move_x = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            move_x -= self.speed
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            move_x += self.speed
            self.facing_right = True

        self.vel_x = move_x
        carried_platform = self.on_moving_platform
        carried_ok = False

        if carried_platform is not None and carried_platform in platforms:
            self.rect.x += int(round(carried_platform.dx))
            self.rect.y += int(round(carried_platform.dy))
            horizontal_overlap = (
                        self.rect.right > carried_platform.rect.left and self.rect.left < carried_platform.rect.right)
            if self.gravity_dir == 1:
                supported = abs(self.rect.bottom - carried_platform.rect.top) <= 2
            else:
                supported = abs(self.rect.top - carried_platform.rect.bottom) <= 2
            carried_ok = horizontal_overlap and supported
            if carried_ok:
                self.on_ground = True
                self.vel_y = 0
            else:
                self.on_moving_platform = None
        else:
            self.on_moving_platform = None

        self._move_axis(move_x, 0, platforms)
        left_limit = max(0, int(camera_x))
        if self.rect.left < left_limit:
            self.rect.left = left_limit

        if not carried_ok:
            self.on_ground = False
            self.vel_y += self.gravity * self.gravity_dir
            max_fall = 14
            if self.gravity_dir == 1:
                self.vel_y = min(self.vel_y, max_fall)
            else:
                self.vel_y = max(self.vel_y, -max_fall)
            self._move_axis(0, self.vel_y, platforms)

        if not self.on_ground:
            for platform in platforms:
                horizontal_overlap = (self.rect.right > platform.rect.left and self.rect.left < platform.rect.right)
                if not horizontal_overlap: continue
                if self.gravity_dir == 1 and abs(self.rect.bottom - platform.rect.top) <= 2:
                    self.on_ground = True
                    self.vel_y = 0
                    self.jumps_left = self.max_jumps
                    if platform.moving: self.on_moving_platform = platform
                    break
                if self.gravity_dir == -1 and abs(self.rect.top - platform.rect.bottom) <= 2:
                    self.on_ground = True
                    self.vel_y = 0
                    self.jumps_left = self.max_jumps
                    if platform.moving: self.on_moving_platform = platform
                    break

        if self.rect.top > HEIGHT + 100 or self.rect.bottom < -100:
            if self.invincible <= 0: self.take_damage()
            if self.dying:
                self.rect.y = max(0, min(self.rect.y, HEIGHT - self.height))
                return
            self._respawn_on_nearest_platform(platforms)
            self.gravity_dir = 1
            self.on_moving_platform = None
            return

        if self.flip_cooldown > 0: self.flip_cooldown -= 1
        if self.invincible > 0: self.invincible -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        for enemy in list(enemies):
            if self.rect.colliderect(enemy.rect) and self.invincible <= 0:
                if self._platform_blocks_line(enemy, platforms): continue
                if not enemy.spiked and self._can_stomp(enemy):
                    enemy.kill()
                    self.vel_y = self.jump_power * self.gravity_dir * 0.7
                    self.on_ground = False
                    self.on_moving_platform = None
                    self.add_score(50)
                    spawn_particles(enemy.rect.centerx, enemy.rect.centery,
                                    enemy.color if hasattr(enemy, 'color') else ORANGE, count=15, speed=5)
                else:
                    self.take_damage()
                    return

        for coin in pygame.sprite.spritecollide(self, coins, True):
            self.add_score(10)
            spawn_particles(coin.rect.centerx, coin.rect.centery, YELLOW, count=8, speed=3)
        for crystal in pygame.sprite.spritecollide(self, crystals, True):
            self.gravity_charges = min(self.gravity_charges + 1, self.max_gravity_charges)
            self.add_score(25)
            spawn_particles(crystal.rect.centerx, crystal.rect.centery, CYAN, count=12, speed=4)
        for heart in list(hearts):
            if self.rect.colliderect(heart.rect) and self.lives < self.max_lives:
                heart.kill()
                self.lives += 1
                self.add_score(50)
                spawn_particles(heart.rect.centerx, heart.rect.centery, RED, count=15, speed=4)

        self._draw_player()
        if self.invincible > 0 and (self.invincible // 4) % 2 == 0:
            self.image.set_alpha(100)
        else:
            self.image.set_alpha(255)

    def _move_axis(self, dx, dy, platforms):
        amount = dx if dx else dy
        if amount == 0: return
        steps = max(1, int(math.ceil(abs(amount))))
        step = 1 if amount > 0 else -1
        horizontal = dx != 0

        for _ in range(steps):
            if horizontal:
                self.rect.x += step
            else:
                self.rect.y += step
            hit = False
            for platform in platforms:
                if not self.rect.colliderect(platform.rect): continue
                hit = True
                if horizontal:
                    if step > 0:
                        self.rect.right = platform.rect.left
                    else:
                        self.rect.left = platform.rect.right
                    self.vel_x = 0
                else:
                    if step > 0:
                        self.rect.bottom = platform.rect.top
                        if self.gravity_dir == 1:
                            self.on_ground = True
                            self.jumps_left = self.max_jumps
                            if platform.moving: self.on_moving_platform = platform
                    else:
                        self.rect.top = platform.rect.bottom
                        if self.gravity_dir == -1:
                            self.on_ground = True
                            self.jumps_left = self.max_jumps
                            if platform.moving: self.on_moving_platform = platform
                    self.vel_y = 0
                break
            if hit: break

    def _platform_blocks_line(self, enemy, platforms):
        for platform in platforms:
            if platform.rect.clipline(self.rect.center, enemy.rect.center):
                return True
        return False

    def _can_stomp(self, enemy):
        if enemy.spiked: return False
        if self.gravity_dir == 1:
            return self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 10
        return self.vel_y < 0 and self.rect.top > enemy.rect.centery - 10


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, moving=False, move_range=0, move_speed=2, axis="x"):
        super().__init__()
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, PLATFORM_COLOR, (0, 0, w, h), border_radius=4)
        pygame.draw.rect(self.image, PLATFORM_BORDER, (2, 2, w - 4, h - 4), border_radius=3)
        pygame.draw.line(self.image, PLATFORM_NEON, (4, 2), (w - 4, 2), 3)
        for i in range(0, w, 20):
            pygame.draw.circle(self.image, (60, 70, 90), (i + 10, h // 2), 3)

        self.rect = self.image.get_rect(topleft=(x, y))
        self.moving = moving
        self.start_x = x
        self.start_y = y
        self.move_range = move_range
        self.move_speed = move_speed
        self.axis = axis
        self.direction = 1
        self.dx = 0
        self.dy = 0

    def update(self):
        self.dx = 0
        self.dy = 0
        if not self.moving: return
        old_x, old_y = self.rect.x, self.rect.y
        if self.axis == "x":
            self.rect.x += self.move_speed * self.direction
            if abs(self.rect.x - self.start_x) >= self.move_range: self.direction *= -1
        else:
            self.rect.y += self.move_speed * self.direction
            if abs(self.rect.y - self.start_y) >= self.move_range: self.direction *= -1
        self.dx = self.rect.x - old_x
        self.dy = self.rect.y - old_y


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, spiked=False, patrol_range=80, move_type="walk"):
        super().__init__()
        self.spiked = spiked
        self.move_type = move_type
        self.image = pygame.Surface((36, 30), pygame.SRCALPHA)
        self.color = PURPLE if move_type == "fly" else (RED if spiked else ORANGE)

        self.anim_timer = 0
        self._draw()

        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.start_y = y
        self.patrol_range = patrol_range
        self.min_x = x - patrol_range
        self.max_x = x + patrol_range
        self.speed = 1.5 if not spiked else 1.0
        self.direction = 1
        self.vel_y = 0
        self.jump_timer = random.randint(40, 100)
        self.fly_angle = random.uniform(0, math.pi * 2)
        self.fly_speed = random.uniform(0.04, 0.08)
        self.fly_amplitude = random.randint(25, 50)
        self.fly_vx = random.choice((-1, 1)) * random.uniform(1.0, 1.7)
        self.fly_vy = random.choice((-1, 1)) * random.uniform(0.5, 1.1)
        self.fly_min_x = x - patrol_range
        self.fly_max_x = x + patrol_range
        self.fly_min_y = y - self.fly_amplitude
        self.fly_max_y = y + self.fly_amplitude
        self.dash_timer = random.randint(90, 160)
        self.is_dashing = False
        self.dash_time_left = 0

    def _draw(self):
        self.image.fill((0, 0, 0, 0))
        c = self.color
        pygame.draw.ellipse(self.image, (*c, 80), (-4, 0, 44, 30))
        pygame.draw.ellipse(self.image, c, (0, 4, 36, 26))
        pygame.draw.polygon(self.image, WHITE, [(6, 10), (16, 14), (6, 18)])
        pygame.draw.polygon(self.image, WHITE, [(30, 10), (20, 14), (30, 18)])
        pygame.draw.circle(self.image, BLACK, (10, 14), 2)
        pygame.draw.circle(self.image, BLACK, (26, 14), 2)

        if self.spiked:
            for i in range(5):
                sx = 4 + i * 7
                pygame.draw.polygon(self.image, (150, 30, 30), [(sx, 8), (sx + 3, -2), (sx + 6, 8)])
        elif self.move_type == "fly":
            wing_offset = int(4 * math.sin(self.anim_timer * 0.3))
            pygame.draw.polygon(self.image, (220, 180, 255), [(-6, 12 + wing_offset), (-6, 2), (4, 12)])
            pygame.draw.polygon(self.image, (220, 180, 255), [(42, 12 - wing_offset), (42, 2), (32, 12)])

    def update(self, platforms):
        self.anim_timer += 1
        if self.move_type == "fly":
            self._update_fly(platforms)
        elif self.move_type == "jump":
            self._update_jump(platforms)
        elif self.move_type == "dash":
            self._update_dash(platforms)
        else:
            self._update_walk(platforms)

    def _move_with_platform_collisions(self, dx, dy, platforms):
        hit_x = hit_y = False
        move_x = int(round(dx))
        if move_x:
            step_x = 1 if move_x > 0 else -1
            for _ in range(abs(move_x)):
                self.rect.x += step_x
                for platform in platforms:
                    if self.rect.colliderect(platform.rect):
                        if step_x > 0:
                            self.rect.right = platform.rect.left
                        else:
                            self.rect.left = platform.rect.right
                        hit_x = True
                        break
                if hit_x: break
        move_y = int(round(dy))
        if move_y:
            step_y = 1 if move_y > 0 else -1
            for _ in range(abs(move_y)):
                self.rect.y += step_y
                for platform in platforms:
                    if self.rect.colliderect(platform.rect):
                        if step_y > 0:
                            self.rect.bottom = platform.rect.top
                        else:
                            self.rect.top = platform.rect.bottom
                        hit_y = True
                        break
                if hit_y: break
        return hit_x, hit_y

    def _update_walk(self, platforms):
        dx = self.speed * self.direction
        hit_x, _ = self._move_with_platform_collisions(dx, 0, platforms)
        if hit_x or self.rect.x <= self.min_x or self.rect.x >= self.max_x:
            self.direction *= -1
            self.rect.x = max(self.min_x, min(self.rect.x, self.max_x))
        self._keep_on_platform(platforms)

    def _update_jump(self, platforms):
        dx = self.speed * self.direction
        hit_x, _ = self._move_with_platform_collisions(dx, 0, platforms)
        if hit_x or self.rect.x <= self.min_x or self.rect.x >= self.max_x:
            self.direction *= -1
            self.rect.x = max(self.min_x, min(self.rect.x, self.max_x))
        self.jump_timer -= 1
        if self.jump_timer <= 0:
            self.vel_y = -8
            self.jump_timer = random.randint(70, 130)
        self.vel_y = min(self.vel_y + 0.4, 10)
        _, hit_y = self._move_with_platform_collisions(0, self.vel_y, platforms)
        if hit_y: self.vel_y = 0

    def _update_fly(self, platforms):
        self.fly_angle += self.fly_speed
        dx = self.fly_vx
        dy = self.fly_vy + math.sin(self.fly_angle) * 0.25
        hit_x, hit_y = self._move_with_platform_collisions(dx, dy, platforms)
        if hit_x: self.fly_vx *= -1
        if hit_y: self.fly_vy *= -1
        if self.rect.left <= self.fly_min_x:
            self.rect.left = self.fly_min_x
            self.fly_vx = abs(self.fly_vx)
        elif self.rect.right >= self.fly_max_x + self.image.get_width():
            self.rect.right = self.fly_max_x + self.image.get_width()
            self.fly_vx = -abs(self.fly_vx)
        if self.rect.top <= self.fly_min_y:
            self.rect.top = self.fly_min_y
            self.fly_vy = abs(self.fly_vy)
        elif self.rect.bottom >= self.fly_max_y + self.image.get_height():
            self.rect.bottom = self.fly_max_y + self.image.get_height()
            self.fly_vy = -abs(self.fly_vy)

    def _update_dash(self, platforms):
        if self.is_dashing:
            dx = self.speed * 3.5 * self.direction
            self.dash_time_left -= 1
            if self.dash_time_left <= 0:
                self.is_dashing = False
                self.dash_timer = random.randint(100, 180)
        else:
            dx = self.speed * self.direction
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.is_dashing = True
                self.dash_time_left = 18
        hit_x, _ = self._move_with_platform_collisions(dx, 0, platforms)
        if hit_x or self.rect.x <= self.min_x or self.rect.x >= self.max_x:
            self.direction *= -1
            self.is_dashing = False
            self.rect.x = max(self.min_x, min(self.rect.x, self.max_x))
        self._keep_on_platform(platforms)

    def _keep_on_platform(self, platforms):
        probe = self.rect.copy()
        probe.y += 2
        if not any(probe.colliderect(p.rect) for p in platforms):
            self.direction *= -1


class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((18, 18), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*YELLOW, 100), (9, 9), 9)
        pygame.draw.circle(self.image, YELLOW, (9, 9), 7)
        pygame.draw.circle(self.image, (255, 250, 200), (9, 9), 4)
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        self.bob = random.uniform(0, math.pi * 2)

    def update(self):
        self.bob += 0.12
        self.rect.y = self.start_y + int(4 * math.sin(self.bob))


class Crystal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((22, 28), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (*CYAN, 80), [(11, -2), (24, 14), (11, 30), (-2, 14)])
        pygame.draw.polygon(self.image, CYAN, [(11, 0), (22, 14), (11, 28), (0, 14)])
        pygame.draw.polygon(self.image, (200, 255, 255), [(11, 4), (18, 14), (11, 24), (4, 14)])
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        self.bob = random.uniform(0, math.pi * 2)

    def update(self):
        self.bob += 0.10
        self.rect.y = self.start_y + int(5 * math.sin(self.bob))


class Heart(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((28, 26), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (8, 8), 8)
        pygame.draw.circle(self.image, RED, (20, 8), 8)
        pygame.draw.polygon(self.image, RED, [(1, 11), (27, 11), (14, 26)])
        pygame.draw.circle(self.image, (255, 150, 160), (7, 6), 3)
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        self.bob = random.uniform(0, math.pi * 2)

    def update(self):
        self.bob += 0.10
        self.rect.y = self.start_y + int(5 * math.sin(self.bob))


class Door(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((48, 70), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (100, 50, 160), (3, 2, 42, 68), border_radius=8)
        pygame.draw.rect(self.image, (190, 130, 255), (8, 7, 32, 63), 3, border_radius=6)
        pygame.draw.ellipse(self.image, (100, 240, 255), (13, 13, 22, 48))
        pygame.draw.circle(self.image, YELLOW, (34, 39), 4)
        self.rect = self.image.get_rect(bottomleft=(x, y))
        self.base_y = self.rect.y - 3
        self.bob = 0.0

    def update(self):
        self.bob += 0.05
        self.rect.y = self.base_y + int(2 * math.sin(self.bob))


def create_level():
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    crystals = pygame.sprite.Group()
    hearts = pygame.sprite.Group()
    heart_platforms = []

    platforms.add(Platform(0, 500, 400, 50))
    current_x = 400
    last_y = 500

    while current_x < LEVEL_WIDTH - 400:
        gap = random.randint(50, 100)
        next_x = current_x + gap
        dy = random.randint(-80, 80)
        next_y = max(200, min(500, last_y + dy))
        width = random.randint(120, 200)

        platform = Platform(next_x, next_y, width, 20)
        platforms.add(platform)
        heart_platforms.append(platform)

        if random.random() < 0.85:
            e_w = 36
            ex = next_x + random.randint(20, max(20, width - e_w - 20))
            ey = next_y - 30
            spiked = random.random() < 0.3
            move_type = random.choice(["walk", "jump", "fly", "dash"])
            if spiked: move_type = random.choice(["walk", "dash"])
            patrol = max(20, min(width // 2 - 20, 60))
            enemies.add(Enemy(ex, ey, spiked=spiked, patrol_range=patrol, move_type=move_type))

        if random.random() < 0.4:
            m_w = random.randint(70, 100)
            m_y = next_y - random.randint(70, 120)
            m_x = next_x + random.randint(10, max(10, width - m_w - 10))
            platforms.add(
                Platform(m_x, m_y, m_w, 16, moving=True, move_range=50, move_speed=random.uniform(1.5, 2.5), axis="x"))
            if random.random() < 0.6:
                coins.add(Coin(m_x + m_w // 2, m_y - 25))

        for i in range(random.randint(1, 3)):
            cx = next_x + 30 + i * (width // 3)
            if cx < next_x + width - 20:
                coins.add(Coin(cx, next_y - 35))

        if random.random() < 0.25:
            crystals.add(Crystal(next_x + width // 2, next_y - 70))

        current_x = next_x + width
        last_y = next_y

    if heart_platforms:
        heart_platform = random.choice(heart_platforms)
        hearts.add(Heart(heart_platform.rect.centerx, heart_platform.rect.top - 35))

    finish_x = LEVEL_WIDTH - 300
    platforms.add(Platform(finish_x, 450, 300, 50))
    door = Door(LEVEL_WIDTH - 100, 450)

    return platforms, enemies, coins, crystals, hearts, door


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("segoeui", 28)
    big_font = pygame.font.SysFont("segoeui", 72)
    small_font = pygame.font.SysFont("segoeui", 20)

    init_stars()

    state = "menu"
    camera_x = 0.0
    level = 1
    shake = 0
    frame_time = 0

    player = platforms = enemies = coins = crystals = hearts = door = None

    def start_game():
        nonlocal player, platforms, enemies, coins, crystals, hearts, door, state, camera_x, level, shake, frame_time
        player = Player(100, 458)
        platforms, enemies, coins, crystals, hearts, door = create_level()
        camera_x = 0.0
        level = 1
        shake = 0
        frame_time = 0
        state = "playing"
        particles.clear()

    def next_level():
        nonlocal platforms, enemies, coins, crystals, hearts, door, camera_x, level
        level += 1
        platforms, enemies, coins, crystals, hearts, door = create_level()
        player.rect.topleft = (100, 458)
        player.vel_x = 0
        player.vel_y = 0
        player.gravity_dir = 1
        player.gravity_charges = player.max_gravity_charges
        player.jumps_left = player.max_jumps
        player.on_ground = False
        player.on_moving_platform = None
        player.invincible = 90
        player.dying = False
        camera_x = 0.0
        spawn_particles(player.rect.centerx, player.rect.centery, GREEN, count=30, speed=5)

    running = True
    while running:
        clock.tick(FPS)
        frame_time += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if state == "menu" and event.key == pygame.K_RETURN:
                    start_game()
                elif state == "game_over" and event.key == pygame.K_RETURN:
                    start_game()
                elif state == "playing" and not player.dying:
                    if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                        player.jump()
                    if event.key == pygame.K_g:
                        player.flip_gravity()

        if state == "playing":
            if player.dying:
                if player.update_death():
                    state = "game_over"
                    shake = 15
            else:
                platforms.update()
                enemies.update(platforms)
                coins.update()
                crystals.update()
                hearts.update()
                door.update()
                player.update(platforms, enemies, coins, crystals, hearts, camera_x)

                if not player.dying and player.rect.colliderect(door.rect):
                    next_level()

                target = player.rect.centerx - WIDTH // 3
                if target > camera_x:
                    camera_x += (target - camera_x) * 0.09
                camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))

                if shake > 0:
                    shake -= 1

        # --- ОТРИСОВКА ---
        if state == "menu":
            draw_menu_screen(screen, frame_time)

        elif state == "playing":
            draw_background(screen, camera_x, frame_time)

            offset_x = random.randint(-shake, shake) if shake > 0 else 0
            offset_y = random.randint(-shake, shake) if shake > 0 else 0

            for platform in platforms:
                screen.blit(platform.image, (platform.rect.x - camera_x + offset_x, platform.rect.y + offset_y))

            for coin in coins:
                draw_glow(screen, coin.rect.center, 12, YELLOW, 0.6, camera_x)
                screen.blit(coin.image, (coin.rect.x - camera_x + offset_x, coin.rect.y + offset_y))

            for crystal in crystals:
                draw_glow(screen, crystal.rect.center, 16, CYAN, 0.8, camera_x)
                screen.blit(crystal.image, (crystal.rect.x - camera_x + offset_x, crystal.rect.y + offset_y))

            for heart in hearts:
                draw_glow(screen, heart.rect.center, 16, RED, 0.6, camera_x)
                screen.blit(heart.image, (heart.rect.x - camera_x + offset_x, heart.rect.y + offset_y))

            for enemy in enemies:
                draw_glow(screen, enemy.rect.center, 20, enemy.color, 0.4, camera_x)
                screen.blit(enemy.image, (enemy.rect.x - camera_x + offset_x, enemy.rect.y + offset_y))

            screen.blit(door.image, (door.rect.x - camera_x + offset_x, door.rect.y + offset_y))

            update_and_draw_particles(screen, camera_x)

            if player.dying:
                death_image = player.get_death_image()
                death_rect = death_image.get_rect(
                    center=(player.rect.centerx - camera_x + offset_x, player.rect.centery + offset_y))
                screen.blit(death_image, death_rect)
            else:
                draw_glow(screen, player.rect.center, 25, BLUE, 0.5, camera_x)
                screen.blit(player.image, (player.rect.x - camera_x + offset_x, player.rect.y + offset_y))

            if player.gravity_dir == -1:
                pygame.draw.polygon(screen, CYAN, [(WIDTH - 40, 70), (WIDTH - 20, 70), (WIDTH - 30, 50)])
            else:
                pygame.draw.polygon(screen, CYAN, [(WIDTH - 40, 50), (WIDTH - 20, 50), (WIDTH - 30, 70)])

            draw_ui(screen, player, font, small_font, level, frame_time)

        elif state == "game_over":
            draw_game_over_screen(screen, player, level, frame_time, camera_x)
            update_and_draw_particles(screen, camera_x)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()