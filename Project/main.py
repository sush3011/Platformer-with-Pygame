# Infinite Jump! - pygame platformer

import pygame as pg
import random
from settings import *
from sprites import *
from os import path


class Game:
    def __init__(self):
        # Initialize pygame and create a window
        pg.init()
        pg.mixer.init()
        self.BGCOLOUR = LIGHTBLUE
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.load_data()

    def load_data(self):

        # load high score
        self.dir = path.dirname(__file__)
        with open(path.join(self.dir, HS_FILE), "r") as f:
            try:
                self.highscore = int(f.read())
            except:
                self.highscore = 0

        # load spritesheet
        img_dir = path.join(self.dir, "img")
        self.spritesheet = Spritesheet(path.join(img_dir, SPRITESHEET))

        # load cloud images
        self.cloud_images = []
        for i in range(1, 4):
            self.cloud_images.append(pg.image.load(path.join(img_dir,f"cloud{i}.png")))

        # load sounds
        self.sound_dir = path.join(self.dir, "sound")
        self.jump_sound = pg.mixer.Sound(path.join(self.sound_dir, "Jump.wav"))
        self.boost_sound = pg.mixer.Sound(path.join(self.sound_dir, "Boost.wav"))
        self.collect_sound = pg.mixer.Sound(path.join(self.sound_dir, "collect.wav"))

    def new(self):
        # Start a new game
        self.score = 0

        # Sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.platforms = pg.sprite.Group()
        self.powerups = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.clouds = pg.sprite.Group()

        self.player = Player(self)
        for plat in PLATFORM_LIST:
            p = Platform(self, *plat)

        self.mob_timer = 0
        pg.mixer.music.load(path.join(self.sound_dir, "Playful.ogg"))

        for i in range(8):
            c = Cloud(self)
            c.rect.y += 500

        self.run()

    def run(self):
        # Game loop
        pg.mixer.music.play(loops=-1)
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.events()
            self.update()
            self.draw()
        pg.mixer.music.fadeout(500)

    def update(self):
        # Game loop - Update
        self.all_sprites.update()

        # spawn a mob?
        now = pg.time.get_ticks()
        if now - self.mob_timer > MOB_SPAWN_RATE + random.choice([-1000, -500, 0, 500, 1000]):
            self.mob_timer = now
            Mob(self)

        # check if player hits a mob
        mob_hits = pg.sprite.spritecollide(self.player, self.mobs, False, pg.sprite.collide_mask)
        if mob_hits:
            self.playing = False

        # check if player hits a platform - only if falling
        if self.player.vel.y > 0:
            hits = pg.sprite.spritecollide(self.player, self.platforms, False)
            if hits:
                lowest = hits[0]
                for hit in hits:
                    if hit.rect.bottom > lowest.rect.centery:
                        lowest = hit
                    if self.player.pos.x < lowest.rect.right + 10 and \
                        self.player.pos.x > lowest.rect.left - 10:
                        if self.player.pos.y < lowest.rect.bottom:
                            self.player.pos.y = hits[0].rect.top
                            self.player.vel.y = 0
                            self.player.jumping = False

        # if player reaches top 1/4 of screen
        if self.player.rect.top <= HEIGHT / 4:
            if random.randrange(100) < 10:
                Cloud(self)
            self.player.pos.y += max(abs(self.player.vel.y), 2)
            for cloud in self.clouds:
                cloud_scroll = random.randrange(1, 10)
                cloud.rect.y += max(abs(self.player.vel.y / cloud_scroll), 2)
            for plat in self.platforms:
                plat.rect.y += max(abs(self.player.vel.y), 2)
                if plat.rect.top >= HEIGHT:
                    plat.kill()
                    self.score += 5
            for mob in self.mobs:
                mob.rect.y += max(abs(self.player.vel.y), 2)

        # if player hits a powerup
        pow_hits = pg.sprite.spritecollide(self.player, self.powerups, True)
        for pow in pow_hits:
            if pow.type == "boost":
                self.boost_sound.play()
                self.player.vel.y = -BOOST_POWER
                self.player.jumping = False

        # spawn new platforms to keep same average number
        while len(self.platforms) < 6:
            width = random.randrange(50, 100)
            p = Platform(self, random.randrange(0, WIDTH - width),
                         random.randrange(-75, -30))
            self.platforms.add(p)
            self.all_sprites.add(p)

        # Die!
        if self.player.rect.bottom > HEIGHT:
            for sprite in self.all_sprites:
                sprite.rect.y -= max(self.player.vel.y, 10)
                if sprite.rect.bottom < 0:
                    sprite.kill()
        if len(self.platforms) == 0:
            self.playing = False

    def events(self):
        # Game loop - Events
        for event in pg.event.get():
            # check for closing window
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    self.player.jump()
            if event.type == pg.KEYUP:
                if event.key == pg.K_SPACE:
                    self.player.jump_cut()

    def draw(self):
        # Game loop - Draw
        self.screen.fill(self.BGCOLOUR)
        self.all_sprites.draw(self.screen)

        self.draw_text("Score: ", 22, BLACK, WIDTH / 2 - 190, 15)
        self.draw_text(str(self.score), 22, BLACK, WIDTH / 2 - 120, 15)

        # after drawing everything, flip the display
        pg.display.flip()

    def show_start_screen(self):
        # Game start screen
        pg.mixer.music.load(path.join(self.sound_dir, "Intro.ogg"))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(self.BGCOLOUR)
        self.draw_text("INFINITE JUMP!", 60, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Use the arrows to move and the spacebar to jump!", 18, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press a key to play!", 40, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        self.draw_text("High Score: " + str(self.highscore), 22, WHITE, WIDTH / 2, 15)
        pg.display.flip()
        self.wait_for_key()
        pg.mixer.music.fadeout(500)

    def show_gameOver_screen(self):
        # Game over screen
        pg.mixer.music.load(path.join(self.sound_dir, "Intro.ogg"))
        pg.mixer.music.play(loops=-1)
        self.screen.fill(self.BGCOLOUR)
        self.draw_text("GAME OVER!", 80, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Score: " + str(self.score), 30, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press a key to play again!", 35, WHITE, WIDTH / 2, HEIGHT * 3 / 4)

        if self.score > self.highscore:
            self.highscore = self.score
            self.draw_text("NEW HIGH SCORE!", 30, WHITE, WIDTH / 2, HEIGHT / 2 + 40)
            with open(path.join(self.dir, HS_FILE), "w") as f:
                f.write(str(self.score))

        else:
            self.draw_text("High Score: " + str(self.highscore), 30, WHITE,WIDTH /2, HEIGHT / 2 + 40)

        pg.display.flip()
        self.wait_for_key()
        pg.mixer.music.fadeout(500)

    def wait_for_key(self):
        waiting = True
        while waiting and self.running:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pg.KEYUP:
                    waiting = False

    def draw_text(self, text, size, colour, x, y):
        font = pg.font.Font(FONT_NAME, size)
        text_surf = font.render(text, True, colour)
        text_rect = text_surf.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surf, text_rect)


g = Game()
g.show_start_screen()
while g.running:
    g.new()
    g.show_gameOver_screen()

pg.quit()





















