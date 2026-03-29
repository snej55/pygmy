import pygame, random, math

from .anim import Anim

class Player:
    def __init__(self, app, dimensions, start_pos):
        self.app = app
        self.dimensions = pygame.Vector2(dimensions)
        self.start_pos = start_pos
        self.pos = pygame.Vector2(start_pos)

        self.falling = 30
        self.grounded = 0
        self.jumping = 30

        self.controls = {"up": False, "down": False, "right": False, "left": False}

        self.movement = pygame.Vector2(0, 0)

        self.flip = False

        self.water = False
        self.angle = 0
        self.angle_vel = 0
        self.ad = 120
        self.death_time = 120
        self.speed = 0.6
        self.jump_height = 3
        self.gravity = 0.23

    def get_rect(self):
        return pygame.Rect(self.pos.x, self.pos.y, self.dimensions.x, self.dimensions.y)

    def update(self, dt, tile_map):
        self.ad += dt
        if self.ad > self.death_time:
            if not self.water:
                self.falling += dt
                self.jumping += dt
                self.grounded += dt

                if self.controls["right"]:
                    self.movement.x += self.speed * dt
                    self.flip = False
                if self.controls["left"]:
                    self.movement.x -= self.speed * dt
                    self.flip = True
                self.movement.x += (self.movement.x * 0.6 - self.movement.x) * dt

                self.movement.y += self.gravity * dt
                self.movement.y = min(self.movement.y, 8)

                if self.falling < 5:
                    if self.jumping < 15:
                        self.movement.y = -self.jump_height
                        self.falling = 6
                        self.jumping = 30

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
                self.dimensions = pygame.Vector2(6, 7)
            else:
                self.dimensions = pygame.Vector2(12, 13)
                speed = 0.08
                if self.controls["right"]:
                    self.movement.x += speed * dt
                    self.angle_vel -= 0.5 * dt
                    self.flip = False
                if self.controls["left"]:
                    self.movement.x -= speed * dt
                    self.angle_vel += 0.5 * dt
                    self.flip = True
                if self.controls["up"]:
                    self.movement.y -= speed * dt
                if self.controls["down"]:
                    self.movement.y += speed * dt

                self.movement.x += (self.movement.x * 0.95 - self.movement.x) * dt
                self.movement.y += 0.01 * dt
                self.movement.y += (self.movement.y * 0.95 - self.movement.y) * dt
                self.angle += self.angle_vel
                self.angle_vel += (self.angle_vel * 0.95 - self.angle_vel) * dt
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

    def die():
        pass

    def draw(self, surf, scroll):
        pygame.draw.rect(surf, (255, 0, 255), (self.pos.x - scroll[0], self.pos.y - scroll[1], self.dimensions.x, self.dimensions.y))