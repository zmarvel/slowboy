
from enum import Enum
import logging

from slowboy.util import Op, ClockListener, uint8toBCD, add_s8, add_s16, twoscompl8, twoscompl16
from slowboy.mmu import MMU
from slowboy.gpu import GPU
from slowboy.interrupts import InterruptHandler

class State(Enum):
    RUN = 0
    HALT = 1
    STOP = 2

class Z80(object):
    reglist = ['b', 'c', None, 'e', 'h', 'd', None, 'a']
    internal_reglist = ['b', 'c', 'd', 'e', 'h', 'l', 'a', 'f']

    def __init__(self, rom=None, mmu=None, gpu=None, log_level=logging.WARNING):
        self.clock = 0
        self.clock_listeners = []
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
        self.sp = 0xfffe
        self.pc = 0x100
        self.state = State.STOP
        self.mmu = MMU(rom=rom) if mmu is None else mmu
        self.gpu = GPU() if gpu is None else gpu
        self.mmu.load_gpu(self.gpu)
        self.register_clock_listener(self.gpu)
        self.interrupt_handler = InterruptHandler()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        console_log_handler = logging.StreamHandler()
        console_log_handler.setLevel(log_level)
        self.logger.addHandler(console_log_handler)

        self._init_opcode_map()

    def _init_opcode_map(self):
        self.opcode_map = {
                0x00: Op(self.nop, 4),
                0x10: Op(self.stop, 4),
                0x76: Op(self.halt, 4),
                0xf3: Op(self.di, 4),
                0xfb: Op(self.ei, 4),

                0x40: Op(self.ld_reg8toreg8('b', 'b'), 4),
                0x41: Op(self.ld_reg8toreg8('b', 'c'), 4),
                0x42: Op(self.ld_reg8toreg8('b', 'd'), 4),
                0x43: Op(self.ld_reg8toreg8('b', 'e'), 4),
                0x44: Op(self.ld_reg8toreg8('b', 'h'), 4),
                0x45: Op(self.ld_reg8toreg8('b', 'l'), 4),
                0x46: Op(self.ld_reg16addrtoreg8('hl', 'b'), 8),
                0x47: Op(self.ld_reg8toreg8('b', 'a'), 4),
                0x48: Op(self.ld_reg8toreg8('c', 'b'), 4),
                0x49: Op(self.ld_reg8toreg8('c', 'c'), 4),
                0x4a: Op(self.ld_reg8toreg8('c', 'd'), 4),
                0x4b: Op(self.ld_reg8toreg8('c', 'e'), 4),
                0x4c: Op(self.ld_reg8toreg8('c', 'h'), 4),
                0x4d: Op(self.ld_reg8toreg8('c', 'l'), 4),
                0x4e: Op(self.ld_reg16addrtoreg8('hl', 'c'), 8),
                0x4f: Op(self.ld_reg8toreg8('c', 'a'), 4),
                0x50: Op(self.ld_reg8toreg8('d', 'b'), 4),
                0x51: Op(self.ld_reg8toreg8('d', 'c'), 4),
                0x52: Op(self.ld_reg8toreg8('d', 'd'), 4),
                0x53: Op(self.ld_reg8toreg8('d', 'e'), 4),
                0x54: Op(self.ld_reg8toreg8('d', 'h'), 4),
                0x55: Op(self.ld_reg8toreg8('d', 'l'), 4),
                0x56: Op(self.ld_reg16addrtoreg8('hl', 'd'), 8),
                0x57: Op(self.ld_reg8toreg8('d', 'a'), 4),
                0x58: Op(self.ld_reg8toreg8('e', 'b'), 4),
                0x59: Op(self.ld_reg8toreg8('e', 'c'), 4),
                0x5a: Op(self.ld_reg8toreg8('e', 'd'), 4),
                0x5b: Op(self.ld_reg8toreg8('e', 'e'), 4),
                0x5c: Op(self.ld_reg8toreg8('e', 'h'), 4),
                0x5d: Op(self.ld_reg8toreg8('e', 'l'), 4),
                0x5e: Op(self.ld_reg16addrtoreg8('hl', 'e'), 8),
                0x5f: Op(self.ld_reg8toreg8('e', 'a'), 4),
                0x60: Op(self.ld_reg8toreg8('h', 'b'), 4),
                0x61: Op(self.ld_reg8toreg8('h', 'c'), 4),
                0x62: Op(self.ld_reg8toreg8('h', 'd'), 4),
                0x63: Op(self.ld_reg8toreg8('h', 'e'), 4),
                0x64: Op(self.ld_reg8toreg8('h', 'h'), 4),
                0x65: Op(self.ld_reg8toreg8('h', 'l'), 4),
                0x66: Op(self.ld_reg16addrtoreg8('hl', 'h'), 8),
                0x67: Op(self.ld_reg8toreg8('h', 'a'), 4),
                0x68: Op(self.ld_reg8toreg8('l', 'b'), 4),
                0x69: Op(self.ld_reg8toreg8('l', 'c'), 4),
                0x6a: Op(self.ld_reg8toreg8('l', 'd'), 4),
                0x6b: Op(self.ld_reg8toreg8('l', 'e'), 4),
                0x6c: Op(self.ld_reg8toreg8('l', 'h'), 4),
                0x6d: Op(self.ld_reg8toreg8('l', 'l'), 4),
                0x6e: Op(self.ld_reg16addrtoreg8('hl', 'l'), 8),
                0x6f: Op(self.ld_reg8toreg8('l', 'a'), 4),
                0x70: Op(self.ld_reg8toreg16addr('b', 'hl'), 8),
                0x71: Op(self.ld_reg8toreg16addr('c', 'hl'), 8),
                0x72: Op(self.ld_reg8toreg16addr('d', 'hl'), 8),
                0x73: Op(self.ld_reg8toreg16addr('e', 'hl'), 8),
                0x74: Op(self.ld_reg8toreg16addr('h', 'hl'), 8),
                0x75: Op(self.ld_reg8toreg16addr('l', 'hl'), 8),
                0x77: Op(self.ld_reg8toreg16addr('a', 'hl'), 8),
                0x78: Op(self.ld_reg8toreg8('a', 'b'), 4),
                0x79: Op(self.ld_reg8toreg8('a', 'c'), 4),
                0x7a: Op(self.ld_reg8toreg8('a', 'd'), 4),
                0x7b: Op(self.ld_reg8toreg8('a', 'e'), 4),
                0x7c: Op(self.ld_reg8toreg8('a', 'h'), 4),
                0x7d: Op(self.ld_reg8toreg8('a', 'l'), 4),
                0x7e: Op(self.ld_reg16addrtoreg8('hl', 'a'), 8),
                0x7f: Op(self.ld_reg8toreg8('a', 'a'), 4),

                0x02: Op(self.ld_reg8toreg16addr('a', 'bc'), 8),
                0x12: Op(self.ld_reg8toreg16addr('a', 'de'), 8),
                0x22: Op(self.ld_reg8toreg16addr_inc('a', 'hl'), 8),
                0x32: Op(self.ld_reg8toreg16addr_dec('a', 'hl'), 8),

                0x06: Op(self.ld_imm8toreg8('b'), 8),
                0x16: Op(self.ld_imm8toreg8('d'), 8),
                0x26: Op(self.ld_imm8toreg8('h'), 8),
                0x36: Op(self.ld_imm8toreg16addr('hl'), 12),

                0x08: Op(self.ld_sptoimm16addr, 8),

                0x0a: Op(self.ld_reg16addrtoreg8('bc', 'a'), 8),
                0x1a: Op(self.ld_reg16addrtoreg8('de', 'a'), 8),
                0x2a: Op(self.ld_reg16addrtoreg8('hl', 'a', inc=True), 8),
                0x3a: Op(self.ld_reg16addrtoreg8('hl', 'a', dec=True), 8),

                0x0e: Op(self.ld_imm8toreg8('c'), 8),
                0x1e: Op(self.ld_imm8toreg8('e'), 8),
                0x2e: Op(self.ld_imm8toreg8('l'), 8),
                0x3e: Op(self.ld_imm8toreg8('a'), 8),

                0xe0: Op(self.ldh_regAtoaddr8, 12), # ldh (imm8), a
                0xf0: Op(self.ldh_addr8toregA, 12), # ldh a, (imm8)
                0xe2: Op(self.ldh_regAtoaddrC, 8), # ldh (c), a
                0xf2: Op(self.ldh_addrCtoregA, 8), # ldh a, (c)

                0xc1: None, # pop bc TODO
                0xd1: None, # pop de TODO
                0xe1: None, # pop hl TODO
                0xf1: None, # pop af TODO (affects flags)

                0xc5: Op(self.push_reg16('bc'), 16), # push bc
                0xd5: Op(self.push_reg16('de'), 16), # push de
                0xe5: Op(self.push_reg16('hl'), 16), # push hl
                0xf5: Op(self.push_reg16('af'), 16), # push af

                0xf8: None, # ld hl, sp+imm8 TODO

                0xf9: Op(self.ld_reg16toreg16('hl', 'sp'), 8),

                0xea: Op(self.ld_reg8toimm16addr('a'), 16),
                0xfa: Op(self.ld_imm16addrtoreg8('a'), 16),

                0x01: Op(self.ld_imm16toreg16('bc'), 12),
                0x11: Op(self.ld_imm16toreg16('de'), 12),
                0x21: Op(self.ld_imm16toreg16('hl'), 12),
                0x31: Op(self.ld_imm16toreg16('sp'), 12),

                # arithmetic and logic

                0x03: Op(self.inc_reg16('bc'), 8),
                0x13: Op(self.inc_reg16('de'), 8),
                0x23: Op(self.inc_reg16('hl'), 8),
                0x33: Op(self.inc_reg16('sp'), 8),
                0x04: Op(self.inc_reg8('b'), 4),
                0x14: Op(self.inc_reg8('d'), 4),
                0x24: Op(self.inc_reg8('h'), 4),
                0x34: Op(self.inc_addrHL, 12),
                0x0c: Op(self.inc_reg8('c'), 4),
                0x1c: Op(self.inc_reg8('e'), 4),
                0x2c: Op(self.inc_reg8('l'), 4),
                0x3c: Op(self.inc_reg8('a'), 4),
                0x05: Op(self.dec_reg8('b'), 4),
                0x15: Op(self.dec_reg8('d'), 4),
                0x25: Op(self.dec_reg8('h'), 4),
                0x35: Op(self.dec_addrHL, 12),
                0x0d: Op(self.dec_reg8('c'), 4),
                0x1d: Op(self.dec_reg8('e'), 4),
                0x2d: Op(self.dec_reg8('l'), 4),
                0x3d: Op(self.dec_reg8('a'), 4),
                0x0b: Op(self.dec_reg16('bc'), 8),
                0x1b: Op(self.dec_reg16('de'), 8),
                0x2b: Op(self.dec_reg16('hl'), 8),
                0x3b: Op(self.dec_reg16('sp'), 8),

                0x80: Op(self.add_reg8toreg8('b', 'a'), 4),
                0x81: Op(self.add_reg8toreg8('c', 'a'), 4),
                0x82: Op(self.add_reg8toreg8('d', 'a'), 4),
                0x83: Op(self.add_reg8toreg8('e', 'a'), 4),
                0x84: Op(self.add_reg8toreg8('h', 'a'), 4),
                0x85: Op(self.add_reg8toreg8('l', 'a'), 4),
                #0x86: self.add_reg16addrtoreg8('hl', 'a'),
                0x87: Op(self.add_reg8toreg8('a', 'a', carry=True), 4),
                0x88: Op(self.add_reg8toreg8('b', 'a', carry=True), 4),
                0x89: Op(self.add_reg8toreg8('c', 'a', carry=True), 4),
                0x8a: Op(self.add_reg8toreg8('d', 'a', carry=True), 4),
                0x8b: Op(self.add_reg8toreg8('e', 'a', carry=True), 4),
                0x8c: Op(self.add_reg8toreg8('h', 'a', carry=True), 4),
                0x8d: Op(self.add_reg8toreg8('l', 'a', carry=True), 4),
                #0x8e: self.add_reg16addrtoreg8('hl', 'a', carry=True),
                0x8f: Op(self.add_reg8toreg8('a', 'a', carry=True), 4),
                0x90: Op(self.sub_reg8fromreg8('b', 'a'), 4),
                0x91: Op(self.sub_reg8fromreg8('c', 'a'), 4),
                0x92: Op(self.sub_reg8fromreg8('d', 'a'), 4),
                0x93: Op(self.sub_reg8fromreg8('e', 'a'), 4),
                0x94: Op(self.sub_reg8fromreg8('h', 'a'), 4),
                0x95: Op(self.sub_reg8fromreg8('l', 'a'), 4),
                #0x96: self.sub_reg16addrfromreg8('hl', 'a'),
                0x97: Op(self.sub_reg8fromreg8('a', 'a', carry=True), 4),
                0x98: Op(self.sub_reg8fromreg8('b', 'a', carry=True), 4),
                0x99: Op(self.sub_reg8fromreg8('c', 'a', carry=True), 4),
                0x9a: Op(self.sub_reg8fromreg8('d', 'a', carry=True), 4),
                0x9b: Op(self.sub_reg8fromreg8('e', 'a', carry=True), 4),
                0x9c: Op(self.sub_reg8fromreg8('h', 'a', carry=True), 4),
                0x9d: Op(self.sub_reg8fromreg8('l', 'a', carry=True), 4),
                #0x9e: self.sub_reg16addrfromreg8('hl', 'a', carry=True),
                0x9f: Op(self.sub_reg8fromreg8('a', 'a', carry=True), 4),
                0xa0: Op(self.and_reg8('b'), 4),
                0xa1: Op(self.and_reg8('c'), 4),
                0xa2: Op(self.and_reg8('d'), 4),
                0xa3: Op(self.and_reg8('e'), 4),
                0xa4: Op(self.and_reg8('h'), 4),
                0xa5: Op(self.and_reg8('l'), 4),
                0xa6: Op(self.and_reg16addr('hl'), 8),
                0xa7: Op(self.and_reg8('a'), 4),
                0xa8: Op(self.xor_reg8('b'), 4),
                0xa9: Op(self.xor_reg8('c'), 4),
                0xaa: Op(self.xor_reg8('d'), 4),
                0xab: Op(self.xor_reg8('e'), 4),
                0xac: Op(self.xor_reg8('h'), 4),
                0xad: Op(self.xor_reg8('l'), 4),
                0xae: Op(self.xor_reg16addr('hl'), 8),
                0xaf: Op(self.xor_reg8('a'), 4),
                0xb0: Op(self.or_reg8('b'), 4),
                0xb1: Op(self.or_reg8('c'), 4),
                0xb2: Op(self.or_reg8('d'), 4),
                0xb3: Op(self.or_reg8('e'), 4),
                0xb4: Op(self.or_reg8('h'), 4),
                0xb5: Op(self.or_reg8('l'), 4),
                0xb6: Op(self.or_reg16addr('hl'), 8),
                0xb7: Op(self.or_reg8('a'), 4),
                0xb8: Op(self.cp_reg8toreg8('a', 'b'), 4),
                0xb9: Op(self.cp_reg8toreg8('a', 'c'), 4),
                0xba: Op(self.cp_reg8toreg8('a', 'd'), 4),
                0xbb: Op(self.cp_reg8toreg8('a', 'e'), 4),
                0xbc: Op(self.cp_reg8toreg8('a', 'h'), 4),
                0xbd: Op(self.cp_reg8toreg8('a', 'l'), 4),
                0xbe: Op(self.cp_reg8toreg16addr('a', 'hl'), 8),
                0xbf: Op(self.cp_reg8toreg8('a', 'a'), 4),
                0xc6: Op(self.add_imm8toreg8('a'), 8),
                0xd6: Op(self.sub_imm8fromreg8('a'), 8),
                0xe6: Op(self.and_imm8, 8),
                0xf6: Op(self.or_imm8, 8),


                0xc7: Op(self.rst, 16), # TODO
                0xd7: Op(self.rst, 16), # TODO
                0xe7: Op(self.rst, 16), # TODO
                0xf7: Op(self.rst, 16), # TODO
                0xcf: Op(self.rst, 16), # TODO
                0xdf: Op(self.rst, 16), # TODO
                0xef: Op(self.rst, 16), # TODO
                0xff: Op(self.rst, 16), # TODO

                # JP instructions take 16 cycles when taken, 12 when not taken
                0xc3: Op(self.jp_imm16addr(), 16),
                0xc2: Op(self.jp_imm16addr('nz'), 16),
                0xd2: Op(self.jp_imm16addr('nc'), 16),
                0xca: Op(self.jp_imm16addr('z'), 16),
                0xda: Op(self.jp_imm16addr('c'), 16),
                0xe9: Op(self.jp_reg16addr('hl'), 16),

                # JR instructions take 12 cycles when taken, 8 when not taken
                0x18: Op(self.jr_imm8(), 12),
                0x20: Op(self.jr_imm8('nz'), 12),
                0x30: Op(self.jr_imm8('nc'), 12),
                0x28: Op(self.jr_imm8('z'), 12),
                0x38: Op(self.jr_imm8('c'), 12),

                # CALL takes 24 cycles when taken, 12 when not taken
                0xcd: Op(self.call_imm16addr(), 24),
                0xc4: Op(self.call_imm16addr('nz'), 24),
                0xd4: Op(self.call_imm16addr('nc'), 24),
                0xcc: Op(self.call_imm16addr('z'), 24),
                0xdc: Op(self.call_imm16addr('c'), 24),

                # RET takes 20 cycles when taken, 8 when not taken
                0xc9: Op(self.ret(), 20),
                0xd9: Op(self.reti, 20),
                0xc0: Op(self.ret('nz'), 20),
                0xd0: Op(self.ret('nc'), 20),
                0xc8: Op(self.ret('z'), 20),
                0xd8: Op(self.ret('c'), 20),
                }

    def __repr__(self):
        return ('Z80('
                'state={state}, '
                'pc={pc:#x}, sp={sp:#x}, '
                'a={a:#x}, b={b:#x}, c={c:#x}, d={d:#x}, e={e:#x}, '
                'h={h:#x}, l={l:#x})'
                ).format(
            state=self.state, pc=self.pc, sp=self.sp,
            a=self.get_reg8('a'), f=self.get_reg8('f'),
            b=self.get_reg8('b'), c=self.get_reg8('c'),
            d=self.get_reg8('d'), e=self.get_reg8('e'),
            h=self.get_reg8('h'), l=self.get_reg8('l'))

    def register_clock_listener(self, listener):
        if not isinstance(listener, ClockListener):
            raise TypeError('listener must implement ClockListener')
        self.clock_listeners.append(listener)

    def get_registers(self):
        return self.registers

    def set_reg8(self, reg8, value):
        """Set :py:data:reg8 to :py:data:value.

        :param reg8: one of B, C, D, E, H, L, A, F
        :param value"""

        reg8 = reg8.lower()

        if reg8 not in self.internal_reglist:
            raise KeyError('unrecognized register {}'.format(reg8))

        self.registers[reg8] = value & 0xff

    def get_reg8(self, reg8):
        """Get the value of :py:data:reg8.

        :param reg8: one of B, C, D, E, H, L, A, F
        :raises KeyError"""

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
        elif reg16 == 'af':
            self.registers['a'] = (value >> 8) & 0xff
            self.registers['f'] = value & 0xff
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
        elif reg16 == 'af':
            return (self.registers['a'] << 8) | self.registers['f']
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
        """Fetch a byte, incrementing the PC as needed."""

        value = self.mmu.get_addr(self.get_pc())
        self.inc_pc()
        return value

    def fetch2(self):
        """Fetch 2 bytes, incrementing the PC as needed."""

        value = self.mmu.get_addr(self.get_pc())
        self.inc_pc()
        value |= self.mmu.get_addr(self.get_pc()) << 8
        self.inc_pc()
        return value

    def step(self):
        self.logger.debug(self)
        opcode = self.fetch()
        print(self.opcode_map[opcode])

        # decode
        op = self.opcode_map[opcode]

        if op is None:
            raise ValueError('op {:#x} is None'.format(opcode))
        # execute
        op.function()

        self.clock += op.cycles

        for listener in self.clock_listeners:
            listener.notify(self.clock, op.cycles)


    def go(self):
        self.state = State.RUN
        while self.state == State.RUN:
            self.logger.debug(self)
            opcode = self.fetch()
            print(self.opcode_map[opcode])

            # decode
            op = self.opcode_map[opcode]

            # execute
            op.function()

            self.clock += op.cycles

            for listener in self.clock_listeners:
                listener.notify(self.clock, op.cycles)

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
                imm16 = self.fetch2()
                self.logger.debug('ld {}, {}'.format(reg16, imm16))
                self.set_sp(imm16)
        else:
            def ld():
                imm16 = self.fetch2()
                self.logger.debug('ld {}, {}'.format(reg16, imm16))
                self.set_reg16(reg16, imm16)
        return ld

    def ld_reg8toreg16addr(self, reg8, reg16):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit double register.

        :param reg8: single byte source register
        :param reg16: two-byte register containing destination address
        :rtype: None → None"""

        def ld():
            self.logger.debug('ld ({}), {}'.format(reg16, reg8))
            self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
        return ld

    def ld_reg8toreg16addr_inc(self, reg8, reg16):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit double register, then increment the address in the
        dregister.

        :param reg8: single byte source register
        :param reg16: two-byte register containing destination address
        :rtype: None → None"""

        def ld():
            # TODO set flags
            self.logger.debug('ld ({}), {}'.format(reg16, reg8))
            self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
            self.set_reg16(reg16, self.get_reg16(reg16) + 1)
        return ld

    def ld_reg8toreg16addr_dec(self, reg8, reg16):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit double register, then decrement the address in the
        dregister.

        :param reg8: single byte source register
        :param reg16: two-byte register containing destination address
        :rtype: None → None"""

        def ld():
            # TODO set flags
            self.logger.debug('ld ({}), {}'.format(reg16, reg8))
            self.mmu.set_addr(self.get_reg16(reg16), self.get_reg8(reg8))
            self.set_reg16(reg16, self.get_reg16(reg16) - 1)
        return ld

    def ld_reg8toimm16addr(self, reg8):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit immediate.

        :param reg8: single byte source register
        :rtype: integer → None"""

        def ld():
            imm16 = self.fetch2()
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
                self.logger.debug('ld {}, ({})'.format(reg8, reg16))
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 + 1)
        elif dec:
            def ld():
                u16 = self.get_reg16(reg16)
                self.logger.debug('ld {}, ({})'.format(reg8, reg16))
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 - 1)
        else:
            def ld():
                u16 = self.get_reg16(reg16)
                self.logger.debug('ld {}, ({})'.format(reg8, reg16))
                self.set_reg8(reg8, self.mmu.get_addr(u16))
        return ld

    def ld_reg16toreg16(self, src_reg16, dest_reg16):
        src_reg16 = src_reg16.lower()
        dest_reg16 = dest_reg16.lower()
        def ld():
            if src_reg16 == 'sp':
                self.set_reg16(dest_reg16, self.get_sp())
            elif dest_reg16 == 'sp':
                self.set_sp(self.get_reg16(src_reg16))
            else:
                self.set_reg16(dest_reg16, self.get_reg16(src_reg16))
        return ld

    def ld_imm16addrtoreg8(self, reg8):
        """Returns a function to load the value at an address given by a 16-bit
        immediate into an 8-bit register.

        :param reg8: the single-byte destination register
        :rtype: integer → None"""

        def ld():
            imm16 = self.fetch2()
            self.set_reg8(reg8, self.mmu.get_addr(imm16))
        return ld

    def ld_sptoimm16addr(self):
        """Loads the most significant byte of the stack pointer into the address
        given by :py:data:imm16 and the least significant byte of the SP into
        :py:data:imm16+1.

        :param imm16: 16-bit address
        :rtype: None"""

        imm16 = self.fetch2()
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

    def ldh_regAtoaddr8(self):
        """0xe0 -- load regA to 0xff00+addr8
        """
        addr8 = self.fetch()
        self.mmu.set_addr(0xff00+addr8, self.get_reg8('a'))

    def ldh_addr8toregA(self):
        """0xf0 -- load (0xff00+addr8) into regA
        """
        addr8 = self.fetch()
        self.set_reg8('a', self.mmu.get_addr(0xff00+addr8))

    def ldh_regAtoaddrC(self):
        """0xe2 -- load regA to (0xff00+regC)
        """
        self.mmu.set_addr(0xff00+self.get_reg8('c'), self.get_reg8('a'))

    def ldh_addrCtoregA(self):
        """0xf2 -- load (0xff00+regC) to regA
        """
        self.set_reg8('a', self.mmu.get_addr(0xff00+self.get_reg8('c')))

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

            result = u8 + 0xff

            self.set_reg8(reg8, result)

            if u8 & 0x0f == 0:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            if (result & 0xff) == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

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
            imm16 = self.fetch2()
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
            imm16 = self.fetch2()
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
            imm16 = self.fetch2()
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
            imm16 = self.fetch2()
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
            imm16 = self.fetch2()
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

    def cp_imm8toregA(self):
        """Compares 8-bit immediate to value in register A, then sets appropriate flags.

        :rtype: None"""

        imm8 = self.fetch()
        result = imm8 - self.mmu.get_addr(self.get_reg16(reg16))

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

        def sla():
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

            self.set_reg8(reg8, result)
        return sla

    def sla_reg16addr(self, reg16):
        """0x20-0x25, 0x27
        Logical shift (addr16) left 1 and place old bit 0 in CF."""

        def sla():
            addr = self.get_reg16(reg16)
            reg = self.mmu.get_addr(addr)
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

            self.mmu.set_addr(addr, result)
        return sla

    def sra_reg8(self, reg8):
        """0x28-0x2d, 0x2f
        Arithmetic shift reg8 right 1 and place old bit 7 in CF."""
        
        def sra():
            reg = self.get_reg8(reg8)
            result = (reg & 0x80) | (reg >> 1)

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

            self.set_reg8(reg8, result)
        return sra

    def sra_reg16addr(self, reg16):
        """0x20-0x25, 0x27
        Arithmetic shift (addr16) right 1 and place old bit 7 in CF."""

        def sra():
            addr16 = self.get_reg16(reg16)
            reg = self.mmu.get_addr(addr16)
            result = (reg & 0x80) | (reg >> 1)

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
        return sra

    def srl_reg8(self, reg8):
        """Logical shift reg8 right 1 and place old LSb in C"""

        def srl():
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

            self.set_reg8(reg8, result)
        return srl

    def srl_reg16addr(self, reg16):
        """Logical shift reg8 right 1 and place old LSb in C"""

        def srl():
            addr = self.get_reg16(reg16)
            reg = self.mmu.get_addr(addr)
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

            self.mmu.set_addr(addr, result)
        return srl

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
                self.logger.debug('jr {:#x}'.format(imm8))
                if (imm8 >> 7) & 1: # negative
                    imm8 = twoscompl16(twoscompl8(imm8))
                self.set_pc(add_s16(self.get_pc(), imm8))
        else:
            def jr():
                imm8 = self.fetch()
                self.logger.debug('jr {}, {:#x}'.format(cond, imm8))
                if check_cond():
                    if (imm8 >> 7) & 1: # negative
                        imm8 = twoscompl16(twoscompl8(imm8))
                    self.set_pc(add_s16(self.get_pc(), imm8))

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
                imm16 = self.fetch2()
                self.set_pc(imm16)
        else:
            def jp():
                imm16 = self.fetch2()
                if check_cond():
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
                imm16 = self.fetch2()
                pc = self.get_pc()
                sp = self.get_sp()
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(imm16)
                self.set_sp(sp - 2)
        else:
            def call():
                imm16 = self.fetch2()
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

    def push_reg16(self, reg16):
        """0xc5, 0xd5, 0xe5, 0xf5"""
        def push():
            self.set_sp(self.get_sp() - 1)
            self.mmu.set_addr(self.get_sp(), self.get_reg16(reg16))
        return push

    def rst(self):
        """0xc7, 0xd7, 0xe7, 0xf7, 0xcf, 0xdf, 0xef, 0xff -- rst xxH"""

        raise NotImplementedError('rst')

    def di(self):
        """0xf3 -- di
        Disable interrupts."""

        self.interrupt_handler.di()

    def ei(self):
        """0xfb -- ei
        Enable interrupts."""

        self.interrupt_handler.ei()
