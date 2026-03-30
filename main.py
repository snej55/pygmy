# Created by Jens Kromdijk 29/03/2026
import pygame, sys, time, moderngl, array, random

from src.util import *
from src.tiles import *
from src.player import *
from src.particles import *

pygame.init()
pygame.mixer.init()

# window dimensions and scaling
WIDTH, HEIGHT = 1200, 900
SCALE = 4
SCROLL_LIMIT = 8

class App:
    def __init__(self):
        print(f"Running from `{get_script_path()}`")
        # no need for separate scaling, pygbag scales canvas automatically
        self.display = pygame.display.set_mode((WIDTH, HEIGHT), flags=pygame.RESIZABLE | pygame.OPENGL | pygame.DOUBLEBUF)
        self.screen = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))

        # setup moderngl
        self.ctx = moderngl.create_context()
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 300 es
            in vec2 aPos;
            in vec2 aTexCoord;
            out vec2 TexCoord;

            void main()
            {
                gl_Position = vec4(aPos, 0.0, 1.0);
                TexCoord = aTexCoord;
            }
            """,
            fragment_shader="""
            #version 300 es
            precision mediump float;
            uniform sampler2D screenTex;
            in vec2 TexCoord;
            out vec4 FragColor;

            void main()
            {
                vec4 tex = texture(screenTex, TexCoord);
                FragColor = tex;
            }
            """,
        )
        self.prog["screenTex"].value = 0

        quadVertices = array.array("f", [-1.0, 1.0, 0.0, 0.0, -1.0, -1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, -1.0, 1.0, 1.0])
        self.vbo = self.ctx.buffer(quadVertices)
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, "2f 2f", "aPos", "aTexCoord")])

        self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
        self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.screenTex.swizzle = "BGRA"

        self.clock = pygame.time.Clock()

        # delta time
        self.dt = 1
        self.last_time = time.time() - 1 / 60

        # load assets
        self.assets = {
            "tiles/grass": load_tile_imgs("tiles/grass.png", TILE_SIZE),
            "tiles/drop": load_images("tiles/drop"),
            "tiles/spikes": load_animation("tiles/spikes.png", 8, 8, 4),
            "tiles/large_decor": load_animation("tiles/large_decor.png", 32, 32, 5),
            "tiles/small_decor": load_animation("tiles/small_decor.png", 12, 12, 4),
            "player/idle": load_animation("player/idle.png", 8, 8, 6),
            "player/run": load_animation("player/run.png", 8, 8, 4),
            "player/jump": load_animation("player/jump.png", 8, 8, 3),
            "player/land": load_animation("player/land.png", 8, 8, 4),
            "player/wall_jump": load_animation("player/wall_jump.png", 8, 8, 4),
            "player/bubble": load_animation("player/bubble.png", 16, 16, 2),
            "spring": load_image("tiles/spring.png"),
            "grass": load_animation("grass.png", 9, 9, 18),
            "particle/leaf": load_animation("particles/leaf.png", 8, 8, 17),
            "particle/bubble": load_animation("particles/bubble.png", 4, 4, 8)
        }

        self.scroll = pygame.Vector2(0, 0)
        self.screen_shake = 0

        self.tile_map = TileMap(self)
        self.tile_map.load("data/maps/0.json")
        self.leaf_spawners = []
        for tree in self.tile_map.extract([('large_decor', 0), ('large_decor', 1), ('large_decor', 2), ('large_decor', 3)], keep=True):
            if tree['type'] == 'large_decor':
                self.leaf_spawners.append((pygame.Rect(2 + tree['pos'][0], 8 + tree['pos'][1], 19, 17), True))
            else:
                self.leaf_spawners.append((pygame.Rect(tree['pos'][0], tree['pos'][1] + 10, 12, 2), False))

        self.player = Player(self, [6, 8], [10, 10])
        self.follow_pos = self.player.get_rect().center

        self.particles = []
        self.wind = ([0, 10], [0, 15], [0, 5])
    
    def __contains__(self, pos):
        return self.scroll[0] <= pos[0] <= self.scroll[0] + self.screen.get_width() and self.scroll[1] <= pos[1] <= self.scroll[1] + self.screen.get_height()
        
    # put all the game stuff here
    def update(self):
        # update delta time
        self.dt = (time.time() - self.last_time) * 60
        self.last_time = time.time()

        self.player.update(self.dt, self.tile_map)
        self.tile_map.update_springs(self.dt, self.player)
        self.tile_map.grass_manager.update([self.player.get_rect()])

        if self.player.ad > self.player.death_time:
            lookahead = 10
            if self.player.flip:
                lookahead *= -1
            target_scroll = [self.player.get_rect().centerx + lookahead - self.screen.get_width() * 0.5, self.player.get_rect().centery - self.screen.get_height() * 0.5]
            
            if abs(target_scroll[0] - self.scroll[0]) > SCROLL_LIMIT:
                self.scroll[0] += (target_scroll[0] - self.scroll[0]) / 30 * self.dt
            if abs(target_scroll[1] - self.scroll[0]) > SCROLL_LIMIT:
                self.scroll[1] += (target_scroll[1] - self.scroll[1]) / 30 * self.dt

        screen_shake_offset = (
            random.random() * self.screen_shake - self.screen_shake / 2,
            random.random() * self.screen_shake - self.screen_shake / 2,
        )
        render_scroll = (int(self.scroll[0] + screen_shake_offset[0]), int(self.scroll[1] + screen_shake_offset[1]))

        self.screen_shake = max(0, self.screen_shake - 1 * self.dt)
        self.screen.fill((0, 0, 0))

        self.tile_map.draw_decor(self.screen, render_scroll)
        self.tile_map.draw(self.screen, render_scroll)
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
        
        hit = False
        for water in self.tile_map.water:
            water.update(self.screen, self.player, render_scroll, self.dt)
            if water.get_rect().colliderect(self.player.get_rect()):
                if not self.player.water:
                    self.player.movement *= 0.6
                self.player.water = True
                hit = True
        if not hit:
            self.player.water = False
        else:
            for key in self.player.controls:
                if self.player.controls[key]:
                    if random.random() / self.dt < 0.5:
                        spread = 5
                        self.particles.append(Bubble(self, "bubble", [self.player.get_rect().centerx + random.random() * spread - spread / 2, self.player.get_rect().centery + random.random() * spread - spread /2], [0, 0], random.random() * 2, True))
    
    def get_texture(self, surf):
        texture = self.ctx.texture(surf.get_size(), 4)
        texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        texture.swizzle = "BGRA"
        texture.write(surf.get_view('1'))
        return texture
    
    def close(self):
        self.screenTex.release()
        pygame.quit()
        sys.exit()

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
                    self.screenTex.release()
                    self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
                    self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
                    self.screenTex.swizzle = "BGRA"
                if event.type == pygame.KEYDOWN:
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
                if event.type == pygame.KEYUP:
                    if event.key in {pygame.K_UP, pygame.K_w, pygame.K_SPACE, pygame.K_k}:
                        self.player.controls["up"] = False
                    elif event.key in {pygame.K_DOWN, pygame.K_s, pygame.K_j}:
                        self.player.controls["down"] = False
                    elif event.key in {pygame.K_RIGHT, pygame.K_d, pygame.K_l}:
                        self.player.controls["right"] = False
                    elif event.key in {pygame.K_LEFT, pygame.K_a, pygame.K_h}:
                        self.player.controls["left"] = False

            # update game
            self.update()

            self.screenTex.write(self.screen.get_view('1'))
            self.screenTex.use(0)

            self.ctx.clear(0, 0, 0)
            self.vao.render(moderngl.TRIANGLE_STRIP)

            pygame.display.flip()
            pygame.display.set_caption(
                f"FPS: {self.clock.get_fps() :.1f} Display: {self.screen.get_width()} * {self.screen.get_height()}"
            )
            self.clock.tick(144)

if __name__ == "__main__":
    App().run()