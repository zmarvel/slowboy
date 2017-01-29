import unittest

import slowboy.z80


class TestZ80(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()

    def test_set_reg8(self):
        self.cpu.set_reg8('B', 0)
        self.cpu.set_reg8('C', 1)
        self.cpu.set_reg8('D', 2)
        self.cpu.set_reg8('E', 3)
        self.cpu.set_reg8('H', 4)
        self.cpu.set_reg8('L', 5)
        self.cpu.set_reg8('A', 6)

        registers = self.cpu.get_registers()

        self.assertEqual(registers['b'], 0)
        self.assertEqual(registers['c'], 1)
        self.assertEqual(registers['d'], 2)
        self.assertEqual(registers['e'], 3)
        self.assertEqual(registers['h'], 4)
        self.assertEqual(registers['l'], 5)
        self.assertEqual(registers['a'], 6)

    def test_get_reg8(self):
        self.cpu.set_reg8('B', 0)
        self.cpu.set_reg8('C', 1)
        self.cpu.set_reg8('D', 2)
        self.cpu.set_reg8('E', 3)
        self.cpu.set_reg8('H', 4)
        self.cpu.set_reg8('L', 5)
        self.cpu.set_reg8('A', 6)

        self.assertEqual(self.cpu.get_reg8('b'), 0)
        self.assertEqual(self.cpu.get_reg8('c'), 1)
        self.assertEqual(self.cpu.get_reg8('d'), 2)
        self.assertEqual(self.cpu.get_reg8('e'), 3)
        self.assertEqual(self.cpu.get_reg8('h'), 4)
        self.assertEqual(self.cpu.get_reg8('l'), 5)
        self.assertEqual(self.cpu.get_reg8('a'), 6)

    def test_set_reg16(self):
        self.cpu.set_reg16('BC', 0x1234)
        self.cpu.set_reg16('DE', 0x3456)
        self.cpu.set_reg16('HL', 0x5678)

        self.assertEqual(self.cpu.get_reg8('B'), 0x12)
        self.assertEqual(self.cpu.get_reg8('C'), 0x34)
        self.assertEqual(self.cpu.get_reg8('D'), 0x34)
        self.assertEqual(self.cpu.get_reg8('E'), 0x56)
        self.assertEqual(self.cpu.get_reg8('H'), 0x56)
        self.assertEqual(self.cpu.get_reg8('L'), 0x78)

    def test_get_reg16(self):
        self.cpu.set_reg16('BC', 0x1234)
        self.cpu.set_reg16('DE', 0x3456)
        self.cpu.set_reg16('HL', 0x5678)

        self.assertEqual(self.cpu.get_reg16('BC'), 0x1234)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x3456)
        self.assertEqual(self.cpu.get_reg16('HL'), 0x5678)

    def test_set_sp(self):
        self.cpu.set_sp(0x51234)

        self.assertEqual(self.cpu.get_sp(), 0x1234)

    def test_get_sp(self):
        self.cpu.set_sp(0x1234)

        self.assertEqual(self.cpu.get_sp(), self.cpu.sp)

    def test_inc_sp(self):
        self.cpu.set_sp(0x1234)
        self.cpu.inc_sp()

        self.assertEqual(self.cpu.get_sp(), 0x1235)

    def test_set_pc(self):
        self.cpu.set_pc(0x1000)

        self.assertEqual(self.cpu.pc, 0x1000)

    def test_get_pc(self):
        self.cpu.set_pc(0x11000)

        self.assertEqual(self.cpu.get_pc(), 0x1000)

    def test_inc_pc(self):
        self.cpu.set_pc(0xffff)
        self.cpu.inc_pc()

        self.assertEqual(self.cpu.get_pc(), 0x0000)

    def test_nop(self):
        regA = self.cpu.get_reg8('A')
        regB = self.cpu.get_reg8('B')
        regC = self.cpu.get_reg8('C')
        regD = self.cpu.get_reg8('D')
        regE = self.cpu.get_reg8('E')
        regH = self.cpu.get_reg8('H')
        regL = self.cpu.get_reg8('L')

        self.cpu.nop()
        self.cpu.nop()

        self.assertEqual(self.cpu.get_reg8('A'), regA)
        self.assertEqual(self.cpu.get_reg8('B'), regB)
        self.assertEqual(self.cpu.get_reg8('C'), regC)
        self.assertEqual(self.cpu.get_reg8('D'), regD)
        self.assertEqual(self.cpu.get_reg8('E'), regE)
        self.assertEqual(self.cpu.get_reg8('H'), regH)
        self.assertEqual(self.cpu.get_reg8('L'), regL)

    def test_ld_imm8toreg8(self):
        self.cpu.ld_imm8toreg8('B')(0) 
        self.cpu.ld_imm8toreg8('C')(1) 
        self.cpu.ld_imm8toreg8('D')(2) 
        self.cpu.ld_imm8toreg8('E')(3) 
        self.cpu.ld_imm8toreg8('H')(4) 
        self.cpu.ld_imm8toreg8('L')(5) 
        self.cpu.ld_imm8toreg8('A')(6) 

        self.assertEqual(self.cpu.get_reg8('B'), 0)
        self.assertEqual(self.cpu.get_reg8('C'), 1)
        self.assertEqual(self.cpu.get_reg8('D'), 2)
        self.assertEqual(self.cpu.get_reg8('E'), 3)
        self.assertEqual(self.cpu.get_reg8('H'), 4)
        self.assertEqual(self.cpu.get_reg8('L'), 5)
        self.assertEqual(self.cpu.get_reg8('A'), 6)

    def test_ld_reg8toreg8(self):
        self.cpu.set_reg8('B', 0)
        self.cpu.set_reg8('C', 1)
        self.cpu.set_reg8('D', 2)
        self.cpu.set_reg8('E', 3)
        self.cpu.set_reg8('H', 4)
        self.cpu.set_reg8('L', 5)
        self.cpu.set_reg8('A', 6)

        self.cpu.ld_reg8toreg8('B', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0)
        self.cpu.ld_reg8toreg8('C', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 1)
        self.cpu.ld_reg8toreg8('D', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 2)
        self.cpu.ld_reg8toreg8('E', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 3)
        self.cpu.ld_reg8toreg8('H', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 4)
        self.cpu.ld_reg8toreg8('L', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 5)
        self.cpu.ld_reg8toreg8('A', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 6)

        self.cpu.ld_reg8toreg8('C', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 1)
        self.cpu.ld_reg8toreg8('D', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 2)
        self.cpu.ld_reg8toreg8('E', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 3)
        self.cpu.ld_reg8toreg8('H', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 4)
        self.cpu.ld_reg8toreg8('L', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 5)
        self.cpu.ld_reg8toreg8('A', 'C')()
        self.assertEqual(self.cpu.get_reg8('C'), 6)

    def test_ld_reg8toreg16addr(self):
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.set_reg16('bc', 0xc000 + x)
            self.cpu.ld_reg8toreg16addr('a', 'bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xc000 + x), x)

    def test_ld_reg8toreg16addr_2(self):
        self.cpu.set_reg16('bc', 0xc000)
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.ld_reg8toreg16addr('a', 'bc', inc=True)()
            self.assertEqual(self.cpu.mmu.get_addr(0xc000 + x), x)

    def test_ld_reg8toreg16addr_3(self):
        self.cpu.set_reg16('bc', 0xc0ff)
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.ld_reg8toreg16addr('a', 'bc', dec=True)()
            self.assertEqual(self.cpu.mmu.get_addr(0xc0ff - x), x)

    def test_ld_reg8toreg16addr_4(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.ld_reg8toreg16addr('a', 'bc', inc=True, dec=True)()

    def test_ld_reg8toimm16addr(self):
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.ld_reg8toimm16addr('a')(0xc000 + x)
            self.assertEqual(self.cpu.mmu.get_addr(0xc000 + x), x)

    def test_ld_imm16addrtoreg8(self):
        for x in range(256):
            self.cpu.mmu.set_addr(0xd000 + x, x)
            self.cpu.ld_imm16addrtoreg8('c')(0xd000 + x)
            self.assertEqual(self.cpu.get_reg8('c'), x)

    def test_ld_reg16addrtoreg8(self):
        self.cpu.set_reg16('hl', 0xd000)
        for x in range(256):
            self.cpu.mmu.set_addr(0xd000 + x, x)
            self.cpu.ld_reg16addrtoreg8('hl', 'c', inc=True)()
            self.assertEqual(self.cpu.get_reg8('c'), x)

    def test_ld_reg16addrtoreg8_2(self):
        self.cpu.set_reg16('hl', 0xd0ff)
        for x in range(256):
            self.cpu.mmu.set_addr(0xd0ff - x, x)
            self.cpu.ld_reg16addrtoreg8('hl', 'c', dec=True)()
            self.assertEqual(self.cpu.get_reg8('c'), x)

    def test_ld_sptoaddr16(self):
        for x in range(2**10):
            self.cpu.set_sp(x)
            self.cpu.ld_sptoimm16addr(0xd000 + 2*x)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x),
                    self.cpu.get_sp() >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1),
                    self.cpu.get_sp() & 0xff)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x), x >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1),
                    x & 0xff)

    def test_ld_sptoaddr16_2(self):
        for x in range(2**10):
            self.cpu.set_sp(x)
            self.cpu.set_reg16('bc', 0xd000 + 2*x)
            self.cpu.ld_sptoreg16addr('bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x),
                    self.cpu.get_sp() >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1),
                    self.cpu.get_sp() & 0xff)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x), x >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1), x & 0xff)

    def test_ld_imm8toaddrHL(self):
        for x in range(2**8):
            self.cpu.set_reg16('hl', 0xcfff)
            self.cpu.ld_imm8toaddrHL(x)
            self.assertEqual(self.cpu.mmu.get_addr(0xcfff), x)

    def test_ld_imm16toreg16(self):
        self.cpu.ld_imm16toreg16('BC')(0x0123)
        self.cpu.ld_imm16toreg16('DE')(0x4567)
        self.cpu.ld_imm16toreg16('HL')(0x89ab)

        self.assertEqual(self.cpu.get_reg16('BC'), 0x0123)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x4567)
        self.assertEqual(self.cpu.get_reg16('HL'), 0x89ab)

    def test_inc_reg8(self):
        self.cpu.set_reg8('b', 0x04)
        self.cpu.inc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x05)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_inc_reg8_2(self):
        self.cpu.set_reg8('b', 0x0f)
        self.cpu.inc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x10)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_inc_reg8_3(self):
        self.cpu.set_reg8('b', 0xff)
        self.cpu.inc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_inc_reg16(self):
        self.cpu.set_reg16('bc', 0xeeff)
        self.cpu.inc_reg16('bc')()

        self.assertEqual(self.cpu.get_reg16('bc'), 0xef00)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_dec_reg8(self):
        self.cpu.set_reg8('b', 0x04)
        self.cpu.dec_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x03)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)

    def test_dec_reg8_2(self):
        self.cpu.set_reg8('b', 0x10)
        self.cpu.dec_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x0f)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)

    def test_dec_reg8_3(self):
        self.cpu.set_reg8('b', 0x00)
        self.cpu.dec_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)

    def test_dec_reg16(self):
        self.cpu.set_reg16('bc', 0xee)
        self.cpu.dec_reg16('bc')()
        self.assertEqual(self.cpu.get_reg16('bc'), 0xed)

    def test_add_reg16toregHL(self):
        self.cpu.set_reg16('bc', 0xffff)
        self.cpu.set_reg16('hl', 0x0001)
        self.cpu.add_reg16toregHL('bc')()
        self.assertEqual(self.cpu.get_reg16('hl'), 0x0000)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_add_reg8toreg8(self):
        self.cpu.set_reg8('b', 0xfe)
        self.cpu.set_reg8('c', 0x01)
        self.cpu.add_reg8toreg8('c', 'b')()
        self.assertEqual(self.cpu.get_reg8('b'), 0xff)
        self.assertEqual(self.cpu.get_reg8('c'), 0x01)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_add_reg8toreg8_2(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3a)
        self.cpu.set_reg8('b', 0xc6)
        self.cpu.add_reg8toreg8('b', 'a')()
        
        self.assertEqual(self.cpu.get_reg8('a'), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_add_reg8toreg8_withcarry(self):
        """Example from the Gameboy Programming Manual"""

        # TODO: add a test using (HL)

        self.cpu.set_reg8('a', 0xe1)
        self.cpu.set_reg8('e', 0x0f)
        self.cpu.set_carry_flag()
        self.cpu.add_reg8toreg8('e', 'a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0xf1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_reg8fromreg8(self):
        self.cpu.set_reg8('b', 0xff)
        self.cpu.set_reg8('c', 0x11)
        self.cpu.sub_reg8fromreg8('c', 'b')()
        self.assertEqual(self.cpu.get_reg8('c'), 0x11)
        self.assertEqual(self.cpu.get_reg8('b'), 0xee)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

        self.cpu.set_reg8('b', 0x00)
        self.cpu.set_reg8('c', 0x01)
        self.cpu.sub_reg8fromreg8('c', 'b')()
        self.assertEqual(self.cpu.get_reg8('c'), 0x01)
        self.assertEqual(self.cpu.get_reg8('b'), 0xff)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_reg8fromreg8_2(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.set_reg8('e', 0x3e)
        self.cpu.sub_reg8fromreg8('e', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm8fromreg8(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.sub_imm8fromreg8('a')(0x0f)

        self.assertEqual(self.cpu.get_reg8('a'), 0x2f)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm16addrfromreg8(self):
        """Example from the Gameboy Programming Manual"""

        u8 = self.cpu.get_reg8('a')
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(addr16, 0x40)
        self.cpu.sub_imm16addrfromreg8('a')(addr16)

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_reg16addrfromreg8(self):
        """Example from the Gameboy Programming Manual"""

        u8 = self.cpu.get_reg8('a')
        addr16 = 0xc000
        self.cpu.set_reg16('hl', addr16)
        
        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(addr16, 0x40)
        self.cpu.sub_reg16addrfromreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_and_reg8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.set_reg8('b', 0x55)
        self.cpu.and_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_reg8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.set_reg8('l', 0x55)
        self.cpu.and_reg8('l')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_imm8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.and_imm8()(0x55)

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_imm8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.and_imm8()(0x55)

        self.assertEqual(self.cpu.get_reg8('a'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_imm16addr(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.and_imm16addr()(addr16)

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_reg16addr(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.set_reg16('bc', addr16)
        self.cpu.and_reg16addr('bc')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_or_reg8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.set_reg8('b', 0x55)
        self.cpu.or_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_reg8('b'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_or_reg8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.set_reg8('b', 0x55)
        self.cpu.or_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_reg8('b'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_or_imm8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.or_imm8()(0x50)

        self.assertEqual(self.cpu.get_reg8('a'), 0xfa)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_or_imm16addr(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.or_imm16addr()(addr16)

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_or_reg16addr(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.set_reg16('hl', addr16)
        self.cpu.or_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_reg8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.set_reg8('h', 0x55)
        self.cpu.xor_reg8('h')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_reg8('h'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_reg8_2(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.set_reg8('b', 0xaa)
        self.cpu.xor_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_reg8('b'), 0xaa)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_imm8(self):
        self.cpu.set_reg8('a', 0x55)
        self.cpu.xor_imm8()(0xaa)

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_imm16addr(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(0xc000, 0xaa)
        self.cpu.xor_imm16addr()(0xc000)

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_imm16addr(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(0xc000, 0x55)
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.xor_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_cp_reg8toreg8(self):
        self.cpu.set_reg8('b', 0x5d)
        self.cpu.set_reg8('d', 0x4d)
        self.cpu.cp_reg8toreg8('b', 'd')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x5d)
        self.assertEqual(self.cpu.get_reg8('d'), 0x4d)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_cp_reg8toreg8_2(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3c)
        self.cpu.set_reg8('b', 0x2f)
        self.cpu.cp_reg8toreg8('a', 'b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.get_reg8('b'), 0x2f)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

        self.cpu.cp_reg8toreg8('b', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.get_reg8('b'), 0x2f)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_cp_reg8toreg8_3(self):
        self.cpu.set_reg8('a', 0x3c)
        self.cpu.set_reg8('b', 0x3c)
        self.cpu.cp_reg8toreg8('a', 'b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.get_reg8('b'), 0x3c)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_cp_reg8toimm16addr(self):
        """Example from the Gameboy Programming Manual"""

        addr16 = 0xc000

        self.cpu.set_reg8('a', 0x3c)
        self.cpu.mmu.set_addr(addr16, 0x40)
        self.cpu.cp_reg8toimm16addr('a')(addr16)

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.mmu.get_addr(addr16), 0x40)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_cp_reg8toreg16addr(self):
        """Example from the Gameboy Programming Manual"""

        addr16 = 0xc000

        self.cpu.set_reg8('a', 0x3c)
        self.cpu.mmu.set_addr(addr16, 0x40)
        self.cpu.set_reg16('hl', addr16)
        self.cpu.cp_reg8toreg16addr('a', 'hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.mmu.get_addr(addr16), 0x40)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)


    def test_rl_reg8(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x95)
        self.cpu.set_carry_flag()
        self.cpu.rl_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x2b)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rlc_reg8(self):
        """Example from the Gameboy Programming Manual
        correction: result should be 0x0b, not 0x0a"""

        self.cpu.set_reg8('a', 0x85)
        self.cpu.reset_carry_flag()
        self.cpu.rlc_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x0b)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rr_reg8(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x81)
        self.cpu.reset_carry_flag()
        self.cpu.rr_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x40)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rrc_reg8(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3b)
        self.cpu.reset_carry_flag()
        self.cpu.rrc_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x9d)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sla_reg8(self):
        # TODO
        raise NotImplementedError('sla_reg8')

    def test_sla_addr16(self):
        # TODO
        raise NotImplementedError('sla_addr16')

    def test_sra_reg8(self):
        # TODO
        raise NotImplementedError('sla_reg8')

    def test_sra_addr16(self):
        # TODO
        raise NotImplementedError('sla_addr16')

    def test_cpl(self):
        self.cpu.set_reg8('a', 0x55)

        self.cpu.cpl()

        self.assertEqual(self.cpu.get_reg8('a'), 0xaa)

    def test_daa(self):
        # 28 = 0x1c
        self.cpu.set_reg8('a', 28)
        self.cpu.daa()

        self.assertEqual(self.cpu.get_reg8('a'), 0x28)

    def test_scf(self):
        self.cpu.reset_carry_flag()
        self.cpu.scf()

        self.assertEqual(self.cpu.get_carry_flag(), 1)

        self.cpu.scf()

        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_ccf(self):
        self.cpu.set_carry_flag()
        self.cpu.ccf()

        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_jr_imm8(self):
        self.cpu.set_pc(0x1000)
        self.cpu.jr_imm8(0x22)

        self.assertEqual(self.cpu.get_pc(), 0x1022)

    def test_jr_imm8_2(self):
        self.cpu.set_pc(0x1000)
        self.cpu.jr_imm8(0xe0)

        self.assertEqual(self.cpu.get_pc(), 0x0fe0)

    def test_jr_condtoimm8(self):
        self.cpu.set_pc(0x1000)
        self.cpu.reset_zero_flag()
        self.cpu.jr_condtoimm8('NZ')(0x20)

        self.assertEqual(self.cpu.get_pc(), 0x1020)

        self.cpu.set_zero_flag()
        self.cpu.jr_condtoimm8('Z')(0x20)

        self.assertEqual(self.cpu.get_pc(), 0x1040)

        self.cpu.reset_carry_flag()
        self.cpu.jr_condtoimm8('NC')(0x20)

        self.assertEqual(self.cpu.get_pc(), 0x1060)

        self.cpu.set_carry_flag()
        self.cpu.jr_condtoimm8('C')(0x20)

        self.assertEqual(self.cpu.get_pc(), 0x1080)

    def test_jp_imm16addr(self):
        self.cpu.set_pc(0xc000)
        self.cpu.jp_imm16addr(0xd000)

        self.assertEqual(self.cpu.get_pc(), 0xd000)

    def test_jp_reg16addr(self):
        self.cpu.set_pc(0xc000)
        self.cpu.set_reg16('hl', 0xd000)
        self.cpu.jp_reg16addr('hl')()

        self.assertEqual(self.cpu.get_pc(), 0xd000)

    def test_jp_condtoaddr16(self):
        self.cpu.set_pc(0xc000)
        self.cpu.reset_zero_flag()
        self.cpu.jp_condtoaddr16('NZ')(0xd000)

        self.assertEqual(self.cpu.get_pc(), 0xd000)

        self.cpu.set_zero_flag()
        self.cpu.jp_condtoaddr16('Z')(0xe000)

        self.assertEqual(self.cpu.get_pc(), 0xe000)

        self.cpu.reset_carry_flag()
        self.cpu.jp_condtoaddr16('NC')(0xf000)

        self.assertEqual(self.cpu.get_pc(), 0xf000)

        self.cpu.set_carry_flag()
        self.cpu.jp_condtoaddr16('C')(0xd000)
        self.assertEqual(self.cpu.get_pc(), 0xd000)

    def test_ret(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret()()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.get_sp(), 0xd002)

    def test_ret_cond(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret(cond='z')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)

        self.cpu.set_zero_flag()
        self.cpu.ret(cond='z')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.get_sp(), 0xd002)

    def test_ret_cond_2(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret(cond='c')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)

        self.cpu.set_carry_flag()
        self.cpu.ret(cond='c')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.get_sp(), 0xd002)

    def test_ret_cond_3(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret(cond='s')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)

        self.cpu.set_sub_flag()
        self.cpu.ret(cond='s')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.get_sp(), 0xd002)

    def test_ret_cond_4(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret(cond='h')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)

        self.cpu.set_halfcarry_flag()
        self.cpu.ret(cond='h')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.get_sp(), 0xd002)

    def test_reti(self):
        raise NotImplementedError('test_reti')

    def test_call_imm16addr(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)

        self.cpu.call_imm16addr()(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_call_imm16addr_z(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)

        self.cpu.call_imm16addr('z')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x00)

        self.cpu.set_zero_flag()

        self.cpu.call_imm16addr('z')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_call_condtoimm16addr_c(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)

        self.cpu.call_imm16addr('c')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x00)

        self.cpu.set_carry_flag()

        self.cpu.call_imm16addr('c')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_call_condtoimm16addr_s(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)

        self.cpu.call_imm16addr('s')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x00)

        self.cpu.set_sub_flag()

        self.cpu.call_imm16addr('s')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_call_condtoimm16addr_h(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)

        self.cpu.call_imm16addr('h')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.get_sp(), 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x00)

        self.cpu.set_halfcarry_flag()

        self.cpu.call_imm16addr('h')(0x2000)

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_call_reg16addr(self):
        self.cpu.set_pc(0x1234)
        self.cpu.set_sp(0xd000)
        self.cpu.set_reg16('hl', 0x2000)

        self.cpu.call_reg16addr('hl')()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.get_sp(), 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp() + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_sp()), 0x34)

    def test_stop(self):
        # TODO
        # for now, just make sure no exceptions are raised. later, we want to
        # check that the CPU waited the appropriate number of cycles.

        self.cpu.stop()

    def test_halt(self):
        # TODO
        # for now, just make sure no exceptions are raised. later, we want to
        # check that the CPU waited the appropriate number of cycles.

        self.cpu.halt()


