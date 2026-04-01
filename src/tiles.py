import pygame, math, time

from .util import read_json
from .grass import GrassManager
from .water import Water

TILE_SIZE = 8
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {"grass", "bricks"}
DANGER_TILES = ["spikes"]

class TileMap:
    def __init__(self, app):
        self.app = app
        self.tile_map = {}
        self.off_grid = []
        self.springs = []
        self.water = []
        self.grass_map = {}
        self.grass_manager = None
        self.light_map = {}
        self.anchors = []
    
    def extract_springs(self):
        self.springs = []
        spring_locs = []
        for loc in self.tile_map:
            if self.tile_map[loc]["type"] == "spring":
                self.springs.append({
                    "pos": (self.tile_map[loc]["pos"][0] * TILE_SIZE, self.tile_map[loc]["pos"][1] * TILE_SIZE + 2),
                    "offset": 0,
                    "vel": 0
                })
                spring_locs.append(loc)
        for loc in spring_locs:
            del self.tile_map[loc]
    
    def update_springs(self, dt, player):
        for spring in self.springs:
            tension = 0.1
            force = -spring["offset"] * tension
            spring["vel"] += force * dt
            spring["offset"] += spring["vel"] * dt
            spring["vel"] += (spring["vel"] * 0.9 - spring["vel"]) * dt
            rect = pygame.Rect(spring["pos"][0] - 1, spring["pos"][1] + spring["offset"], 10, 4)
            if rect.colliderect(player.get_rect()):
                player.movement.y = -4.5
                spring["offset"] = 4
    
    def render_springs(self, surf, scroll):
        screen_rect = pygame.Rect(0, 0, surf.get_width(), surf.get_height())
        for spring in self.springs:
            rect = pygame.Rect(spring["pos"][0] - scroll[0], spring["pos"][1] + spring["offset"] - scroll[1], 8, 4)
            if screen_rect.colliderect(rect):
                pygame.draw.line(surf, (175, 191, 210), (rect.x + 3, rect.y), (rect.x + 3, spring["pos"][1] + 8 - scroll[1]))
                pygame.draw.line(surf, (79, 103, 129), (rect.x + 4, rect.y), (rect.x + 4, spring["pos"][1] + 8 - scroll[1]))
                surf.blit(self.app.assets["spring"], (rect.x, rect.y))

    def load(self, path):
        data = read_json(path)

        self.tile_map = {}
        self.off_grid = []
        self.water = []
        self.anchors = []

        for tile in data["level"]["tiles"]:
            tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
            img = None
            try:
                img = self.app.assets[f"tiles/{tile['type']}"][tile["variant"]].copy()
            except KeyError:
                pass
            self.tile_map[tile_loc] = {
                "type": tile["type"],
                "variant": tile["variant"],
                "pos": tile["pos"],
                "img": img
            }

        # load off grid tiles
        self.off_grid.extend(data["level"]["off_grid"])
        for tile in self.off_grid:
            tile["type"] = tile["type"]
        
        for water in data["level"]["water"]:
            self.water.append(Water(water[0], water[1], [water[2], water[3]], 3))
        
        for anchor in data["level"]["anchors"]:
            self.anchors.append({"start": anchor["start"].copy(), "end": anchor["end"].copy(), "angle": 0, "pos": anchor["start"].copy(), "time": 0})
        
        self.extract_springs()
        self.extract_grass()
        self.calculate_light_map()
    
    def extract_grass(self):
        grass_locs = []
        self.grass_map = {}
        for loc in self.tile_map:
            if self.tile_map[loc]["type"] == "grass_key":
                self.grass_map[loc] = None
                grass_locs.append(loc)
        
        for loc in grass_locs:
            del self.tile_map[loc]
        
        self.grass_manager = GrassManager(self.app, self.app.assets["grass"])
        self.grass_manager.load(self.grass_map, 8, 2)
    
    def update_anchors(self, dt):
        for anchor in self.anchors:
            anchor["time"] += dt
            target = anchor["end"]
            base = anchor["start"]
            
            dist = (math.sin(anchor["time"] * 0.01) + 1) * 0.5
            anchor["pos"][0] = base[0] + (target[0] - base[0]) * dist
            anchor["pos"][1] = base[1] + (target[1] - base[1]) * dist
            # print(dist)

            anchor["angle"] += math.cos(anchor["time"] * 0.01) * dt * 10
    
    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.off_grid.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.off_grid.remove(tile)
        for loc in self.tile_map.copy():
            tile = self.tile_map[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= TILE_SIZE
                matches[-1]['pos'][1] *= TILE_SIZE
                if not keep:
                    del self.tile_map[loc]
        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // TILE_SIZE), int(pos[1] // TILE_SIZE))
        for offset in OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            if check_loc in self.tile_map:
                tiles.append(self.tile_map[check_loc])
        return tiles

    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // TILE_SIZE)) + ";" + str(int(pos[1] // TILE_SIZE))
        if tile_loc in self.tile_map:
            if self.tile_map[tile_loc]["type"] in PHYSICS_TILES:
                return self.tile_map[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(tile["pos"][0] * TILE_SIZE, tile["pos"][1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        return rects

    def danger_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in DANGER_TILES:
                rects.append(
                    pygame.Rect(tile["pos"][0] * TILE_SIZE, tile["pos"][1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                )
        return rects

    def draw_decor(self, surf, scroll):
        for tile in self.off_grid:
            surf.blit(
                self.app.assets[f"tiles/{tile['type']}"][tile["variant"]], (tile["pos"][0] - scroll[0], tile["pos"][1] - scroll[1])
            )

    def draw(self, surf, scroll):
        self.render_springs(surf, scroll)
        self.grass_manager.draw(surf, (scroll[0] + 8, scroll[1] - 3))
        for x in range(scroll[0] // TILE_SIZE, (scroll[0] + surf.get_width()) // TILE_SIZE + 1):
            for y in range(scroll[1] // TILE_SIZE, (scroll[1] + surf.get_height()) // TILE_SIZE + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tile_map:
                    tile = self.tile_map[loc]

                    surf.blit(
                        self.app.assets[f"tiles/{tile["type"]}"][tile["variant"]],
                        (x * TILE_SIZE - scroll[0], y * TILE_SIZE - scroll[1]),
                    )
        
        anchor_img = self.app.assets["anchor"]
        for anchor in self.anchors:
            rot_surf = pygame.transform.rotate(anchor_img, anchor["angle"])            
            surf.blit(rot_surf, (anchor["pos"][0] + int(anchor_img.get_width() / 2) - int(rot_surf.get_width() / 2) - scroll[0], anchor["pos"][1] + int(anchor_img.get_height() / 2) - int(rot_surf.get_height() / 2) - scroll[1]))

    def calculate_light_map(self):
        print("Generating light map...")
        start = time.time()
        self.light_map = {}
        levelMin = [1000000, 1000000]
        levelMax = [0, 0]
        for loc in self.tile_map:
            x, y = [int(c) for c in loc.split(';')]
            levelMin[0] = min(levelMin[0], x)
            levelMin[1] = min(levelMin[1], y)
            levelMax[0] = max(levelMax[0], x)
            levelMax[1] = max(levelMax[1], y)
        # levelMin[0] -= 100
        # levelMax[0] += 100
        levelMin[1] -= 10
        # levelMax[1] += 100
        
        queue = []
        for x in range(levelMax[0] - levelMin[0]):
            for y in range(levelMax[1] - levelMin[1]):
                loc = f'{x};{y}'
                tile_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                attenuation = 1.0
                for water in self.water:
                    if water.get_rect().colliderect(tile_rect):
                        attenuation = 0.7
                if not (loc in self.tile_map):
                    queue.append({"pos": [x, y], "attenuation": attenuation})
                elif not (self.tile_map[loc]["type"] in PHYSICS_TILES):
                    queue.append({"pos": [x, y], "attenuation": attenuation})
        
        absorb = 0.7
        while len(queue) > 0:
            for tile in queue.copy():
                self.light_map[f"{tile["pos"][0]};{tile["pos"][1]}"] = tile["attenuation"]
                for shift in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
                    pos = [tile["pos"][0] + shift[0], tile["pos"][1] + shift[1]]
                    check_loc = f"{pos[0]};{pos[1]}"
                    if not (check_loc in self.light_map) and (levelMin[0] <= pos[0] < levelMax[0] and levelMin[1] <= pos[1] < levelMax[1]):
                        solid = False
                        if check_loc in self.tile_map:
                            if self.tile_map[check_loc]["type"] in PHYSICS_TILES:
                                solid = True
                        if solid:
                            attenuation = max(tile["attenuation"] * absorb, 0.0)
                            self.light_map[check_loc] = attenuation
                            queue.append({"pos": pos, "attenuation": attenuation})
                        else:
                            tile_rect = pygame.Rect(pos[0] * TILE_SIZE, pos[1] * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                            attenuation = 1.0
                            self.light_map[check_loc] = attenuation
                            queue.append({"pos": pos, "attenuation": attenuation})
                queue.remove(tile)
            # print(f"{len(self.light_map)}/{(levelMax[0] - levelMin[0]) * (levelMax[1] - levelMin[1])}")
        print(f"Generated light map! ({(time.time() - start) * 1000 :.2f} ms)")
                

    def get_light_data(self, surf, scroll) -> pygame.Surface:
        grid_size = (math.ceil(surf.get_width() / TILE_SIZE) + 2, math.ceil(surf.get_height() / TILE_SIZE) + 2)

        light_surf = pygame.Surface(grid_size)
        light_surf.fill((0, 0, 0))

        offset_x = math.floor(scroll[0] / TILE_SIZE) - 1
        offset_y = math.floor(scroll[1] / TILE_SIZE) - 1

        for x in range(grid_size[0]):
            tile_x = offset_x + x
            for y in range(grid_size[1]):
                tile_y = offset_y + y
                loc = f"{tile_x};{tile_y}"
                if loc in self.light_map:
                    r = self.light_map[loc]
                    g = self.light_map[loc] ** 1.2
                    b = self.light_map[loc] ** 1.5
                    light_surf.set_at((x, y), (r * 255, g * 255, b * 255))

        return light_surf
