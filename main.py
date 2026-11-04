
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
PURPLE = (160, 80, 220)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 32
        self.height = 42
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.facing_right = True
        self._draw_player()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
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
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.invincible = 0
        self.on_moving_platform = None

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
            self.on_moving_platform = None
            return True
        return False

    def jump(self):
        if self.jumps_left > 0:
            self.vel_y = self.jump_power * self.gravity_dir
            self.jumps_left -= 1
            self.on_ground = False
            self.on_moving_platform = None

    def _respawn_on_nearest_platform(self, platforms):
        player_cx = self.rect.centerx
        best_plat = None
        best_score = float('inf')

        for p in platforms:
            dx = abs(p.rect.centerx - player_cx)
            if dx > 500:
                continue
            dy = abs(p.rect.centery - self.rect.centery)
            score = dx + dy * 0.5
            if score < best_score:
                best_score = score
                best_plat = p

        if best_plat:
            if self.gravity_dir == 1:
                self.rect.midbottom = (best_plat.rect.centerx, best_plat.rect.top - 2)
            else:
                self.rect.midtop = (best_plat.rect.centerx, best_plat.rect.bottom + 2)
            self.vel_y = 0
            self.vel_x = 0
            self.on_ground = True
            self.jumps_left = self.max_jumps
        else:
            self.rect.topleft = (100, 400)
            self.vel_y = 0

    def take_damage(self):
        if self.invincible <= 0:
            self.lives -= 1
            self.invincible = 90
            self.combo = 0
            self.on_moving_platform = None
            return True
        return False

    def add_score(self, points):
        self.combo += 1
        self.combo_timer = 120
        multiplier = min(1 + self.combo // 3, 5)
        self.score += points * multiplier

    def update(self, platforms, enemies, coins, crystals, camera_x):
        keys = pygame.key.get_pressed()

        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True

        self.vel_y += self.gravity * self.gravity_dir
        max_fall = 14

        if self.gravity_dir == 1:
            self.vel_y = min(self.vel_y, max_fall)
        else:
            self.vel_y = max(self.vel_y, -max_fall)

        if self.on_moving_platform is not None:
            plat = self.on_moving_platform
            self.rect.x += plat.dx
            self.rect.y += plat.dy

        self.rect.x += int(self.vel_x)
        self._collide_platforms(platforms, "x")

        left_limit = int(camera_x)
        if self.rect.left < left_limit:
            self.rect.left = left_limit
        if self.rect.left < 0:
            self.rect.left = 0

        self.rect.y += int(self.vel_y)
        self.on_ground = False
        self.on_moving_platform = None
        self._collide_platforms(platforms, "y")

        if self.rect.top > HEIGHT + 100 or self.rect.bottom < -100:
            self.take_damage()
            self._respawn_on_nearest_platform(platforms)
            self.gravity_dir = 1

        if self.flip_cooldown > 0:
            self.flip_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 0

        for enemy in list(enemies):
            if self.rect.colliderect(enemy.rect) and self.invincible <= 0:
                if not enemy.spiked and self._can_stomp(enemy):
                    enemy.kill()
                    self.vel_y = self.jump_power * self.gravity_dir * 0.7
                    self.add_score(50)
                else:
                    self.take_damage()

        for coin in pygame.sprite.spritecollide(self, coins, True):
            self.add_score(10)

        for crystal in pygame.sprite.spritecollide(self, crystals, True):
            self.gravity_charges = min(self.gravity_charges + 1, self.max_gravity_charges)
            self.add_score(25)

        self._draw_player()

        if self.invincible > 0 and (self.invincible // 5) % 2 == 0:
            self.image.set_alpha(120)
        else:
            self.image.set_alpha(255)

    def _can_stomp(self, enemy):
        if enemy.spiked:
            return False
        if self.gravity_dir == 1:
            return self.vel_y > 0 and self.rect.bottom < enemy.rect.centery + 10
        return self.vel_y < 0 and self.rect.top > enemy.rect.centery - 10

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
                            if platform.moving:
                                self.on_moving_platform = platform
                        elif self.vel_y < 0:
                            self.rect.top = platform.rect.bottom
                            self.vel_y = 0
                    else:
                        if self.vel_y < 0:
                            self.rect.top = platform.rect.bottom
                            self.vel_y = 0
                            self.on_ground = True
                            self.jumps_left = self.max_jumps
                            if platform.moving:
                                self.on_moving_platform = platform
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
        self.dx = 0
        self.dy = 0

    def update(self):
        self.dx = 0
        self.dy = 0
        if not self.moving:
            return

        old_x, old_y = self.rect.x, self.rect.y

        if self.axis == "x":
            self.rect.x += self.move_speed * self.direction
            if abs(self.rect.x - self.start_x) >= self.move_range:
                self.direction *= -1
        else:
            self.rect.y += self.move_speed * self.direction
            if abs(self.rect.y - self.start_y) >= self.move_range:
                self.direction *= -1

        self.dx = self.rect.x - old_x
        self.dy = self.rect.y - old_y


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, spiked=False, patrol_range=80, move_type="walk"):
        super().__init__()
        self.spiked = spiked
        self.move_type = move_type
        self.image = pygame.Surface((36, 30), pygame.SRCALPHA)
        self._draw()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.start_x = x
        self.start_y = y
        self.patrol_range = patrol_range
        self.speed = 1.5 if not spiked else 1.0
        self.direction = 1
        self.vel_y = 0
        self.jump_timer = random.randint(40, 100)
        self.fly_angle = random.uniform(0, math.pi * 2)
        self.fly_speed = random.uniform(0.04, 0.08)
        self.fly_amplitude = random.randint(25, 50)
        self.dash_timer = random.randint(90, 160)
        self.is_dashing = False
        self.dash_time_left = 0

    def _draw(self):
        self.image.fill((0, 0, 0, 0))

        if self.move_type == "fly":
            color = PURPLE
        elif self.spiked:
            color = RED
        else:
            color = ORANGE

        pygame.draw.ellipse(self.image, color, (0, 4, 36, 26))
        pygame.draw.circle(self.image, WHITE, (12, 14), 5)
        pygame.draw.circle(self.image, WHITE, (24, 14), 5)
        pygame.draw.circle(self.image, BLACK, (13, 14), 2)
        pygame.draw.circle(self.image, BLACK, (25, 14), 2)

        if self.spiked:
            for i in range(5):
                sx = 4 + i * 7
                pygame.draw.polygon(
                    self.image, (180, 40, 40),
                    [(sx, 8), (sx + 3, 0), (sx + 6, 8)]
                )
        elif self.move_type == "fly":
            pygame.draw.polygon(self.image, (200, 150, 255), [(0, 12), (0, 6), (0, 18)])
            pygame.draw.polygon(self.image, (200, 150, 255), [(36, 12), (36, 6), (36, 18)])

    def update(self, platforms):
        if self.move_type == "fly":
            self._update_fly()
        elif self.move_type == "jump":
            self._update_jump(platforms)
        elif self.move_type == "dash":
            self._update_dash(platforms)
        else:
            self._update_walk(platforms)

    def _update_walk(self, platforms):
        self.rect.x += self.speed * self.direction

        if abs(self.rect.x - self.start_x) >= self.patrol_range:
            self.direction *= -1
            self.rect.x = self.start_x + self.patrol_range * (1 if self.direction < 0 else -1)

        self._keep_on_platform(platforms)

    def _update_jump(self, platforms):
        self.rect.x += self.speed * self.direction

        if abs(self.rect.x - self.start_x) >= self.patrol_range:
            self.direction *= -1

        self.jump_timer -= 1
        if self.jump_timer <= 0:
            self.vel_y = -8
            self.jump_timer = random.randint(70, 130)

        self.vel_y += 0.4
        self.rect.y += int(self.vel_y)

        for p in platforms:
            if self.rect.colliderect(p.rect) and self.vel_y > 0:
                self.rect.bottom = p.rect.top
                self.vel_y = 0
                break

    def _update_fly(self):
        self.fly_angle += self.fly_speed
        self.rect.x = int(self.start_x + math.sin(self.fly_angle * 0.7) * self.patrol_range)
        self.rect.y = int(self.start_y + math.sin(self.fly_angle) * self.fly_amplitude)

    def _update_dash(self, platforms):
        if self.is_dashing:
            self.rect.x += self.speed * 3.5 * self.direction
            self.dash_time_left -= 1

            if self.dash_time_left <= 0:
                self.is_dashing = False
                self.dash_timer = random.randint(100, 180)
        else:
            self.rect.x += self.speed * self.direction
            self.dash_timer -= 1

            if self.dash_timer <= 0:
                self.is_dashing = True
                self.dash_time_left = 18

        if abs(self.rect.x - self.start_x) >= self.patrol_range + 20:
            self.direction *= -1
            self.is_dashing = False
            self.rect.x = self.start_x + (self.patrol_range + 20) * (1 if self.direction < 0 else -1)

        self._keep_on_platform(platforms)

    def _keep_on_platform(self, platforms):
        self.rect.y += 4
        on_platform = any(self.rect.colliderect(p.rect) for p in platforms)
        self.rect.y -= 4

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
        self.rect.y = self.start_y + int(4 * math.sin(self.bob))


class Crystal(pygame.sprite.Sprite):
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
        self.rect.y = self.start_y + int(5 * math.sin(self.bob))


class Goal(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((36, 60), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (180, 180, 180), (14, 0, 8, 60))
        pygame.draw.polygon(self.image, GREEN, [(22, 4), (36, 16), (22, 28)])
        self.rect = self.image.get_rect(bottomleft=(x, y))


def create_level():
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    coins = pygame.sprite.Group()
    crystals = pygame.sprite.Group()

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

        if random.random() < 0.85:
            e_w = 36
            ex = next_x + random.randint(20, max(20, width - e_w - 20))
            ey = next_y - 30
            spiked = random.random() < 0.3
            move_type = random.choice(["walk", "jump", "fly", "dash"])

            if spiked:
                move_type = random.choice(["walk", "dash"])

            patrol = max(20, min(width // 2 - 20, 60))
            enemies.add(Enemy(ex, ey, spiked, patrol, move_type))

        if random.random() < 0.4:
            m_w = random.randint(70, 100)
            m_y = next_y - random.randint(70, 120)
            m_x = next_x + random.randint(10, max(10, width - m_w - 10))

            platforms.add(
                Platform(
                    m_x, m_y, m_w, 16,
                    moving=True,
                    move_range=50,
                    move_speed=random.uniform(1.5, 2.5),
                    axis="x"
                )
            )

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

    finish_x = LEVEL_WIDTH - 300
    platforms.add(Platform(finish_x, 450, 300, 50))
    goal = Goal(LEVEL_WIDTH - 100, 450)

    return platforms, enemies, coins, crystals, goal


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

    grav_text = font.render(
        f"Гравитация: {player.gravity_charges}/{player.max_gravity_charges}",
        True, CYAN
    )
    screen.blit(grav_text, (580, 10))

    hint = small_font.render(
        "A/D — ходьба  |  Пробел — прыжок  |  G — переворот гравитации",
        True, (160, 160, 180)
    )
    screen.blit(hint, (20, HEIGHT - 28))


def draw_text_center(screen, text, font, color, y):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    screen.blit(surf, rect)


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
        player = Player(100, 480)
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
            player.update(platforms, enemies, coins, crystals, camera_x)

            target = player.rect.centerx - WIDTH // 3
            if target > camera_x:
                camera_x += (target - camera_x) * 0.09

            camera_x = max(0, min(camera_x, LEVEL_WIDTH - WIDTH))

            if player.rect.colliderect(goal.rect):
                state = "win"

            if player.lives <= 0:
                state = "lose"

        screen.fill(DARK)

        if state == "menu":
            draw_text_center(screen, "GRAVITY FLIP", big_font, CYAN, 180)
            draw_text_center(screen, "Платформер с переворотом гравитации", font, WHITE, 255)
            draw_text_center(screen, "Нажми ENTER чтобы начать", font, YELLOW, 350)
            draw_text_center(screen, "A/D — движение   Пробел — прыжок   G — гравитация", small_font, (150, 150, 170), 440)
            draw_text_center(screen, "Уровень генерируется каждый раз заново", small_font, (150, 150, 170), 470)

        elif state == "playing":
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

            if player.gravity_dir == -1:
                pygame.draw.polygon(screen, CYAN, [(WIDTH-40, 70), (WIDTH-20, 70), (WIDTH-30, 50)])
            else:
                pygame.draw.polygon(screen, CYAN, [(WIDTH-40, 50), (WIDTH-20, 50), (WIDTH-30, 70)])

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
