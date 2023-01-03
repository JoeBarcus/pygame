import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
FPS = 60

WIDTH = 1000
HEIGHT = 1000

TILE_SIZE = 50
GAME_OVER = 0
MAIN_MENU = True
LEVEL = 0
MAX_LEVELS = 7
SCORE = 0
WHITE = (255,255,255)
BLUE = (0,0,255)

# draw screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Sweet game!')

font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)

#images
sun_img = pygame.image.load('assets/sun.png')
bg_img = pygame.image.load('assets/sky.png')
restart_img = pygame.image.load('assets/restart_btn.png')
start_img = pygame.image.load('assets/start_btn.png')
exit_img = pygame.image.load('assets/exit_btn.png')

#sounds
coin_fx = pygame.mixer.Sound('assets/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('assets/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('assets/game_over.wav')
game_over_fx.set_volume(0.5)
# pygame.mixer.music.load('assets/music.wav')
# pygame.mixer.music.play(-1, 0.0, 5000)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x,y))

def reset_level(level):
    player.reset(100, HEIGHT - 130)
    blob_group.empty()
    platform_group.empty()
    lava_group.empty()
    exit_group.empty()
    if path.exists(f'data/level{LEVEL}_data'):
        pickle_in = open(f'data/level{LEVEL}_data', 'rb')
        world_data = pickle.load(pickle_in)
    world = World(world_data)
    return world

class Button():
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.clicked = False

    def draw(self):
        action = False
        #mouse position
        pos = pygame.mouse.get_pos()

        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True
        
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        screen.blit(self.image, self.rect)

        return action


class Player():
    def __init__(self, x, y):
        self.reset(x, y)

    def update(self, GAME_OVER):
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20

        if GAME_OVER == 0:

            #keypresses
            key = pygame.key.get_pressed()
            if key[pygame.K_SPACE] and self.jumped == False and self.in_air == False:
                jump_fx.play()
                self.vel_y -= 15
                self.jumped = True
            if key[pygame.K_SPACE] == False:
                self.jumped = False
            if key[pygame.K_a]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_d]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if key[pygame.K_a] == False and key[pygame.K_d] == False:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            #animation
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]


            #gravity
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            #check for collisions
            self.in_air = True
            for tile in world.tile_list:
                #x direction collisions
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #y direction collisions
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #check if below ground
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    #check if above ground
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False

            #check for platform collisions
            for platform in platform_group:
                #x direction
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                #y direction
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    #below platform
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        self.vel_y = 0
                        dy = 0
                    #move sideways with platform
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction


            #Check for enemy collisions
            if pygame.sprite.spritecollide(self, blob_group, False):
                GAME_OVER = -1
                game_over_fx.play()

            #Check for lava collisions
            if pygame.sprite.spritecollide(self, lava_group, False):
                GAME_OVER = -1
                game_over_fx.play()

            #Check for exit collisions
            if pygame.sprite.spritecollide(self, exit_group, False):
                GAME_OVER = 1

            self.rect.x += dx
            self.rect.y += dy

        elif GAME_OVER == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, BLUE, (WIDTH // 2), HEIGHT // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        screen.blit(self.image, self.rect)
        #pygame.draw.rect(screen, (255,255,255), self.rect, 2)

        return GAME_OVER
    
    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(1,5):
            img_right = pygame.image.load(f'assets/guy{num}.png')
            img_right = pygame.transform.scale(img_right, (40, 80))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
        self.dead_image = pygame.image.load('assets/ghost.png')
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True

class World():
    def __init__(self, data):
        self.tile_list = []

        dirt_img = pygame.image.load('assets/dirt.png')
        grass_img = pygame.image.load('assets/grass.png')
        
        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (TILE_SIZE, TILE_SIZE))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * TILE_SIZE
                    img_rect.y = row_count * TILE_SIZE
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (TILE_SIZE, TILE_SIZE))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * TILE_SIZE
                    img_rect.y = row_count * TILE_SIZE
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * TILE_SIZE, row_count * TILE_SIZE + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * TILE_SIZE, row_count * TILE_SIZE, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * TILE_SIZE, row_count * TILE_SIZE, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * TILE_SIZE, row_count * TILE_SIZE + TILE_SIZE // 2)
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * TILE_SIZE + (TILE_SIZE // 2) - 15, row_count * TILE_SIZE + (TILE_SIZE // 2))
                    coin_group.add(coin)                    
                if tile == 8:
                    exit = Exit(col_count * TILE_SIZE + 25, row_count * TILE_SIZE - (TILE_SIZE // 2) + 35)
                    exit_group.add(exit)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])
            #pygame.draw.rect(screen, (255,255,255), tile[1], 2)

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('assets/blob.png')
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/platform.png')
        self.image = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1


class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/lava.png')
        self.image = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/coin.png')
        self.image = pygame.transform.scale(img, (TILE_SIZE // 2, TILE_SIZE // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('assets/exit.png')
        self.image = pygame.transform.scale(img, (TILE_SIZE, int(TILE_SIZE * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)


player = Player(100, HEIGHT - 130)

blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

score_coin = Coin(TILE_SIZE // 2, TILE_SIZE // 3)
coin_group.add(score_coin)

if path.exists(f'data/level{LEVEL}_data'):
    pickle_in = open(f'data/level{LEVEL}_data', 'rb')
    world_data = pickle.load(pickle_in)
world = World(world_data)

restart_button = Button(WIDTH // 2 - 50, HEIGHT // 2 + 100, restart_img)
start_button = Button(WIDTH // 2 - 350, HEIGHT // 2 , start_img)
exit_button = Button(WIDTH // 2 + 150, HEIGHT // 2, exit_img)

run = True

while run:

    clock.tick(FPS)

    screen.blit(bg_img, (0,0))
    screen.blit(sun_img, (100,100))

    if MAIN_MENU == True:
        if exit_button.draw():
            run = False
        if start_button.draw():
            MAIN_MENU = False
    else:

        world.draw()

        if GAME_OVER == 0:
            blob_group.update()
            platform_group.update()
            if pygame.sprite.spritecollide(player, coin_group, True):
                coin_fx.play()
                SCORE += 1
            draw_text('  X ' + str(SCORE), font_score, WHITE, TILE_SIZE - 10, 10)


        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)


        GAME_OVER = player.update(GAME_OVER)

        if GAME_OVER == -1:
            if restart_button.draw():
                world_data = []
                world = reset_level(LEVEL)
                GAME_OVER = 0
                SCORE = 0

        if GAME_OVER == 1:
            LEVEL += 1
            if LEVEL <= MAX_LEVELS:
                world_data = []
                world = reset_level(LEVEL)
                GAME_OVER = 0
            else:
                draw_text('YOU WIN!', font, BLUE, (WIDTH // 2) - 140, HEIGHT // 2)
                if restart_button.draw():
                    level = 0
                    world_data = []
                    world = reset_level(LEVEL)
                    GAME_OVER = 0
                    SCORE = 0


    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    pygame.display.update()

pygame.quit()