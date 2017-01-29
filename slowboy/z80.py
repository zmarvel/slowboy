
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

    def ld_imm8toreg8(self, reg8):
        """Returns a function to load an 8-bit immediate into :py:data:reg8.

        :param reg8: single byte register
        :rtype: integer → None """

        def ld(imm8):
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

        def ld(imm16):
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

        def ld(imm16):
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

    def ld_imm16addrtoreg8(self, reg8):
        """Returns a function to load the value at an address given by a 16-bit
        immediate into an 8-bit register.

        :param reg8: the single-byte destination register
        :rtype: integer → None"""

        def ld(imm16):
            self.set_reg8(reg8, self.mmu.get_addr(imm16))
        return ld

    def ld_sptoimm16addr(self, imm16):
        """Loads the most significant byte of the stack pointer into the address
        given by :py:data:imm16 and the least significant byte of the SP into
        :py:data:imm16+1.

        :param imm16: 16-bit address
        :rtype: None"""

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

    def ld_imm8toaddrHL(self, imm8):
        """0x36"""

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

        def add(imm8):
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

        def sub(imm8):
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

        def sub(imm16):
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

        def band(imm8):
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

        def band(imm16):
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

        def bor(imm8):
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

        def bor(imm16):
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

        def bxor(imm8):
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

        def bxor(imm16):
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

        def cp(imm16):
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
