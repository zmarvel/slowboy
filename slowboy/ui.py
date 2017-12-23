
import logging
import sdl2
import sdl2.ext
import select

from slowboy.mmu import MMU
from slowboy.z80 import Z80

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

regs = ('a', 'f', 'b', 'c', 'd', 'e', 'h', 'l')

font_map = ["!\"%'YZ+,-.X=_?0 ",
            "123456789ABCDEFG",
            "HIJKLMNOPQRSTUVW"
            ]

class SDLUI():
    def __init__(self, romfile, log_level=logging.WARNING):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        with open(romfile, 'rb') as f:
            rom = f.read()
        self.cpu = Z80(rom=rom, log_level=log_level)

        self.window = sdl2.ext.Window('slowboy', (SCREEN_WIDTH+32, SCREEN_HEIGHT+32))
        self.window.show()
        self.surface = self.window.get_surface()
        #sprite_factory = sdl2.ext.SpriteFactory(sprite_type=sdl2.ext.SOFTWARE)
        #self.font_surf = sprite_factory.from_image('/home/zack/src/slowboy/alchemy_font.bmp')
        #self.font = sdl2.ext.BitmapFont(self.font_surf, (8, 8), mapping=font_map)

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
        self.present(self.surface)
        #sdl2.SDL_FillRect(self.surface, sdl2.SDL_Rect(0, SCREEN_HEIGHT, SCREEN_WIDTH+32, 32), 0xffffffff)
        #sdl2.SDL_FillRect(self.surface, sdl2.SDL_Rect(SCREEN_WIDTH, 0, 32, SCREEN_HEIGHT), 0xffffffff)

        #text_sprite = self.font.render('1024 ABCD')
        #self.font.render_on(self.text_surface, '1024 ABCD', (0, 0))
        #w, h = text_sprite.size
        #src = sdl2.SDL_Rect(0, 0, w, h)
        #dest = sdl2.SDL_Rect(0, SCREEN_HEIGHT, w, h)
        #sdl2.SDL_BlitSurface(text_sprite.surface, src, self.surface, dest)

        #lines = []
        #for reg in regs:
        #    val = self.cpu.registers[reg]
        #    line = '{} {:02x}'.format(reg, val).upper()
        #    lines.append(line)
        #lines.append('PC  ')
        #lines.append('{:04x}'.format(self.cpu.get_pc()).upper())
        #lines.append('SP  ')
        #lines.append('{:04x}'.format(self.cpu.get_sp()).upper())
        #lines = '\n'.join(lines)
        #text_sprite = self.font.render(lines)
        #w, h = text_sprite.size
        #src = sdl2.SDL_Rect(0, 0, w, h)
        #dest = sdl2.SDL_Rect(SCREEN_WIDTH, 0, w, h)
        #sdl2.SDL_BlitSurface(text_sprite.surface, src, self.surface, dest)
        self.window.refresh()

    def present(self, surface):
        #self.cpu.gpu.bgp = 0xe4
        self.cpu.gpu.draw(surface) # TODO improve performance
        self.cpu.gpu.present()

if __name__ == '__main__':
    import sys
    import logging
    root_logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    #ui = SDLUI(sys.argv[1], logger=root_logger, log_level=logging.DEBUG)
    ui = SDLUI(sys.argv[1], log_level=root_logger.level)
    ui.start()
    running = True
    step = True

    while running:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.events.SDL_QUIT:
                running = False
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_s:
                    step = True
                    ui.step()
                elif event.key.keysym.sym == sdl2.SDLK_c:
                    step = False
                elif event.key.keysym.sym == sdl2.SDLK_q:
                    running = False
                    break

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

        if step:
            pass
        else:
            ui.step()


        rlist, _, _ = select.select((sys.stdin,), (), (), 0.001)
        if rlist:
            line = sys.stdin.readline().rstrip()
            if line == 's':
                step = True
                ui.step()
            elif line == 'c':
                step = False
            elif line == 'q':
                running = False
            elif line == 'reg':
                pc = ui.cpu.get_pc()
                op = ui.cpu.mmu.get_addr(pc)
                print('pc:', hex(pc), ui.cpu.opcode_map[op].description)
                print('sp:', hex(ui.cpu.get_sp()))
                for reg in regs:
                    print('{}: {:#02x}'.format(reg, ui.cpu.get_reg8(reg)))
            elif line.startswith('regwatch'):
                cmd, arg = line.split(' ')
                watched_reg = None if arg == 'None' else arg
            elif line == 'rominfo':
                ui.cpu.mmu.log_rominfo()
            elif line == 'debug':
                logging.getLogger().setLevel(logging.DEBUG)
                #root_logger.setLevel(logging.DEBUG)
                #logging.getLogger('slowboy.ui').setLevel(logging.DEBUG)
                #logging.getLogger('slowboy.z80').setLevel(logging.DEBUG)
                #ui.logger.setLevel(logging.DEBUG)
                #ui.cpu.logger.setLevel(logging.DEBUG)
                #ui.cpu.mmu.logger.setLevel(logging.DEBUG)
                #ui.cpu.gpu.logger.setLevel(logging.DEBUG)
                print('set logger to DEBUG')
            elif line == 'info':
                logging.getLogger().setLevel(logging.INFO)
                print('set logger to INFO')

        if step:
            sdl2.SDL_Delay(1)

        #sdl2.SDL_UpdateWindowSurface(ui.window.window)
