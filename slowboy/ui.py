
import logging
import sdl2
import sdl2.ext
import select
import sys
import argparse as ap

from slowboy.mmu import MMU
from slowboy.z80 import Z80
from slowboy.gpu import SCREEN_WIDTH, SCREEN_HEIGHT, VRAM_START, OAM_START, BACKGROUND_SIZE
from slowboy.util import hexdump, print_lines


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

    def start(self):
        # self.cpu.go()
        pass

    def step(self):
        self.cpu.step()
        self.present(self.surface)

    def present(self, surface):
        if self.cpu.gpu.draw(surface):
            self.window.refresh()
        self.cpu.gpu.present()

def command(ui, state):
    line = sys.stdin.readline().rstrip()
    line = line.split(' ')
    command = line[0]
    if command == 's':
        state['step'] = True
        ui.step()
    elif command == 'c':
        state['step'] = False
    elif command == 'q':
        ui.cpu.log_regs(log=ui.logger.info)
        ui.cpu.log_op(log=ui.logger.info)
        state['running'] = False
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
            if src == 'vram':
                bgdata_start = 0x8000 - VRAM_START
                print_lines(hexdump(ui.cpu.gpu.vram[bgdata_start:bgdata_start+0x1800], 16, start=0x8000))
            elif src == 'map':
                bgmap_start = 0x9800 - VRAM_START
                print_lines(hexdump(ui.cpu.gpu.vram[bgmap_start:bgmap_start+0x800], 16, start=0x9800))
            elif src == 'oam':
                print_lines(hexdump(ui.cpu.gpu.oam, 16, start=OAM_START))
            else:
                raise ValueError('Expected "map," "vram," or "oam."')
        elif subc == 'display':
            src = line[2]
            import PIL
            from PIL import Image
            if src == 'data':
                #img = Image.frombytes("L", BACKGROUND_SIZE, bytes(ui.cpu.gpu._bgtileset.to_rgb().data))
                #img.show()
                from slowboy.gpu import GBTileset
                vram = ui.cpu.gpu.vram
                start = 0x8800-VRAM_START
                tileset = GBTileset(vram[start:start+0x1000], (32*8, 8*8), (8, 8))
                palette = ui.cpu.gpu._bgpalette
                img = Image.frombytes("L", (32*8, 8*8), bytes(tileset.to_rgb(palette).data))
                img.show()
            elif src == 'map':
                raise NotImplementedError('display "map"')
            else:
                raise ValueError('Expected "map" or "data".')
    elif command == 'regwatch':
        arg = line[1]
        watched_reg = None if arg == 'None' else arg
    elif command == 'watch':
        if line[1] == 'list':
            for wp in ui.cpu.mmu.watchpoints:
                print(hex(wp))
        else:
            addr = int(line[1], 16)
            def hit_watchpoint(addr, value):
                state['step'] = True
                print('hit watchpoint at {:#04x}'.format(addr))
            ui.cpu.mmu.watchpoints[addr] = hit_watchpoint
    elif command == 'rominfo':
        ui.cpu.mmu.log_rominfo()
    elif command == 'debug':
        logging.getLogger().setLevel(logging.DEBUG)
        print('set logger to DEBUG')
    elif command  == 'info':
        logging.getLogger().setLevel(logging.INFO)
        print('set logger to INFO')
    elif command == 'flags':
        print('H: ', ui.cpu.get_carry_flag())
        print('C: ', ui.cpu.get_halfcarry_flag())
        print('N: ', ui.cpu.get_sub_flag())
        print('Z: ', ui.cpu.get_zero_flag())
    elif command == 'break': # break
        def hit_breakpoint(addr):
            state['step'] = True
            print('hit breakpoint at {:#04x}'.format(ui.cpu.pc))

        if line[1] == 'unset':
            addr = line[2]
            breakpoint = int(addr, 16)
            del state['breakpoints'][breakpoint]
            print('unset breakpoint at {:#04x}'.format(breakpoint))
        elif line[1] == 'list':
            print(' '.join(map(hex, state['breakpoints'].keys())))
        else:
            addr = line[1]
            breakpoint = int(addr, 16)
            state['breakpoints'][breakpoint] = hit_breakpoint
            print('set breakpoint at {:#04x}'.format(breakpoint))
    elif command == 'until':
        def hit_until(addr):
            state['step'] = True
            del state['breakpoints'][addr]
            print('hit breakpoint at {:#04x}'.format(ui.cpu.pc))
        breakpoint = int(line[1], 16)
        state['breakpoints'][breakpoint] = hit_until
        state['step'] = False
    elif command == 'mem':
        start = int(line[1], 16)
        end = int(line[2], 16) if len(line) > 1 else start+1
        buf = bytes(ui.cpu.mmu.get_addr(addr) for addr in range(start, end))
        print_lines(hexdump(buf, 16, start=start))
    elif command == 'stack':
        start = ui.cpu.sp
        n = int(line[1])
        end = start + n
        print(hex(start), hex(end))
        buf = bytes(ui.cpu.mmu.get_addr(addr) for addr in range(start, end))
        print_lines(hexdump(buf, min(n, 16), start=start))


