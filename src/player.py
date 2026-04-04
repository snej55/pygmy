import pygame, random, math

from .anim import Anim
from .particles import *
from .util import load_palette
from .sparks import Spark

class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.start_pos = start_pos
        self.pos = pygame.Vector2(start_pos)

        self.falling = 30
        self.grounded = 0
        self.jumping = 30

        self.controls = {"up": False, "down": False, "right": False, "left": False, "dashing": False}

        self.movement = pygame.Vector2(0, 0)
        self.last_movement = pygame.Vector2(0, 0)

        self.idle = Anim(self.app.assets["player/idle"], 0.3)
        self.run = Anim(self.app.assets["player/run"], 0.6)
        self.jump = Anim(self.app.assets["player/jump"], 0.2, True)
        self.land = Anim(self.app.assets["player/land"], 0.2, False)
        self.wall_jump = Anim(self.app.assets["player/wall_jump"], 0.5, False)
        self.flip = False
        self.grounded = 0

        self.palette = load_palette(self.app.assets["player/idle"][0])
        self.colors = []
        pxarray = pygame.pixelarray.PixelArray(self.app.assets["player/idle"][0])
        for row in pxarray:
            for color in row:
                self.colors.append(self.app.assets["player/idle"][0].unmap_rgb(color))

        self.water = False
        self.angle = 0
        self.angle_vel = 0
        self.ad = 120
        self.death_time = 60
        self.speed = 0.9
        self.jump_height = 3.07
        self.gravity = 0.215
        self.collisions = {"right": False, "left": False, "up": False, "down": False}
        self.wall_slide = False
        self.wall_timer = 0
        self.rebound = pygame.Vector2(0, 0)
        self.dashing = 0
        self.sliding = 100
        self.down_timer = 0
        self.dash_length = 12
        self.dash_timer = 0

        self.water = False

        for _ in range(random.randint(20, 30)):
            angle = random.random() * math.pi * 2 
            speed = random.random() * 0.5
            pvel = [math.cos(angle) * speed, math.sin(angle) * speed]
            self.app.particles.append(Particle(self.app, 'feather', self.get_rect().center, pvel, random.randint(0, 7), True))
            self.app.particles[-1].particle_type = "leaf"

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        self.collisions = {"right": False, "left": False, "up": False, "down": False}
        self.ad += dt
        if self.ad > self.death_time:
            if not self.water:
                self.sliding += dt
                self.handle_animation(dt)
                fm = pygame.Vector2(self.movement.x * dt + self.rebound.x * dt, self.movement.y * dt + self.rebound.y * dt)

                self.pos.x += fm.x
                r = self.get_rect()
                for rect in tile_map.physics_rects_around(r.center):
                    if r.colliderect(rect):
                        if fm.x > 0:
                            r.right = rect.left
                            self.collisions["right"] = True
                            if not self.dashing:
                                for _ in range(math.floor((abs(self.movement.y) + abs(self.movement.x)) * dt)):
                                    speed = random.random() + 0.2
                                    angle = math.atan2(-self.movement.y, -self.movement.x) + random.random() * math.pi * 0.25
                                    self.app.kickup.append([[r.right - 1, r.centery], [math.cos(angle) * speed, math.sin(angle) * speed], random.random() * 0.05 + 0.95, random.choice([(144, 75, 65), (209, 147, 95)])])
                        if fm.x < 0:
                            r.left = rect.right
                            self.collisions["left"] = True
                            if not self.dashing:
                                for _ in range(math.floor((abs(self.movement.y) + abs(self.movement.x)) * dt)):
                                    speed = random.random() + 0.2
                                    angle = math.atan2(-self.movement.y, -self.movement.x) + random.random() * math.pi * 0.25
                                    self.app.kickup.append([[r.left + 1, r.centery], [math.cos(angle) * speed, math.sin(angle) * speed], random.random() * 0.05 + 0.95, random.choice([(144, 75, 65), (209, 147, 95)])])
                        # if abs(self.movement.x) > 1:
                        #     self.app.assets["sfx"]["land"].play()
                        self.pos.x = r.x
                        self.movement.x = 0
                        self.rebound.x = 0

                self.pos.y += fm.y
                r = self.get_rect()
                for rect in tile_map.physics_rects_around(r.center):
                    if r.colliderect(rect):
                        if fm.y >= 0:
                            r.bottom = rect.top
                            self.falling = 0
                            self.collisions["down"] = True
                            if not self.dashing:
                                for _ in range(math.floor((abs(self.movement.y) + abs(self.movement.x)) * dt)):
                                    speed = random.random() + 0.2
                                    angle = math.atan2(-self.movement.y, -self.movement.x) + random.random() * math.pi * 0.25
                                    self.app.kickup.append([[r.centerx, r.bottom - 1], [math.cos(angle) * speed, math.sin(angle) * speed], random.random() * 0.05 + 0.95, random.choice([(144, 75, 65), (209, 147, 95)])])
                        elif fm.y < 0:
                            r.top = rect.bottom
                            self.collisions["up"] = True
                            if not self.dashing:
                                for _ in range(math.floor((abs(self.movement.y) + abs(self.movement.x)) * dt)):
                                    speed = random.random() + 0.2
                                    angle = math.atan2(-self.movement.y, -self.movement.x) + random.random() * math.pi * 0.25
                                    self.app.kickup.append([[r.centerx, r.top + 1], [math.cos(angle) * speed, math.sin(angle) * speed], random.random() * 0.05 + 0.95, random.choice([(144, 75, 65), (209, 147, 95)])])
                        if abs(self.movement.y) > 1:
                            self.app.assets["sfx"]["land"].play()
                        self.movement.y = 0
                        self.pos.y = r.y
                        self.rebound.y = 0
                
                r = self.get_rect()
                tiles = tile_map.tiles_around(r.center)
                hit = False
                for tile in tiles:
                    if tile["type"] == "drop":
                        rect = pygame.Rect(tile["pos"][0] * 8, tile["pos"][1] * 8, 8, 2)
                        if rect.colliderect(r) and fm.y > 0:
                            hit = True
                            if self.down_timer <= 0 and not self.controls["down"]:
                                self.falling = 0
                                r.bottom = rect.top
                                self.collisions["down"] = True
                                self.movement.y = 0
                                self.pos.y = r.y
                                self.rebound.y = 0
                            else:
                                self.down_timer = 2
                # if self.down_timer > 0:
                #     self.controls["down"] = True
                # else:
                #     self.controls["down"] = False
                if not hit:
                    self.down_timer -= 1
                
                self.last_movement = fm.copy()

                self.falling += dt
                self.jumping += dt
                self.grounded += dt

                if self.wall_timer <= 0:
                    if self.controls["right"]:
                        self.movement.x += self.speed * dt
                        self.flip = False
                        if self.rebound.x > 0:
                            self.rebound.x += (self.rebound.x * 0.4 - self.rebound.x) * dt
                    if self.controls["left"]:
                        self.movement.x -= self.speed * dt
                        self.flip = True
                        if self.rebound.x < 0:
                            self.rebound.x += (self.rebound.x * 0.4 - self.rebound.x) * dt
                self.wall_timer -= dt
                self.movement.x += (self.movement.x * 0.65 - self.movement.x) * dt

                self.rebound += (self.rebound * 0.9 - self.rebound) * dt

                gravity_mod = 1.0
                if -0.6 < self.movement.y < 0.2:
                    gravity_mod = 0.8
                elif self.movement.y > 0.1:
                    gravity_mod = 1.2
                self.movement.y += self.gravity * dt * gravity_mod
                self.movement.y = min(self.movement.y, 8)

                self.wall_slide = False
                if (self.collisions["left"] or self.collisions["right"]) and self.falling > 8:
                    self.wall_slide = True
                    self.sliding = 0
                    self.movement.y = min(self.movement.y, 1.5)
                    if self.collisions["right"]:
                        self.flip = False
                    else:
                        self.flip = True

                if self.jumping < 15:
                    if self.wall_slide:
                        speed = 4
                        height = 2.78
                        if self.flip and self.last_movement[0] < 0:
                            self.rebound.x = speed
                            self.movement.y = -height
                            self.falling = 8
                            self.jumping = 30
                            self.wall_timer = 12
                            self.app.assets["sfx"]["walljump"].play()
                        elif not self.flip and self.last_movement[0] > 0:
                            self.rebound.x = -speed
                            self.movement.y = -height
                            self.falling = 8
                            self.jumping = 30
                            self.wall_timer = 12
                            self.app.assets["sfx"]["walljump"].play()
                    else:
                        if self.falling < 5:
                            self.movement.y = -self.jump_height
                            self.falling = 6
                            self.jumping = 30
                
                self.dash_timer = max(0, self.dash_timer - dt)
                if self.controls['dashing']:
                    if self.wall_timer <= 0 and self.dash_timer == 0:
                        self.app.screen_shake = max(8, self.app.screen_shake)
                        if self.flip:
                            self.dashing = -55
                        else:
                            self.dashing = 55
                        self.wall_timer = 10
                        self.app.assets["sfx"]["hit1"].play()
                        self.dash_timer = 20
                    self.controls["dashing"] = False
                first = self.dashing
                if self.dashing < 0:
                    self.dashing = min(self.dashing + self.dash_length * dt, 0)
                else:
                    self.dashing = max(self.dashing - self.dash_length * dt, 0)
                if not self.dashing and first != self.dashing:
                    for _ in range(int(10)):
                        angle = random.random() * math.pi * 2 
                        speed = random.random() * 0.5
                        pvel = [math.cos(angle) * speed, math.sin(angle) * speed]
                        self.app.particles.append(Particle(self.app, 'feather', self.get_rect().center, pvel, random.randint(0, 7), True))
                        self.app.particles[-1].particle_type = "leaf"
                        # self.app.particles[-1].speed = 0.5

                if self.dashing:
                    self.app.slomo = 1.1
                    if random.random() / dt < 1.0:
                        feather = Particle(self.app, "feather", self.get_rect().center, [0, 0], random.randint(1, 3), True)
                        feather.particle_type = "leaf"
                        self.app.particles.append(feather)
                    if abs(self.dashing) > 40:
                        self.movement[0] += self.dashing * 0.3 * dt
                        self.movement[1] += -0.1 * dt
                    else:
                        if self.falling > 5:
                            self.movement[0] += self.dashing * 0.01 * dt
                        else:
                            self.movement[0] += self.dashing * 0.001 * dt
            else:
                self.controls["dashing"] = False
                self.dashing = 0
                speed = 0.18
                if self.controls["right"]:
                    self.movement.x += speed * dt
                    self.angle_vel -= 0.15 * dt
                    self.flip = False
                if self.controls["left"]:
                    self.movement.x -= speed * dt
                    self.angle_vel += 0.15 * dt
                    self.flip = True
                if self.controls["up"]:
                    self.movement.y -= speed * dt
                if self.controls["down"]:
                    self.movement.y += speed * dt

                self.movement.x += (self.movement.x * 0.9 - self.movement.x) * dt
                self.movement.y += 0.01 * dt
                self.movement.y += (self.movement.y * 0.9 - self.movement.y) * dt
                self.angle += self.angle_vel
                self.angle_vel += (self.angle_vel * 0.9 - self.angle_vel) * dt
                self.angle += (0 - self.angle) * 0.02 * dt
                self.angle = self.angle % 360

                fm = pygame.Vector2(self.movement.x * dt, self.movement.y * dt)

                self.pos.x += fm.x
                r = self.get_rect()
                for rect in tile_map.physics_rects_around(r.center):
                    if r.colliderect(rect):
                        if fm.x > 0:
                            r.right = rect.left
                        if fm.x < 0:
                            r.left = rect.right
                        self.pos.x = r.x
                        self.movement.x = 0

                self.pos.y += fm.y
                r = self.get_rect()
                for rect in tile_map.physics_rects_around(r.center):
                    if r.colliderect(rect):
                        if fm.y >= 0:
                            r.bottom = rect.top
                            self.falling = 0
                        elif fm.y < 0:
                            r.top = rect.bottom
                        self.movement.y = 0
                        self.pos.y = r.y
        for rect in tile_map.danger_rects_around(self.get_rect().center):
            if rect.colliderect(self.get_rect()):
                self.die()
                return
        
        r = self.get_rect()
        for anchor in tile_map.anchors:
            closest_x = max(r.left, min(anchor["pos"][0], r.right))
            closest_y = max(r.top, min(anchor["pos"][1], r.bottom))

            if ((anchor["pos"][0] - closest_x) ** 2 + (anchor["pos"][1] - closest_y) ** 2 < 100):
                self.die()
                return
    
    def handle_animation(self, dt):
        if self.falling > 5:
            if self.sliding < 3:
                self.wall_jump.update(dt)
            else:
                self.jump.update(dt)
                self.wall_jump.reset()
            self.idle.reset()
            self.run.reset()
            self.land.reset()
            self.grounded = 0
        elif self.grounded < len(self.land.animation) / self.land.speed:
            self.wall_jump.reset()
            self.land.update(dt)
            self.jump.reset()
            self.run.reset()
            self.idle.reset()
        elif self.controls["left"] or self.controls["right"]:
            self.run.update(dt)
            self.idle.reset()
        else:
            self.idle.update(dt)
            self.run.reset()
        self.grounded += dt

    def die(self):
        self.ad = 0
        self.app.screen_shake = max(self.app.screen_shake, 16)
        self.app.assets["sfx"]["explosion"].play()
        for _ in range(random.randint(20, 30)):
            angle = random.random() * math.pi * 2 
            speed = random.random() * 0.5
            pvel = [math.cos(angle) * speed, math.sin(angle) * speed]
            self.app.particles.append(Particle(self.app, 'feather', self.get_rect().center, pvel, random.randint(0, 7), True))
            self.app.particles[-1].particle_type = "leaf"
        for _ in range(random.randint(50, 60)):
            spread = 5
            self.app.particles.append(Particle(self.app, "explosion", [self.get_rect().centerx + random.random() * spread - spread / 2, self.get_rect().centery + random.random() * spread - spread / 2], [0, random.random() * -1 - 0.5], random.random(), False))
            self.app.particles[-1].speed = 0.3
            self.app.particles[-1].decay = 50
        for i, color in enumerate(self.colors):
            if color != (0, 0, 0, 0) and color != (0, 0, 0, 255):
                pos = [self.pos.x - 1 + (i % 8), self.pos.y + math.floor(i / 8)]
                angle = 2 * math.pi * random.random()
                speed = random.random() + 0.5
                self.app.kickup.append([pos, [math.cos(angle) * speed, math.sin(angle) * speed - 2], random.random() * 0.05 + 0.95, random.choice(self.palette)])
        for _ in range(random.randint(20, 30)):
            angle = random.random() * math.pi * 2
            speed = random.random() * 3
            self.app.sparks.append(
                Spark(self.get_rect().center, angle, speed, [246, 242, 195])
            )
        for _ in range(random.randint(30, 50)):
            angle = -math.pi * 0.5 + (random.random() - 0.5) 
            speed = random.random() + 1
            self.app.smoke.append([list(self.get_rect().center), [math.cos(angle) * speed, math.sin(angle) * speed], 1, random.randint(200, 255), 0, random.random() * 720 - 360, (200, 200, 255)])
        for _ in range(random.randint(50, 60)):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.app.particles.append(Particle(self.app, 'particle', self.get_rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
            self.app.particles[-1].speed += 0.1
            self.app.cinders.append([list((self.get_rect().centerx, self.get_rect().bottom)), [math.cos(angle) * speed, math.sin(angle) * speed], random.randint(2, 20), (246, 242, 195)])
        for _ in range(random.randint(1, 3)):
            speed = random.random() * 5
            angle = random.random() * math.pi * 2
            self.app.particles.append(Particle(self.app, 'particle', self.get_rect().center, [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], random.randint(0, 7)))
            self.app.cinders.append([list((self.get_rect().centerx, self.get_rect().bottom)), [self.movement[0] * speed, self.movement[1] * -1], random.randint(20, 30), (246, 242, 195)])
        self.app.create_shockwave(self.get_rect().center)
        self.pos = pygame.Vector2(self.start_pos)
        self.movement = pygame.Vector2(0, 0)
        self.rebound = pygame.Vector2(0, 0)
        self.flip = False
        self.grounded = 100
        self.falling = 100
        self.jumping = 100
        self.app.slomo = 0.05
        self.dashing = False
        self.controls["dashing"] = False

    def dash(self):
        if not self.dashing:
            if self.flip:
                self.dashing = -50
                self.app.screen_shake = max(4, self.app.screen_shake)
            else:
                self.dashing = 50
                self.app.screen_shake = max(4, self.app.screen_shake)

    def draw(self, surf, scroll):
        if self.ad >= self.death_time and not self.dashing:
            if not self.water:
                anim = None
                if self.falling > 5:
                    anim = self.jump
                    if self.sliding < 3:
                        anim = self.wall_jump
                elif self.grounded < len(self.land.animation) / self.land.speed:
                    anim = self.land
                elif self.controls["left"] or self.controls["right"]:
                    anim = self.run
                else:
                    anim = self.idle
                anim.flip = self.flip
                anim.draw(surf, scroll, (self.pos.x - 1, self.pos.y))
            else:
                pb = self.app.assets["player/bubble"][0]
                rot_surf = pygame.transform.rotate(pb, self.angle)
                surf.blit(
                    rot_surf,
                    (
                        self.pos.x
                        + int(pb.get_width() / 2)
                        - int(rot_surf.get_width() / 2)
                        - scroll[0] - self.dimensions.x,
                        self.pos.y
                        + int(pb.get_height() / 2)
                        - int(rot_surf.get_height() / 2)
                        - scroll[1] - self.dimensions.y / 2,
                    ),
                )