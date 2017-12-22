
import logging
from PIL import Image
import sdl2
from random import randint

from slowboy.mmu import MMU
from slowboy.z80 import Z80
from slowboy.gpu import GPU
from slowboy.gfx import RGBTileset, GBTileset

class HeadlessUI():
    def __init__(self, romfile, log_level=logging.WARNING):
        with open(romfile, 'rb') as f:
            rom = f.read()
        mmu = MMU(rom)
        self.cpu = Z80(mmu=mmu, log_level=log_level)

    def start(self):
        self.cpu.go()

SCREEN_WIDTH = 160
SCREEN_HEIGHT = 144

class SDLUI():
    def __init__(self, romfile, log_level=logging.WARNING):
        with open(romfile, 'rb') as f:
            rom = f.read()
        self.cpu = Z80(rom=rom, log_level=log_level)
        #img = Image.open('test_tiles2.png').convert('L')
        #rgb_tileset = RGBTileset(img.tobytes(), img.size, (8, 8))
        #gb_tileset = rgb_tileset.to_gb([0x00, 0x40, 0xc0, 0xff])

        self.window = sdl2.ext.Window('slowboy', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.window.show()
        self.surface = self.window.get_surface()
        #surface = SDL_CreateRGBSurfaceWithFormat(0, BACKGROUND_WIDTH, BACKGROUND_HEIGHT,
        #                                         32, sdl2.SDL_PIXELFORMAT_RGBA32)
        #tilemap0 = bytes(randint(0, 255) for _ in range(0x400))
        #tilemap1 = bytes(randint(0, 255) for _ in range(0x400))
        #print(tilemap0, tilemap1)
        #print(gb_tileset.data)
        #print(len(gb_tileset.data))
        #assert len(gb_tileset.data) == 384*16
        #assert len(tilemap0) + len(tilemap1) == 0x800
        #self._tileset_data = gb_tileset.data 
        #data = self._tileset_data + tilemap0 + tilemap1
        #self.gpu.load_vram(data)
        #self.gpu.load_oam()

    def start(self):
        #self.cpu.go()
        pass

    def step(self):
        self.cpu.step()
        self.present()
        self.window.refresh()

    def present(self):
        self.cpu.gpu.bgp = 0xe4
        self.cpu.gpu.draw(self.surface)
        self.cpu.gpu.present()
        #tilemap0 = bytes(randint(0, 255) for _ in range(0x400))
        #tilemap1 = bytes(randint(0, 255) for _ in range(0x400))
        #data = self._tileset_data + tilemap0 + tilemap1
        #self.gpu.load_vram(data)

if __name__ == '__main__':
    import sys
    ui = SDLUI(sys.argv[1])
    ui.start()
    running = True
    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.events.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                #if event.key.keysym.sym == sdl2.SDLK_DOWN:
                #    scy += 1
                #    scy = min(BACKGROUND_HEIGHT-SCREEN_HEIGHT, scy)
                #elif event.key.keysym.sym == sdl2.SDLK_UP:
                #    scy -= 1
                #    scy = max(0, scy)
                #elif event.key.keysym.sym == sdl2.SDLK_RIGHT:
                #    scx += 1
                #    scx = min(BACKGROUND_WIDTH-SCREEN_WIDTH, scx)
                #elif event.key.keysym.sym == sdl2.SDLK_LEFT:
                #    scx -= 1
                #    scx = max(0, scx)
                #draw_screen(renderer, (scx, scy))
                pass

        sdl2.SDL_Delay(10)

        print('[')
        ui.step()
        print(']')
        #sdl2.SDL_UpdateWindowSurface(ui.window.window)
