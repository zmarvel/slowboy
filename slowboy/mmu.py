

class MMU():
    def __init__(self, rom):
        self.rom = rom
        self.cartridge_ram = bytes()
        self.wram = bytes()
        self.sprite_table = bytes()
        self.hram = bytes()
        pass

    def get_addr16(self, addr):
        if addr < 0x4000:
            # ROM Bank 0 (16 KB)
            pass
        elif addr < 0x8000:
            # ROM Bank 1+ (16 KB)
            pass
        elif addr < 0xa000:
            # VRAM (8 KB)
            pass
        elif addr < 0xc000:
            # cartridge RAM (8 KB)
            pass
        elif addr < 0xd000:
            # WRAM 0 (4 KB)
            pass
        elif addr < 0xe000:
            # WRAM 1 (4 KB)
            pass
        elif addr < 0xfe00:
            # echo RAM 0xc000–ddff
            pass
        elif addr < 0xfea0:
            # sprite table
            pass
        elif addr < 0xff00:
            # invalid
            raise ValueError('invalid address {}'.format(addr))
        elif addr < 0xff80:
            # IO
            pass
        elif addr < 0xff00:
            # HRAM
            pass
        elif addr == 0xffff:
            # interrupt enable register
            pass
        else:
            raise ValueError('invalid address {}'.format(addr))


