from functools import partial

from slowboy.util import uint8toBCD

class Z80(object):
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
            'l': 0,
            'sp': 0,
            'pc': 0
        }
        return

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
        elif reg16 == 'sp':
            self.registers['sp'] = value & 0xffff
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
        elif reg16 == 'sp':
            return self.registers['sp']
        else:
            raise KeyError('unrecognized register {}'.format(reg16))

    def _advance(self):
        """Advance the program counter."""

        # op = self.rom[self.registers['pc']]
        self.registers['pc'] += 1

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
        """0x02, 0x12, 0x22, 0x32"""
        # TODO

        raise NotImplementedError('ld (reg16), reg8 / ld (imm16), reg8')

    def ld_addr16toreg8(self, addr16, reg8):
        """0x0a, 0x1a, 0x4e, 0x5e, 0x6e, 0x7e, 0x77, 0x46, 0x56, 0x66"""

        raise NotImplementedError('ld reg8, (reg16) / ld reg8, (addr16)')

    def ld_sptoaddr16(self, addr16):
        """0x08"""
        # TODO

        raise NotImplementedError('ld (imm16), SP')

    def ld_imm8toaddrHL(self, imm8):
        """0x36"""

        raise NotImplementedError('ld (HL), imm8')

    def inc_reg8(self, reg8):
        """0x04, 0x14, 0x24, 0x34 -- inc reg8
        TODO: overflow, carry"""

        self.set_reg8(reg8, self.get_reg8(reg8) + 1)

    def inc_reg16(self, reg16):
        """0x03, 0x13, 0x23, 0x33 -- inc reg16"""

        self.set_reg16(reg16, self.get_reg16(reg16) + 1)

    def dec_reg8(self, reg8):
        """0x05, 0x15, 0x25, 0x35 -- dec reg8"""

        self.set_reg8(reg8, self.get_reg8(reg8) - 1)

    def dec_reg16(self, reg16):
        """0x0b, 0x1b, 0x2b, 0x3b -- dec reg16"""

        self.set_reg16(reg16, self.get_reg16(reg16) - 1)

    def inc_addrHL(self):
        """0x34 -- inc (HL)"""

        raise NotImplementedError('inc *(HL)')

    def dec_addrHL(self):
        """0x35 -- dec (HL)"""

        raise NotImplementedError('dec *(HL)')

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
            result = dest_u8  + (((src_u8  ^ 0xff) + 1) & 0xff)

        self.set_reg8(dest_reg8, result)

        if result & 0xff == 0:
            self.set_zero_flag()
        else:
            self.reset_zero_flag()

        # TODO: set halfcarry flag if a borrow from bit 4 occured
        if (dest_u8 & 0x0f) + (src_u8 & 0x0f) > 0x0f:
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
            result = u8  + (((imm8  ^ 0xff) + 1) & 0xff)
        
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

        raise NotImplementedError('sub (HL), sbc (HL)')

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

        raise NotImplementedError('and (HL)')

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

        raise NotImplementedError('or (HL)')

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

        raise NotImplementedError('cp (HL)')

    def rlca(self):
        """0x07"""

        if self.registers['a'] & 0x80 == 0x80:
            self.set_carry_flag()
        self.set_reg8('a', self.get_reg8('a') << 1) 

    def rla(self):
        """0x17"""

        last_carry = self.get_carry_flag()

    def rrca(self):
        """0x0f"""

        last_carry = self.get_carry_flag()

        regA = self.get_reg8('a')
        if regA & 0x01 == 0x01:
            self.set_carry_flag()

        self.set_reg8('a', regA >> 1)

        regA = self.get_reg8('a')
        if regA & 0x80 == 0x80:
            self.set_carry_flag()

        self.set_reg8('a', (self.get_reg8('a') << 1) | last_carry)

    def rra(self):
        """0x1f"""

        last_carry = self.get_carry_flag()

        regA = self.get_reg8('a')
        if regA & 0x01 == 0x01:
            self.set_carry_flag()

        self.set_reg8('a', (self.get_reg8('a') >> 1) | (last_carry << 7))

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

    def jr_condtoimm8(self, imm8, zero=False, carry=False):
        """0x18
        Conditionally jump forward by a signed immediate offset."""

        raise NotImplementedError('conditional jump to 8-bit immediate')

    def jp_condtoimm8(self, addr16, zero=False, carry=False):
        """0xc2, 0xd2, 0xc3, 0xca, 0xda
        Conditional absolute jump to 16-bit address."""

        raise NotImplementedError('jp f, addr16')