if __name__ == '__main__':
    import sys
    import logging
    root_logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)

    parser = ap.ArgumentParser(description='slowboy SDL interface')
    parser.add_argument('rom', type=str,
                        help='GameBoy ROM file path')
    args = parser.parse_args()

    # ui = SDLUI(sys.argv[1], logger=root_logger, log_level=logging.DEBUG)
    ui = SDLUI(args.rom, log_level=root_logger.level)
    ui.start()
    state = {
        'running': True,
        'step': True,
        'breakpoints': {},
    }

    button_map = {
        sdl2.SDLK_DOWN: 'down',
        sdl2.SDLK_UP: 'up',
        sdl2.SDLK_LEFT: 'left',
        sdl2.SDLK_RIGHT: 'right',
        sdl2.SDLK_RETURN: 'start',
        sdl2.SDLK_RSHIFT: 'select',
        sdl2.SDLK_a: 'a',
        sdl2.SDLK_z: 'b',
    }

    while state['running']:
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.events.SDL_QUIT:
                state['running'] = False
                ui.cpu.log_regs(log=ui.logger.info)
                ui.cpu.log_op(log=ui.logger.info)
                break
            if event.type == sdl2.SDL_KEYDOWN:
                if event.key.keysym.sym == sdl2.SDLK_s:
                    state['step'] = True
                    ui.step()
                elif event.key.keysym.sym == sdl2.SDLK_c:
                    state['step'] = False
                elif event.key.keysym.sym == sdl2.SDLK_q:
                    ui.cpu.log_regs(log=ui.logger.info)
                    ui.cpu.log_op(log=ui.logger.info)
                    for a in sorted(ui.cpu._calls.keys()):
                        print(hex(a), ui.cpu._calls[a])
                    state['running'] = False
                    break
                elif event.key.keysym.sym == sdl2.SDLK_d:
                    ui.cpu.gpu.logger.setLevel(logging.DEBUG)
                elif event.key.keysym.sym == sdl2.SDLK_i:
                    ui.cpu.gpu.logger.setLevel(logging.INFO)
                elif event.key.keysym.sym == sdl2.SDLK_r:
                    ui.cpu.log_regs(log=ui.logger.info)
                elif event.key.keysym.sym in button_map:
                    ui.cpu.mmu.press_button(button_map[event.key.keysym.sym])
            if event.type == sdl2.SDL_KEYUP:
                if event.key.keysym.sym in button_map:
                    ui.cpu.mmu.unpress_button(button_map[event.key.keysym.sym])

        if ui.cpu.pc in state['breakpoints'] and not state['step']:
            state['breakpoints'][ui.cpu.pc](ui.cpu.pc)

        if not state['step']:
            ui.step()

        rlist, _, _ = select.select((sys.stdin,), (), (), 0)
        if rlist:
            command(ui, state)

        if state['step']:
            sdl2.SDL_Delay(100)

        # sdl2.SDL_UpdateWindowSurface(ui.window.window)
