# Created by Jens Kromdijk 29/03/2026
import pygame, sys, time, moderngl, array, random

from src.util import *
from src.tiles import *
from src.player import *
from src.particles import *
from src.sparks import *

pygame.init()
pygame.mixer.init()
pygame.font.init()

# window dimensions and scaling
WIDTH, HEIGHT = 1200, 900
SCALE = 5
UI_SCALE = 2
SCROLL_LIMIT = 8
SMOKE_DELAY = 6

class App:
    def __init__(self):
        print(f"Running from `{get_script_path()}`")
        # no need for separate scaling, pygbag scales canvas automatically
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
        self.screen = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.ui_surf = pygame.Surface(((WIDTH // UI_SCALE, HEIGHT // UI_SCALE)))

        # setup moderngl
        self.ctx = None
        self.prog = None
        self.vbo = None
        self.vao = None
        self.setup_gl()

        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"
        self.screenTex.repeat_x = False
        self.screenTex.repeat_y = False

        self.uiTex = self.ctx.texture(self.ui_surf.get_size(), 4)
        self.uiTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.uiTex.swizzle = "BGRA"

        self.water_surf = self.screen.copy()
        self.waterTex = self.ctx.texture(self.screen.get_size(), 4)
        self.waterTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.waterTex.swizzle = "BGRA"

        self.lightTex = self.ctx.texture(self.get_grid_size(), 4)
        self.lightTex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.lightTex.swizzle = "BGRA"
        self.lightTex.repeat_x = False
        self.lightTex.repeat_y = False

        self.clock = pygame.time.Clock()

        # delta time
        self.dt = 1
        self.last_time = time.time() - 1 / 60
        self.time = 0
        self.slomo = 1

        # load assets
        self.assets = {
            "tiles/grass": load_tile_imgs("tiles/grass.png", TILE_SIZE),
            "tiles/marsh": load_tile_imgs("tiles/marsh.png", TILE_SIZE),
            "tiles/bricks": load_tile_imgs("tiles/bricks.png", TILE_SIZE),
            "tiles/wood": load_tile_imgs("tiles/wood.png", TILE_SIZE),
            "tiles/autumn": load_tile_imgs("tiles/autumn.png", TILE_SIZE),
            "tiles/drop": load_images("tiles/drop"),
            "tiles/spikes": load_animation("tiles/spikes.png", 8, 8, 4),
            "tiles/bars": load_animation("tiles/bars.png", 8, 8, 1),
            "tiles/large_decor": load_animation("tiles/large_decor.png", 32, 32, 5),
            "tiles/small_decor": load_animation("tiles/small_decor.png", 12, 12, 4),
            "tiles/big_tree": load_animation("tiles/big_tree.png", 8, 8, 38),
            "player/idle": load_animation("player/idle.png", 8, 8, 6),
            "player/run": load_animation("player/run.png", 8, 8, 4),
            "player/jump": load_animation("player/jump.png", 8, 8, 3),
            "player/land": load_animation("player/land.png", 8, 8, 4),
            "player/wall_jump": load_animation("player/wall_jump.png", 8, 8, 4),
            "player/bubble": load_animation("player/bubble.png", 16, 16, 2),
            "spring": load_image("tiles/spring.png"),
            "grass": load_animation("grass.png", 9, 9, 18),
            "particle/leaf": load_animation("particles/leaf.png", 8, 8, 17),
            "particle/feather": load_animation("particles/feather.png", 8, 8, 17),
            "particle/bubble": load_animation("particles/bubble.png", 4, 4, 8),
            "particle/explosion": load_animation("particles/explosion.png", 5, 5, 15),
            "particle/particle": load_animation("particles/particle.png", 5, 5, 4),
            "firefly": load_animation("particles/firefly.png", 5, 5, 20),
            "noise": load_image("noise.png"),
            "anchor": load_image("anchor.png"),
            "blaster": load_animation("blaster.png", 21, 21, 4),
            "bullet": load_image("bullet.png"),
            "portal": load_image("portal.png"),
            "title": load_image("title.png"),
            "sfx": {
                "countdown": load_sound("countdown.wav"),
                "break": load_sound("explosion.wav"),
                "explosion": load_sound("explosion_1.wav"),
                "hit": load_sound("hitHurt.wav"),
                "hit1": load_sound("hit_3.wav"),
                "impact": load_sound("impact.wav"),
                "spring": load_sound("turtle.wav"),
                "water_in": load_sound("water_in.wav"),
                "water_out": load_sound("water_out.wav"),
                "shoot": load_sound("shoot.wav"),
                "transition": load_sound("transition.wav"),
                "walljump": load_sound("walljump.wav"),
                "land": load_sound("land.wav")
            }
        }
        self.assets["sfx"]["impact"].set_volume(0.5)

        self.font = load_font("dogicapixel.ttf")
        pygame.mixer.music.load(get_script_path() + "data/audio/music/warm_nocturne.ogg", "ogg")

        self.noiseTex = self.ctx.texture(self.assets["noise"].get_size(), 4)
        self.noiseTex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.noiseTex.swizzle = "BGRA"
        self.noiseTex.repeat_x = True
        self.noiseTex.repeat_y = True
        self.noiseTex.write(self.assets["noise"].get_view('1'))
        self.prog["noise"].value = 1
        self.prog["lightTex"].value = 2
        self.prog["waterTex"].value = 3
        self.prog["uiTex"].value = 4

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.tile_map = TileMap(self)
        self.level = 0
        self.tile_map.load("data/maps/1.json")
        self.leaf_spawners = []
        for tree in self.tile_map.extract([('large_decor', 0), ('large_decor', 1), ('large_decor', 2), ('large_decor', 3)], keep=True):
            if tree['type'] == 'large_decor':
                self.leaf_spawners.append((pygame.Rect(2 + tree['pos'][0], 8 + tree['pos'][1], 19, 17), True))
            else:
                self.leaf_spawners.append((pygame.Rect(tree['pos'][0], tree['pos'][1] + 10, 12, 2), False))

        self.particles = []
        self.wind = ([0, 10], [0, 15], [0, 5])
        self.kickup = []
        self.kickup_surf = pygame.Surface((1, 1))
        self.sparks = []
        self.smoke = []
        self.fireflies = []
        for _ in range(10):
            # [pos, dir, angle]
            self.fireflies.append([[random.random() * 10000, random.random() * 10000], random.random() * math.pi * 2, random.random() * 10 + 10, random.random() * 4 * random.choice([-1, 1]), random.random() * 50])
        self.cinders = PhysicsParticles(self, trail=True, bounce=0.3, explode=True, friction=0.7)
        self.shockwave_time = 1000
        self.shockwave_center = [0, 0]
        self.player = Player(self, [6, 8], self.tile_map.start_pos)
        self.follow_pos = self.player.get_rect().center

        self.fade_timer = 1000

        self.fade = 0
        self.fade_vel = 0
        self.total_time = 0
        self.start_time = 0
        self.load_level(15)

        pygame.mixer.music.play(-1)

        self.state = "menu"
        self.menu_timer = 0
        self.title_pos = -100

        self.texts = {
            "0": [
                "Hello there...",
                "You appear to have been cooped up in a miserable little prison - with only a decrepit old playground and the lovely sentry next door for company.",
                "But never fear, you still possess one trick that your guards have not anticipated in their hubris... one which will leave those bird-brains shell-shocked!",
                "The jail may seem impervious, but the bars of your cell are impotent to contain your gallinaceous might - soon they shall shatter and fall in your domineering aura, allowing you to escape from this dastardly place once and for all!",
                "Nevertheless, beware! For you have been incarcerated in an isolated outback, and as you vamoose you must navigate the treacherous surroundings, where some of your captors still lurk...",
                "Will you risk it for the biscuit in a dashing escape - or will you stay put like a lily-livered chicken? It's an easy choice >:)"
            ], "1": [
                "You escaped! You're not out of the woods yet though - this terrain doesn't look friendly and there's another obnoxious guard waiting to poach any unsuspecting escapees!"
            ], "2": [
                "I hope you don't mind getting wet!"
            ],
            "3": ["You might need to climb a bit now... time to claim the higher ground!"],
            "4": ["It's looking a bit barren here - and a bit more hostile."],
            "5": ["Still easy going for now, but is it getting a bit more claustrophobic? These caves are getting tighter... almost like it's slowly digesting you."],
            "6": ["Right - this is getting a bit eggstreme."],
            "7": ["You managed to scramble out of that one... don't dice yourself on these sawblades! (tip: press down to drop through platforms)"],
            "8": ["It's looking a bit grim here - how will you appoach this one?"],
            "9": ["Try to make sure we have more left than drumsticks."],
            "10": ["It'll take some eggspertise to scramble up this one... just make sure you don't eggcelerate down too fast!"],
            "11": ["Time to go for a swim!"],
            "12": ["This looks familiar..."],
            "13": ["You'll need some deft footwork for this one - don't rush it!"],
            "14": ["It's looking like flappy bird over here!"],
            "15": ["On to the final stretch... you sure got some eggsercise!"]
        }

        self.titles = [
            "The Prison",
            "The Forest: P1",
            "The Forest: P2",
            "The Forest: P3",
            "The Wastelands: P1",
            "The Wastelands: P2"
        ]

        self.text_idx = 0
        self.text_timer = 0
        self.box_y = 0
        self.text_mode = True

        self.bar_timer = 0

    def reset_menu(self):
        self.menu_timer = 0
        self.title_pos = -100

    def menu(self):
        self.total_time = 0
        self.menu_timer += self.dt
        self.title_pos += (self.ui_surf.get_height() * 0.25 - self.title_pos) * 0.5 * self.dt 
        self.ui_surf.fill((0, 0, 0))

        self.ui_surf.blit(self.assets["title"], (self.ui_surf.get_width() / 2 - self.assets["title"].get_width() / 2, self.title_pos))

        text = "A fowl little adventure"
        render_text = ""
        for i in range(min(int(max(0, self.menu_timer - 100) * 0.2), len(text))):
            render_text += text[i]
        text_surf = self.font.render(render_text, False, (246, 242, 195))
        self.ui_surf.blit(text_surf, (self.ui_surf.get_width() / 2 - self.font.size(text)[0] / 2, self.ui_surf.get_height() * 0.25 + 50))

        if time.time() % 2 > 0.5:
            text_surf = self.font.render("[hit ENTER to start]", False, (246, 242, 195))
            self.ui_surf.blit(text_surf, (self.ui_surf.get_width() / 2 - text_surf.get_width() / 2, self.ui_surf.get_height() * 0.75))
        
        self.fade = min(1, max(0, self.fade + self.fade_vel * self.dt))
        if self.fade == 1:
            self.fade_vel = -0.02
            self.start_time = time.time()
            self.state = "game"
        
        width = 200
        if self.fade > 0:
            if self.fade_vel > 0:
                for x in range(math.ceil(self.ui_surf.get_width() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width, 0, width / 2, self.ui_surf.get_height() * self.fade * 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width + width / 2, self.ui_surf.get_height() * (1 - self.fade * 2), width / 2, self.ui_surf.get_height() * self.fade * 2))
            else:
                for y in range(math.ceil(self.ui_surf.get_height() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (0, y * width, self.ui_surf.get_width() * self.fade * 2, width / 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (self.ui_surf.get_width() * (1 - self.fade * 2), y * width + width / 2, self.ui_surf.get_width() * self.fade * 2, width / 2))
        
        self.uiTex.write(self.ui_surf.get_view('1'))
        self.water_surf.fill((0, 0, 0))
        # self.update_fireflies([0, 0])
        self.waterTex.write(self.water_surf.get_view('1'))
    
    def win(self):
        self.menu_timer += self.dt
        self.title_pos += (self.ui_surf.get_height() * 0.25 - self.title_pos) * 0.5 * self.dt 
        self.ui_surf.fill((0, 0, 0))

        self.ui_surf.blit(self.assets["title"], (self.ui_surf.get_width() / 2 - self.assets["title"].get_width() / 2, self.title_pos))

        sec = math.floor(self.total_time) % 60
        if sec < 10:
            sec = "0" + str(sec)
        else:
            sec = str(sec)
        minutes = math.floor((self.total_time) / 60) % 60
        if minutes < 10:
            minutes = "0" + str(minutes)
        else:
            minutes = str(minutes)
        hours = math.floor((self.total_time) / 3600) % 60
        if hours < 10:
            hours = "0" + str(hours)
        else:
            hours = str(hours)
        text = f"You escaped! ...in {hours}:{minutes}:{sec}"
        render_text = ""
        for i in range(min(int(max(0, self.menu_timer - 100) * 0.2), len(text))):
            render_text += text[i]
        text_surf = self.font.render(render_text, False, (246, 242, 195))
        self.ui_surf.blit(text_surf, (self.ui_surf.get_width() / 2 - self.font.size(text)[0] / 2, self.ui_surf.get_height() * 0.25 + 50))

        if time.time() % 2 > 0.5:
            text_surf = self.font.render("[hit ENTER to attempt again]", False, (246, 242, 195))
            self.ui_surf.blit(text_surf, (self.ui_surf.get_width() / 2 - text_surf.get_width() / 2, self.ui_surf.get_height() * 0.75))
        
        self.fade = min(1, max(0, self.fade + self.fade_vel * self.dt))
        if self.fade == 1:
            self.fade_vel = -0.02
            self.state = "menu"
        
        width = 200
        if self.fade > 0:
            if self.fade_vel > 0:
                for x in range(math.ceil(self.ui_surf.get_width() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width, 0, width / 2, self.ui_surf.get_height() * self.fade * 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width + width / 2, self.ui_surf.get_height() * (1 - self.fade * 2), width / 2, self.ui_surf.get_height() * self.fade * 2))
            else:
                for y in range(math.ceil(self.ui_surf.get_height() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (0, y * width, self.ui_surf.get_width() * self.fade * 2, width / 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (self.ui_surf.get_width() * (1 - self.fade * 2), y * width + width / 2, self.ui_surf.get_width() * self.fade * 2, width / 2))
        
        self.uiTex.write(self.ui_surf.get_view('1'))

        self.water_surf.fill((0, 0, 0))
        # self.update_fireflies([0, 0])
        self.waterTex.write(self.water_surf.get_view('1'))
    
    def load_level(self, level):
        self.start_time = time.time()
        self.level = level
        path = "data/maps/" + str(level) + ".json"
        try:
            self.tile_map.load(path)
        except FileNotFoundError:
            self.load_level(0)
            self.state = "win"
            self.end_time = time.time()
        self.leaf_spawners = []
        for tree in self.tile_map.extract([('large_decor', 0), ('large_decor', 1), ('large_decor', 2), ('large_decor', 3)], keep=True):
            if tree['type'] == 'large_decor':
                self.leaf_spawners.append((pygame.Rect(2 + tree['pos'][0], 8 + tree['pos'][1], 19, 17), True))
            else:
                self.leaf_spawners.append((pygame.Rect(tree['pos'][0], tree['pos'][1] + 10, 12, 2), False))
        self.particles = []
        self.kickup = []
        self.sparks = []
        self.smoke = []
        self.cinders = PhysicsParticles(self, trail=True, bounce=0.3, explode=True, friction=0.7)
        self.shockwave_time = 1000
        self.shockwave_center = [0, 0]
        self.player = Player(self, [6, 8], self.tile_map.start_pos)
        self.follow_pos = self.player.get_rect().center
        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.text_idx = 0
        self.text_timer = 0
        self.box_y = 0
        self.text_mode = True

        self.bar_timer = 0
    
    def create_shockwave(self, pos):
        self.shockwave_time = 0
        self.shockwave_center = list(pos)
    
    def update_fireflies(self, scroll):
        for fly in self.fireflies:
            fly[0][0] += math.cos(fly[1]) * fly[2] * self.dt * 0.05
            fly[0][1] += math.sin(fly[1]) * fly[2] * self.dt * 0.05
            fly[1] += fly[3] * self.dt * 0.003
            if random.random() * 4 < self.dt:
                fly[3] = random.random() * 2 * random.choice([-1, 1])
                fly[2] = random.random() * 5 + 5
            loc = (((fly[0][0] - scroll[0]) % self.screen.get_width()), ((fly[0][1] - scroll[1]) % self.screen.get_height()))
            fly[4] = (fly[4] + 0.1 * self.dt) % len(self.assets["firefly"])
            surf = self.assets["firefly"][math.floor(fly[4])]
            surf.set_alpha(100)
            self.water_surf.blit(surf, loc)
    
    def get_grid_size(self):
        return (math.ceil(self.screen.get_width() / TILE_SIZE) + 2, math.ceil(self.screen.get_height() / TILE_SIZE) + 2)
    
    def setup_gl(self):
        self.ctx = moderngl.create_context()

        vert_src = ""
        with open("data/shaders/screenShader.vert", "r") as f:
            vert_src = f.read()
        frag_src = ""
        with open("data/shaders/screenShader.frag", "r") as f:
            frag_src = f.read()
        self.prog = self.ctx.program(
            vertex_shader=vert_src,
            fragment_shader=frag_src
        )
        self.prog["screenTex"].value = 0

        quadVertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(quadVertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])
    
    def __contains__(self, pos):
        return self.scroll[0] <= pos[0] <= self.scroll[0] + self.screen.get_width() and self.scroll[1] <= pos[1] <= self.scroll[1] + self.screen.get_height()
    
    def update_kickup(self, render_scroll):
        # p: [pos, vel, size, color]
        decay = 0.01
        bounce = 0.7
        friction = 0.98
        gravity = 0.125

        for i, p in sorted(enumerate(self.kickup), reverse=True):
            p[2] -= decay * self.dt
            if p[2] <= 0:
                self.kickup.pop(i)
            else: 
                self.kickup_surf.fill(p[3])
                self.kickup_surf.set_alpha(int(p[2] * 255))
                self.screen.blit(self.kickup_surf, (int(p[0][0] - render_scroll[0]), int(p[0][1] - render_scroll[1])))
            p[0][0] += p[1][0] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][0] -= p[1][0] * self.dt
                p[1][0] *= -bounce
                p[1][1] *= friction
            p[0][1] += p[1][1] * self.dt
            if self.tile_map.solid_check(p[0]):
                p[0][1] -= p[1][1] * self.dt
                p[1][1] *= -bounce
                p[1][0] *= friction
            p[1][1] = min(8, p[1][1] + gravity * self.dt)
    
    def update_sparks(self, render_scroll):
        for i, spark in sorted(enumerate(self.sparks), reverse=True):
            spark.update(self.dt)
            if spark.speed >= 0:
                spark.draw(self.screen, render_scroll)
            else:
                self.sparks.pop(i)
    
    @staticmethod
    def alpha_surf(dim, alpha, color):
        surf = pygame.Surface(dim)
        surf.fill(color)
        surf.set_alpha(alpha)
        return surf.convert_alpha()
    
    def calc_smoke(self, smoke, render_scroll):
        smoke[0][0] += smoke[1][0] * self.dt
        smoke[0][1] += smoke[1][1] * self.dt
        smoke[1][0] += (smoke[1][0] * 0.9 - smoke[1][0]) * self.dt
        smoke[1][1] += (smoke[1][1] * 0.98 - smoke[1][1]) * self.dt
        smoke[4] += (smoke[5] - smoke[4]) / 10 * self.dt
        smoke[3] = max(0, smoke[3] - SMOKE_DELAY * self.dt)
        smoke[2] += 0.2 * self.dt
        surf = pygame.transform.rotate(self.alpha_surf([smoke[2], smoke[2]], smoke[3], smoke[6]), smoke[4])
        if not smoke[3]:
            self.smoke.remove(smoke)
        return (surf, (smoke[0][0] - surf.get_width() * 0.5 - render_scroll[0], smoke[0][1] - surf.get_height() * 0.5 - render_scroll[1]))
        
    # put all the game stuff here
    def update(self):
        self.fade_timer += self.dt
        if 40 < self.fade_timer < 100:
            self.fade_timer = 200
            self.fade_vel = 0.02
        
        if not self.text_mode and len(self.tile_map.bar_locs):
            self.bar_timer += self.dt
            if self.bar_timer > 60:
                self.tile_map.break_bar(self.tile_map.bar_locs[0])
                self.tile_map.bar_locs.pop(0)
                self.bar_timer = 0

        self.player.update(self.dt, self.tile_map)
        self.tile_map.update_springs(self.dt, self.player)
        self.tile_map.grass_manager.update([self.player.get_rect()])
        self.tile_map.update_anchors(self.dt)

        if self.player.ad > self.player.death_time:
            lookahead = 10
            if self.player.flip:
                lookahead *= -1
            target_scroll = [self.player.get_rect().centerx + lookahead - self.screen.get_width() * 0.5, self.player.get_rect().centery - self.screen.get_height() * 0.5]
            
            if abs(target_scroll[0] - self.scroll[0]) > SCROLL_LIMIT:
                self.scroll[0] += (target_scroll[0] - self.scroll[0]) / 30 * self.dt
            if abs(target_scroll[1] - self.scroll[0]) > SCROLL_LIMIT:
                self.scroll[1] += (target_scroll[1] - self.scroll[1]) / 30 * self.dt
        
        self.scroll[0] = max(self.scroll[0], 0)
        
        screen_shake_offset = (
            random.random() * self.screen_shake - self.screen_shake / 2,
            random.random() * self.screen_shake - self.screen_shake / 2,
        )
        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))
        self.prog["scrollX"].value = render_scroll[0]
        self.prog["scrollY"].value = render_scroll[1]
        self.prog["screenShake"].value = screen_shake_offset[0] * 0.01;

        self.screen_shake = max(0, self.screen_shake - 1 * self.dt)

        self.tile_map.draw_decor(self.screen, render_scroll)
        self.tile_map.draw(self.screen, render_scroll)
        self.tile_map.update_blasters(self.screen, render_scroll, self.dt)
        if self.fade == 0:
            self.screen.blit(self.assets["portal"], (self.tile_map.portal_pos[0] - render_scroll[0], self.tile_map.portal_pos[1] - render_scroll[1] + math.sin(self.time * 0.05) * 4))
        if self.player.get_rect().colliderect(pygame.Rect(self.tile_map.portal_pos[0], self.tile_map.portal_pos[1], 10, 12)):
            self.fade_timer = 0
            self.assets["sfx"]["impact"].play()
            self.screen_shake = 32
            for i, color in enumerate(self.tile_map.portal_colors):
                if color != (0, 0, 0, 0) and color != (0, 0, 0, 255):
                    angle = random.random() * math.pi * 2
                    speed = random.random() - 0.5
                    self.kickup.append([[self.tile_map.portal_pos[0] + (i % 10), self.tile_map.portal_pos[1] + math.floor(i / 10)], [math.cos(angle) * speed, math.sin(angle) * speed], 1, color])
            self.tile_map.portal_pos = [-10000, -10000]
        self.player.draw(self.screen, render_scroll)

        average_gust = 0
        for gust in self.wind:
            gust[0] -= (gust[1] + math.sin(gust[0] * 0.025) * 0.3) * self.dt * 0.5
            if not ((gust[0], self.scroll[1] + self.screen.get_height() / 2) in self):
                gust[1] = 5 * (random.random() + 0.5) * 2
                gust[0] = self.scroll[0] + self.screen.get_width() - gust[1] * self.dt
            average_gust += gust[1]
        average_gust *= 0.5

        for rect, fix in self.leaf_spawners:
            if random.random() * 20000 / (average_gust * 0.15) / self.dt < rect.width * rect.height:
                pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                if not self.tile_map.solid_check(pos) and fix:
                    self.particles.append(Particle(self, 'leaf', pos, (-0.1, 0.3), frame=random.randint(0, 16), solid=True))
                else:
                    self.particles.append(Particle(self, 'leaf', pos, (-0.1, 0.3), frame=random.randint(0, 16), solid=False))

        for particle in self.particles.copy():
            kill = particle.update()
            particle.draw(self.screen, render_scroll)
            if particle.particle_type == 'leaf' and (not particle.done):
                particle.pos[0] += math.sin(particle.frame * 0.08) * 0.8 * self.dt - 0.5 * self.dt * (average_gust * 0.1)
                particle.vel[1] = min(0.2, particle.vel[1] + 0.005 / (average_gust * 0.1) * self.dt)
            if kill:
                self.particles.remove(particle)
        self.update_kickup(render_scroll)
        self.update_sparks(render_scroll)
        self.cinders.update(self.screen, render_scroll)

        self.screen.fblits([self.calc_smoke(smoke, render_scroll) for smoke in self.smoke.copy()])
        
        self.water_surf.fill((0, 0, 0))
        self.update_fireflies(render_scroll)
        hit = False
        for water in self.tile_map.water:
            water.update(self.water_surf, self.player, render_scroll, self.dt)
            if water.get_rect().colliderect(self.player.get_rect()):
                if not self.player.water:
                    self.player.movement *= 0.6
                    self.assets["sfx"]["water_in"].play()
                self.player.water = True
                hit = True
        self.waterTex.write(self.water_surf.get_view('1'))
        if not hit:
            if self.player.water:
                self.assets["sfx"]["water_out"].play()
            self.player.water = False
        else:
            for key in self.player.controls:
                if self.player.controls[key]:
                    if random.random() / self.dt < 0.5:
                        spread = 5
                        self.particles.append(Bubble(self, "bubble", [self.player.get_rect().centerx + random.random() * spread - spread / 2, self.player.get_rect().centery + random.random() * spread - spread /2], [0, 0], random.random() * 2, True))
        
        light_surf = self.tile_map.get_light_data(self.screen, render_scroll)
        self.lightTex.write(light_surf.get_view('1'))

        center = [(self.shockwave_center[0] - render_scroll[0]) / self.screen.get_width(), (self.shockwave_center[1] - render_scroll[1]) / self.screen.get_height()]
        self.prog["shockwave"].value = tuple(center)
        self.prog["shockwaveTime"].value = self.shockwave_time
        self.shockwave_time += 0.001 * self.dt
        self.shockwave_time += (self.shockwave_time * 1.5 - self.shockwave_time) * self.dt
        self.shockwave_time = min(self.shockwave_time, 1000000)
    
    def get_texture(self, surf):
        texture = self.ctx.texture(surf.get_size(), 4)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = "BGRA"
        texture.write(surf.get_view('1'))
        return texture
    
    def close(self):
        self.noiseTex.release()
        self.screenTex.release()
        self.lightTex.release()
        self.waterTex.release()
        self.uiTex.release()
        pygame.quit()
        sys.exit()
    
    def renderUI(self):
        self.ui_surf.fill((0, 0, 0))
        
        sec = math.floor(time.time() - self.start_time + self.total_time) % 60
        if sec < 10:
            sec = "0" + str(sec)
        else:
            sec = str(sec)
        minutes = math.floor((time.time() - self.start_time + self.total_time) / 60) % 60
        if minutes < 10:
            minutes = "0" + str(minutes)
        else:
            minutes = str(minutes)
        hours = math.floor((time.time() - self.start_time + self.total_time) / 3600) % 60
        if hours < 10:
            hours = "0" + str(hours)
        else:
            hours = str(hours)
        text = f"{hours}:{minutes}:{sec}"
        text_surf = self.font.render(text, False, (246, 242, 195), (1, 1, 1))
        time_padding = 3
        pygame.draw.rect(self.ui_surf, (22, 13, 19), (10 - time_padding, 10 - time_padding, text_surf.get_width() + time_padding * 2, text_surf.get_height() + time_padding * 2), 0, 2)
        pygame.draw.rect(self.ui_surf, (246, 242, 195), (10 - time_padding - 1, 10 - time_padding - 1, text_surf.get_width() + time_padding * 2 + 2, text_surf.get_height() + time_padding * 2 + 2), 1, 2)
        self.ui_surf.blit(text_surf, (10, 10))

        self.text_mode = self.text_idx < len(self.texts[str(self.level)])
        if self.text_mode:
            self.box_y += (1 - self.box_y) * 0.1 * self.dt
        else:
            self.box_y += -self.box_y * 0.1 * self.dt
        box_height = 100
        padding = 4
        pygame.draw.rect(self.ui_surf, (22, 13, 19), (0, self.ui_surf.get_height() - box_height * self.box_y, self.ui_surf.get_width(), box_height * self.box_y))
        pygame.draw.rect(self.ui_surf, (246, 242, 195), (1, self.ui_surf.get_height() - box_height * self.box_y + 1, self.ui_surf.get_width() - 2, box_height * self.box_y - 2), 1)

        text_surf = self.font.render("Press [ENTER] to continue or press [z] to skip narrator", False, (246, 242, 195))
        self.ui_surf.blit(text_surf, (1 + padding, self.ui_surf.get_height() - box_height * self.box_y + 85))

        self.text_timer += self.dt
        if self.text_mode:
            self.start_time = time.time()
            type_speed = 0.6
            full_text = self.texts[str(self.level)][self.text_idx]
            render_text = [""]
            idx = 0
            for i in range(min(int(max(0, self.text_timer - 100) * type_speed), len(full_text))):
                if full_text[i] == "-":
                    self.text_timer -= type_speed * 0.5 * self.dt
                if full_text[i] == " ":
                    temp = render_text[idx]
                    break_text = False
                    for j in range(len(full_text) - i - 1):
                        if full_text[i + j + 1] == " ":
                            break_text = False
                            break
                        else:
                            temp += full_text[i + j]
                        if self.font.size(temp)[0] >= self.ui_surf.get_width() - 2 - padding * 3:
                            break_text = True
                            break
                    if break_text:
                        render_text.append("")
                        idx += 1

                render_text[idx] += full_text[i]
            
            for i, line in enumerate(render_text):
                text_surf = self.font.render(line, False, (246, 242, 195), None)
                self.ui_surf.blit(text_surf, (1 + padding, self.ui_surf.get_height() - box_height * self.box_y + 1 + padding + 12 * i))
            
            if (self.text_timer - 100) * type_speed > len(full_text):
                pygame.draw.rect(self.ui_surf, (246, 242, 195), (1 + padding + text_surf.get_width() + 2, self.ui_surf.get_height() - box_height * self.box_y + 1 + padding + 12 * idx, 5, 8))
            else:
                if time.time() * 0.2 % type_speed * 2 < type_speed:
                    pygame.draw.rect(self.ui_surf, (246, 242, 195), (1 + padding + text_surf.get_width() + 2, self.ui_surf.get_height() - box_height * self.box_y + 1 + padding + 12 * idx, 5, 8))


        self.fade = min(1, max(0, self.fade + self.fade_vel * self.dt))
        if self.fade == 1:
            self.total_time += time.time() - self.start_time
            self.fade_vel = -0.02
            self.load_level(self.level + 1)
            self.assets["sfx"]["transition"].play()
        
        width = 200
        if self.fade > 0:
            if self.fade_vel > 0:
                for x in range(math.ceil(self.ui_surf.get_width() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width, 0, width / 2, self.ui_surf.get_height() * self.fade * 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (x * width + width / 2, self.ui_surf.get_height() * (1 - self.fade * 2), width / 2, self.ui_surf.get_height() * self.fade * 2))
            else:
                for y in range(math.ceil(self.ui_surf.get_height() / width)):
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (0, y * width, self.ui_surf.get_width() * self.fade * 2, width / 2))
                    pygame.draw.rect(self.ui_surf, (1, 1, 1), (self.ui_surf.get_width() * (1 - self.fade * 2), y * width + width / 2, self.ui_surf.get_width() * self.fade * 2, width / 2))

        self.uiTex.write(self.ui_surf.get_view('1'))

    def run(self):
        while True:
            # update event loop
            for event in pygame.event.get():
                # just return to quit
                if event.type == pygame.QUIT:
                    self.close()
                    return

                # handle window resizing on desktop
                if event.type == pygame.VIDEORESIZE:
                    width, height = event.size 
                    if width < WIDTH:
                        width = WIDTH
                    if height < HEIGHT:
                        height = HEIGHT
                    self.ctx.viewport = (0, 0, width, height)
                    self.display = pygame.display.set_mode((width, height), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
                    self.screen = pygame.Surface((width // SCALE, height // SCALE))
                    self.ui_surf = pygame.Surface(((width // UI_SCALE, height // UI_SCALE)))
                    self.screenTex.release()
                    self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
                    self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
                    self.screenTex.swizzle = "BGRA"
                    self.screenTex.repeat_x = False
                    self.screenTex.repeat_y = False
                    self.uiTex.release()
                    self.uiTex = self.ctx.texture(self.ui_surf.get_size(), 4)
                    self.uiTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
                    self.uiTex.swizzle = "BGRA"
                    self.waterTex.release()
                    self.waterTex = self.ctx.texture(self.screen.get_size(), 4)
                    self.waterTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
                    self.waterTex.swizzle = "BGRA"
                    self.water_surf = self.screen.copy()
                    self.lightTex.release()
                    self.lightTex = self.ctx.texture(self.get_grid_size(), 4)
                    self.lightTex.filter = (moderngl.LINEAR, moderngl.LINEAR)
                    self.lightTex.swizzle = "BGRA"
                    self.lightTex.repeat_x = False
                    self.lightTex.repeat_y = False
                if event.type == pygame.KEYDOWN:
                    if self.state == "game":
                        if self.text_mode:
                            if event.key == pygame.K_RETURN:
                                self.text_idx += 1
                                self.text_timer = 100
                            elif event.key == pygame.K_z:
                                self.text_idx = 97123497234
                                self.text_timer = 50
                        elif self.player.ad > self.player.death_time:
                            if event.key in {pygame.K_UP, pygame.K_w, pygame.K_SPACE, pygame.K_k}:
                                self.player.controls["up"] = True
                                self.player.jumping = 0
                            elif event.key in {pygame.K_DOWN, pygame.K_s, pygame.K_j}:
                                self.player.controls["down"] = True
                            elif event.key in {pygame.K_RIGHT, pygame.K_d, pygame.K_l}:
                                self.player.controls["right"] = True
                            elif event.key in {pygame.K_LEFT, pygame.K_a, pygame.K_h}:
                                self.player.controls["left"] = True
                            elif event.key in {pygame.K_x}:
                                if abs(self.player.dashing) < 20:
                                    self.player.controls['dashing'] = True
                    elif self.state == "menu" or self.state == "win":
                        if event.key == pygame.K_RETURN:
                            self.fade_vel = 0.02
                            self.assets["sfx"]["transition"].play()
                if event.type == pygame.KEYUP:
                    if self.state == "game":
                        if event.key in {pygame.K_UP, pygame.K_w, pygame.K_SPACE, pygame.K_k}:
                            self.player.controls["up"] = False
                        elif event.key in {pygame.K_DOWN, pygame.K_s, pygame.K_j}:
                            self.player.controls["down"] = False
                        elif event.key in {pygame.K_RIGHT, pygame.K_d, pygame.K_l}:
                            self.player.controls["right"] = False
                        elif event.key in {pygame.K_LEFT, pygame.K_a, pygame.K_h}:
                            self.player.controls["left"] = False

            # update game
            # update delta time
            self.slomo += (1 - self.slomo) * 0.3 * self.dt
            self.dt = (time.time() - self.last_time) * 60 * self.slomo
            self.dt = min(self.dt, 3)
            self.last_time = time.time()
            self.screen.fill((0, 0, 0))
            if self.state == "game":
                self.update()
                self.renderUI()
            elif self.state == "menu":
                self.menu()
            else:
                self.win()

            self.screenTex.write(self.screen.get_view('1'))
            self.screenTex.use(0)

            self.noiseTex.use(1)
            self.lightTex.use(2)
            self.waterTex.use(3)
            self.uiTex.use(4)

            self.time += self.dt
            self.prog["time"].value = self.time
            self.prog["scrWidth"].value = self.screen.get_width()
            self.prog["scrHeight"].value = self.screen.get_height()

            self.ctx.clear(0, 0, 0)
            self.vao.render(moderngl.TRIANGLE_STRIP)

            pygame.display.flip()
            pygame.display.set_caption(
                f"FPS: {self.clock.get_fps() :.1f} Display: {self.screen.get_width()} * {self.screen.get_height()}"
            )
            self.clock.tick(144)

if __name__ == "__main__":
    App().menu()
    App().run()