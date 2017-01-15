

class MMU():
    def __init__(self, rom: bytes = None):
        self.rom = rom
        self.cartridge_ram = bytearray(8*1024)
        self.wram = bytearray(4*1024 + 4*1024)
        self.sprite_table = bytearray(160)
        self.hram = bytearray(127)

    def load_rom(self, filename):
        with open(filename, 'rb') as f:
            self.rom = f.read()
        return self.rom

    def unload_rom(self):
        self.rom = None

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
            raise NotImplementedError('VRAM')
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
            # sprite table
            raise NotImplementedError('sprite table')
        elif addr < 0xff00:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            raise NotImplementedError('memory-mapped IO')
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
            raise NotImplementedError('interrupt enable register')
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
            raise NotImplementedError('VRAM')
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
            # sprite table
            raise NotImplementedError('sprite table')
        elif addr < 0xff00:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            raise NotImplementedError('memory-mapped IO')
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
            raise NotImplementedError('interrupt enable register')
        else:
            raise ValueError('invalid address {}'.format(addr))


