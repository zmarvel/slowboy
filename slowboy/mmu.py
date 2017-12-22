
from slowboy.gpu import GPU

class MMU():
    def __init__(self, rom: bytes=None, gpu: GPU=None):
        self.rom = rom
        self.gpu = None
        self.cartridge_ram = bytearray(8*1024)
        self.wram = bytearray(4*1024 + 4*1024)
        self.sprite_table = bytearray(160)
        self.hram = bytearray(127)
        self.interrupt_enable = 0

    def load_rom(self, romdata):
        self.rom = romdata

    def unload_rom(self):
        self.rom = None

    def load_gpu(self, gpu):
        self.gpu = gpu

    def unload_gpu(self):
        self.gpu = None

    def get_addr(self, addr):
        if addr < 0:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0x4000:
            # ROM Bank 0 (16 KB)
            return self.rom[addr]
        elif addr < 0x8000:
            # ROM Bank 1+ (16 KB)
            return self.rom[addr]
        elif addr < 0xa000:
            # VRAM (8 KB)
            return self.gpu.get_vram(addr - 0x8000)
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
            return self.gpu.get_oam(addr - 0xfe00)
        elif addr < 0xff00:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            if addr == 0xff00:
                raise NotImplementedError('JOYP register')
            elif addr == 0xff01 | addr == 0xff02:
                raise NotImplementedError('Serial transfer registers')
            elif addr == 0xff04:
                raise NotImplementedError('DIV register')
            elif addr == 0xff05:
                raise NotImplementedError('TIMA register')
            elif addr == 0xff06:
                raise NotImplementedError('TMA register')
            elif addr == 0xff07:
                raise NotImplementedError('TAC register')
            elif addr == 0xff0f:
                raise NotImplementedError('IF register')
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
                raise NotImplementedError('DMA register')
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
            return self.interrupt_enable
        else:
            raise ValueError('invalid address {}'.format(addr))

    def set_addr(self, addr, value):
        value = value & 0xff

        if addr < 0:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0x8000:
            # ROM
            raise ValueError('invalid address {} (in ROM)'.format(addr))
        elif addr < 0xa000:
            # VRAM (8 KB)
            self.gpu.set_vram(addr - 0x8000, value)
        elif addr < 0xc000:
            # cartridge RAM (8 KB)
            self.cartridge_ram[addr - 0xa000] = value
        elif addr < 0xd000:
            # WRAM 0 (4 KB)
            self.wram[addr - 0xc000] = value
        elif addr < 0xe000:
            # WRAM 1 (4 KB)
            self.wram[addr - 0xc000] = value
        elif addr < 0xfe00:
            # echo RAM 0xc000–ddff
            self.set_addr(addr - 0x2000, value)
        elif addr < 0xfea0:
            # sprite table (OAM)
            self.gpu.set_oam(addr - 0xfe00, value)
        elif addr < 0xff00:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            if addr == 0xff00:
                raise NotImplementedError('JOYP register')
            elif addr == 0xff01 | addr == 0xff02:
                raise NotImplementedError('Serial transfer registers')
            elif addr == 0xff04:
                raise NotImplementedError('DIV register')
            elif addr == 0xff05:
                raise NotImplementedError('TIMA register')
            elif addr == 0xff06:
                raise NotImplementedError('TMA register')
            elif addr == 0xff07:
                raise NotImplementedError('TAC register')
            elif addr == 0xff0f:
                raise NotImplementedError('IF register')
            elif addr == 0xff10:
                raise NotImplementedError('IF register')
            elif addr < 0xff40:
                raise NotImplementedError('sound registers')
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
                raise NotImplementedError('DMA register')
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
                raise NotImplementedError('memory-mapped IO addr {}'.format(hex(addr)))
        elif addr < 0xffff:
            # HRAM
            self.hram[addr - 0xff80] = value
        elif addr == 0xffff:
            # interrupt enable register
            # bit 0: v-blank interrupt
            # bit 1: LCD STAT interrupt
            # bit 2: timer interrupt
            # bit 3: serial interrupt
            # bit 4: joypad interrupt
            self.interrupt_enable = value
        else:
            raise ValueError('invalid address {}'.format(addr))


