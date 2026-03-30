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

        self.water = False
        self.angle = 0
        self.angle_vel = 0
        self.ad = 120
        self.death_time = 120
        self.speed = 0.9
        self.jump_height = 3.07
        self.gravity = 0.23
        self.collisions = {"right": False, "left": False, "up": False, "down": False}
        self.wall_slide = False
        self.wall_timer = 0
        self.rebound = pygame.Vector2(0, 0)
        self.dashing = 0
        self.sliding = 100
        self.down_timer = 0

        self.water = False

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
                        if fm.x < 0:
                            r.left = rect.right
                            self.collisions["left"] = True
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
                        elif fm.y < 0:
                            r.top = rect.bottom
                            self.collisions["up"] = True
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

                self.movement.y += self.gravity * dt
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
                        elif not self.flip and self.last_movement[0] > 0:
                            self.rebound.x = -speed
                            self.movement.y = -height
                            self.falling = 8
                            self.jumping = 30
                            self.wall_timer = 12
                    else:
                        if self.falling < 5:
                            self.movement.y = -self.jump_height
                            self.falling = 6
                            self.jumping = 30
                
                if self.controls['dashing']:
                    if self.wall_timer <= 0:
                        self.app.screen_shake = max(8, self.app.screen_shake)
                        if self.flip:
                            self.dashing = -55
                        else:
                            self.dashing = 55
                        self.wall_timer = 10
                    self.controls["dashing"] = False
                if self.dashing < 0:
                    self.dashing = min(self.dashing + 25 * dt, 0)
                else:
                    self.dashing = max(self.dashing - 25 * dt, 0)
                if self.dashing:
                    if abs(self.dashing) > 40:
                        self.movement[0] += self.dashing * 0.3
                        self.movement[1] += -0.1 * dt 
                    else:
                        if self.falling > 5:
                            self.movement[0] += self.dashing * 0.01
                        else:
                            self.movement[0] += self.dashing * 0.001
            else:
                speed = 0.08
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
        pass

    def dash(self):
        if not self.dashing:
            if self.flip:
                self.dashing = -50
                self.app.screen_shake = max(4, self.app.screen_shake)
            else:
                self.dashing = 50
                self.app.screen_shake = max(4, self.app.screen_shake)

    def draw(self, surf, scroll):
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