import pygame, math

class Particle:
    def __init__(self, app, particle_type, pos, vel=[0, 0], frame=0, solid=False, friction=(1, 1)):
        self.app = app
        self.particle_type = particle_type
        self.pos = list(pos)
        self.vel = list(vel)
        self.animation = self.app.assets['particle/' + self.particle_type].copy()
        self.alpha = 255
        if self.particle_type == 'leaf':
            self.alpha = 10
        self.frame = frame % len(self.animation)
        self.done = False
        self.speed = 0.1
        self.solid = solid
        self.friction = pygame.Vector2(friction)
        self.timer = 0
    
    def img(self):
        self.frame += max(0.025, self.speed) * self.app.dt
        if self.frame >= len(self.animation):
            self.done = True
            return self.animation[-1]
        return self.animation[math.floor(self.frame)]
    
    def update(self):
        kill = False
        if self.done:
            if self.particle_type == 'particle':
                self.alpha -= 200 * self.app.dt
            self.alpha -= 2 * self.app.dt
            kill = self.particle_type == 'explode' or self.particle_type == 'star'
            if self.alpha < 15:
                kill = True
                self.alpha = 0
        else:
            self.alpha = min(255, self.alpha + 4 * self.app.dt)
        self.pos[0] += self.vel[0] * self.app.dt
        self.vel[0] += (self.vel[0] * self.friction.x - self.vel[0]) * self.app.dt
        if self.solid:
            check = self.app.tile_map.solid_check(self.pos)
            if check: 
                self.pos[0] -= self.vel[0] * self.app.dt
                self.vel[0] = 0
        self.pos[1] += self.vel[1] * self.app.dt
        self.vel[1] += (self.vel[1] * self.friction.y - self.vel[1]) * self.app.dt
        if self.solid:
            check = self.app.tile_map.solid_check(self.pos)
            if check:
                self.done = True
                self.vel[1] = 0
                self.vel[0] = 0
                self.speed = 0
        self.timer += 1 * self.app.dt
        if self.timer > 600:
            kill = True
            print(f'''
                    solid: {self.solid}
                    particle_type: {self.particle_type}
                    done: {self.done}
                    alpha: {self.alpha}
                    frame: {self.frame}
                    anim: {len(self.animation)}
                    speed: {self.speed}
                ''')
        return kill
    
    def draw(self, surf, scroll):
        img = self.img()
        if self.pos in self.app:
            img.set_alpha(self.alpha)
            surf.blit(img, (self.pos[0] - scroll[0] - img.get_width() // 2, self.pos[1] - scroll[1] - img.get_height() // 2))