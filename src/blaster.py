import pygame, math, random, time

from .anim import Anim
from .sparks import Spark

INTERVAL = 100

class Blaster:
    def __init__(self, app, pos):
        self.app = app
        self.pos = list(pos)
        self.start_pos = list(pos)
        # pos, dir, speed, timer
        self.bullets = []
        self.anim = Anim(self.app.assets["blaster"], 0.0, False)
        self.angle = 0
        self.target_angle = 0
        self.shooting = False
        self.timer = random.random() * INTERVAL
    
    def shoot(self):
        for i in range(4):
            angle = self.angle + i * math.pi * 0.5
            speed = 5
            self.bullets.append([[self.pos[0] + 10 + 9 * math.cos(angle), self.pos[1] + 10 + 9 * math.sin(angle)], angle, speed, 0])
            for _ in range(random.randint(3, 4)):
                self.app.sparks.append(Spark([self.pos[0] + 10 + 9 * math.cos(angle), self.pos[1] + 10 + 9 * math.sin(angle)], angle + random.random() - 0.5, random.random() + 0.5, (246, 242, 195)))
        self.target_angle = math.atan2(self.app.player.get_rect().centery - self.pos[1], self.app.player.get_rect().centerx - self.pos[0])
    
    def update(self, surf, scroll, dt, tile_map):
        self.timer += dt
        self.angle += (self.target_angle - self.angle) * 0.05 * dt 
        self.pos[1] = self.start_pos[1] + math.sin(time.time()) * 8

        if self.timer > INTERVAL:
            self.timer = 0
            self.anim.speed = 0.3
        
        if self.anim.finished:
            self.shoot()
            scr_rect = pygame.Rect(scroll[0], scroll[1], surf.get_width(), surf.get_height())
            if scr_rect.colliderect(pygame.Rect(self.pos[0], self.pos[1], 21, 21)):
                self.app.assets["sfx"]["shoot"].play()
            self.anim.reset()
            self.anim.speed = 0.0
        
        self.anim.update(dt)

        for bullet in self.bullets.copy():
            bullet[0][0] += math.cos(bullet[1]) * bullet[2] * dt
            if tile_map.solid_check(bullet[0]):
                for _ in range(random.randint(3, 4)):
                    self.app.sparks.append(Spark(list(bullet[0]), bullet[1] + math.pi + random.random() - 0.5, random.random() + 0.5, (246, 242, 195)))
                self.bullets.remove(bullet)
                continue

            bullet[0][1] += math.sin(bullet[1]) * bullet[2] * dt
            if tile_map.solid_check(bullet[0]):
                for _ in range(random.randint(3, 4)):
                    self.app.sparks.append(Spark(list(bullet[0]), bullet[1] + math.pi + random.random() - 0.5, random.random() + 0.5, (246, 242, 195)))
                self.bullets.remove(bullet)
                continue
                
            if self.app.player.get_rect().collidepoint(bullet[0]):
                self.app.player.die()
                for _ in range(random.randint(3, 4)):
                    self.app.sparks.append(Spark(list(bullet[0]), random.random() * 2 * math.pi, random.random() + 0.5, (246, 242, 195)))
                self.bullets.remove(bullet)
                continue
            
            bullet[3] += dt
            if bullet[3] > 600:
                for _ in range(random.randint(3, 4)):
                    self.app.sparks.append(Spark(list(bullet[0]), random.random() * 2 * math.pi, random.random() + 0.5, (246, 242, 195)))
                self.bullets.remove(bullet)
                continue
            
            img = self.app.assets["bullet"]
            rot_surf = pygame.transform.rotate(img, math.degrees(bullet[1]))
            surf.blit(rot_surf, (bullet[0][0] + int(img.get_width() / 2) - int(rot_surf.get_width()) - scroll[0], bullet[0][1] + int(img.get_height() / 2) - int(rot_surf.get_height() / 2) - scroll[1]))

        self.anim.draw(surf, scroll, self.pos, math.degrees(-self.angle))
