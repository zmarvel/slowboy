
import enum

from slowboy.util import uint8toBCD
from slowboy.mmu import MMU

class State(enum.Enum):
    RUN = 0
    HALT = 1
    STOP = 2

class Z80(object):
    reglist = ['b', 'c', None, 'e', 'h', 'd', None, 'a']

    def __init__(self):
        self.clk = 0
        self.m = 0
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
        self.pc = 0
        self.state = State.STOP
        self.mmu = MMU()

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

    def go(self):

        self.state = State.RUN
        while self.state == State.RUN:
            # fetch
            opcode = self.mmu.get_addr(self.get_pc())
            self.inc_pc()

            # decode
            op, args = self.decode(opcode)

            # execute
            op(*args)

    def decode(self, opcode):
        """Call the appropriate method of `Z80` based on `opcode`.

        TODO: Since this class is about 1000 lines now, I'm considering how to
        split it up. A Decoder class might depend on other classes implementing
        CPU instructions, each depending on and sharing a CPU state."""

        if opcode & 0xc0 == 0x40:
            print('{opcode:<#6x} ld rd, rs'.format(opcode=opcode))
            rd = (opcode >> 3) & 0x07
            rs = opcode & 0x07
            return self.ld_reg8toreg8, (self.reglist[rs], self.reglist[rs])
        else:
            raise ValueError('Unrecognized opcode {:#x}'.format(opcode))

    def nop(self):
        """0x00"""
        # TODO

        pass

    def stop(self):
        """0x10"""
        # TODO

        pass

    def halt(self):
        """0x76"""
        # TODO

        pass

    def ld_imm8toreg8(self, imm8, reg8):
        """0x06, 0x16, 0x26"""

        self.set_reg8(reg8, imm8)

    def ld_reg8toreg8(self, src_reg8, dest_reg8):
        self.set_reg8(dest_reg8, self.get_reg8(src_reg8))

    def ld_imm16toreg16(self, imm16, reg16):
        """0x01, 0x11, 0x21, 0x31"""

        self.set_reg16(reg16, imm16)

    def ld_reg8toaddr16(self, reg8, addr16, inc=False, dec=False):
        """0x02, 0x12, 0x22, 0x32

        If addr16 is a string such as 'BC', an address will be read from that
        double-register. Otherwise, it will be taken literally."""

        if isinstance(addr16, str):
            reg16 = addr16
            addr16 = self.get_reg16(reg16)

        self.mmu.set_addr(addr16, self.get_reg8(reg8))

        if inc:
            self.set_reg16(reg16, self.get_reg16(reg16) + 1)
        elif dec:
            self.set_reg16(reg16, self.get_reg16(reg16) - 1)

    def ld_addr16toreg8(self, addr16, reg8):
        """0x0a, 0x1a, 0x4e, 0x5e, 0x6e, 0x7e, 0x77, 0x46, 0x56, 0x66

        If addr16 is a string such as 'BC', an address will be read from that
        double-register. Otherwise, it will be taken literally."""

        if isinstance(addr16, str):
            reg16 = addr16
            addr16 = self.get_reg16(reg16)

            self.set_reg8(reg8, self.mmu.get_addr(addr16))
        else:
            self.set_reg8(reg8, self.mmu.get_addr(addr16))

    def ld_sptoaddr16(self, addr16):
        """0x08"""

        if isinstance(addr16, str):
            reg16 = addr16
            addr16 = self.get_reg16(reg16)

        self.mmu.set_addr(addr16, self.get_sp() >> 8)
        self.mmu.set_addr(addr16 + 1, self.get_sp() & 0xff)

    def ld_imm8toaddrHL(self, imm8):
        """0x36"""

        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, imm8)

    def inc_reg8(self, reg8):
        """0x04, 0x14, 0x24, 0x34 -- inc reg8
        TODO: overflow, carry"""

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

    def inc_reg16(self, reg16):
        """0x03, 0x13, 0x23, 0x33 -- inc reg16"""

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

    def dec_reg8(self, reg8):
        """0x05, 0x15, 0x25, 0x35 -- dec reg8"""

        # TODO: according to the Z80 manual, dec does not affect the carry flag,
        # but it does affect the half-carry flag when a borrow from bit 4 occurs.

        u8 = self.get_reg8(reg8)

        self.set_reg8(reg8, u8 + 0xff)

        if u8 & 0x0f == 0:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        self.set_sub_flag()

    def dec_reg16(self, reg16):
        """0x0b, 0x1b, 0x2b, 0x3b -- dec reg16"""

        u16 = self.get_reg16(reg16)

        self.set_reg16(reg16, u16 + 0xffff)

        if u16 & 0x00ff == 0:
            self.set_halfcarry_flag()
        else:
            self.reset_halfcarry_flag()

        self.set_sub_flag()

    def inc_addrHL(self):
        """0x34 -- inc (HL)"""

        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, self.mmu.get_addr(addr16) + 1)

    def dec_addrHL(self):
        """0x35 -- dec (HL)"""

        addr16 = self.get_reg16('hl')
        self.mmu.set_addr(addr16, self.mmu.get_addr(addr16) - 1)

    def add_reg16toregHL(self, reg16):
        """0x09, 0x19, 0x29, 0x39 -- add HL, reg16"""

        result = self.get_reg16('HL') + self.get_reg16(reg16)
        self.set_reg16('HL', result)

        if result > 0xffff:
            self.set_carry_flag()
        else:
            self.reset_carry_flag()

    def add_reg8toreg8(self, src_reg8, dest_reg8, carry=False):
        """0x80-0x85, 0x87-0x8d, 0x8f -- add src_reg8, dest_reg8"""

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

    def add_imm8toreg8(self, imm8, reg8, carry=False):
        """0xc6, 0xce -- add reg8, imm8"""

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

    def sub_reg8fromreg8(self, src_reg8, dest_reg8, carry=False):
        """0x90-0x95, 0x97-0x9d, 0x9f -- sub reg8
        dest_reg8 = dest_reg8 - src_reg8"""
        
        src_u8 = self.get_reg8(src_reg8)
        dest_u8 = self.get_reg8(dest_reg8)

        if carry:
            # TODO
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

    def sub_imm8fromreg8(self, imm8, reg8, carry=False):
        """0xd6, 0xde -- sub imm8"""

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

    def sub_addr16fromreg8(self, addr16, reg8, carry=False):
        """0x96, 0x9e -- sub/sbc (HL)"""

        x = self.get_reg8(reg8)
        if isinstance(addr16, str):
            y = self.mmu.get_addr(self.get_reg16(addr16))
        else:
            y = self.mmu.get_addr(addr16)

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

    def and_reg8(self, reg8):
        """0xa0–a7, except 0xa6 -- and reg8
        a = a & reg8"""

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

    def and_imm8(self, imm8):
        """0xe6 -- and imm8
        a = a & imm8"""

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

    def and_addr16(self, addr16):
        """0xa6 -- and (HL)
        a = a & (addr16)"""

        if isinstance(addr16, str):
            addr16 = self.get_reg16(addr16)

        x = self.get_reg8('a')
        y = self.mmu.get_addr(addr16)
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

    def or_reg8(self, reg8):
        """0xb0–b7, except 0xb6 -- or reg8
        a = a | reg8"""

        result = self.get_reg8('a') | self.get_reg8(reg8)
        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_sub_flag()

    def or_imm8(self, imm8):
        """0xf6 -- or imm8
        a = a | imm8"""

        result = self.get_reg8('a') | imm8
        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_sub_flag()

    def or_addr16(self, addr16):
        """0xb6 -- or (HL)
        a = a | (addr16)"""

        result = self.get_reg8('a') | self.mmu.get_addr(addr16)
        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_sub_flag()

    def xor_reg8(self, reg8):
        """0xa8-af, except 0xae -- xor reg8
        a = a ^ reg8"""

        result = self.get_reg8('a') ^ self.get_reg8(reg8)
        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        self.reset_sub_flag()

    def xor_imm8(self, imm8):
        """0xee -- xor imm8
        a = a ^ imm8"""

        result = self.get_reg8('a') ^ imm8
        self.set_reg8('a', result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

    def xor_addr16(self, addr16):
        """0xae
        a = a ^ (addr16)"""

        raise NotImplementedError('xor (HL)')

    def cp_reg8toreg8(self, reg8_1, reg8_2):
        """0xb8–bf, except 0be
        Compare regA to regB means calculate regA - regB and
            * set Z if regA == regB
            * set NZ (reset Z) if regA != regB
            * set C if regA < regB
            * set NC (reset C) if regA >= regB
        """

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

    def cp_reg8toaddr16(self, reg8, addr16):
        """0xbe: TODO, similar to `cp_reg8toreg8`"""

        result = self.get_reg8(reg8) - self.mmu.get_addr(addr16)

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
        """0x17, CB 0x10-0x17
        shift reg8 left 1, place old bit 7 in CF, place old CF in bit 0."""

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

    def rlc_reg8(self, reg8):
        """0x07, CB 0x00-0x07
        shift reg8 left 1, place old bit 7 in CF and bit 0."""

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

    def rr_reg8(self, reg8):
        """0x1f, CB 0x18-0x1f
        shift reg8 right 1, place old bit 0 in CF, place old CF in bit 7."""

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

    def rrc_reg8(self, reg8):
        """0x0f, CB 0x08-0x0f
        logical shift reg8 right 1, place old bit 0 in CF and bit 7."""

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

    def jr_condtoimm8(self, cond, imm8):
        """0x28, 0x38
        Conditional relative jump by a signed immediate."""

        cond = cond.lower()
        if cond == 'z':
            if self.get_zero_flag() == 1:
                self.set_pc(self.get_pc() + imm8)
        elif cond == 'nz':
            if self.get_zero_flag() == 0:
                self.set_pc(self.get_pc() + imm8)
        elif cond == 'c':
            if self.get_carry_flag() == 1:
                self.set_pc(self.get_pc() + imm8)
        elif cond == 'nc':
            if self.get_carry_flag() == 0:
                self.set_pc(self.get_pc() + imm8)

    def jr_imm8(self, imm8):
        """0x18 --- jr imm8
        Relative jump by a signed immediate."""

        off = (imm8 ^ 0x80) - 0x80
        self.set_pc(self.get_pc() + off)

    def jp_condtoaddr16(self, cond, addr16):
        """0xc2, 0xd2, 0xca, 0xda
        Conditional absolute jump to 16-bit address."""

        cond = cond.lower()
        if cond == 'z':
            if self.get_zero_flag() == 1:
                self.set_pc(addr16)
        elif cond == 'nz':
            if self.get_zero_flag() == 0:
                self.set_pc(addr16)
        elif cond == 'c':
            if self.get_carry_flag() == 1:
                self.set_pc(addr16)
        elif cond == 'nc':
            if self.get_carry_flag() == 0:
                self.set_pc(addr16)

    def jp_addr16(self, addr16):
        """0xc3, 0xe9 -- jp addr16"""

        self.set_pc(addr16)

    def ret(self, cond=None):
        """0xc9 -- ret"""

        if cond == 'z':
            if self.get_zero_flag() == 0:
                return
        elif cond == 'c':
            if self.get_carry_flag() == 0:
                return
        elif cond == 's':
            if self.get_sub_flag() == 0:
                return
        elif cond == 'h':
            if self.get_halfcarry_flag() == 0:
                return

        sp = self.get_sp()
        pc = self.mmu.get_addr(sp + 1) << 8 | self.mmu.get_addr(sp)
        self.set_pc(pc)
        self.set_sp(sp + 2)

    def reti(self):
        """0xd9 -- reti"""
        raise NotImplementedError('reti')

    def ret_cond(self, cond):
        """0xc0, 0xc8, 0xc9, 0xd0, 0xd8, 0xd9 -- ret / reti / ret cond
        cond may be one of Z, C, S, H."""

        raise NotImplementedError('ret / reti')

    def call_condtoaddr16(self, cond, addr16):
        """0xc4, 0xd4, 0xcc, 0xdc -- call cond, addr16
        cond may be one of Z, C, S, H."""

        pc = self.get_pc()
        sp = self.get_sp()

        cond = cond.lower()
        if cond == 'z':
            if self.get_zero_flag() == 1:
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(addr16)
                self.set_sp(sp - 2)
        elif cond == 'c':
            if self.get_carry_flag() == 1:
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(addr16)
                self.set_sp(sp - 2)
        elif cond == 's':
            if self.get_sub_flag() == 1:
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(addr16)
                self.set_sp(sp - 2)
        elif cond == 'h':
            if self.get_halfcarry_flag() == 1:
                self.mmu.set_addr(sp - 1, pc >> 8)
                self.mmu.set_addr(sp - 2, pc & 0xff)
                self.set_pc(addr16)
                self.set_sp(sp - 2)

    def call_addr16(self, addr16):
        """0xcd -- call addr16"""

        pc = self.get_pc()
        sp = self.get_sp()
        self.mmu.set_addr(sp - 1, pc >> 8)
        self.mmu.set_addr(sp - 2, pc & 0xff)
        self.set_pc(addr16)
        self.set_sp(sp - 2)

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
