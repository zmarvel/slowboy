

class gb_z80(object):
    c = 0
    m = 0
    registers = {
            'a': 0, 'f': 0,
            'b': 0, 'c': 0,
            'd': 0, 'e': 0,
            'h': 0, 'l': 0,
            'sp': 0,
            'pc': 0
            }

    instructions = {
            }

    def read_register(self, hi: str, lo: str = None) -> int:
        if lo:
            return (registers[hi] << 8) | registers[lo]
        return registers[hi]

    def write_register(self, hi: str, lo: str = None, v: int):
        if lo:
            registers[hi] = v >> 8
            registers[lo] = v & 0x0f
        registers[hi] = v
    
    def set_zero_flag(self):
        registers['f'] |= 0x80
    
    def reset_zero_flag(self):
        registers['f'] &= 0x7f

    def set_carry_flag(self):
        registers['f'] |= 0x10

    def reset_carry_flag(self):
        registers['f'] &= 0xef

    def set_addsub_flag(self):
        registers['f'] |= 0x40

    def reset_addsub_flag(self):
        registers['f'] &= 0xbf

    def set_halfcarry_flag(self):
        registers['f'] |= 0x20

    def reset_halfcarry_flag(self):
        registers['f'] &= 0xdf

