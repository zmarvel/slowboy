

# import faulthandler
# faulthandler.enable()


from enum import Enum
import logging
from collections import defaultdict, deque
# from functools import partial
from time import sleep

from slowboy.util import Op, ClockListener, twoscompl8, twoscompl16, add_s16
from slowboy.mmu import MMU
from slowboy.gpu import GPU
from slowboy.interrupts import InterruptController
from slowboy.timer import Timer


Z_FLAG_OFFSET = 7
Z_FLAG_MASK = 1 << Z_FLAG_OFFSET
N_FLAG_OFFSET = 6
N_FLAG_MASK = 1 << N_FLAG_OFFSET
HC_FLAG_OFFSET = 5
HC_FLAG_MASK = 1 << HC_FLAG_OFFSET
C_FLAG_OFFSET = 4
C_FLAG_MASK = 1 << C_FLAG_OFFSET


class Z80Error(Exception):
    pass


class State(Enum):
    RUN = 0
    HALT = 1
    STOP = 2


class Z80:
    reglist = ['b', 'c', None, 'e', 'h', 'd', None, 'a']
    internal_reglist = ['b', 'c', 'd', 'e', 'h', 'l', 'a', 'f']

    def __init__(self, rom=None, mmu=None, gpu=None, timer=None,
                 debug=False, debug_address=None, cmd_q=[], resp_q=[],
                 log_level=logging.WARNING):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self.logger.addFilter(self)

        self.clock = 0
        self.clock_listeners = []

        self.state = State.STOP
        if mmu is None:
            self.mmu = MMU(rom=rom, logger=self.logger, log_level=log_level)
        else:
            self.mmu = mmu
        # self.gpu = GPU(logger=self.logger, log_level=log_level) if gpu is None else gpu
        self.gpu = GPU(logger=self.logger) if gpu is None else gpu
        self.mmu.load_gpu(self.gpu)
        self.register_clock_listener(self.gpu)

        self.timer = Timer(logger=self.logger) if timer is None else timer
        self.mmu.load_timer(self.timer)
        self.register_clock_listener(self.timer)

        self._saved_pc = None
        self._in_interrupt = False

        self.interrupt_controller = InterruptController(logger=self.logger)
        self.mmu.load_interrupt_controller(self.interrupt_controller)
        self.gpu.load_interrupt_controller(self.interrupt_controller)
        self.timer.register_interrupt_listener(self.interrupt_controller)

        self._init_opcode_map()

        self.registers = {
            'a': 0x01,
            'f': 0xb0,
            'b': 0x00,
            'c': 0x13,
            'd': 0x00,
            'e': 0xd8,
            'h': 0x01,
            'l': 0x4d,
        }
        self._sp = 0xfffe
        self._pc = 0x100
        self.op_pc = self.pc
        if rom is not None:
            self.opcode = self.mmu.get_addr(self.op_pc)
            if self.opcode in self.opcode_map:
                self.op = self.opcode_map[self.opcode]
            elif self.opcode == 0xcb:
                self.opcode = self.mmu.get_addr(self.op_pc+1)
                self.op = self.cb_opcode_map[self.opcode]

        # self._branches = defaultdict(lambda: 0)
        self._opcode_ring = deque(maxlen=10)

        self.debug = debug
        self.cmd_q = cmd_q
        self.resp_q = resp_q
        self.trace = False
        self.step = False

        self.breakpoints = []

    def _init_opcode_map(self):
        self.opcode_map = {
                0x00: Op(self.nop, 4, 'nop'),
                0x10: Op(self.stop, 4, 'stop'),
                0x76: Op(self.halt, 4, 'halt'),
                0xf3: Op(self.di, 4, 'di'),
                0xfb: Op(self.ei, 4, 'ei'),

                0x40: Op(self.ld_reg8toreg8('b', 'b'), 4, 'ld b, b'),
                0x41: Op(self.ld_reg8toreg8('c', 'b'), 4, 'ld b, c'),
                0x42: Op(self.ld_reg8toreg8('d', 'b'), 4, 'ld b, d'),
                0x43: Op(self.ld_reg8toreg8('e', 'b'), 4, 'ld b, e'),
                0x44: Op(self.ld_reg8toreg8('h', 'b'), 4, 'ld b, h'),
                0x45: Op(self.ld_reg8toreg8('l', 'b'), 4, 'ld b, l'),
                0x46: Op(self.ld_reg16addrtoreg8('hl', 'b'), 8, 'ld b, (hl)'),
                0x47: Op(self.ld_reg8toreg8('a', 'b'), 4, 'ld b, a'),
                0x48: Op(self.ld_reg8toreg8('b', 'c'), 4, 'ld c, b'),
                0x49: Op(self.ld_reg8toreg8('c', 'c'), 4, 'ld c, c'),
                0x4a: Op(self.ld_reg8toreg8('d', 'c'), 4, 'ld c, d'),
                0x4b: Op(self.ld_reg8toreg8('e', 'c'), 4, 'ld c, e'),
                0x4c: Op(self.ld_reg8toreg8('h', 'c'), 4, 'ld c, h'),
                0x4d: Op(self.ld_reg8toreg8('l', 'c'), 4, 'ld c, l'),
                0x4e: Op(self.ld_reg16addrtoreg8('hl', 'c'), 8, 'ld c, (hl)'),
                0x4f: Op(self.ld_reg8toreg8('a', 'c'), 4, 'ld c, a'),
                0x50: Op(self.ld_reg8toreg8('b', 'd'), 4, 'ld d, b'),
                0x51: Op(self.ld_reg8toreg8('c', 'd'), 4, 'ld d, c'),
                0x52: Op(self.ld_reg8toreg8('d', 'd'), 4, 'ld d, d'),
                0x53: Op(self.ld_reg8toreg8('e', 'd'), 4, 'ld d, e'),
                0x54: Op(self.ld_reg8toreg8('h', 'd'), 4, 'ld d, h'),
                0x55: Op(self.ld_reg8toreg8('l', 'd'), 4, 'ld d, l'),
                0x56: Op(self.ld_reg16addrtoreg8('hl', 'd'), 8, 'ld d, (hl)'),
                0x57: Op(self.ld_reg8toreg8('a', 'd'), 4, 'ld d, a'),
                0x58: Op(self.ld_reg8toreg8('b', 'e'), 4, 'ld e, b'),
                0x59: Op(self.ld_reg8toreg8('c', 'e'), 4, 'ld e, c'),
                0x5a: Op(self.ld_reg8toreg8('d', 'e'), 4, 'ld e, d'),
                0x5b: Op(self.ld_reg8toreg8('e', 'e'), 4, 'ld e, e'),
                0x5c: Op(self.ld_reg8toreg8('h', 'e'), 4, 'ld e, h'),
                0x5d: Op(self.ld_reg8toreg8('l', 'e'), 4, 'ld e, l'),
                0x5e: Op(self.ld_reg16addrtoreg8('hl', 'e'), 8, 'ld e, (hl)'),
                0x5f: Op(self.ld_reg8toreg8('a', 'e'), 4, 'ld e, a'),
                0x60: Op(self.ld_reg8toreg8('b', 'h'), 4, 'ld h, b'),
                0x61: Op(self.ld_reg8toreg8('c', 'h'), 4, 'ld h, c'),
                0x62: Op(self.ld_reg8toreg8('d', 'h'), 4, 'ld h, d'),
                0x63: Op(self.ld_reg8toreg8('e', 'h'), 4, 'ld h, e'),
                0x64: Op(self.ld_reg8toreg8('h', 'h'), 4, 'ld h, h'),
                0x65: Op(self.ld_reg8toreg8('l', 'h'), 4, 'ld h, l'),
                0x66: Op(self.ld_reg16addrtoreg8('hl', 'h'), 8, 'ld h, (hl)'),
                0x67: Op(self.ld_reg8toreg8('a', 'h'), 4, 'ld h, a'),
                0x68: Op(self.ld_reg8toreg8('b', 'l'), 4, 'ld l, b'),
                0x69: Op(self.ld_reg8toreg8('c', 'l'), 4, 'ld l, c'),
                0x6a: Op(self.ld_reg8toreg8('d', 'l'), 4, 'ld l, d'),
                0x6b: Op(self.ld_reg8toreg8('e', 'l'), 4, 'ld l, e'),
                0x6c: Op(self.ld_reg8toreg8('h', 'l'), 4, 'ld l, h'),
                0x6d: Op(self.ld_reg8toreg8('l', 'l'), 4, 'ld l, l'),
                0x6e: Op(self.ld_reg16addrtoreg8('hl', 'l'), 8, 'ld l, (hl)'),
                0x6f: Op(self.ld_reg8toreg8('a', 'l'), 4, 'ld l, a'),
                0x70: Op(self.ld_reg8toreg16addr('b', 'hl'), 8, 'ld (hl), b'),
                0x71: Op(self.ld_reg8toreg16addr('c', 'hl'), 8, 'ld (hl), c'),
                0x72: Op(self.ld_reg8toreg16addr('d', 'hl'), 8, 'ld (hl), d'),
                0x73: Op(self.ld_reg8toreg16addr('e', 'hl'), 8, 'ld (hl), e'),
                0x74: Op(self.ld_reg8toreg16addr('h', 'hl'), 8, 'ld (hl), h'),
                0x75: Op(self.ld_reg8toreg16addr('l', 'hl'), 8, 'ld (hl), l'),
                0x77: Op(self.ld_reg8toreg16addr('a', 'hl'), 8, 'ld (hl), a'),
                0x78: Op(self.ld_reg8toreg8('b', 'a'), 4, 'ld a, b'),
                0x79: Op(self.ld_reg8toreg8('c', 'a'), 4, 'ld a, c'),
                0x7a: Op(self.ld_reg8toreg8('d', 'a'), 4, 'ld a, d'),
                0x7b: Op(self.ld_reg8toreg8('e', 'a'), 4, 'ld a, e'),
                0x7c: Op(self.ld_reg8toreg8('h', 'a'), 4, 'ld a, h'),
                0x7d: Op(self.ld_reg8toreg8('l', 'a'), 4, 'ld a, l'),
                0x7e: Op(self.ld_reg16addrtoreg8('hl', 'a'), 8, 'ld a, (hl)'),
                0x7f: Op(self.ld_reg8toreg8('a', 'a'), 4, 'ld a, a'),

                0x02: Op(self.ld_reg8toreg16addr('a', 'bc'), 8, 'ld (bc), a'),
                0x12: Op(self.ld_reg8toreg16addr('a', 'de'), 8, 'ld (de), a'),
                0x22: Op(self.ld_reg8toreg16addr_inc('a', 'hl'), 8, 'ldi (hl), a'),
                0x32: Op(self.ld_reg8toreg16addr_dec('a', 'hl'), 8, 'ldd (hl), a'),

                0x06: Op(self.ld_imm8toreg8('b'), 8, 'ld b, d8'),
                0x16: Op(self.ld_imm8toreg8('d'), 8, 'ld d, d8'),
                0x26: Op(self.ld_imm8toreg8('h'), 8, 'ld h, d8'),
                0x36: Op(self.ld_imm8toaddrHL, 12, 'ld (hl), d8'),

                0x08: Op(self.ld_sptoimm16addr, 8, 'ld (a16), sp'),

                0x0a: Op(self.ld_reg16addrtoreg8('bc', 'a'), 8, 'ld a, (bc)'),
                0x1a: Op(self.ld_reg16addrtoreg8('de', 'a'), 8, 'ld a, (de)'),
                0x2a: Op(self.ld_reg16addrtoreg8('hl', 'a', inc=True), 8, 'ldi a, (hl)'),
                0x3a: Op(self.ld_reg16addrtoreg8('hl', 'a', dec=True), 8, 'ldd a, (hl)'),

                0x0e: Op(self.ld_imm8toreg8('c'), 8, 'ld c, d8'),
                0x1e: Op(self.ld_imm8toreg8('e'), 8, 'ld e, d8'),
                0x2e: Op(self.ld_imm8toreg8('l'), 8, 'ld l, d8'),
                0x3e: Op(self.ld_imm8toreg8('a'), 8, 'ld a, d8'),

                0xe0: Op(self.ldh_regAtoaddr8, 12, 'ldh (d8), a'),
                0xf0: Op(self.ldh_addr8toregA, 12, 'ldh a, (d8)'),
                0xe2: Op(self.ldh_regAtoaddrC, 8, 'ldh (c), a'),
                0xf2: Op(self.ldh_addrCtoregA, 8, 'ldh a, (c)'),

                0xc1: Op(self.pop_reg16('bc'), 16, 'pop bc'),
                0xd1: Op(self.pop_reg16('de'), 16, 'pop de'),
                0xe1: Op(self.pop_reg16('hl'), 16, 'pop hl'),
                0xf1: Op(self.pop_reg16('af'), 16, 'pop af'),

                0xc5: Op(self.push_reg16('bc'), 16, 'push bc'),
                0xd5: Op(self.push_reg16('de'), 16, 'push de'),
                0xe5: Op(self.push_reg16('hl'), 16, 'push hl'),
                0xf5: Op(self.push_reg16('af'), 16, 'push af'),

                0xf8: Op(self.ld_spimm8toregHL, 12, 'ld hl, sp+d8'),

                0xf9: Op(self.ld_reg16toreg16('hl', 'sp'), 8, 'ld sp, hl'),

                0xea: Op(self.ld_reg8toimm16addr('a'), 16, 'ld (a16), a'),
                0xfa: Op(self.ld_imm16addrtoreg8('a'), 16, 'ld a, (a16)'),

                0x01: Op(self.ld_imm16toreg16('bc'), 12, 'ld bc, d16'),
                0x11: Op(self.ld_imm16toreg16('de'), 12, 'ld de, d16'),
                0x21: Op(self.ld_imm16toreg16('hl'), 12, 'ld hl, d16'),
                0x31: Op(self.ld_imm16toreg16('sp'), 12, 'ld sp, d16'),

                # arithmetic and logic

                0x03: Op(self.inc_reg16('bc'), 8, 'inc bc'),
                0x13: Op(self.inc_reg16('de'), 8, 'inc de'),
                0x23: Op(self.inc_reg16('hl'), 8, 'inc hl'),
                0x33: Op(self.inc_reg16('sp'), 8, 'inc sp'),
                0x04: Op(self.inc_reg8('b'), 4, 'inc b'),
                0x14: Op(self.inc_reg8('d'), 4, 'inc d'),
                0x24: Op(self.inc_reg8('h'), 4, 'inc h'),
                0x34: Op(self.inc_addrHL, 12, 'inc (hl)'),
                0x0c: Op(self.inc_reg8('c'), 4, 'inc c'),
                0x1c: Op(self.inc_reg8('e'), 4, 'inc e'),
                0x2c: Op(self.inc_reg8('l'), 4, 'inc l'),
                0x3c: Op(self.inc_reg8('a'), 4, 'inc a'),
                0x05: Op(self.dec_reg8('b'), 4, 'dec b'),
                0x15: Op(self.dec_reg8('d'), 4, 'dec d'),
                0x25: Op(self.dec_reg8('h'), 4, 'dec h'),
                0x35: Op(self.dec_addrHL, 12, 'dec (hl)'),
                0x0d: Op(self.dec_reg8('c'), 4, 'dec c'),
                0x1d: Op(self.dec_reg8('e'), 4, 'dec e'),
                0x2d: Op(self.dec_reg8('l'), 4, 'dec l'),
                0x3d: Op(self.dec_reg8('a'), 4, 'dec a'),
                0x0b: Op(self.dec_reg16('bc'), 8, 'dec bc'),
                0x1b: Op(self.dec_reg16('de'), 8, 'dec de'),
                0x2b: Op(self.dec_reg16('hl'), 8, 'dec hl'),
                0x3b: Op(self.dec_reg16('sp'), 8, 'dec sp'),

                0x80: Op(self.add_reg8toreg8('b', 'a'), 4, 'add a, b'),
                0x81: Op(self.add_reg8toreg8('c', 'a'), 4, 'add a, c'),
                0x82: Op(self.add_reg8toreg8('d', 'a'), 4, 'add a, d'),
                0x83: Op(self.add_reg8toreg8('e', 'a'), 4, 'add a, e'),
                0x84: Op(self.add_reg8toreg8('h', 'a'), 4, 'add a, h'),
                0x85: Op(self.add_reg8toreg8('l', 'a'), 4, 'add a, l'),
                0x86: Op(self.add_reg16addrtoreg8('hl', 'a'), 8, 'add a, (hl)'),
                0x87: Op(self.add_reg8toreg8('a', 'a'), 4, 'add a, a'),
                0x88: Op(self.add_reg8toreg8('b', 'a', carry=True), 4, 'add a, b'),
                0x89: Op(self.add_reg8toreg8('c', 'a', carry=True), 4, 'adc a, c'),
                0x8a: Op(self.add_reg8toreg8('d', 'a', carry=True), 4, 'adc a, d'),
                0x8b: Op(self.add_reg8toreg8('e', 'a', carry=True), 4, 'adc a, e'),
                0x8c: Op(self.add_reg8toreg8('h', 'a', carry=True), 4, 'adc a, h'),
                0x8d: Op(self.add_reg8toreg8('l', 'a', carry=True), 4, 'adc a, l'),
                0x8e: Op(self.add_reg16addrtoreg8('hl', 'a', carry=True), 8, 'adc a, (hl)'),
                0x8f: Op(self.add_reg8toreg8('a', 'a', carry=True), 4, 'adc a, a'),
                0x90: Op(self.sub_reg8fromreg8('b', 'a'), 4, 'sub a, b'),
                0x91: Op(self.sub_reg8fromreg8('c', 'a'), 4, 'sub a, c'),
                0x92: Op(self.sub_reg8fromreg8('d', 'a'), 4, 'sub a, d'),
                0x93: Op(self.sub_reg8fromreg8('e', 'a'), 4, 'sub a, e'),
                0x94: Op(self.sub_reg8fromreg8('h', 'a'), 4, 'sub a, h'),
                0x95: Op(self.sub_reg8fromreg8('l', 'a'), 4, 'sub a, l'),
                0x96: Op(self.sub_reg16addrfromreg8('hl', 'a'), 8, 'sub a, (hl)'),
                0x97: Op(self.sub_reg8fromreg8('a', 'a'), 4, 'sub a, a'),
                0x98: Op(self.sub_reg8fromreg8('b', 'a', carry=True), 4, 'sbc a, b'),
                0x99: Op(self.sub_reg8fromreg8('c', 'a', carry=True), 4, 'sbc a, c'),
                0x9a: Op(self.sub_reg8fromreg8('d', 'a', carry=True), 4, 'sbc a, d'),
                0x9b: Op(self.sub_reg8fromreg8('e', 'a', carry=True), 4, 'sbc a, e'),
                0x9c: Op(self.sub_reg8fromreg8('h', 'a', carry=True), 4, 'sbc a, h'),
                0x9d: Op(self.sub_reg8fromreg8('l', 'a', carry=True), 4, 'sbc a, l'),
                0x9e: Op(self.sub_reg16addrfromreg8('hl', 'a', carry=True), 8, 'sbc a, (hl)'),
                0x9f: Op(self.sub_reg8fromreg8('a', 'a', carry=True), 4, 'sbc a, a'),
                0xa0: Op(self.and_reg8('b'), 4, 'and b'),
                0xa1: Op(self.and_reg8('c'), 4, 'and c'),
                0xa2: Op(self.and_reg8('d'), 4, 'and d'),
                0xa3: Op(self.and_reg8('e'), 4, 'and e'),
                0xa4: Op(self.and_reg8('h'), 4, 'and h'),
                0xa5: Op(self.and_reg8('l'), 4, 'and l'),
                0xa6: Op(self.and_reg16addr('hl'), 8, 'and (hl)'),
                0xa7: Op(self.and_reg8('a'), 4, 'and a'),
                0xa8: Op(self.xor_reg8('b'), 4, 'xor b'),
                0xa9: Op(self.xor_reg8('c'), 4, 'xor c'),
                0xaa: Op(self.xor_reg8('d'), 4, 'xor d'),
                0xab: Op(self.xor_reg8('e'), 4, 'xor e'),
                0xac: Op(self.xor_reg8('h'), 4, 'xor h'),
                0xad: Op(self.xor_reg8('l'), 4, 'xor l'),
                0xae: Op(self.xor_reg16addr('hl'), 8, 'xor (hl)'),
                0xaf: Op(self.xor_reg8('a'), 4, 'xor a'),
                0xb0: Op(self.or_reg8('b'), 4, 'or b'),
                0xb1: Op(self.or_reg8('c'), 4, 'or c'),
                0xb2: Op(self.or_reg8('d'), 4, 'or d'),
                0xb3: Op(self.or_reg8('e'), 4, 'or e'),
                0xb4: Op(self.or_reg8('h'), 4, 'or h'),
                0xb5: Op(self.or_reg8('l'), 4, 'or l'),
                0xb6: Op(self.or_reg16addr('hl'), 8, 'or (hl)'),
                0xb7: Op(self.or_reg8('a'), 4, 'or a'),
                0xb8: Op(self.cp_reg8toreg8('a', 'b'), 4, 'cp b'),
                0xb9: Op(self.cp_reg8toreg8('a', 'c'), 4, 'cp c'),
                0xba: Op(self.cp_reg8toreg8('a', 'd'), 4, 'cp d'),
                0xbb: Op(self.cp_reg8toreg8('a', 'e'), 4, 'cp e'),
                0xbc: Op(self.cp_reg8toreg8('a', 'h'), 4, 'cp h'),
                0xbd: Op(self.cp_reg8toreg8('a', 'l'), 4, 'cp l'),
                0xbe: Op(self.cp_regAtoregHLaddr, 8, 'cp (hl)'),
                0xbf: Op(self.cp_reg8toreg8('a', 'a'), 4, 'cp a'),
                0xc6: Op(self.add_imm8toreg8('a'), 8, 'add a, d8'),
                0xd6: Op(self.sub_imm8fromreg8('a'), 8, 'sub a, d8'),
                0xe6: Op(self.and_imm8(), 8, 'and a, d8'),
                0xf6: Op(self.or_imm8(), 8, 'or a, d8'),

                0xce: Op(self.add_imm8toreg8('a', carry=True), 8, 'adc a, d8'),
                0xde: Op(self.sub_imm8fromreg8('a', carry=True), 8, 'sbc a, d8'),
                0xee: Op(self.xor_imm8(), 8, 'xor d8'),
                0xfe: Op(self.cp_imm8toregA, 8, 'cp d8'),

                0xe8: Op(self.add_imm8toregSP, 16, 'add sp, d8'),

                0x09: Op(self.add_reg16toregHL('bc'), 8, 'add hl, bc'),
                0x19: Op(self.add_reg16toregHL('de'), 8, 'add hl, de'),
                0x29: Op(self.add_reg16toregHL('hl'), 8, 'add hl, hl'),
                0x39: Op(self.add_reg16toregHL('sp'), 8, 'add hl, sp'),

                0x07: Op(self.rlc_reg8('a'), 4, 'rlca'),
                0x17: Op(self.rl_reg8('a'), 4, 'rla'),
                0x27: Op(self.daa, 4, 'daa'),
                0x37: Op(self.scf, 4, 'scf'),

                0x0f: Op(self.rrc_reg8('a'), 4, 'rrca'),
                0x1f: Op(self.rr_reg8('a'), 4, 'rra'),
                0x2f: Op(self.cpl, 4, 'cpl'),
                0x3f: Op(self.ccf, 4, 'ccl'),

                0xc7: Op(self.rst(0x00), 4, 'rst 0x00'),
                0xd7: Op(self.rst(0x10), 4, 'rst 0x10'),
                0xe7: Op(self.rst(0x20), 4, 'rst 0x20'),
                0xf7: Op(self.rst(0x30), 4, 'rst 0x30'),
                0xcf: Op(self.rst(0x08), 4, 'rst 0x08'),
                0xdf: Op(self.rst(0x18), 4, 'rst 0x18'),
                0xef: Op(self.rst(0x28), 4, 'rst 0x28'),
                0xff: Op(self.rst(0x38), 4, 'rst 0x38'),

                # JP instructions take 16 cycles when taken, 12 when not taken
                0xc3: Op(self.jp_imm16addr(), 16, 'jp a16'),
                0xc2: Op(self.jp_imm16addr('nz'), 16, 'jp nz, a16'),
                0xd2: Op(self.jp_imm16addr('nc'), 16, 'jp nc, a16'),
                0xca: Op(self.jp_imm16addr('z'), 16, 'jp z, a16'),
                0xda: Op(self.jp_imm16addr('c'), 16, 'jp c, a16'),
                0xe9: Op(self.jp_reg16addr('hl'), 4, 'jp hl'),

                # JR instructions take 12 cycles when taken, 8 when not taken
                0x18: Op(self.jr_imm8(), 12, 'jr d8'),
                0x20: Op(self.jr_imm8('nz'), 12, 'jr nz, d8'),
                0x30: Op(self.jr_imm8('nc'), 12, 'jr nc, d8'),
                0x28: Op(self.jr_imm8('z'), 12, 'jr z, d8'),
                0x38: Op(self.jr_imm8('c'), 12, 'jr c, d8'),

                # CALL takes 24 cycles when taken, 12 when not taken
                0xcd: Op(self.call_imm16addr(), 24, 'call a16'),
                0xc4: Op(self.call_imm16addr('nz'), 24, 'call nz, a16'),
                0xd4: Op(self.call_imm16addr('nc'), 24, 'call nc, a16'),
                0xcc: Op(self.call_imm16addr('z'), 24, 'call z, a16'),
                0xdc: Op(self.call_imm16addr('c'), 24, 'call c, a16'),

                # RET takes 20 cycles when taken, 8 when not taken
                0xc9: Op(self.ret(), 20, 'ret'),
                0xd9: Op(self.reti, 20, 'reti'),
                0xc0: Op(self.ret('nz'), 20, 'ret nz'),
                0xd0: Op(self.ret('nc'), 20, 'ret nc'),
                0xc8: Op(self.ret('z'), 20, 'ret z'),
                0xd8: Op(self.ret('c'), 20, 'ret c'),
                }

        self.cb_opcode_map = {
            0x00: Op(self.rlc_reg8('b'), 8, 'rlc b'),
            0x01: Op(self.rlc_reg8('c'), 8, 'rlc c'),
            0x02: Op(self.rlc_reg8('d'), 8, 'rlc d'),
            0x03: Op(self.rlc_reg8('e'), 8, 'rlc e'),
            0x04: Op(self.rlc_reg8('h'), 8, 'rlc h'),
            0x05: Op(self.rlc_reg8('l'), 8, 'rlc l'),
            0x06: Op(self.rlc_regHLaddr, 16, 'rlc (hl)'),
            0x07: Op(self.rlc_reg8('a'), 8, 'rlc a'),

            0x08: Op(self.rrc_reg8('b'), 8, 'rrc b'),
            0x09: Op(self.rrc_reg8('c'), 8, 'rrc c'),
            0x0a: Op(self.rrc_reg8('d'), 8, 'rrc d'),
            0x0b: Op(self.rrc_reg8('e'), 8, 'rrc e'),
            0x0c: Op(self.rrc_reg8('h'), 8, 'rrc h'),
            0x0d: Op(self.rrc_reg8('l'), 8, 'rrc l'),
            0x0e: Op(self.rrc_regHLaddr, 16, 'rrc (hl)'),
            0x0f: Op(self.rrc_reg8('a'), 8, 'rrc a'),

            0x10: Op(self.rl_reg8('b'), 8, 'rl b'),
            0x11: Op(self.rl_reg8('c'), 8, 'rl c'),
            0x12: Op(self.rl_reg8('d'), 8, 'rl d'),
            0x13: Op(self.rl_reg8('e'), 8, 'rl e'),
            0x14: Op(self.rl_reg8('h'), 8, 'rl h'),
            0x15: Op(self.rl_reg8('l'), 8, 'rl l'),
            0x16: Op(self.rl_regHLaddr, 16, 'rl (hl)'),
            0x17: Op(self.rl_reg8('a'), 8, 'rl a'),

            0x18: Op(self.rr_reg8('b'), 8, 'rr b'),
            0x19: Op(self.rr_reg8('c'), 8, 'rr c'),
            0x1a: Op(self.rr_reg8('d'), 8, 'rr d'),
            0x1b: Op(self.rr_reg8('e'), 8, 'rr e'),
            0x1c: Op(self.rr_reg8('h'), 8, 'rr h'),
            0x1d: Op(self.rr_reg8('l'), 8, 'rr l'),
            0x1e: Op(self.rr_regHLaddr, 16, 'rr (hl)'),
            0x1f: Op(self.rr_reg8('a'), 8, 'rr a'),

            0x20: Op(self.sla_reg8('b'), 8, 'sla b'),
            0x21: Op(self.sla_reg8('c'), 8, 'sla c'),
            0x22: Op(self.sla_reg8('d'), 8, 'sla d'),
            0x23: Op(self.sla_reg8('e'), 8, 'sla e'),
            0x24: Op(self.sla_reg8('h'), 8, 'sla h'),
            0x25: Op(self.sla_reg8('l'), 8, 'sla l'),
            0x26: Op(self.sla_regHLaddr, 16, 'sla (hl)'),
            0x27: Op(self.sla_reg8('a'), 8, 'sla a'),

            0x28: Op(self.sra_reg8('b'), 8, 'sra b'),
            0x29: Op(self.sra_reg8('c'), 8, 'sra c'),
            0x2a: Op(self.sra_reg8('d'), 8, 'sra d'),
            0x2b: Op(self.sra_reg8('e'), 8, 'sra e'),
            0x2c: Op(self.sra_reg8('h'), 8, 'sra h'),
            0x2d: Op(self.sra_reg8('l'), 8, 'sra l'),
            0x2e: Op(self.sra_regHLaddr, 16, 'sra (hl)'),
            0x2f: Op(self.sra_reg8('a'), 8, 'sra a'),

            0x30: Op(self.swap_reg8('b'), 8, 'swap b'),
            0x31: Op(self.swap_reg8('c'), 8, 'swap c'),
            0x32: Op(self.swap_reg8('d'), 8, 'swap d'),
            0x33: Op(self.swap_reg8('e'), 8, 'swap e'),
            0x34: Op(self.swap_reg8('h'), 8, 'swap h'),
            0x35: Op(self.swap_reg8('l'), 8, 'swap l'),
            0x36: Op(self.swap_regHLaddr, 16, 'swap (hl)'),
            0x37: Op(self.swap_reg8('a'), 8, 'swap a'),

            0x38: Op(self.srl_reg8('b'), 8, 'srl b'),
            0x39: Op(self.srl_reg8('c'), 8, 'srl c'),
            0x3a: Op(self.srl_reg8('d'), 8, 'srl d'),
            0x3b: Op(self.srl_reg8('e'), 8, 'srl e'),
            0x3c: Op(self.srl_reg8('h'), 8, 'srl h'),
            0x3d: Op(self.srl_reg8('l'), 8, 'srl l'),
            0x3e: Op(self.srl_regHLaddr, 16, 'srl (hl)'),
            0x3f: Op(self.srl_reg8('a'), 8, 'srl a'),

            0x40: Op(self.bit_reg8(0, 'b'), 8, 'bit 0, b'),
            0x41: Op(self.bit_reg8(0, 'c'), 8, 'bit 0, c'),
            0x42: Op(self.bit_reg8(0, 'd'), 8, 'bit 0, d'),
            0x43: Op(self.bit_reg8(0, 'e'), 8, 'bit 0, e'),
            0x44: Op(self.bit_reg8(0, 'h'), 8, 'bit 0, h'),
            0x45: Op(self.bit_reg8(0, 'l'), 8, 'bit 0, l'),
            0x46: Op(self.bit_regHLaddr(0), 16, 'bit 0, (hl)'),
            0x47: Op(self.bit_reg8(0, 'a'), 8, 'bit 0, a'),

            0x48: Op(self.bit_reg8(1, 'b'), 8, 'bit 1, b'),
            0x49: Op(self.bit_reg8(1, 'c'), 8, 'bit 1, c'),
            0x4a: Op(self.bit_reg8(1, 'd'), 8, 'bit 1, d'),
            0x4b: Op(self.bit_reg8(1, 'e'), 8, 'bit 1, e'),
            0x4c: Op(self.bit_reg8(1, 'h'), 8, 'bit 1, h'),
            0x4d: Op(self.bit_reg8(1, 'l'), 8, 'bit 1, l'),
            0x4e: Op(self.bit_regHLaddr(1), 16, 'bit 1, (hl)'),
            0x4f: Op(self.bit_reg8(1, 'a'), 8, 'bit 1, a'),

            0x50: Op(self.bit_reg8(2, 'b'), 8, 'bit 2, b'),
            0x51: Op(self.bit_reg8(2, 'c'), 8, 'bit 2, c'),
            0x52: Op(self.bit_reg8(2, 'd'), 8, 'bit 2, d'),
            0x53: Op(self.bit_reg8(2, 'e'), 8, 'bit 2, e'),
            0x54: Op(self.bit_reg8(2, 'h'), 8, 'bit 2, h'),
            0x55: Op(self.bit_reg8(2, 'l'), 8, 'bit 2, l'),
            0x56: Op(self.bit_regHLaddr(2), 16, 'bit 2, (hl)'),
            0x57: Op(self.bit_reg8(2, 'a'), 8, 'bit 2, a'),

            0x58: Op(self.bit_reg8(3, 'b'), 8, 'bit 3, b'),
            0x59: Op(self.bit_reg8(3, 'c'), 8, 'bit 3, c'),
            0x5a: Op(self.bit_reg8(3, 'd'), 8, 'bit 3, d'),
            0x5b: Op(self.bit_reg8(3, 'e'), 8, 'bit 3, e'),
            0x5c: Op(self.bit_reg8(3, 'h'), 8, 'bit 3, h'),
            0x5d: Op(self.bit_reg8(3, 'l'), 8, 'bit 3, l'),
            0x5e: Op(self.bit_regHLaddr(3), 16, 'bit 3, (hl)'),
            0x5f: Op(self.bit_reg8(3, 'a'), 8, 'bit 3, a'),

            0x60: Op(self.bit_reg8(4, 'b'), 8, 'bit 4, b'),
            0x61: Op(self.bit_reg8(4, 'c'), 8, 'bit 4, c'),
            0x62: Op(self.bit_reg8(4, 'd'), 8, 'bit 4, d'),
            0x63: Op(self.bit_reg8(4, 'e'), 8, 'bit 4, e'),
            0x64: Op(self.bit_reg8(4, 'h'), 8, 'bit 4, h'),
            0x65: Op(self.bit_reg8(4, 'l'), 8, 'bit 4, l'),
            0x66: Op(self.bit_regHLaddr(4), 16, 'bit 4, (hl)'),
            0x67: Op(self.bit_reg8(4, 'a'), 8, 'bit 4, a'),

            0x68: Op(self.bit_reg8(5, 'b'), 8, 'bit 5, b'),
            0x69: Op(self.bit_reg8(5, 'c'), 8, 'bit 5, c'),
            0x6a: Op(self.bit_reg8(5, 'd'), 8, 'bit 5, d'),
            0x6b: Op(self.bit_reg8(5, 'e'), 8, 'bit 5, e'),
            0x6c: Op(self.bit_reg8(5, 'h'), 8, 'bit 5, h'),
            0x6d: Op(self.bit_reg8(5, 'l'), 8, 'bit 5, l'),
            0x6e: Op(self.bit_regHLaddr(5), 16, 'bit 5, (hl)'),
            0x6f: Op(self.bit_reg8(5, 'a'), 8, 'bit 5, a'),

            0x70: Op(self.bit_reg8(6, 'b'), 8, 'bit 6, b'),
            0x71: Op(self.bit_reg8(6, 'c'), 8, 'bit 6, c'),
            0x72: Op(self.bit_reg8(6, 'd'), 8, 'bit 6, d'),
            0x73: Op(self.bit_reg8(6, 'e'), 8, 'bit 6, e'),
            0x74: Op(self.bit_reg8(6, 'h'), 8, 'bit 6, h'),
            0x75: Op(self.bit_reg8(6, 'l'), 8, 'bit 6, l'),
            0x76: Op(self.bit_regHLaddr(6), 16, 'bit 6, (hl)'),
            0x77: Op(self.bit_reg8(6, 'a'), 8, 'bit 6, a'),

            0x78: Op(self.bit_reg8(7, 'b'), 8, 'bit 7, b'),
            0x79: Op(self.bit_reg8(7, 'c'), 8, 'bit 7, c'),
            0x7a: Op(self.bit_reg8(7, 'd'), 8, 'bit 7, d'),
            0x7b: Op(self.bit_reg8(7, 'e'), 8, 'bit 7, e'),
            0x7c: Op(self.bit_reg8(7, 'h'), 8, 'bit 7, h'),
            0x7d: Op(self.bit_reg8(7, 'l'), 8, 'bit 7, l'),
            0x7e: Op(self.bit_regHLaddr(7), 16, 'bit 7, (hl)'),
            0x7f: Op(self.bit_reg8(7, 'a'), 8, 'bit 7, a'),

            0x80: Op(self.res_reg8(0, 'b'), 8, 'res 0, b'),
            0x81: Op(self.res_reg8(0, 'c'), 8, 'res 0, c'),
            0x82: Op(self.res_reg8(0, 'd'), 8, 'res 0, d'),
            0x83: Op(self.res_reg8(0, 'e'), 8, 'res 0, e'),
            0x84: Op(self.res_reg8(0, 'h'), 8, 'res 0, h'),
            0x85: Op(self.res_reg8(0, 'l'), 8, 'res 0, l'),
            0x86: Op(self.res_regHLaddr(0), 16, 'res 0, (hl)'),
            0x87: Op(self.res_reg8(0, 'a'), 8, 'res 0, a'),

            0x88: Op(self.res_reg8(1, 'b'), 8, 'res 1, b'),
            0x89: Op(self.res_reg8(1, 'c'), 8, 'res 1, c'),
            0x8a: Op(self.res_reg8(1, 'd'), 8, 'res 1, d'),
            0x8b: Op(self.res_reg8(1, 'e'), 8, 'res 1, e'),
            0x8c: Op(self.res_reg8(1, 'h'), 8, 'res 1, h'),
            0x8d: Op(self.res_reg8(1, 'l'), 8, 'res 1, l'),
            0x8e: Op(self.res_regHLaddr(1), 16, 'res 1, (hl)'),
            0x8f: Op(self.res_reg8(1, 'a'), 8, 'res 1, a'),

            0x90: Op(self.res_reg8(2, 'b'), 8, 'res 2, b'),
            0x91: Op(self.res_reg8(2, 'c'), 8, 'res 2, c'),
            0x92: Op(self.res_reg8(2, 'd'), 8, 'res 2, d'),
            0x93: Op(self.res_reg8(2, 'e'), 8, 'res 2, e'),
            0x94: Op(self.res_reg8(2, 'h'), 8, 'res 2, h'),
            0x95: Op(self.res_reg8(2, 'l'), 8, 'res 2, l'),
            0x96: Op(self.res_regHLaddr(2), 16, 'res 2, (hl)'),
            0x97: Op(self.res_reg8(2, 'a'), 8, 'res 2, a'),

            0x98: Op(self.res_reg8(3, 'b'), 8, 'res 3, b'),
            0x99: Op(self.res_reg8(3, 'c'), 8, 'res 3, c'),
            0x9a: Op(self.res_reg8(3, 'd'), 8, 'res 3, d'),
            0x9b: Op(self.res_reg8(3, 'e'), 8, 'res 3, e'),
            0x9c: Op(self.res_reg8(3, 'h'), 8, 'res 3, h'),
            0x9d: Op(self.res_reg8(3, 'l'), 8, 'res 3, l'),
            0x9e: Op(self.res_regHLaddr(3), 16, 'res 3, (hl)'),
            0x9f: Op(self.res_reg8(3, 'a'), 8, 'res 3, a'),

            0xa0: Op(self.res_reg8(4, 'b'), 8, 'res 4, b'),
            0xa1: Op(self.res_reg8(4, 'c'), 8, 'res 4, c'),
            0xa2: Op(self.res_reg8(4, 'd'), 8, 'res 4, d'),
            0xa3: Op(self.res_reg8(4, 'e'), 8, 'res 4, e'),
            0xa4: Op(self.res_reg8(4, 'h'), 8, 'res 4, h'),
            0xa5: Op(self.res_reg8(4, 'l'), 8, 'res 4, l'),
            0xa6: Op(self.res_regHLaddr(4), 16, 'res 4, (hl)'),
            0xa7: Op(self.res_reg8(4, 'a'), 8, 'res 4, a'),

            0xa8: Op(self.res_reg8(5, 'b'), 8, 'res 5, b'),
            0xa9: Op(self.res_reg8(5, 'c'), 8, 'res 5, c'),
            0xaa: Op(self.res_reg8(5, 'd'), 8, 'res 5, d'),
            0xab: Op(self.res_reg8(5, 'e'), 8, 'res 5, e'),
            0xac: Op(self.res_reg8(5, 'h'), 8, 'res 5, h'),
            0xad: Op(self.res_reg8(5, 'l'), 8, 'res 5, l'),
            0xae: Op(self.res_regHLaddr(5), 16, 'res 5, (hl)'),
            0xaf: Op(self.res_reg8(5, 'a'), 8, 'res 5, a'),

            0xb0: Op(self.res_reg8(6, 'b'), 8, 'res 6, b'),
            0xb1: Op(self.res_reg8(6, 'c'), 8, 'res 6, c'),
            0xb2: Op(self.res_reg8(6, 'd'), 8, 'res 6, d'),
            0xb3: Op(self.res_reg8(6, 'e'), 8, 'res 6, e'),
            0xb4: Op(self.res_reg8(6, 'h'), 8, 'res 6, h'),
            0xb5: Op(self.res_reg8(6, 'l'), 8, 'res 6, l'),
            0xb6: Op(self.res_regHLaddr(6), 16, 'res 6, (hl)'),
            0xb7: Op(self.res_reg8(6, 'a'), 8, 'res 6, a'),

            0xb8: Op(self.res_reg8(7, 'b'), 8, 'res 7, b'),
            0xb9: Op(self.res_reg8(7, 'c'), 8, 'res 7, c'),
            0xba: Op(self.res_reg8(7, 'd'), 8, 'res 7, d'),
            0xbb: Op(self.res_reg8(7, 'e'), 8, 'res 7, e'),
            0xbc: Op(self.res_reg8(7, 'h'), 8, 'res 7, h'),
            0xbd: Op(self.res_reg8(7, 'l'), 8, 'res 7, l'),
            0xbe: Op(self.res_regHLaddr(7), 16, 'res 7, (hl)'),
            0xbf: Op(self.res_reg8(7, 'a'), 8, 'res 7, a'),

            0xc0: Op(self.set__reg8(0, 'b'), 8, 'set 0, b'),
            0xc1: Op(self.set__reg8(0, 'c'), 8, 'set 0, c'),
            0xc2: Op(self.set__reg8(0, 'd'), 8, 'set 0, d'),
            0xc3: Op(self.set__reg8(0, 'e'), 8, 'set 0, e'),
            0xc4: Op(self.set__reg8(0, 'h'), 8, 'set 0, h'),
            0xc5: Op(self.set__reg8(0, 'l'), 8, 'set 0, l'),
            0xc6: Op(self.set_regHLaddr(0), 16, 'set 0, (hl)'),
            0xc7: Op(self.set__reg8(0, 'a'), 8, 'set 0, a'),

            0xc8: Op(self.set__reg8(1, 'b'), 8, 'set 1, b'),
            0xc9: Op(self.set__reg8(1, 'c'), 8, 'set 1, c'),
            0xca: Op(self.set__reg8(1, 'd'), 8, 'set 1, d'),
            0xcb: Op(self.set__reg8(1, 'e'), 8, 'set 1, e'),
            0xcc: Op(self.set__reg8(1, 'h'), 8, 'set 1, h'),
            0xcd: Op(self.set__reg8(1, 'l'), 8, 'set 1, l'),
            0xce: Op(self.set_regHLaddr(1), 16, 'set 1, (hl)'),
            0xcf: Op(self.set__reg8(1, 'a'), 8, 'set 1, a'),

            0xd0: Op(self.set__reg8(2, 'b'), 8, 'set 2, b'),
            0xd1: Op(self.set__reg8(2, 'c'), 8, 'set 2, c'),
            0xd2: Op(self.set__reg8(2, 'd'), 8, 'set 2, d'),
            0xd3: Op(self.set__reg8(2, 'e'), 8, 'set 2, e'),
            0xd4: Op(self.set__reg8(2, 'h'), 8, 'set 2, h'),
            0xd5: Op(self.set__reg8(2, 'l'), 8, 'set 2, l'),
            0xd6: Op(self.set_regHLaddr(2), 16, 'set 2, (hl)'),
            0xd7: Op(self.set__reg8(2, 'a'), 8, 'set 2, a'),

            0xd8: Op(self.set__reg8(3, 'b'), 8, 'set 3, b'),
            0xd9: Op(self.set__reg8(3, 'c'), 8, 'set 3, c'),
            0xda: Op(self.set__reg8(3, 'd'), 8, 'set 3, d'),
            0xdb: Op(self.set__reg8(3, 'e'), 8, 'set 3, e'),
            0xdc: Op(self.set__reg8(3, 'h'), 8, 'set 3, h'),
            0xdd: Op(self.set__reg8(3, 'l'), 8, 'set 3, l'),
            0xde: Op(self.set_regHLaddr(3), 16, 'set 3, (hl)'),
            0xdf: Op(self.set__reg8(3, 'a'), 8, 'set 3, a'),

            0xe0: Op(self.set__reg8(4, 'b'), 8, 'set 4, b'),
            0xe1: Op(self.set__reg8(4, 'c'), 8, 'set 4, c'),
            0xe2: Op(self.set__reg8(4, 'd'), 8, 'set 4, d'),
            0xe3: Op(self.set__reg8(4, 'e'), 8, 'set 4, e'),
            0xe4: Op(self.set__reg8(4, 'h'), 8, 'set 4, h'),
            0xe5: Op(self.set__reg8(4, 'l'), 8, 'set 4, l'),
            0xe6: Op(self.set_regHLaddr(4), 16, 'set 4, (hl)'),
            0xe7: Op(self.set__reg8(4, 'a'), 8, 'set 4, a'),

            0xe8: Op(self.set__reg8(5, 'b'), 8, 'set 5, b'),
            0xe9: Op(self.set__reg8(5, 'c'), 8, 'set 5, c'),
            0xea: Op(self.set__reg8(5, 'd'), 8, 'set 5, d'),
            0xeb: Op(self.set__reg8(5, 'e'), 8, 'set 5, e'),
            0xec: Op(self.set__reg8(5, 'h'), 8, 'set 5, h'),
            0xed: Op(self.set__reg8(5, 'l'), 8, 'set 5, l'),
            0xee: Op(self.set_regHLaddr(5), 16, 'set 5, (hl)'),
            0xef: Op(self.set__reg8(5, 'a'), 8, 'set 5, a'),

            0xf0: Op(self.set__reg8(6, 'b'), 8, 'set 6, b'),
            0xf1: Op(self.set__reg8(6, 'c'), 8, 'set 6, c'),
            0xf2: Op(self.set__reg8(6, 'd'), 8, 'set 6, d'),
            0xf3: Op(self.set__reg8(6, 'e'), 8, 'set 6, e'),
            0xf4: Op(self.set__reg8(6, 'h'), 8, 'set 6, h'),
            0xf5: Op(self.set__reg8(6, 'l'), 8, 'set 6, l'),
            0xf6: Op(self.set_regHLaddr(6), 16, 'set 6, (hl)'),
            0xf7: Op(self.set__reg8(6, 'a'), 8, 'set 6, a'),

            0xf8: Op(self.set__reg8(7, 'b'), 8, 'set 7, b'),
            0xf9: Op(self.set__reg8(7, 'c'), 8, 'set 7, c'),
            0xfa: Op(self.set__reg8(7, 'd'), 8, 'set 7, d'),
            0xfb: Op(self.set__reg8(7, 'e'), 8, 'set 7, e'),
            0xfc: Op(self.set__reg8(7, 'h'), 8, 'set 7, h'),
            0xfd: Op(self.set__reg8(7, 'l'), 8, 'set 7, l'),
            0xfe: Op(self.set_regHLaddr(7), 16, 'set 7, (hl)'),
            0xff: Op(self.set__reg8(7, 'a'), 8, 'set 7, a'),
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

    def filter(self, record):
        record.msg = 'PC={:#04x}: {}'.format(self.pc, record.msg)
        return True

    def log_regs(self, log=None):
        if log is None:
            log = self.logger.debug

        log('af=%#06x', self.get_reg16('af'))
        log('bc=%#06x', self.get_reg16('bc'))
        log('de=%#06x', self.get_reg16('de'))
        log('hl=%#06x', self.get_reg16('hl'))
        log('pc=%#06x', self.pc)
        log('sp=%#06x ', self.sp)

    def log_op(self, log=None):
        if log is None:
            log = self.logger.debug
        log('pc=%#06x (%#04x:%s)', self.op_pc, self.opcode, self.op.description)

    def register_clock_listener(self, listener):
        if not isinstance(listener, ClockListener):
            raise TypeError('listener must implement ClockListener')
        self.clock_listeners.append(listener)

    def set_message_queues(self, cmd_q, resp_q):
        self.cmd_q = cmd_q
        self.resp_q = resp_q

    def get_message_queues(self):
        return self.cmd_q, self.resp_q

    # Debug hooks
    def set_breakpoint(self, addr):
        self.breakpoints.append(addr)

    def remove_breakpoint(self, addr):
        self.breakpoints.remove(addr)

    def get_registers(self):
        return self.registers

    def get_register(self, register):
        if len(register) == 1:
            return self.get_reg8(register)
        elif len(register) == 2:
            return self.get_reg16(register)

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
        if reg16 == 'sp':
            self.sp = value & 0xffff
        elif reg16 == 'af':
            hi = (value >> 8) & 0xff
            self.registers['a'] = hi
        else:
            hi = (value >> 8) & 0xff
            lo = value & 0xff
            self.registers[reg16[0]] = hi
            self.registers[reg16[1]] = lo

    def get_reg16(self, reg16):
        reg16 = reg16.lower()
        if reg16 == 'sp':
            return self.sp
        elif reg16 == 'pc':
            return self.pc
        else:
            hi = self.registers[reg16[0]]
            lo = self.registers[reg16[1]]
            return (hi << 8) | lo

    def read_register(self, reg):
        if len(reg) == 1:
            return self.get_reg8(reg)
        elif len(reg) == 2:
            return self.get_reg16(reg)
        else:
            raise ValueError('Unrecognized register')

    @property
    def sp(self):
        return self._sp

    @sp.setter
    def sp(self, u16):
        self._sp = u16 & 0xffff
        # self.logger.debug('Set SP=%#x', self._sp)

    def inc_sp(self):
        self.sp = (self.sp + 1) & 0xffff

    @property
    def pc(self):
        return self._pc

    @pc.setter
    def pc(self, value):
        self._opcode_ring.append((self._pc, value))
        value = value & 0xffff
        # Specific to AntHill
        #if value > 0x6438 and value < 0x8000:
        #    raise ValueError('Invalid jump from {:x} to {:x}'.format(self._pc, value))
        #print('PC', hex(value))
        self._pc = value

    def inc_pc(self):
        self.pc = self.pc + 1

    def get_pc(self):
        return self.pc

    def set_zero_flag(self):
        self.registers['f'] |= Z_FLAG_MASK

    def reset_zero_flag(self):
        self.registers['f'] &= ~Z_FLAG_MASK

    def get_zero_flag(self):
        return (self.get_reg8('f') >> Z_FLAG_OFFSET) & 1

    def set_sub_flag(self):
        self.registers['f'] |= N_FLAG_MASK

    def reset_sub_flag(self):
        self.registers['f'] &= ~N_FLAG_MASK

    def get_sub_flag(self):
        return (self.get_reg8('f') >> N_FLAG_OFFSET) & 1

    def set_halfcarry_flag(self):
        self.registers['f'] |= HC_FLAG_MASK

    def reset_halfcarry_flag(self):
        self.registers['f'] &= ~HC_FLAG_MASK

    def get_halfcarry_flag(self):
        return (self.registers['f'] >> HC_FLAG_OFFSET) & 1

    def set_carry_flag(self):
        self.registers['f'] |= C_FLAG_MASK

    def reset_carry_flag(self):
        self.registers['f'] &= ~C_FLAG_MASK

    def get_carry_flag(self):
        return (self.registers['f'] >> C_FLAG_OFFSET) & 1

    def fetch(self):
        """Fetch a byte, incrementing the PC as needed."""

        value = self.mmu.get_addr(self.pc)
        self.inc_pc()
        return value

    def fetch2(self):
        """Fetch 2 bytes, incrementing the PC as needed."""

        value = self.fetch()
        value |= self.fetch() << 8
        return value

    def send_command(self, cmd):
        self.cmd_q.append(cmd)

    # def handle_command(self):
    #     if cmd.code == ShutdownCommand.code:
    #         self.state = State.HALT
    #     elif cmd.code == StepCommand.code:
    #         self._step = True
    #     elif cmd.code == ContinueCommand.code:
    #         self.trace = False
    #     elif cmd.code == SetBreakpointCommand.code:
    #         self.set_breakpoint(cmd.address)
    #     elif cmd.code == ReadRegisterCommand.code:
    #         reg = ReadRegisterCommand.decode_register(cmd.register)
    #         value = self.read_register(reg)
    #         self.resp_q.append(ReadRegisterResponse(reg, value))
    #     elif cmd.code == ReadMemoryCommand.code:
    #         addr = cmd.address
    #         length = cmd.length
    #         values = bytes([self.mmu.get_addr(a) for a in range(addr, addr+length)])
    #         self.resp_q.append(ReadMemoryResponse(addr, values))
    #     else:
    #         raise UnrecognizedCommandException()

    def go(self):
        self.state = State.RUN
        while self.state != State.STOP:
            # self.step()

            if self.trace and not self.step:
                sleep(0.5)
                continue

            if self.state != State.RUN:
                if self.interrupt_controller.has_interrupt:
                    self.state = State.RUN
                elif not self.trace:
                    continue

            # for cmd in self.cmd_q:
            #     self.handle_command(cmd)
            #     print('resp_q: {}'.format(self.resp_q))

            # Only handle one interrupt at a time
            if not self._in_interrupt and self.interrupt_controller.has_interrupt:
                interrupt = self.interrupt_controller.get_interrupt()
                # self._saved_pc = self.pc
                pc = self.pc
                hi = (pc >> 8) & 0xff
                lo = pc & 0xff
                self.mmu.set_addr(self.sp-1, hi)
                self.mmu.set_addr(self.sp-2, lo)
                self.sp -= 2
                self._in_interrupt = True
                self.pc = 0x0040 + interrupt.value*8
                self.interrupt_controller.acknowledge_interrupt(interrupt)

            # fetch
            self.op_pc = self.pc
            # opcode = self.fetch()
            opcode = self.mmu.get_addr(self.pc)
            self.pc += 1
            self.opcode = opcode

            # decode
            if opcode == 0xcb:
                # cb_opcode = self.fetch()
                cb_opcode = self.mmu.get_addr(self.pc)
                self.pc += 1
                self.cb_opcode = cb_opcode
                op = self.cb_opcode_map[cb_opcode]
            else:
                op = self.opcode_map[opcode]
            self.op = op

            if self.trace:
                self.log_regs()
                self.log_op()

            # execute
            try:
                op.function()
            except:
                self.log_regs(self.logger.error)
                self.log_op(self.logger.error)
                raise

            self.clock += op.cycles

            for listener in self.clock_listeners:
                listener.notify(self.clock, op.cycles)

            self.step = False

        print('Emulator shutdown')

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
            self.set_reg8(reg8, imm8)
        return ld

    def ld_reg8toreg8(self, src_reg8, dest_reg8):
        """Returns a function to load :py:data:src_reg8 into :py:data:dest_reg8.

        :param src_reg8: single byte source register
        :param dest_reg8: single byte destination register
        :rtype: None → None """

        def ld():
            self.set_reg8(dest_reg8, self.get_reg8(src_reg8))
        return ld

    def ld_imm16toreg16(self, reg16):
        """Returns a function to load a 16-bit immediate into :py:data:reg16.

        :param reg16: two-byte register
        :rtype: integer → None """

        def ld():
            imm16 = self.fetch2()
            self.set_reg16(reg16, imm16)
        return ld

    def ld_reg8toreg16addr(self, reg8, reg16):
        """Returns a function to load an 8-bit register value into an address
        given by a 16-bit double register.

        :param reg8: single byte source register
        :param reg16: two-byte register containing destination address
        :rtype: None → None"""

        def ld():
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
            addr = self.get_reg16(reg16)
            self.mmu.set_addr(addr, self.get_reg8(reg8))
            self.set_reg16(reg16, addr + 0xffff)
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
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 + 1)
        elif dec:
            def ld():
                u16 = self.get_reg16(reg16)
                self.set_reg8(reg8, self.mmu.get_addr(u16))
                self.set_reg16(reg16, u16 + 0xffff)
        else:
            def ld():
                u16 = self.get_reg16(reg16)
                self.set_reg8(reg8, self.mmu.get_addr(u16))
        return ld

    def ld_reg16toreg16(self, src_reg16, dest_reg16):
        def ld():
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

        :rtype: None"""

        imm16 = self.fetch2()
        self.mmu.set_addr(imm16, self.sp >> 8)
        self.mmu.set_addr(imm16 + 1, self.sp & 0xff)

    def ld_spimm8toregHL(self):
        imm8 = self.fetch()

        result = (self.sp & 0xff) + imm8
        if (self.sp & 0x0f) + (imm8 & 0x0f) > 0xf:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        if result > 0xff:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.reset_zero_flag()
        self.reset_sub_flag()

        result += self.sp & 0xff00

        self.set_reg16('hl', result)

    def ld_sptoreg16addr(self, reg16):
        """Returns a function that loads the stack pointer into the 16-bit
        register :py:data:reg16.

        :param reg16: the destination double register
        :rtype: None → None"""

        def ld():
            addr = self.get_reg16(reg16)

            self.mmu.set_addr(addr, self.sp >> 8)
            self.mmu.set_addr(addr + 1, self.sp & 0xff)
        return ld

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
            self.set_reg8(reg8, result & 0xff)

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

        :param reg16: the double register to decrement
        :rtype: None → None"""

        def dec():
            u16 = self.get_reg16(reg16)

            result = u16 + 0xffff
            self.set_reg16(reg16, result)
        return dec

    def inc_addrHL(self):
        """Increments the value at the address in HL."""

        addr16 = self.get_reg16('hl')
        u8 = self.mmu.get_addr(addr16)
        result = u8 + 1

        if u8 & 0xf == 0xf:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_sub_flag()

        self.mmu.set_addr(addr16, result & 0xff)

    def dec_addrHL(self):
        """Decrements the value at the address in HL."""

        addr16 = self.get_reg16('hl')
        u8 = self.mmu.get_addr(addr16)
        result = u8 + 0xff

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        if u8 & 0x0f == 0x0:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        self.set_sub_flag()

        self.mmu.set_addr(addr16, result & 0xff)

    def add_reg16toregHL(self, reg16):
        """Returns a function that adds :py:data:reg16 to the double register
        HL.

        :param reg16: source double register
        :rtype: None → None"""

        def add():
            x = self.get_reg16('hl')
            y = self.get_reg16(reg16)
            result = x + y
            self.set_reg16('hl', result)

            if ((x & 0xfff) + (y & 0xfff)) > 0xfff:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.reset_sub_flag()

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

    def add_imm8toregSP(self):
        """Returns a function that an 8-bit immediate to reg SP.
        SP = SP + imm8
        """

        imm8 = self.fetch()
        sp = self.sp
        lo = (sp & 0xff) + imm8
        # if negative, sign-extend
        if imm8 & 0x80:
            self.sp = add_s16(sp, 0xff00 | imm8)
        else:
            self.sp = add_s16(sp, imm8)

        if (sp & 0xf) + (imm8 & 0xf) > 0xf:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        if lo > 0xff:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.reset_sub_flag()
        self.reset_zero_flag()

    def add_reg16addrtoreg8(self, reg16, reg8, carry=False):
        """Returns a function that adds (reg16) to reg8 and stores the result
        in reg8.

        :param reg16: source address of operand 1
        :param reg8: dest register, operand 2
        :param carry: (reg16) + reg8 + 1
        :rtype: None → None"""

        def add():
            addr = self.get_reg16(reg16)
            src_u8 = self.mmu.get_addr(addr)
            dest_u8 = self.get_reg8(reg8)

            c = self.get_carry_flag() if carry else 0
            result = src_u8 + dest_u8 + c

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (dest_u8 & 0x0f) + (src_u8 & 0x0f) + c > 0x0f:
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
        :param carry: Set the carry flag?
        :rtype: None → None"""

        def sub():
            src_u8 = self.get_reg8(src_reg8)
            dest_u8 = self.get_reg8(dest_reg8)

            result = dest_u8 + (((src_u8 ^ 0xff) + 1) & 0xff)
            if carry:
                # result -= 1
                result += (self.get_carry_flag() ^ 0xff) + 1

            self.set_reg8(dest_reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if src_u8 & 0x0f > dest_u8 & 0x0f:
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

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
        :param carry: Set the carry flag?
        :rtype: int → None"""

        def sub():
            imm8 = self.fetch()
            u8 = self.get_reg8(reg8)

            c = self.get_carry_flag() if carry else 0
            result = u8 + ((((imm8 + c) ^ 0xff) + 1) & 0xff)

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

        :param reg8: The single destination register.
        :param carry: Set the carry flag?
        :rtype: None → None"""

        def sub():
            imm16 = self.fetch2()
            x = self.get_reg8(reg8)
            y = self.mmu.get_addr(imm16)

            c = self.get_carry_flag() if carry else 0
            result = x + ((((y + c) ^ 0xff) + 1) & 0xff)

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (x & 0x0f) < ((y + c) & 0x0f):
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

            self.set_sub_flag()

            if result > 0xff:
                self.reset_carry_flag()
            else:
                self.set_carry_flag()
        return sub

    def sub_reg16addrfromreg8(self, reg16: str, reg8: str, carry: bool=False):
        """Returns a function that subtracts the value at the address given by
        :py:data:reg16 from :py:data:reg8.

        reg8 = reg8 - (reg16)

        :param reg16: The double register containing the source address of
                      operand 1
        :param reg8: Destination register, operand 2.
        :param carry: reg8 - (reg16) - 1
        :rtype: None → None"""

        def sub():
            x = self.get_reg8(reg8)
            y = self.mmu.get_addr(self.get_reg16(reg16))

            c = self.get_carry_flag() if carry else 0
            result = x + ((((y + c) ^ 0xff) + 1) & 0xff)

            self.set_reg8(reg8, result)

            if result & 0xff == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()

            if (x & 0x0f) < ((y + c) & 0x0f):
                self.set_halfcarry_flag()
            else:
                self.reset_halfcarry_flag()

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

            self.set_halfcarry_flag()
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

            self.set_halfcarry_flag()
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

            self.set_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
            self.reset_sub_flag()
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

            self.reset_carry_flag()
            self.reset_halfcarry_flag()
            self.reset_sub_flag()
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

    def cp_regAtoregHLaddr(self):
        """Compares register A to the address in double register HL, then
        sets the appropriate flags as specified in :py:method:cp_reg8toreg8.

        :param reg8: single register
        :param reg16: double register holding an address"""

        result = self.get_reg8('a') - self.mmu.get_addr(self.get_reg16('hl'))

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

    def cp_imm8toregA(self):
        """Compares 8-bit immediate to value in register A, then sets appropriate flags.

        :rtype: None"""

        imm8 = self.mmu.get_addr(self.pc)
        self.pc += 1
        result = self.get_reg8('a') - imm8

        if result & 0xff == 0:
            self.registers['f'] |= Z_FLAG_MASK
        else:
            self.registers['f'] &= ~Z_FLAG_MASK

        if result > 0:
            self.registers['f'] |= HC_FLAG_MASK
        else:
            self.registers['f'] &= ~HC_FLAG_MASK

        self.registers['f'] |= N_FLAG_MASK

        if result < 0:
            self.registers['f'] |= C_FLAG_MASK
        else:
            self.registers['f'] &= ~C_FLAG_MASK

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

    def rl_regHLaddr(self):
        last_carry = self.get_carry_flag()
        reg = self.get_reg16('hl')
        d8 = self.mmu.get_addr(reg)
        result = (d8 << 1) | last_carry

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if d8 & 0x80 == 0x80:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(reg, result)

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

    def rlc_regHLaddr(self):
        reg = self.get_reg16('hl')
        d8 = self.mmu.get_addr(reg)
        result = (d8 << 1) | (d8 >> 7)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if result & 0x100 == 0x100:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(reg, result)

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

    def rr_regHLaddr(self):
        last_carry = self.get_carry_flag()
        reg = self.get_reg16('hl')
        d8 = self.mmu.get_addr(reg)
        result = (d8 >> 1) | (last_carry << 7)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if d8 & 0x01 == 0x01:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(reg, result)

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

    def rrc_regHLaddr(self):
        reg = self.get_reg16('hl')
        d8 = self.mmu.get_addr(reg)
        result = (d8 >> 1) | ((d8 << 7) & 0x80)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_halfcarry_flag()
        self.reset_sub_flag()

        if d8 & 0x01 == 0x01:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

        self.mmu.set_addr(reg, result)

    def sla_reg8(self, reg8):
        """CB 0x20-0x25, 0x27
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

    def sla_regHLaddr(self):
        """CB 0x20-0x25, 0x27
        Logical shift (addr16) left 1 and place old bit 0 in CF."""

        addr = self.get_reg16('hl')
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

    def sra_reg8(self, reg8):
        """CB 0x28-0x2d, 0x2f
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

    def sra_regHLaddr(self):
        """CB 0x20-0x25, 0x27
        Arithmetic shift (addr16) right 1 and place old bit 7 in CF."""

        addr16 = self.get_reg16('hl')
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

    def swap_reg8(self, reg8):
        def swap():
            d8 = self.get_reg8(reg8)
            hi = d8 >> 4
            lo = d8 & 0xf
            result = (lo << 4) | hi
            self.set_reg8(reg8, result)
            if d8 == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
            self.reset_carry_flag()
            self.reset_halfcarry_flag()
            self.reset_sub_flag()
        return swap

    def swap_regHLaddr(self):
        addr = self.get_reg16('hl')
        d8 = self.mmu.get_addr(addr)
        hi = d8 >> 4
        lo = d8 & 0xf
        result = (lo << 4) | hi
        self.mmu.set_addr(addr, result)
        if d8 == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()
        self.reset_carry_flag()
        self.reset_halfcarry_flag()
        self.reset_sub_flag()

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

    def srl_regHLaddr(self):
        """Logical shift reg8 right 1 and place old LSb in C"""

        addr = self.get_reg16('hl')
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

    def bit_reg8(self, i, reg8):
        def bit():
            d8 = self.get_reg8(reg8)
            if (d8 >> i) & 0x1 == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
            self.set_halfcarry_flag()
            self.reset_sub_flag()
        return bit

    def bit_regHLaddr(self, i):
        def bit():
            addr = self.get_reg16('hl')
            d8 = self.mmu.get_addr(addr)
            if (d8 >> i) & 0x1 == 0:
                self.set_zero_flag()
            else:
                self.reset_zero_flag()
            self.set_halfcarry_flag()
            self.reset_sub_flag()
        return bit

    def res_reg8(self, i, reg8):
        def res():
            d8 = self.get_reg8(reg8)
            result = d8 & ((1 << i) ^ 0xff)
            self.set_reg8(reg8, result)
        return res

    def res_regHLaddr(self, i):
        def res():
            addr = self.get_reg16('hl')
            d8 = self.mmu.get_addr(addr)
            result = d8 & ((1 << i) ^ 0xff)
            self.mmu.set_addr(addr, result)
        return res

    def set__reg8(self, i, reg8):
        def set():
            d8 = self.get_reg8(reg8)
            result = d8 | (1 << i)
            self.set_reg8(reg8, result)
        return set

    def set_regHLaddr(self, i):
        def set():
            addr = self.get_reg16('hl')
            d8 = self.mmu.get_addr(addr)
            result = d8 | (1 << i)
            self.mmu.set_addr(addr, result)
        return set

    def cpl(self):
        """0x2f: ~A"""

        result = self.get_reg8('a') ^ 0xff
        self.set_reg8('a', result)
        self.set_halfcarry_flag()
        self.set_sub_flag()

    def daa(self):
        """0x27: adjust regA following BCD addition.

        NOTE: This could certainly be simplified, but I just reproduced the
        table in The Game Boy Programming Manual, p. 110."""

        reg = self.get_reg8('a')

        hi = reg >> 4
        lo = reg & 0xf
        c = self.get_carry_flag()
        h = self.get_halfcarry_flag()

        if self.get_sub_flag() == 0:
            if c == 0 and hi <= 0x9 \
               and h == 0 and lo < 0xa:
                result = reg
                self.reset_carry_flag()
            elif c == 0 and hi <= 0x8 \
                    and h == 0 and 0xa <= lo <= 0xf:
                result = reg+0x06
                self.reset_carry_flag()
            elif c == 0 and hi <= 0x9 \
                    and h == 1 and lo <= 0x3:
                result = reg+0x06
                self.reset_carry_flag()
            elif c == 0 and 0xa <= hi <= 0xf \
                    and h == 0 and lo <= 0x9:
                result = reg+0x60
                self.set_carry_flag()
            elif c == 0 and 0x9 <= hi <= 0xf \
                    and h == 0 and 0xa <= lo <= 0xf:
                result = reg+0x66
                self.set_carry_flag()
            elif c == 0 and 0xa <= hi <= 0xf \
                    and h == 1 and lo <= 0x3:
                result = reg+0x66
                self.set_carry_flag()
            elif c == 1 and hi <= 0x2 \
                    and h == 0 and lo <= 0x9:
                result = reg+0x60
                self.set_carry_flag()
            elif c == 1 and hi <= 0x2 \
                    and h == 0 and 0xa <= lo <= 0xf:
                result = reg+0x66
                self.set_carry_flag()
            elif c == 1 and hi <= 0x3 \
                    and h == 1 and lo <= 0x3:
                result = reg+0x66
                self.set_carry_flag()
            else:
                raise ValueError('unrecognized condition')
        else:
            if c == 0 and hi <= 0x9 \
               and h == 0 and lo <= 0x9:
                self.reset_carry_flag()
                result = reg
            elif c == 0 and hi <= 0x8 \
                    and h == 1 and 0x6 <= lo <= 0xf:
                self.reset_carry_flag()
                result = reg+0xfa
            elif c == 1 and 0x7 <= hi <= 0xf \
                    and h == 0 and lo <= 0x9:
                self.set_carry_flag()
                result = reg+0xa0
            elif c == 1 and 0x6 <= hi <= 0xf \
                    and h == 1 and 0x6 <= lo <= 0xf:
                self.set_carry_flag()
                result = reg+0x9a
            else:
                raise ValueError('unrecognized condition')

        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

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
        lrtype: int → None"""

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
                imm8 = self.mmu.get_addr(self.pc)
                self.pc += 1
                # Skip incrementing PC because we'll set it anyway
                if imm8 > 127: # negative
                    imm8 |= 0xff00
                target = add_s16(self.pc, imm8)
                #self._branches[(self.pc, target)] += 1
                self.pc = target
        else:
            def jr():
                imm8 = self.mmu.get_addr(self.pc)
                self.pc += 1
                if check_cond():
                    if imm8 > 127: # negative
                        imm8 |= 0xff00
                    target = add_s16(self.pc, imm8)
                    #self._branches[(self.pc, target)] += 1
                    self.pc = target

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
                #self._branches[(self.pc, imm16)] += 1
                self.pc = imm16
        else:
            def jp():
                imm16 = self.fetch2()
                if check_cond():
                    #self._branches[(self.pc, imm16)] += 1
                    self.pc = imm16

        return jp

    def jp_reg16addr(self, reg16):
        """Returns a function that performs an uncoditional jump to the address
        in :py:data:reg16"""

        def jp():
            target = self.get_reg16(reg16)
            #self._branches[(self.pc, target)] += 1
            self.pc = target
        return jp

    def ret(self, cond=None):
        """Returns a function that, based on cond, will get the return address
        from the stack and return.

        :param cond: one (or none) of Z, C, S, H
        :rtype: None → None"""

        if cond is None:
            def retc():
                sp = self.sp
                pc = (self.mmu.get_addr(sp + 1) << 8) | self.mmu.get_addr(sp)
                self.pc = pc
                self.sp = sp + 2
        else:
            cond = cond.lower()
            def retc():
                flag = False
                if cond == 'z':
                    flag = self.get_zero_flag() == 1
                elif cond == 'nz':
                    flag = self.get_zero_flag() == 0
                elif cond == 'c':
                    flag = self.get_carry_flag() == 1
                elif cond == 'nc':
                    flag = self.get_carry_flag() == 0
                else:
                    raise ValueError('cond must be one of Z, NZ, C, NC')

                if flag:
                    sp = self.sp
                    pc = (self.mmu.get_addr(sp + 1) << 8) | self.mmu.get_addr(sp)
                    self.pc = pc
                    self.sp = (sp + 2) & 0xffff

        return retc

    def reti(self):
        """0xd9 -- reti"""

        lo = self.mmu.get_addr(self.sp)
        hi = self.mmu.get_addr(self.sp + 1)
        self.pc = (hi << 8) | lo
        self.sp = self.sp + 2
        self._in_interrupt = False

    def call_imm16addr(self, cond: str=None):
        """Returns a function that, based on :py:data:cond, pushes the current
        address in the program counter and jumps to the 16-bit immediate
        parameter of the function.

        :param cond: one of Z, C, S, H
        :rtype: int → None"""

        if cond is None:
            def call():
                imm16 = self.fetch2()
                #self._branches[(self.pc, imm16)] += 1
                pc = self.pc
                sp = self.sp
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.pc = imm16
                self.sp = sp - 2
        else:
            cond = cond.lower()
            def call():
                if cond == 'z':
                    flag = self.get_zero_flag() == 1
                elif cond == 'nz':
                    flag = self.get_zero_flag() == 0
                elif cond == 'c':
                    flag = self.get_carry_flag() == 1
                elif cond == 'nc':
                    flag = self.get_carry_flag() == 0
                else:
                    raise ValueError('cond must be one of Z, NZ, C, NC')

                imm16 = self.fetch2()
                #self._branches[(self.pc, imm16)] += 1
                pc = self.pc
                sp = self.sp
                if flag:
                    self.mmu.set_addr(sp - 1, pc >> 8)
                    self.mmu.set_addr(sp - 2, pc & 0xff)
                    self.pc = imm16
                    self.sp = sp - 2
        return call

    def push_reg16(self, reg16):
        """0xc5, 0xd5, 0xe5, 0xf5"""
        def push():
            d16 = self.get_reg16(reg16)
            hi = d16 >> 8
            lo = d16 & 0xff
            self.sp = self.sp - 1
            self.mmu.set_addr(self.sp, hi)
            self.sp = self.sp - 1
            self.mmu.set_addr(self.sp, lo)
        return push

    def pop_reg16(self, reg16):
        """0xc1, 0xd1, 0xe1, 0xf1"""
        def pop():
            lo = self.mmu.get_addr(self.sp)
            self.sp = self.sp + 1
            hi = self.mmu.get_addr(self.sp)
            self.sp = self.sp + 1
            self.set_reg16(reg16, (hi << 8) | lo)
        return pop

    def rst(self, addr):
        """0xc7, 0xd7, 0xe7, 0xf7, 0xcf, 0xdf, 0xef, 0xff -- rst xxH"""

        def panic(msg):
            self.logger.error('PANIC!')
            self.logger.error(msg)
            self.log_regs(self.logger.error)
            pcs = []
            for pc in self._opcode_ring:
                prev, curr = pc
                pcs.append('{} ({}) → {} ({})'.format(hex(prev), self.opcode_map[self.mmu.get_addr(prev)].description,
                                                        hex(curr), self.opcode_map[self.mmu.get_addr(curr)].description))
            self.logger.error(pcs)
            self.logger.error('')
            raise RuntimeError()

        def rst_addr():
            #panic('in rst({:x})'.format(addr))
            pc = self.pc
            hi = pc >> 8
            lo = pc & 0xff

            self.sp -= 1
            self.mmu.set_addr(self.sp, hi)
            self.sp -= 1
            self.mmu.set_addr(self.sp, lo)

            self.pc = addr

        return rst_addr

    def di(self):
        """0xf3 -- di
        Disable interrupts."""

        self.interrupt_controller.di()

    def ei(self):
        """0xfb -- ei
        Enable interrupts."""

        self.interrupt_controller.ei()
