
import logging
import sdl2
import sdl2.ext
import argparse as ap
import threading
from collections import deque

from slowboy.mmu import MMU
from slowboy.z80 import Z80, State
from slowboy.gpu import SCREEN_WIDTH, SCREEN_HEIGHT, VRAM_START, OAM_START, BACKGROUND_SIZE
from slowboy.util import hexdump, print_lines

from slowboy.debug.debug_thread import DebugThread


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


class EmulatorThread(threading.Thread):
    def __init__(self, z80: Z80, cmd_q: deque, resp_q: deque):
        super().__init__()
        self.cpu = z80
        self.cmd_q = cmd_q
        self.resp_q = resp_q
        self.cpu.set_message_queues(cmd_q, resp_q)

    def stop(self):
        print('EmulatorThread begins shutdown')
        self.cpu.stop()

    def run(self):
        print('EmulatorThread started')
        self.cpu.go()
        print('EmulatorThread finished')


class SDLUI():
    def __init__(self, romfile, debug=False, debug_address=None,
                 log_level=logging.WARNING):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        rom = bytearray(0x8000)
        with open(romfile, 'rb') as f:
            rom_read = f.read()
            print('Read {} B from ROM file'.format(len(rom_read)))
            rom[0:len(rom_read)] = rom_read
        self.cpu = Z80(rom=rom, debug=debug, debug_address=debug_address,
                       log_level=log_level)

        self.window = sdl2.ext.Window('slowboy', (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.window.show()
        self.surface = self.window.get_surface()

        self.debug_cmd_q = None
        self.debug_resp_q = None
        self.debug = debug
        if debug:
            self.debug_thread = DebugThread(debug_address, self.cpu)
            self.debug_cmd_q = self.debug_thread.command_queue
            self.debug_resp_q = self.debug_thread.response_queue
            self.debug_thread.start()
        self.cmd_q = deque()
        self.resp_q = deque()
        self.emulator_thread = EmulatorThread(self.cpu, self.cmd_q, self.resp_q)

    def stop(self):
        print('SDLUI.stop called')
        self.emulator_thread.stop()
        self.emulator_thread.join(timeout=1)
        if self.debug:
            self.debug_thread.stop()
            self.debug_thread.join(timeout=1)
        print('SDLUI.stop finished')

    def start(self):
        self.cpu.state = State.RUN
        self.emulator_thread.start()

    def step(self):
        if self.cpu.gpu.draw(self.surface):
            self.window.refresh()

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
            from PIL import Image
            if src == 'data':
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
    logging.basicConfig(level=logging.WARNING)

    parser = ap.ArgumentParser(description='slowboy SDL interface')
    parser.add_argument('rom', type=str,
                        help='GameBoy ROM file path')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Start the emulator in debug mode.')
    parser.add_argument('--debug-port', type=int, default=9099,
                        help='Debugger listening port (default=9099)')
    parser.add_argument('--debug-address', type=str, default='127.0.0.1',
                        help='Debugger listening address (default=127.0.0.1)')
    parser.add_argument('--profile', action='store_true',
                        help='Print profiling info on exit.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    if args.profile:
        import yappi
        yappi.start()

    ui = SDLUI(args.rom, debug=args.debug,
               debug_address=(args.debug_address, args.debug_port),
               log_level=root_logger.level)
    ui.start()
    state = {
        'running': True,
        'step': False,
        'breakpoints': {},
    }

    if args.verbose:
        root_logger.setLevel(logging.DEBUG)
        ui.cpu.logger.setLevel(logging.DEBUG)

    if args.debug:
        ui.cpu.trace = True

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

    try:
        while state['running']:
            events = sdl2.ext.get_events()
            for event in events:
                if event.type == sdl2.events.SDL_QUIT:
                    state['running'] = False
                    ui.stop()
                    ui.cpu.log_regs(log=ui.logger.info)
                    ui.cpu.log_op(log=ui.logger.info)
                    break
                if event.type == sdl2.SDL_KEYDOWN:
                    if event.key.keysym.sym == sdl2.SDLK_s:
                        ui.cpu.trace = True
                        ui.cpu.step = True
                        ui.step()
                    elif event.key.keysym.sym == sdl2.SDLK_c:
                        ui.cpu.step = False
                        ui.cpu.trace = False
                    elif event.key.keysym.sym == sdl2.SDLK_q:
                        ui.stop()
                        ui.cpu.log_regs(log=ui.logger.info)
                        ui.cpu.log_op(log=ui.logger.info)
                        # for a in sorted(ui.cpu._calls.keys()):
                        #    print(hex(a), ui.cpu._calls[a])
                        # for branch in sorted(ui.cpu._branches.keys(), key=lambda k: ui.cpu._branches[k]):
                        #    src, dst = branch
                        #    print("{:#04x} → {:#04x}: {}".format(src, dst, ui.cpu._branches[branch]))

                        state['running'] = False
                        break
                    elif event.key.keysym.sym == sdl2.SDLK_d:
                        ui.cpu.logger.setLevel(logging.DEBUG)
                        ui.cpu.mmu.logger.setLevel(logging.DEBUG)
                        ui.cpu.gpu.logger.setLevel(logging.DEBUG)
                    elif event.key.keysym.sym == sdl2.SDLK_i:
                        ui.cpu.logger.setLevel(logging.INFO)
                        ui.cpu.mmu.logger.setLevel(logging.INFO)
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

            if not ui.cpu.trace:
                ui.step()

            if ui.cpu.trace:
                sdl2.SDL_Delay(100)

    except KeyboardInterrupt:
        ui.stop()
    finally:
        if args.profile:
            yappi.get_func_stats().print_all()
