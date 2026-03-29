# Created by Jens Kromdijk 29/03/2026
import pygame, os, json, math
from pathlib import Path

global SCRIPT_PATH
SCRIPT_PATH = './'
BASE_IMG_PATH = "data/images/"
BASE_AUDIO_PATH = "data/audio/"

def load_image(path) -> pygame.Surface:
    global SCRIPT_PATH
    surf = pygame.image.load(SCRIPT_PATH + BASE_IMG_PATH + path).convert()
    surf.set_colorkey((0, 0, 0))
    return surf


def load_images(path):
    global SCRIPT_PATH
    imgs = []
    for img_path in os.listdir(SCRIPT_PATH + BASE_IMG_PATH + path):
        imgs.append(load_image(path + "/" + img_path))
    return imgs


def load_sound(path) -> pygame.mixer.Sound:
    global SCRIPT_PATH
    return pygame.mixer.Sound(SCRIPT_PATH + BASE_AUDIO_PATH + path)


def load_animation(path, xsize, y, length):
    sheet = load_image(path)
    animation = []
    for x in range(length):
        animation.append(snip(sheet, [x * xsize, 0], [xsize, y]))
    return animation


def load_tile_imgs(path, tile_size):
    img = load_image(path)
    img_surf = pygame.Surface((tile_size, tile_size))
    tiles = []
    dimensions = [int(img.get_width() / tile_size), int(img.get_height() / tile_size)]
    for y in range(dimensions[1]):
        for x in range(dimensions[0]):
            img_surf.fill((0, 0, 0))
            img_surf.blit(img, (-x * tile_size, -y * tile_size))
            img_surf.convert()
            img_surf.set_colorkey((0, 0, 0))
            tiles.append(img_surf.copy())
    return tiles


def snip(spritesheet, pos, dimensions):
    clip_rect = pygame.Rect(pos, dimensions)
    image = spritesheet.subsurface(clip_rect)
    return image


def read_json(path):
    global SCRIPT_PATH
    f = open(SCRIPT_PATH + path, "r")
    data = json.load(f)
    f.close()
    return data


def write_json(path, data):
    global SCRIPT_PATH
    f = open(SCRIPT_PATH + path, "w")
    json.dump(data, f)
    f.close()


def load_palette(img: pygame.Surface):
    img_array = pygame.pixelarray.PixelArray(img)
    palette = []
    for row in img_array:
        for color in row:
            c = img.unmap_rgb(color)
            if c != (0, 0, 0, 0) and c != (0, 0, 0, 255):
                palette.append(tuple(c))
    return palette
