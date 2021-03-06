
import logging

from slowboy.gpu import GPU, VRAM_START, OAM_START
from slowboy.interrupts import InterruptController
from slowboy.timer import Timer

JOYP_SELECT_BUTTON_MASK = 0x20
JOYP_SELECT_DIRECTION_MASK = 0x10


class MMU():
    def __init__(self, rom: bytes=None, gpu: GPU=None, timer: Timer=None,
                 interrupt_controller: InterruptController=None,
                 logger=None, log_level=logging.WARNING):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger.getChild(__class__.__name__)
        self.logger.propagate = True
        self.logger.setLevel(log_level)

        self.rom = rom
        if rom is not None:
            self.log_rominfo()
        self.gpu = gpu
        self.timer = timer
        self.interrupt_controller = interrupt_controller
        self.cartridge_ram = bytearray(8*1024)
        self.wram = bytearray(4*1024 + 4*1024)
        self.sprite_table = bytearray(160)
        self.hram = bytearray(127)

        self._joyp = 0
        self._buttons = {
            'down': False,
            'up': False,
            'left': False,
            'right': False,
            'start': False,
            'select': False,
            'b': False,
            'a': False,
        }

        self._dma = 0

        # Mapping of address to callback
        self.watchpoints = {}

    def load_rom(self, romdata):
        self.rom = romdata
        self.log_rominfo()

    def load_rom_from_file(self, romfile):
        with open(romfile, 'rb') as f:
            self.load_rom(f.read())

    def log_rominfo(self):
        log = self.logger.info
        log('title: {}'.format(bytes(self.rom[0x134:0x144])))
        log('licensee code: {}'.format(bytes(self.rom[0x144:0x146])))
        log('SGB flag: {:#02x}'.format(self.rom[0x146]))
        log('cart type: {:#02x}'.format(self.rom[0x147]))

        # decode ROM size code
        size_code = self.rom[0x148]
        if size_code == 0x00:
            rom_size = '32 kB'
        elif size_code == 0x01:
            rom_size = '64 kB'
        elif size_code == 0x02:
            rom_size = '128 kB'
        elif size_code == 0x03:
            rom_size = '256 kB'
        elif size_code == 0x04:
            rom_size = '512 kB'
        elif size_code == 0x05:
            rom_size = '1 MB'
        elif size_code == 0x06:
            rom_size = '2 MB'
        elif size_code == 0x07:
            rom_size = '3 MB'
        elif size_code == 0x52:
            rom_size = '1.1 MB'
        elif size_code == 0x53:
            rom_size = '1.2 MB'
        elif size_code == 0x54:
            rom_size = '1.5 MB'
        else:
            raise ValueError('unrecognized ROM size code')

        log('ROM size: {}'.format(rom_size))

        # decode RAM size code
        size_code = self.rom[0x149]
        if size_code == 0x00:
            ram_size = 'None'
        elif size_code == 0x01:
            ram_size = '2 kB'
        elif size_code == 0x02:
            ram_size = '8 kB'
        elif size_code == 0x03:
            ram_size = '32 kB'
        else:
            raise ValueError('unrecognized RAM size code: {:#x}'.format(size_code))

        log('RAM size: {}'.format(rom_size))

        log('destination code: {:#02x}'.format(self.rom[0x14a]))
        log('old licensee code: {:#02x}'.format(self.rom[0x14b]))
        log('header checksum: {:#02x}'.format(self.rom[0x14d]))
        log('global checksum: {:#04x}'.format((self.rom[0x14e] << 8) | self.rom[0x14f]))

    def unload_rom(self):
        self.rom = None

    def load_gpu(self, gpu: GPU):
        self.gpu = gpu

    def unload_gpu(self):
        self.gpu = None

    def load_timer(self, timer: Timer):
        self.timer = timer

    def unload_timer(self):
        self.timer = None

    def load_interrupt_controller(self, interrupt_controller: InterruptController):
        self.interrupt_controller = interrupt_controller

    def get_addr(self, addr):
        #if addr in self.watchpoints:
        #    self.watchpoints[addr](addr, None)

        if addr < 0:
            # invalid
            raise ValueError('invalid address {:#04x}'.format(addr))
        elif addr < 0x4000:
            # ROM Bank 0 (16 KB)
            return self.rom[addr]
        elif addr < 0x8000:
            # ROM Bank 1+ (16 KB)
            return self.rom[addr]
        elif addr < 0xa000:
            # VRAM (8 KB)
            return self.gpu.get_vram(addr - VRAM_START)
        elif addr < 0xc000:
            # cartridge RAM (8 KB)
            return self.cartridge_ram[addr - 0xa000]
        elif addr < 0xd000:
            # WRAM 0 (4 KB)
            return self.wram[addr - 0xc000]
        elif addr < 0xe000:
            # WRAM 1 (4 KB)
            return self.wram[addr - 0xc000]
        elif addr < 0xfe00:
            # echo RAM 0xc000–ddff
            return self.get_addr(addr - 0x2000)
        elif addr < 0xfea0:
            # sprite table (OAM)
            return self.gpu.get_oam(addr - OAM_START)
        elif addr < 0xff00:
            # invalid
            self.logger.debug('read from invalid address %#04x', addr)
            return 0
            #raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            if addr == 0xff00:
                return self.joyp
            elif addr == 0xff01 | addr == 0xff02:
                raise NotImplementedError('Serial transfer registers')
            elif addr == 0xff04:
                return self.timer.div
            elif addr == 0xff05:
                return self.timer.tima
            elif addr == 0xff06:
                return self.timer.tma
            elif addr == 0xff07:
                return self.timer.tac
            elif addr == 0xff0f:
                # IF
                return self.interrupt_controller.if_
            elif addr == 0xff10:
                raise NotImplementedError('IF register')
            elif addr < 0xff40:
                raise NotImplementedError('sound registers')
            elif addr == 0xff40:
                return self.gpu.lcdc
            elif addr == 0xff41:
                return self.gpu.stat
            elif addr == 0xff42:
                return self.gpu.scy
            elif addr == 0xff43:
                return self.gpu.scx
            elif addr == 0xff44:
                return self.gpu.ly
            elif addr == 0xff45:
                return self.gpu.lyc
            elif addr == 0xff46:
                return self.dma
            elif addr == 0xff47:
                return self.gpu.bgp
            elif addr == 0xff48:
                return self.gpu.obp0
            elif addr == 0xff49:
                return self.gpu.obp1
            elif addr == 0xff4a:
                return self.gpu.wy
            elif addr == 0xff4b:
                return self.gpu.wx
            else:
                raise NotImplementedError('memory-mapped IO addr {}'.format(hex(addr)))
        elif addr < 0xffff:
            # HRAM
            return self.hram[addr - 0xff80]
        elif addr == 0xffff:
            # interrupt enable register
            # bit 0: v-blank interrupt
            # bit 1: LCD STAT interrupt
            # bit 2: timer interrupt
            # bit 3: serial interrupt
            # bit 4: joypad interrupt
            if self.interrupt_controller is not None:
                return self.interrupt_controller.ie
            else:
                self.logger.warning('read from interrupt controller when there is '
                               'not one loaded')
                return 0
        else:
            raise ValueError('invalid address {:#04x}'.format(addr))

    def set_addr(self, addr, value):
        value = value & 0xff

        if addr in self.watchpoints:
            self.watchpoints[addr](addr, value)

        if addr < 0:
            # invalid
            raise ValueError('invalid address {:#04x}'.format(addr))
        elif addr < 0x8000:
            # ROM 0x0000-0x8000
            self.logger.warning('cannot write to read-only address %#04x (in ROM)', addr)
        elif addr < 0xa000:
            # VRAM (8 KB) 0x8000-0xa000
            self.gpu.set_vram(addr - VRAM_START, value)
        elif addr < 0xc000:
            # cartridge RAM (8 KB) 0xa000-0xc000
            self.cartridge_ram[addr - 0xa000] = value
        elif addr < 0xd000:
            # WRAM 0 (4 KB) 0xc000-0xd000
            self.wram[addr - 0xc000] = value
        elif addr < 0xe000:
            # WRAM 1 (4 KB) 0xd000-0xe000
            self.wram[addr - 0xc000] = value
        elif addr < 0xfe00:
            # echo RAM 0xc000–ddff
            self.set_addr(addr - 0x2000, value)
        elif addr < 0xfea0:
            # sprite table (OAM) 0xfe00-fe9
            self.gpu.set_oam(addr - OAM_START, value)
        elif addr < 0xff00:
            # invalid
            self.logger.debug('write to invalid address %#04x', addr)
        elif addr < 0xff80:
            # IO 0xff00-0xff7f
            if addr == 0xff00:
                self.joyp = value
            elif addr == 0xff01 | addr == 0xff02:
                raise NotImplementedError('Serial transfer registers')
            elif addr == 0xff04:
                self.timer.div = value
            elif addr == 0xff05:
                self.timer.tima = value
            elif addr == 0xff06:
                self.timer.tma = value
            elif addr == 0xff07:
                self.timer.tac = value
            elif addr == 0xff0f:
                # IF
                self.interrupt_controller.if_ = value
            elif addr < 0xff40:
                self.logger.warn('not implemented: sound registers')
            elif addr == 0xff40:
                self.gpu.lcdc = value
            elif addr == 0xff41:
                self.gpu.stat = value
            elif addr == 0xff42:
                self.gpu.scy = value
            elif addr == 0xff43:
                self.gpu.scx = value
            elif addr == 0xff44:
                self.gpu.ly = value
            elif addr == 0xff45:
                self.gpu.lyc = value
            elif addr == 0xff46:
                self.dma = value
            elif addr == 0xff47:
                self.gpu.bgp = value
            elif addr == 0xff48:
                self.gpu.obp0 = value
            elif addr == 0xff49:
                self.gpu.obp1 = value
            elif addr == 0xff4a:
                self.gpu.wy = value
            elif addr == 0xff4b:
                self.gpu.wx = value
            else:
                self.logger.warning('not implemented: memory-mapped IO addr %#06x', addr)
        elif addr < 0xffff:
            # HRAM 0xff80-0xfffe
            self.hram[addr - 0xff80] = value
        elif addr == 0xffff:
            # interrupt enable register
            # bit 0: v-blank interrupt
            # bit 1: LCD STAT interrupt
            # bit 2: timer interrupt
            # bit 3: serial interrupt
            # bit 4: joypad interrupt
            if self.interrupt_controller is not None:
                self.interrupt_controller.ie = value
            else:
                self.logger.warning('write to interrupt controller when there '
                                    'is not one loaded')
        else:
            raise ValueError('invalid address {:#04x}'.format(hex(addr)))

    @property
    def joyp(self):
        joyp = self._joyp & 0xf0
        if joyp & JOYP_SELECT_BUTTON_MASK:
            if not self._buttons['down']:
                joyp |= 0x08
            if not self._buttons['up']:
                joyp |= 0x04
            if not self._buttons['left']:
                joyp |= 0x02
            if not self._buttons['right']:
                joyp |= 0x01
        if joyp & JOYP_SELECT_DIRECTION_MASK:
            if not self._buttons['start']:
                joyp |= 0x08
            else:
                pass
            if not self._buttons['select']:
                joyp |= 0x04
            if not self._buttons['b']:
                joyp |= 0x02
            if not self._buttons['a']:
                joyp |= 0x01
        return joyp

    @joyp.setter
    def joyp(self, value):
        self._joyp = value & 0x30

    def press_button(self, button: str):
        print(button, 'DOWN', hex(self.joyp))
        self._buttons[button] = True

    def unpress_button(self, button: str):
        print(button, 'UP', hex(self.joyp))
        self._buttons[button] = False

    @property
    def dma(self):
        return self._dma

    @dma.setter
    def dma(self, value):
        value = value & 0xff
        self._dma = value
        for i in range(0xa0):
            self.gpu.set_oam(i, self.get_addr(value*0x100+i))
