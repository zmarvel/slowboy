
import enum
import logging

from slowboy.util import uint8toBCD
from slowboy.mmu import MMU

class State(enum.Enum):
    RUN = 0
    HALT = 1
    STOP = 2

class Z80(object):
    reglist = ['b', 'c', None, 'e', 'h', 'd', None, 'a']

    def __init__(self, mmu=None, log_level=logging.WARNING):
        self.clk = 0
        self.registers = {
            'a': 0,
            'f': 0,
            'b': 0,
            'c': 0,
            'd': 0,
            'e': 0,
            'h': 0,
            'l': 0
        }
        self.sp = 0
        self.pc = 0x100
        self.state = State.STOP
        if mmu:
            self.mmu = mmu
        else:
            self.mmu = MMU()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        self._init_opcode_map()

    def _init_opcode_map(self):
        self.opcode_map = {
                0x00: self.nop,
                0x10: self.stop,
                0x76: self.halt,
                0xf3: self.di,
                0xfb: self.ei,

                0x40: self.ld_reg8toreg8('b', 'b'),
                0x41: self.ld_reg8toreg8('b', 'c'),
                0x42: self.ld_reg8toreg8('b', 'd'),
                0x43: self.ld_reg8toreg8('b', 'e'),
                0x44: self.ld_reg8toreg8('b', 'h'),
                0x45: self.ld_reg8toreg8('b', 'l'),
                0x46: self.ld_reg16addrtoreg8('hl', 'b'),
                0x47: self.ld_reg8toreg8('b', 'a'),
                0x48: self.ld_reg8toreg8('c', 'b'),
                0x49: self.ld_reg8toreg8('c', 'c'),
                0x4a: self.ld_reg8toreg8('c', 'd'),
                0x4b: self.ld_reg8toreg8('c', 'e'),
                0x4c: self.ld_reg8toreg8('c', 'h'),
                0x4d: self.ld_reg8toreg8('c', 'l'),
                0x4e: self.ld_reg16addrtoreg8('hl', 'c'),
                0x4f: self.ld_reg8toreg8('c', 'a'),
                0x50: self.ld_reg8toreg8('d', 'b'),
                0x51: self.ld_reg8toreg8('d', 'c'),
                0x52: self.ld_reg8toreg8('d', 'd'),
                0x53: self.ld_reg8toreg8('d', 'e'),
                0x54: self.ld_reg8toreg8('d', 'h'),
                0x55: self.ld_reg8toreg8('d', 'l'),
                0x56: self.ld_reg16addrtoreg8('hl', 'd'),
                0x57: self.ld_reg8toreg8('d', 'a'),
                0x58: self.ld_reg8toreg8('e', 'b'),
                0x59: self.ld_reg8toreg8('e', 'c'),
                0x5a: self.ld_reg8toreg8('e', 'd'),
                0x5b: self.ld_reg8toreg8('e', 'e'),
                0x5c: self.ld_reg8toreg8('e', 'h'),
                0x5d: self.ld_reg8toreg8('e', 'l'),
                0x5e: self.ld_reg16addrtoreg8('hl', 'e'),
                0x5f: self.ld_reg8toreg8('e', 'a'),
                0x60: self.ld_reg8toreg8('h', 'b'),
                0x61: self.ld_reg8toreg8('h', 'c'),
                0x62: self.ld_reg8toreg8('h', 'd'),
                0x63: self.ld_reg8toreg8('h', 'e'),
                0x64: self.ld_reg8toreg8('h', 'h'),
                0x65: self.ld_reg8toreg8('h', 'l'),
                0x66: self.ld_reg16addrtoreg8('hl', 'h'),
                0x67: self.ld_reg8toreg8('h', 'a'),
                0x68: self.ld_reg8toreg8('l', 'b'),
                0x69: self.ld_reg8toreg8('l', 'c'),
                0x6a: self.ld_reg8toreg8('l', 'd'),
                0x6b: self.ld_reg8toreg8('l', 'e'),
                0x6c: self.ld_reg8toreg8('l', 'h'),
                0x6d: self.ld_reg8toreg8('l', 'l'),
                0x6e: self.ld_reg16addrtoreg8('hl', 'l'),
                0x6f: self.ld_reg8toreg8('l', 'a'),
                0x70: self.ld_reg8toreg16addr('b', 'hl'),
                0x71: self.ld_reg8toreg16addr('c', 'hl'),
                0x72: self.ld_reg8toreg16addr('d', 'hl'),
                0x73: self.ld_reg8toreg16addr('e', 'hl'),
                0x74: self.ld_reg8toreg16addr('h', 'hl'),
                0x75: self.ld_reg8toreg16addr('l', 'hl'),
                0x77: self.ld_reg8toreg16addr('a', 'hl'),
                0x78: self.ld_reg8toreg8('a', 'b'),
                0x79: self.ld_reg8toreg8('a', 'c'),
                0x7a: self.ld_reg8toreg8('a', 'd'),
                0x7b: self.ld_reg8toreg8('a', 'e'),
                0x7c: self.ld_reg8toreg8('a', 'h'),
                0x7d: self.ld_reg8toreg8('a', 'l'),
                0x7e: self.ld_reg16addrtoreg8('hl', 'a'),
                0x7f: self.ld_reg8toreg8('a', 'a'),

                0x02: self.ld_reg8toreg16addr('a', 'bc'),
                0x12: self.ld_reg8toreg16addr('a', 'de'),
                0x22: self.ld_reg8toreg16addr('a', 'hl', inc=True),
                0x32: self.ld_reg8toreg16addr('a', 'hl', dec=True),

                0x06: self.ld_imm8toreg8('b'),
                0x16: self.ld_imm8toreg8('d'),
                0x26: self.ld_imm8toreg8('h'),
                0x36: self.ld_imm8toreg16addr('hl'),

                0x08: self.ld_sptoimm16addr,

                0x0a: self.ld_reg16addrtoreg8('bc', 'a'),
                0x1a: self.ld_reg16addrtoreg8('de', 'a'),
                0x2a: self.ld_reg16addrtoreg8('hl', 'a', inc=True),
                0x3a: self.ld_reg16addrtoreg8('hl', 'a', dec=True),

                0x0e: self.ld_imm8toreg8('c'),
                0x1e: self.ld_imm8toreg8('e'),
                0x2e: self.ld_imm8toreg8('l'),
                0x3e: self.ld_imm8toreg8('a'),

                0xe0: None, # ldh (imm8), a TODO
                0xf0: None, # ldh a, (imm8) TODO
                0xe2: None, # ld (c), a TODO
                0xf2: None, # ld a, (c) TODO

                0xc1: None, # pop bc TODO
                0xd1: None, # pop de TODO
                0xe1: None, # pop hl TODO
                0xf1: None, # pop af TODO (affects flags)

                0xc5: None, # push bc TODO
                0xd5: None, # push de TODO
                0xe5: None, # push hl TODO
                0xf5: None, # push af TODO

                0xf8: None, # ld hl, sp+imm8 TODO

                0xf9: self.ld_reg16toreg16('hl', 'sp'),

                0xea: self.ld_reg8toimm16addr('a'),
                0xfa: self.ld_imm16addrtoreg8('a'),

                0x01: self.ld_imm16toreg16('bc'),
                0x11: self.ld_imm16toreg16('de'),
                0x21: self.ld_imm16toreg16('hl'),
                0x31: self.ld_imm16toreg16('sp'),

                # arithmetic and logic

                0x03: self.inc_reg16('bc'),
                0x13: self.inc_reg16('de'),
                0x23: self.inc_reg16('hl'),
                0x33: self.inc_reg16('sp'),
                0x04: self.inc_reg8('b'),
                0x14: self.inc_reg8('d'),
                0x24: self.inc_reg8('h'),
                0x34: self.inc_addrHL,
                0x0c: self.inc_reg8('c'),
                0x1c: self.inc_reg8('e'),
                0x2c: self.inc_reg8('l'),
                0x3c: self.inc_reg8('a'),
                0x05: self.dec_reg8('b'),
                0x15: self.dec_reg8('d'),
                0x25: self.dec_reg8('h'),
                0x35: self.dec_addrHL,
                0x0d: self.dec_reg8('c'),
                0x1d: self.dec_reg8('e'),
                0x2d: self.dec_reg8('l'),
                0x3d: self.dec_reg8('a'),
                0x0b: self.dec_reg16('bc'),
                0x1b: self.dec_reg16('de'),
                0x2b: self.dec_reg16('hl'),
                0x3b: self.dec_reg16('sp'),

                0x80: self.add_reg8toreg8('b', 'a'),
                0x81: self.add_reg8toreg8('c', 'a'),
                0x82: self.add_reg8toreg8('d', 'a'),
                0x83: self.add_reg8toreg8('e', 'a'),
                0x84: self.add_reg8toreg8('h', 'a'),
                0x85: self.add_reg8toreg8('l', 'a'),
                #0x86: self.add_reg16addrtoreg8('hl', 'a'),
                0x87: self.add_reg8toreg8('a', 'a', carry=True),
                0x88: self.add_reg8toreg8('b', 'a', carry=True),
                0x89: self.add_reg8toreg8('c', 'a', carry=True),
                0x8a: self.add_reg8toreg8('d', 'a', carry=True),
                0x8b: self.add_reg8toreg8('e', 'a', carry=True),
                0x8c: self.add_reg8toreg8('h', 'a', carry=True),
                0x8d: self.add_reg8toreg8('l', 'a', carry=True),
                #0x8e: self.add_reg16addrtoreg8('hl', 'a', carry=True),
                0x8f: self.add_reg8toreg8('a', 'a', carry=True),
                0x90: self.sub_reg8fromreg8('b', 'a'),
                0x91: self.sub_reg8fromreg8('c', 'a'),
                0x92: self.sub_reg8fromreg8('d', 'a'),
                0x93: self.sub_reg8fromreg8('e', 'a'),
                0x94: self.sub_reg8fromreg8('h', 'a'),
                0x95: self.sub_reg8fromreg8('l', 'a'),
                #0x96: self.sub_reg16addrfromreg8('hl', 'a'),
                0x97: self.sub_reg8fromreg8('a', 'a', carry=True),
                0x98: self.sub_reg8fromreg8('b', 'a', carry=True),
                0x99: self.sub_reg8fromreg8('c', 'a', carry=True),
                0x9a: self.sub_reg8fromreg8('d', 'a', carry=True),
                0x9b: self.sub_reg8fromreg8('e', 'a', carry=True),
                0x9c: self.sub_reg8fromreg8('h', 'a', carry=True),
                0x9d: self.sub_reg8fromreg8('l', 'a', carry=True),
                #0x9e: self.sub_reg16addrfromreg8('hl', 'a', carry=True),
                0x9f: self.sub_reg8fromreg8('a', 'a', carry=True),
                0xa0: self.and_reg8('b'),
                0xa1: self.and_reg8('c'),
                0xa2: self.and_reg8('d'),
                0xa3: self.and_reg8('e'),
                0xa4: self.and_reg8('h'),
                0xa5: self.and_reg8('l'),
                0xa6: self.and_reg16addr('hl'),
                0xa7: self.and_reg8('a'),
                0xa8: self.xor_reg8('b'),
                0xa9: self.xor_reg8('c'),
                0xaa: self.xor_reg8('d'),
                0xab: self.xor_reg8('e'),
                0xac: self.xor_reg8('h'),
                0xad: self.xor_reg8('l'),
                0xae: self.xor_reg16addr('hl'),
                0xaf: self.xor_reg8('a'),
                0xb0: self.or_reg8('b'),
                0xb1: self.or_reg8('c'),
                0xb2: self.or_reg8('d'),
                0xb3: self.or_reg8('e'),
                0xb4: self.or_reg8('h'),
                0xb5: self.or_reg8('l'),
                0xb6: self.or_reg16addr('hl'),
                0xb7: self.or_reg8('a'),
                0xb8: self.cp_reg8toreg8('a', 'b'),
                0xb9: self.cp_reg8toreg8('a', 'c'),
                0xba: self.cp_reg8toreg8('a', 'd'),
                0xbb: self.cp_reg8toreg8('a', 'e'),
                0xbc: self.cp_reg8toreg8('a', 'h'),
                0xbd: self.cp_reg8toreg8('a', 'l'),
                0xbe: self.cp_reg8toreg16addr('a', 'hl'),
                0xbf: self.cp_reg8toreg8('a', 'a'),
                0xc6: self.add_imm8toreg8('a'),
                0xd6: self.sub_imm8fromreg8('a'),
                0xe6: self.and_imm8,
                0xf6: self.or_imm8,


                0xc7: self.rst, # TODO
                0xd7: self.rst, # TODO
                0xe7: self.rst, # TODO
                0xf7: self.rst, # TODO
                0xcf: self.rst, # TODO
                0xdf: self.rst, # TODO
                0xef: self.rst, # TODO
                0xff: self.rst, # TODO

                0xc3: self.jp_imm16addr(),
                0xc2: self.jp_imm16addr('nz'),
                0xd2: self.jp_imm16addr('nc'),
                0xca: self.jp_imm16addr('z'),
                0xda: self.jp_imm16addr('c'),
                0xe9: self.jp_reg16addr('hl'),

                0x18: self.jr_imm8(),
                0x20: self.jr_imm8('nz'),
                0x30: self.jr_imm8('nc'),
                0x28: self.jr_imm8('z'),
                0x38: self.jr_imm8('c'),

                0xcd: self.call_imm16addr(),
                0xc4: self.call_imm16addr('nz'),
                0xd4: self.call_imm16addr('nc'),
                0xcc: self.call_imm16addr('z'),
                0xdc: self.call_imm16addr('c'),

                0xc9: self.ret(),
                0xd9: self.reti,
                0xc0: self.ret('nz'),
                0xd0: self.ret('nc'),
                0xc8: self.ret('z'),
                0xd8: self.ret('c'),
                }

    def __repr__(self):
        return ('Z80('
                'state={state}, '
                'pc={pc:#x}, sp={sp:#x}, '
                'a={a:#x}, b={b:#x}, c={c:#x}, d={d:#x}, e={e:#x}, '
                'h={h:#x}, l={l:#x})'
                ).format(
                        state=self.state, pc=self.pc, sp=self.sp,
                        a=self.get_reg8('a'), b=self.get_reg8('b'),
                        c=self.get_reg8('c'), d=self.get_reg8('d'),
                        e=self.get_reg8('e'), h=self.get_reg8('h'),
                        l=self.get_reg8('l'))

    def get_registers(self):
        return self.registers

    def set_reg8(self, reg8, value):
        self.registers[reg8.lower()] = value & 0xff

    def get_reg8(self, reg8):
        return self.registers[reg8.lower()]

    def set_reg16(self, reg16, value):
        reg16 = reg16.lower()
        if reg16 == 'bc':
            self.registers['b'] = (value >> 8) & 0xff
            self.registers['c'] = value & 0xff
        elif reg16 == 'de':
            self.registers['d'] = (value >> 8) & 0xff
            self.registers['e'] = value & 0xff
        elif reg16 == 'hl':
            self.registers['h'] = (value >> 8) & 0xff
            self.registers['l'] = value & 0xff
        else:
            raise KeyError('unrecognized register {}'.format(reg16))

    def get_reg16(self, reg16):
        reg16 = reg16.lower()
        if reg16 == 'bc':
            return (self.registers['b'] << 8) | self.registers['c']
        elif reg16 == 'de':
            return (self.registers['d'] << 8) | self.registers['e']
        elif reg16 == 'hl':
            return (self.registers['h'] << 8) | self.registers['l']
        else:
            raise KeyError('unrecognized register {}'.format(reg16))

    def set_sp(self, u16):
        self.sp = u16 & 0xffff

    def inc_sp(self):
        self.sp = (self.sp + 1) & 0xffff

    def get_sp(self):
        return self.sp

    def set_pc(self, addr16):
        self.pc = addr16 & 0xffff

    def inc_pc(self):
        self.pc = (self.pc + 1) & 0xffff

    def get_pc(self):
        return self.pc

    def set_zero_flag(self):
        self.registers['f'] |= 0x80

    def reset_zero_flag(self):
        self.registers['f'] &= 0x7f

    def get_zero_flag(self):
        return (self.get_reg8('f') >> 7) & 1

    def set_sub_flag(self):
        self.registers['f'] |= 0x40

    def reset_sub_flag(self):
        self.registers['f'] &= 0xbf

    def get_sub_flag(self):
        return (self.get_reg8('f') >> 6) & 1

    def set_halfcarry_flag(self):
        self.registers['f'] |= 0x20

    def reset_halfcarry_flag(self):
        self.registers['f'] &= 0xdf

    def get_halfcarry_flag(self):
        # TODO: actually use this

        return (self.registers['f'] >> 5) & 1

    def set_carry_flag(self):
        self.registers['f'] |= 0x10

    def reset_carry_flag(self):
        self.registers['f'] &= 0xef

    def get_carry_flag(self):
        return (self.registers['f'] >> 4) & 1

    def fetch(self):
        opcode = self.mmu.get_addr(self.get_pc())
        self.inc_pc()
        return opcode

    def go(self):
        self.state = State.RUN
        while self.state == State.RUN:
            self.logger.debug(self)
            opcode = self.fetch()

            # decode
            op = self.opcode_map[opcode]

            # execute
            op()

    def nop(self):
        """0x00"""

        pass

    def stop(self):
        """0x10"""

        self.state = State.STOP

    def halt(self):
        """0x76"""

        self.state = State.HALT

    def ld_imm8toreg8(self, reg8):
        """Returns a function to load an 8-bit immediate into :py:data:reg8.

        :param reg8: single byte register
        :rtype: integer → None """

        def ld():
            imm8 = self.fetch()
            self.logger.debug('ld {}, {}'.format(reg8, imm8))
            self.set_reg8(reg8, imm8)
        return ld

    def ld_reg8toreg8(self, src_reg8, dest_reg8):
        """Returns a function to load :py:data:src_reg8 into :py:data:dest_reg8.

        :param src_reg8: single byte source register
        :param dest_reg8: single byte destination register
        :rtype: None → None """

        def ld():
            self.logger.debug('ld {}, {}'.format(dest_reg8, src_reg8))
            self.set_reg8(dest_reg8, self.get_reg8(src_reg8))
        return ld

    def ld_imm16toreg16(self, reg16):
        """Returns a function to load a 16-bit immediate into :py:data:reg16.

        :param reg16: two-byte register
        :rtype: integer → None """

        if reg16 == 'sp':
            def ld():
                imm16 = self.fetch() << 8
                imm16 |= self.fetch()
                self.set_sp(imm16)
        else:
            def ld():
                imm16 = self.fetch() << 8
                imm16 |= self.fetch()
                self.set_reg16(reg16, imm16)
        return ld

    def ld_reg8toreg16addr(self, reg8, reg16, inc=False, dec=False):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit double register.

        :param reg8: single byte source register
        :param reg16: two-byte register containing destination address
        :param inc: increment the value in :py:data:reg16 after storing
                    :py:data:reg8 to memory
        :param dec: decrement the value in :py:data:reg16 after storing
                    :py:data:reg8 to memory
        :rtype: None → None"""

        if inc and dec:
            raise ValueError('only one of inc and dec may be true')
        elif inc:
            def ld():
                self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
                self.set_reg16(reg16, self.get_reg16(reg16) + 1)
        elif dec:
            def ld():
                self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
                self.set_reg16(reg16, self.get_reg16(reg16) - 1)
        else:
            def ld():
                self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
        return ld

    def ld_reg8toimm16addr(self, reg8):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit immediate.

        :param reg8: single byte source register
        :rtype: integer → None"""

        def ld():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            self.mmu.set_addr(imm16, self.get_reg8(reg8))
        return ld

    def ld_reg16addrtoreg8(self, reg16, reg8, inc=False, dec=False):
        """Returns a function to load the value at an address given by a 16-bit
        double register into an 8-bit register.

        :param reg16: 16-bit double register containing the source address
        :param reg8: 8-bit destination register
        :param inc: increment the value in reg16 after the ld operation
        :param dec: decrement the value in reg16 after the ld operation
        :rtype: None → None"""
        if inc and dec:
            raise ValueError('only one of inc and dec may be true')
        elif inc:
            def ld():
                u16 = self.get_reg16(reg16)
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 + 1)
        elif dec:
            def ld():
                u16 = self.get_reg16(reg16)
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 - 1)
        else:
            def ld():
                u16 = self.get_reg16(reg16)
                self.set_reg8(reg8, self.mmu.get_addr(u16))
        return ld

    def ld_reg16toreg16(self, src_reg16, dest_reg16):
        src_reg16 = src_reg16.lower()
        if src_reg16 == 'sp':
            self.set_reg16(dest_reg16, self.get_sp())
        elif dest_reg16 == 'sp':
            self.set_sp(self.get_reg16(src_reg16))
        else:
            self.set_reg16(dest_reg16, self.get_reg16(src_reg16))

    def ld_imm16addrtoreg8(self, reg8):
        """Returns a function to load the value at an address given by a 16-bit
        immediate into an 8-bit register.

        :param reg8: the single-byte destination register
        :rtype: integer → None"""

        def ld():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            self.set_reg8(reg8, self.mmu.get_addr(imm16))
        return ld

    def ld_sptoimm16addr(self):
        """Loads the most significant byte of the stack pointer into the address
        given by :py:data:imm16 and the least significant byte of the SP into
        :py:data:imm16+1.

        :param imm16: 16-bit address
        :rtype: None"""

        imm16 = self.fetch() << 8
        imm16 |= self.fetch()
        self.mmu.set_addr(imm16, self.get_sp() >> 8)
        self.mmu.set_addr(imm16 + 1, self.get_sp() & 0xff)

    def ld_sptoreg16addr(self, reg16):
        """Returns a function that loads the stack pointer into the 16-bit
        register :py:data:reg16.

        :param reg16: the destination double register
        :rtype: None → None"""

        def ld():
            addr = self.get_reg16(reg16)

            self.mmu.set_addr(addr, self.get_sp() >> 8)
            self.mmu.set_addr(addr + 1, self.get_sp() & 0xff)
        return ld

    def ld_imm8toreg16addr(self, reg16):

        def ld():
            imm8 = self.fetch()
            addr16 = self.get_reg16('hl')
            self.mmu.set_addr(addr16, imm8)


    def ld_imm8toaddrHL(self):
        """0x36"""

        imm8 = self.fetch()
        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, imm8)

    def inc_reg8(self, reg8):
        """Returns a function that increments :py:data:reg8.

        :param reg8: the 8-bit register to increment
        :rtype: None → None"""

        def inc():
            u8 = self.get_reg8(reg8)

            result = u8 + 1
            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if u8 & 0x0f == 0xf:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
        return inc

    def inc_reg16(self, reg16):
        """Returns a function that increments :py:data:reg16.

        :param reg16: the double register to increment
        :rtype: None → None"""

        def inc():
            u16 = self.get_reg16(reg16)

            result = u16 + 1
            self.set_reg16(reg16, result)

            if result & 0xffff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if u16 & 0x00ff == 0xff:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
        return inc

    def dec_reg8(self, reg8):
        """Returns a function that decrements :py:data:reg8.

        :param reg8: the 8-bit register to decrement
        :rtype: None → None"""

        def dec():
            u8 = self.get_reg8(reg8)

            self.set_reg8(reg8, u8 + 0xff)

            if u8 & 0x0f == 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()
        return dec

    def dec_reg16(self, reg16):
        """Returns a function that decrements :py:data:reg16.

        :param reg8: the double register to decrement
        :rtype: None → None"""

        def dec():
            u16 = self.get_reg16(reg16)

            self.set_reg16(reg16, u16 + 0xffff)

            if u16 & 0x00ff == 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()
        return dec

    def inc_reg16addr(self, reg16):
        """Increments the value at the address in `reg16`."""

        def inc():
            addr16 = self.get_reg16(reg16)
            self.mmu.set_addr(addr16, self.mmu.get_addr(addr16) + 1)
        return inc

    def inc_addrHL(self):
        """Increments the value at the address in HL."""

        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, self.mmu.get_addr(addr16) + 1)

    def dec_addrHL(self):
        """Decrements the value at the address in HL."""

        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, self.mmu.get_addr(addr16) - 1)


    def add_reg16toregHL(self, reg16):
        """Returns a function that adds :py:data:reg16 to the double register
        HL.

        :param reg16: source double register
        :rtype: None → None"""

        def add():
            result = self.get_reg16('HL') + self.get_reg16(reg16)
            self.set_reg16('HL', result)

            if result > 0xffff:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return add

    def add_reg8toreg8(self, src_reg8, dest_reg8, carry=False):
        """Returns a function that adds the given two 8-bit registers.
        dest_reg8 = dest_reg8 + src_reg8

        :param src_reg8: source single-byte register
        :param dest_reg8: destination single-byte register
        :param carry: src_reg8 + dest_reg8 + 1
        :rtype: None → None"""

        def add():
            src_u8 = self.get_reg8(src_reg8)
            dest_u8 = self.get_reg8(dest_reg8)

            if carry:
                result = src_u8 + dest_u8 + self.get_carry_flag()
            else:
                result = src_u8 + dest_u8

            self.set_reg8(dest_reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (dest_u8 & 0x0f) + (src_u8 & 0x0f) > 0x0f:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()

            if result > 0xff:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return add

    def add_imm8toreg8(self, reg8, carry=False):
        """Returns a function that adds the given two 8-bit registers.
        reg8 = reg8 + imm8

        :param reg8: destination single-byte register
        :param carry: reg8 + imm8 + 1
        :rtype: int → None"""

        def add():
            imm8 = self.fetch()
            u8 = self.get_reg8(reg8)

            if carry:
                result = u8 + imm8 + self.get_carry_flag()
            else:
                result = u8 + imm8
            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (u8 & 0x0f) + (imm8 & 0x0f) > 0x0f:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()

            if result > 0xff:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return add

    def sub_reg8fromreg8(self, src_reg8, dest_reg8, carry=False):
        """Returns a function that subtracts src_reg8 from dest_reg8.

        :param src_reg8: The source single-byte register
        :param dest_reg8: The destination single-byte register
        :rtype: None → None"""

        def sub():
            src_u8 = self.get_reg8(src_reg8)
            dest_u8 = self.get_reg8(dest_reg8)

            if carry:
                # TODO (also document it)
                raise NotImplementedError('sbc imm8 / sbc reg8 / sbc (HL)')
            else:
                result = dest_u8 + (((src_u8 ^ 0xff) + 1) & 0xff)

            self.set_reg8(dest_reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (dest_u8 & 0x0f) + (((src_u8 ^ 0xff) + 1) & 0x0f) > 0x0f:
                self.reset_halfcarry_flag()
            else:
                self.set_halfcarry_flag()

            self.set_sub_flag()

            if result > 0xff:
                self.reset_carry_flag()
            else:
                self.set_carry_flag()
        return sub

    def sub_imm8fromreg8(self, reg8, carry=False):
        """Returns a function that subtracts an 8-bit immediate value from the
        given :py:data:reg8.

        :param reg8: The destination single register.
        :rtype: int → None"""

        def sub():
            imm8 = self.fetch()
            u8 = self.get_reg8(reg8)

            if carry:
                # TODO
                raise NotImplementedError('sbc imm8 / sbc reg8 / sbc (HL)')
            else:
                result = u8 + (((imm8 ^ 0xff) + 1) & 0xff)

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            # TODO: set halfcarry flag if a borrow from bit 4 occured
            # this will need updated when carry is completed too
            if ((u8 & 0x0f) + ((imm8 ^ 0xff) & 0x0f) + 1) > 0x0f:
                self.reset_halfcarry_flag()
            else:
                self.set_halfcarry_flag()

            self.set_sub_flag()

            if result > 0xff:
                self.reset_carry_flag()
            else:
                self.set_carry_flag()
        return sub

    def sub_imm16addrfromreg8(self, reg8, carry=False):
        """Returns a function that subtracts the value at the address given by
        :py:data:reg16 from :py:data:reg8.

        :param reg16: The double register containing the source address
        :param reg8: The single destination register.
        :rtype: None → None"""

        def sub():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            x = self.get_reg8(reg8)
            y = self.mmu.get_addr(imm16)

            if carry:
                raise NotImplementedError('sbc (HL)')
            else:
                result = x + (((y ^ 0xff) + 1) & 0xff)

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if ((x & 0x0f) + ((y ^ 0xff) & 0x0f) + 1) > 0x0f:
                self.reset_halfcarry_flag()
            else:
                self.set_halfcarry_flag()

            self.set_sub_flag()

            if result > 0xff:
                self.reset_carry_flag()
            else:
                self.set_carry_flag()
        return sub

    def sub_reg16addrfromreg8(self, reg16, reg8, carry=False):
        """Returns a function that subtracts the value at the address given by
        :py:data:reg16 from :py:data:reg8.

        :param reg16: The double register containing the source address
        :param reg8: The single destination register.
        :rtype: None → None"""

        def sub():
            x = self.get_reg8(reg8)
            y = self.mmu.get_addr(self.get_reg16(reg16))

            if carry:
                raise NotImplementedError('sbc (HL)')
            else:
                result = x + (((y ^ 0xff) + 1) & 0xff)

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if ((x & 0x0f) + ((y ^ 0xff) & 0x0f) + 1) > 0x0f:
                self.reset_halfcarry_flag()
            else:
                self.set_halfcarry_flag()

            self.set_sub_flag()

            if result > 0xff:
                self.reset_carry_flag()
            else:
                self.set_carry_flag()
        return sub



    def and_reg8(self, reg8):
        """Returns a function that performs a bitwise AND with the accumulator
        register A.

        :param reg8: a single register
        :rtype: None → None"""

        def band():
            result = self.get_reg8('a') & self.get_reg8(reg8)
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (result >> 4) & 1 == 1:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
            self.reset_carry_flag()
        return band

    def and_imm8(self):
        """Returns a function that performs a bitwise AND with its 8-bit
        immediate argument and the accumulator register A.

        :rtype: int → None"""

        def band():
            imm8 = self.fetch()
            result = self.get_reg8('a') & imm8
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (result >> 4) & 1 == 1:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
            self.reset_carry_flag()
        return band

    def and_imm16addr(self):
        """Returns a function that performs a bitwise AND with the 8-bit value
        at the address given as an argument to the function and the accumulator
        register A.

        :rtype: int → None"""

        def band():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            x = self.get_reg8('a')
            y = self.mmu.get_addr(imm16)
            result = x & y
            self.set_reg8('a', result)

            if result == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (result >> 4) & 0x1 == 1:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
            self.reset_carry_flag()
        return band

    def and_reg16addr(self, reg16):
        """Returns a function that performs a bitwise AND with the 8-bit value
        at the address in the given double register and the accumulator
        register.

        :param reg16: double register to AND with A.
        :rtype: None → None"""

        def band():
            x = self.get_reg8('a')
            y = self.mmu.get_addr(self.get_reg16(reg16))
            result = x & y
            self.set_reg8('a', result)

            if result == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (result >> 4) & 0x1 == 1:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()
            self.reset_carry_flag()
        return band

    def or_reg8(self, reg8):
        """Returns a function that stores the result of bitwise OR between
        :py:data:reg8 and A in the accumulator register A.

        :param reg8: single operand register
        :rtype: None → None"""

        def bor():
            result = self.get_reg8('a') | self.get_reg8(reg8)
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_sub_flag()
        return bor

    def or_imm8(self):
        """Returns a function that performs a bitwise OR between its single
        8-bit immediate parameter and A, then stores the result in A.

        :rtype: int → None"""

        def bor():
            imm8 = self.fetch()
            result = self.get_reg8('a') | imm8
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_sub_flag()
        return bor

    def or_imm16addr(self):
        """Returns a function that performs a bitwise OR between the value at
        the address given by the function's single 16-bit immediate parameter
        and A, then stores the result in A.

        :rtype: int → None"""

        def bor():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            result = self.get_reg8('a') | self.mmu.get_addr(imm16)
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_sub_flag()
        return bor

    def or_reg16addr(self, reg16):
        """Returns a function that performs a bitwise OR between the value at
        the address given by the function's single 16-bit immediate parameter
        and A, then stores the result in A.

        :rtype: None → None"""

        def bor():
            result = self.get_reg8('a') | self.mmu.get_addr(self.get_reg16(reg16))
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_sub_flag()
        return bor

    def xor_reg8(self, reg8):
        """Returns a function that performs a bitwise XOR between :py:data:reg8
        and A and stores the result in A.

        :param reg8: the single register operand
        :rtype: None → None"""

        def bxor():
            result = self.get_reg8('a') ^ self.get_reg8(reg8)
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_sub_flag()
        return bxor

    def xor_imm8(self):
        """Returns a function that performs a bitwise XOR between its 8-bit
        immediate parameter and A and stores the result in A.

        :rtype: int → None"""

        def bxor():
            imm8 = self.fetch()
            result = self.get_reg8('a') ^ imm8
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
        return bxor

    def xor_imm16addr(self):
        """Returns a function that performs a bitwise XOR between the value at
        the address given by its 16-bit immediate parameter and A, then stores
        the result in A.

        :rtype: int → None"""

        def bxor():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            result = self.get_reg8('a') ^ self.mmu.get_addr(imm16)
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
        return bxor

    def xor_reg16addr(self, reg16):
        """Returns a function that performs a bitwise XOR between the value at
        the address in :py:data:reg16 and A, then stores the result in A.

        :param reg16: address of the operand
        :rtype: None → None"""

        def bxor():
            result = self.get_reg8('a') ^ self.mmu.get_addr(self.get_reg16(reg16))
            self.set_reg8('a', result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
        return bxor

    def cp_reg8toreg8(self, reg8_1, reg8_2):
        """Returns a function that compares :py:data:reg8_1 and :py:data:reg8_2
        then sets the appropriate flags.

        Compare regA to regB means calculate regA - regB and
            * set Z if regA == regB
            * set NZ (reset Z) if regA != regB
            * set C if regA < regB
            * set NC (reset C) if regA >= regB

        :rtype: None → None"""

        def cp():
            result = self.get_reg8(reg8_1) - self.get_reg8(reg8_2)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if result > 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()

            if result < 0:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return cp

    def cp_reg8toimm16addr(self, reg8):
        """Returns a function that takes a 16-bit immediate and compares the
        given :py:data:reg8 with the value at the address given by this
        immediate, then sets the appropriate flags as specified in
        :py:method:cp_reg8toreg8.

        :param reg8: single register
        :rtype: int → None"""

        def cp():
            imm16 = self.fetch() << 8
            imm16 |= self.fetch()
            result = self.get_reg8(reg8) - self.mmu.get_addr(imm16)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if result > 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()

            if result < 0:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return cp

    def cp_reg8toreg16addr(self, reg8, reg16):
        """Returns a function that compares the given :py:data:reg8 with the
        value at address given by :py:data:reg16, then sets the appropriate
        flags as specified in :py:method:cp_reg8toreg8.

        :param reg8: single register
        :param reg16: double register holding an address
        :rtype: int → None"""

        def cp():
            result = self.get_reg8(reg8) - self.mmu.get_addr(self.get_reg16(reg16))

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if result > 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()

            if result < 0:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()
        return cp

    def rl_reg8(self, reg8):
        """Returns a function that shift :py:data:reg8 left 1, places the old
        bit 7 in the carry flag, and places old carry flag in bit 0.
        
        :param reg8: the number of bits to shift
        :rtype None → None"""

        def rl():
            last_carry = self.get_carry_flag()
            reg = self.get_reg8(reg8)
            result = (reg << 1) | last_carry

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_halfcarry_flag()
            self.reset_sub_flag()

            if reg & 0x80 == 0x80:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()

            self.set_reg8(reg8, result)
        return rl

    def rlc_reg8(self, reg8):
        """Returns a function that shifts :py:data:reg8 left 1, then 
        places the old bit 7 in the carry flag and bit 0.
        
        :param reg8: number of bits to rotate
        :rtype None → None"""

        def rlc():
            reg = self.get_reg8(reg8)
            result = (reg << 1) | (reg >> 7)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_halfcarry_flag()
            self.reset_sub_flag()

            if reg & 0x80 == 0x80:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()

            self.set_reg8(reg8, result)
        return rlc

    def rr_reg8(self, reg8):
        """Returns a function that shifts :py:data:reg8 right 1, places the old
        bit 0 in the carry flag, and place old carry in bit 7.
        
        :param reg8: the operand single register
        :rtype: None → None"""

        def rr():
            last_carry = self.get_carry_flag()
            reg = self.get_reg8(reg8)
            result = (reg >> 1) | (last_carry << 7)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_halfcarry_flag()
            self.reset_sub_flag()

            if reg & 0x01 == 0x01:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()

            self.set_reg8(reg8, result)
        return rr

    def rrc_reg8(self, reg8):
        """0x0f, CB 0x08-0x0f
        logical shift reg8 right 1, place old bit 0 in CF and bit 7."""

        def rrc():
            reg = self.get_reg8(reg8)
            result = (reg >> 1) | ((reg << 7) & 0x80)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            self.reset_halfcarry_flag()
            self.reset_sub_flag()

            if reg & 0x01 == 0x01:
                self.set_carry_flag()
            else:
                self.reset_carry_flag()

            self.set_reg8(reg8, result)
        return rrc

    def sla_reg8(self, reg8):
        """0x20-0x25, 0x27
        Logical shift reg8 left 1 and place old bit 0 in CF."""

        reg = self.get_reg8(reg8)
        result = reg << 1

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if (reg >> 7) & 0x01 == 1:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.set_reg8(result)

        raise NotImplementedError('sla reg8')

    def sla_addr16(self, addr16):
        """0x20-0x25, 0x27
        Logical shift (addr16) left 1 and place old bit 0 in CF."""

        reg = self.mmu.get_addr(addr16)
        result = reg << 1

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if (reg >> 7) & 0x01 == 1:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(result)

        raise NotImplementedError('sla (HL)')

    def sra_reg8(self, reg8):
        """0x28-0x2d, 0x2f
        Logical shift reg8 right 1 and place old bit 7 in CF."""
        
        reg = self.get_reg8(reg8)
        result = reg >> 1

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if reg & 0x01 == 1:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.set_reg8(result)

        raise NotImplementedError('sra reg8')

    def sra_addr16(self, addr16):
        """0x20-0x25, 0x27
        Logical shift (addr16) right 1 and place old bit 7 in CF."""

        reg = self.mmu.get_addr(addr16)
        result = reg >> 1

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if reg & 0x01 == 1:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(addr16, result)

        raise NotImplementedError('sra (HL)')

    def cpl(self):
        """0x2f: ~A"""

        self.set_reg8('a', ~self.get_reg8('a'))

    def daa(self):
        """0x27: adjust regA following BCD addition."""

        self.set_reg8('a', uint8toBCD(self.get_reg8('a')))

    def scf(self):
        """0x37: set carry flag"""

        self.set_carry_flag()

    def ccf(self):
        """0x3f: clear carry flag"""

        self.reset_carry_flag()

    def jr_imm8(self, cond=None):
        """Returns a function that takes a signed immediate and performs a
        relative jump by this immediate if :py:data:cond is true.

        :param cond: Z, NZ, C, NC
        :rtype: int → None"""

        if cond:
            cond = cond.lower()
        if cond == 'z':
            def check_cond():
                return self.get_zero_flag() == 1
        elif cond == 'nz':
            def check_cond():
                return self.get_zero_flag() == 0
        elif cond == 'c':
            def check_cond():
                return self.get_carry_flag() == 1
        elif cond == 'nc':
            def check_cond():
                return self.get_carry_flag() == 0
        elif cond is not None:
            raise ValueError('cond must be one of Z, NZ, C, NC')

        if cond is None:
            def jr():
                imm8 = self.fetch()
                self.set_pc(imm8)
        else:
            def jr():
                if check_cond():
                    imm8 = self.fetch()
                    self.set_pc(imm8)

        return jr

    def jp_imm16addr(self, cond=None):
        """Returns a function taking a 16-bit immediate that conditionally
        performs an absolute jump to that immediate if :py:data:cond is met.

        :param cond: Z, NZ, C, NC
        :rtype: int → None"""

        if cond:
            cond = cond.lower()
        if cond == 'z':
            def check_cond():
                return self.get_zero_flag() == 1
        elif cond == 'nz':
            def check_cond():
                return self.get_zero_flag() == 0
        elif cond == 'c':
            def check_cond():
                return self.get_carry_flag() == 1
        elif cond == 'nc':
            def check_cond():
                return self.get_carry_flag() == 0
        elif cond is not None:
            raise ValueError('cond must be one of Z, NZ, C, NC')

        if cond is None:
            def jp():
                imm16 = self.fetch() << 8
                imm16 |= self.fetch()
                self.set_pc(imm16)
        else:
            def jp():
                if check_cond():
                    imm16 = self.fetch() << 8
                    imm16 |= self.fetch()
                    self.set_pc(imm16)

        return jp

    def jp_reg16addr(self, reg16):
        """Returns a function that performs an uncoditional jump to the address
        in :py:data:reg16"""

        def jp():
            self.set_pc(self.get_reg16(reg16))
        return jp

    def ret(self, cond=None):
        """Returns a function that, based on cond, will get the return address
        from the stack and return.

        :param cond: one (or none) of Z, C, S, H
        :rtype: None → None"""

        if cond == 'z':
            def check_cond():
                return self.get_zero_flag() == 1
        elif cond == 'nz':
            def check_cond():
                return self.get_zero_flag() == 0
        elif cond == 'c':
            def check_cond():
                return self.get_carry_flag() == 1
        elif cond == 'nc':
            def check_cond():
                return self.get_carry_flag() == 0
        elif cond is not None:
            raise ValueError('cond must be one of Z, NZ, C, NC')

        if cond is None:
            def retc():
                sp = self.get_sp()
                pc = self.mmu.get_addr(sp + 1) << 8 | self.mmu.get_addr(sp)
                self.set_pc(pc)
                self.set_sp(sp + 2)
        else:
            def retc():
                if check_cond():
                    sp = self.get_sp()
                    pc = self.mmu.get_addr(sp + 1) << 8 | self.mmu.get_addr(sp)
                    self.set_pc(pc)
                    self.set_sp(sp + 2)

        return retc

    def reti(self):
        """0xd9 -- reti"""
        raise NotImplementedError('reti')

    def call_imm16addr(self, cond=None):
        """Returns a function that, based on :py:data:cond, pushes the current
        address in the program counter and jumps to the 16-bit immediate
        parameter of the function.

        :param cond: one of Z, C, S, H
        :rtype: int → None"""

        if cond is not None:
            cond = cond.lower()

        if cond == 'z':
            def check_cond():
                return self.get_zero_flag() == 1
        elif cond == 'nz':
            def check_cond():
                return self.get_zero_flag() == 0
        elif cond == 'c':
            def check_cond():
                return self.get_carry_flag() == 1
        elif cond == 'nc':
            def check_cond():
                return self.get_carry_flag() == 0
        elif cond is not None:
            raise ValueError('cond must be one of Z, NZ, C, NC')

        if cond is None:
            def call():
                imm16 = self.fetch() << 8
                imm16 |= self.fetch()
                pc = self.get_pc()
                sp = self.get_sp()
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(imm16)
                self.set_sp(sp - 2)
        else:
            def call():
                imm16 = self.fetch() << 8
                imm16 |= self.fetch()
                pc = self.get_pc()
                sp = self.get_sp()
                if check_cond():
                    self.mmu.set_addr(sp - 1, pc >> 8)
                    self.mmu.set_addr(sp - 2, pc & 0xff)
                    self.set_pc(imm16)
                    self.set_sp(sp - 2)
        return call

    def call_reg16addr(self, reg16, cond=None):
        """Returns a function that, based on :py:data:cond, pushes the current
        address in the program counter and jumps to the address in
        :py:data:reg16.

        :param cond: one of Z, C, S, H
        :param reg16: address to call
        :rtype: int → None"""

        pc = self.get_pc()
        sp = self.get_sp()

        if cond is not None:
            cond = cond.lower()

        if cond == 'z':
            def check_cond():
                return self.get_zero_flag() == 1
        elif cond == 'c':
            def check_cond():
                return self.get_carry_flag() == 1
        elif cond == 's':
            def check_cond():
                return self.get_sub_flag() == 1
        elif cond == 'h':
            def check_cond():
                return self.get_halfcarry_flag() == 1
        elif cond is not None:
            raise ValueError('cond must be one of Z, C, S, H')

        if cond is None:
            def call():
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(self.get_reg16(reg16))
                self.set_sp(sp - 2)
        else:
            def call():
                if check_cond():
                    self.mmu.set_addr(sp - 1, pc >> 8)
                    self.mmu.set_addr(sp - 2, pc & 0xff)
                    self.set_pc(self.get_reg16(reg16))
                    self.set_sp(sp - 2)
        return call

    def rst(self):
        """0xc7, 0xd7, 0xe7, 0xf7, 0xcf, 0xdf, 0xef, 0xff -- rst xxH"""

        raise NotImplementedError('rst')

    def di(self):
        """0xf3 -- di
        Disable interrupts."""

        raise NotImplementedError('di')

    def ei(self):
        """0xfb -- ei
        Enable interrupts."""

        raise NotImplementedError('ei')
