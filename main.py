# Created by Jens Kromdijk 29/03/2026
import pygame, sys, time, moderngl, array, math

pygame.init()
pygame.mixer.init()


# window dimensions and scaling
WIDTH, HEIGHT = 640, 480
SCALE = 2

class App:
    def __init__(self):
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

    # put all the game stuff here
    def update(self):
        # update delta time
        self.dt = (time.time() - self.last_time) * 60
        self.last_time = time.time()

        # just a test, usually just fill it with black
        self.screen.fill((int(255 - (math.sin(time.time()) * 125 + 125)), int(math.sin(time.time()) * 125 + 125), 0))
        pygame.draw.rect(self.screen, (0, 0, 255), (0, 0, 10, 10))
        pygame.draw.rect(self.screen, (0, 0, 255), (self.screen.get_width() - 10, self.screen.get_height() - 10, 10, 10))
    
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
                if event.type in {pygame.WINDOWRESIZED, pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED}:
                    width, height = pygame.display.get_window_size()
                    self.ctx.viewport = (0, 0, width, height)
                    self.screen = pygame.Surface((width // SCALE, height // SCALE))
                    self.screenTex.release()
                    self.screenTex = self.ctx.texture(self.screen.get_size(), 4)
                    self.screenTex.filter = (moderngl.NEAREST, moderngl.NEAREST)
                    self.screenTex.swizzle = "BGRA"

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