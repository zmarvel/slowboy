

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

    def read_register(self, reg: str) -> int:
        if len(reg) == 1:
            return (registers[reg[0]] << 8) | registers[reg[1]]
        return registers[reg]

    def write_register(self, reg: str, v: int):
        if len(reg) == 1
        if lo:
            registers[reg[0]] = v >> 8
            registers[reg[1]] = v & 0x0f
        registers[reg] = v
    
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

