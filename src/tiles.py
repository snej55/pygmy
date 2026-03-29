import pygame
from .util import read_json

TILE_SIZE = 8
OFFSETS = {(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (0, 0)}
PHYSICS_TILES = {"grass"}
DANGER_TILES = ["spikes"]

class TileMap:
    def __init__(self, app):
        self.app = app
        self.tile_map = {}
        self.off_grid = []
        self.springs = []
    
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

        for tile in data["level"]["tiles"]:
            tile_loc = f"{tile['pos'][0]};{tile['pos'][1]}"
            self.tile_map[tile_loc] = {
                "type": tile["type"],
                "variant": tile["variant"],
                "pos": tile["pos"],
            }

        # load off grid tiles
        self.off_grid.extend(data["level"]["off_grid"])
        for tile in self.off_grid:
            tile["type"] = tile["type"]
        
        self.extract_springs()

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
        for x in range(scroll[0] // TILE_SIZE, (scroll[0] + surf.get_width()) // TILE_SIZE + 1):
            for y in range(scroll[1] // TILE_SIZE, (scroll[1] + surf.get_height()) // TILE_SIZE + 1):
                loc = str(x) + ";" + str(y)
                if loc in self.tile_map:
                    tile = self.tile_map[loc]

                    surf.blit(
                        self.app.assets[f"tiles/{tile["type"]}"][tile["variant"]],
                        (x * TILE_SIZE - scroll[0], y * TILE_SIZE - scroll[1]),
                    )
