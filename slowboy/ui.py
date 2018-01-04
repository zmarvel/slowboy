
import logging
import sdl2
import sdl2.ext
import select

from slowboy.mmu import MMU
from slowboy.z80 import Z80
from slowboy.gpu import SCREEN_WIDTH, SCREEN_HEIGHT, VRAM_START, BACKGROUND_SIZE
from slowboy.util import hexdump


class HeadlessUI():
    def __init__(self, romfile, log_level=logging.WARNING):
        with open(romfile, 'rb') as f:
            rom = f.read()
        mmu = MMU(rom)
        self.cpu = Z80(mmu=mmu, log_level=log_level)

    def start(self):
        self.cpu.go()


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
        # sprite_factory = sdl2.ext.SpriteFactory(sprite_type=sdl2.ext.SOFTWARE)
        # self.font_surf = sprite_factory.from_image('/home/zack/src/slowboy/alchemy_font.bmp')
        # self.font = sdl2.ext.BitmapFont(self.font_surf, (8, 8), mapping=font_map)

        # surface = SDL_CreateRGBSurfaceWithFormat(0, BACKGROUND_WIDTH, BACKGROUND_HEIGHT,
        #                                          32, sdl2.SDL_PIXELFORMAT_RGBA32)
        # tilemap0 = bytes(randint(0, 255) for _ in range(0x400))
        # tilemap1 = bytes(randint(0, 255) for _ in range(0x400))
        # print(tilemap0, tilemap1)
        # print(gb_tileset.data)
        # print(len(gb_tileset.data))
        # assert len(gb_tileset.data) == 384*16
        # assert len(tilemap0) + len(tilemap1) == 0x800
        # self._tileset_data = gb_tileset.data
        # data = self._tileset_data + tilemap0 + tilemap1
        # self.gpu.load_vram(data)
        # self.gpu.load_oam()

    def start(self):
        # self.cpu.go()
        pass

    def step(self):
        self.cpu.step()
        self.present(self.surface)
        # sdl2.SDL_FillRect(self.surface, sdl2.SDL_Rect(0, SCREEN_HEIGHT, SCREEN_WIDTH+32, 32), 0xffffffff)
        # sdl2.SDL_FillRect(self.surface, sdl2.SDL_Rect(SCREEN_WIDTH, 0, 32, SCREEN_HEIGHT), 0xffffffff)

        # text_sprite = self.font.render('1024 ABCD')
        # self.font.render_on(self.text_surface, '1024 ABCD', (0, 0))
        # w, h = text_sprite.size
        # src = sdl2.SDL_Rect(0, 0, w, h)
        # dest = sdl2.SDL_Rect(0, SCREEN_HEIGHT, w, h)
        # sdl2.SDL_BlitSurface(text_sprite.surface, src, self.surface, dest)

        # lines = []
        # for reg in regs:
        #     val = self.cpu.registers[reg]
        #     line = '{} {:02x}'.format(reg, val).upper()
        #     lines.append(line)
        # lines.append('PC  ')
        # lines.append('{:04x}'.format(self.cpu.get_pc()).upper())
        # lines.append('SP  ')
        # lines.append('{:04x}'.format(self.cpu.get_sp()).upper())
        # lines = '\n'.join(lines)
        # text_sprite = self.font.render(lines)
        # w, h = text_sprite.size
        # src = sdl2.SDL_Rect(0, 0, w, h)
        # dest = sdl2.SDL_Rect(SCREEN_WIDTH, 0, w, h)
        # sdl2.SDL_BlitSurface(text_sprite.surface, src, self.surface, dest)

    def present(self, surface):
        if self.cpu.gpu.draw(surface):
            self.window.refresh()
        self.cpu.gpu.present()

if __name__ == '__main__':
    import sys
    import logging
    root_logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    # ui = SDLUI(sys.argv[1], logger=root_logger, log_level=logging.DEBUG)
    ui = SDLUI(sys.argv[1], log_level=root_logger.level)
    ui.start()
    running = True
    step = True
    breakpoint = None

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

                # if event.key.keysym.sym == sdl2.SDLK_DOWN:
                #     scy += 1
                #     scy = min(BACKGROUND_HEIGHT-SCREEN_HEIGHT, scy)
                # elif event.key.keysym.sym == sdl2.SDLK_UP:
                #     scy -= 1
                #     scy = max(0, scy)
                # elif event.key.keysym.sym == sdl2.SDLK_RIGHT:
                #     scx += 1
                #     scx = min(BACKGROUND_WIDTH-SCREEN_WIDTH, scx)
                # elif event.key.keysym.sym == sdl2.SDLK_LEFT:
                #     scx -= 1
                #     scx = max(0, scx)
                # draw_screen(renderer, (scx, scy))

        if ui.cpu.pc == breakpoint and not step:
            step = True
            print('hit breakpoint', hex(breakpoint))

        if not step:
            ui.step()

        rlist, _, _ = select.select((sys.stdin,), (), (), 0)
        if rlist:
            line = sys.stdin.readline().rstrip()
            line = line.split(' ')
            command = line[0]
            if command == 's':
                step = True
                ui.step()
            elif command == 'c':
                step = False
            elif command == 'q':
                running = False
            elif command == 'reg':
                ui.cpu.log_regs(log=ui.logger.info)
                ui.cpu.log_op(log=ui.logger.info)
            elif command == 'gpu':
                subc = line[1]
                if subc == 'reg':
                    ui.cpu.gpu.log_regs(log=ui.logger.info)
                elif subc == 'debug':
                    ui.cpu.gpu.logger.setLevel(logging.DEBUG)
                elif subc == 'info':
                    ui.cpu.gpu.logger.setLevel(logging.INFO)
                elif subc == 'dump':
                    src = line[2]
                    if src == 'data':
                        bgdata_start = 0x8000 - VRAM_START
                        for line in hexdump(ui.cpu.gpu.vram[bgdata_start:bgdata_start+0x1800], 16):
                            print(line)
                    elif src == 'map':
                        bgmap_start = 0x9800 - VRAM_START
                        for line in hexdump(ui.cpu.gpu.vram[bgmap_start:bgmap_start+0x800], 16, start=VRAM_START):
                            print(line)
                    else:
                        raise ValueError('Expected "map" or "data".')
                elif subc == 'display':
                    src = line[2]
                    import PIL
                    from PIL import Image
                    if src == 'data':
                        #img = Image.frombytes("L", BACKGROUND_SIZE, bytes(ui.cpu.gpu._bgtileset.to_rgb().data))
                        #img.show()
                        from slowboy.gpu import GBTileset
                        vram = ui.cpu.gpu.vram
                        tileset = GBTileset(vram[0x8000-VRAM_START:0x8000-VRAM_START+0x1800], (32*8, 12*8), (8, 8))
                        palette = ui.cpu.gpu._bgpalette
                        img = Image.frombytes("L", (32*8, 12*8), bytes(tileset.to_rgb(palette).data))
                        img.show()
                    elif src == 'map':
                        raise NotImplementedError('display "map"')
                    else:
                        raise ValueError('Expected "map" or "data".')
            elif command == 'regwatch':
                cmd, arg = line.split(' ')
                watched_reg = None if arg == 'None' else arg
            elif line == 'rominfo':
                ui.cpu.mmu.log_rominfo()
            elif line == 'debug':
                logging.getLogger().setLevel(logging.DEBUG)
                print('set logger to DEBUG')
            elif line == 'info':
                logging.getLogger().setLevel(logging.INFO)
                print('set logger to INFO')
            elif line == 'flags':
                print('H: ', ui.cpu.get_carry_flag())
                print('C: ', ui.cpu.get_halfcarry_flag())
                print('N: ', ui.cpu.get_sub_flag())
                print('Z: ', ui.cpu.get_zero_flag())
            elif line == 'break': # break
                _, addr = line.split(' ')
                breakpoint = int(addr, 16)
                print('set breakpoint at {:#04x}'.format(breakpoint))
            elif line == 'mem':
                line = line.split(' ')
                start = int(line[1], 16)
                end = int(line[2], 16) if len(line) > 1 else start+1
                for addr in range(start, end):
                    print(hex(addr), ':', hex(ui.cpu.mmu.get_addr(addr)))

        if step:
            sdl2.SDL_Delay(100)

        # sdl2.SDL_UpdateWindowSurface(ui.window.window)
