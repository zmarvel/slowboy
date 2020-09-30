import unittest

import slowboy.z80


class TestZ80(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()

    def test_init(self):
        self.assertEqual(self.cpu.pc, 0x100)
        self.assertEqual(self.cpu.sp, 0xfffe)
        self.assertEqual(self.cpu.registers['a'], 0x01)
        self.assertEqual(self.cpu.registers['f'], 0xb0)
        self.assertEqual(self.cpu.registers['b'], 0x00)
        self.assertEqual(self.cpu.registers['c'], 0x13)
        self.assertEqual(self.cpu.registers['d'], 0x00)
        self.assertEqual(self.cpu.registers['e'], 0xd8)
        self.assertEqual(self.cpu.registers['h'], 0x01)
        self.assertEqual(self.cpu.registers['l'], 0x4d)
        self.assertEqual(self.cpu.state, slowboy.z80.State.STOP)

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

    def test_set_reg8_invalid_argument(self):
        with self.assertRaises(KeyError) as cm:
            self.cpu.set_reg8('BC', 0xbc)

        with self.assertRaises(KeyError) as cm:
            self.cpu.set_reg8('de', 0xde)

        with self.assertRaises(KeyError) as cm:
            self.cpu.set_reg8('HL', 0xbc)

        with self.assertRaises(KeyError) as cm:
            self.cpu.set_reg8('sp', 0xde)

        with self.assertRaises(KeyError) as cm:
            self.cpu.set_reg8('PC', 0xff)

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

    def test_get_reg8_invalid_argument(self):
        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('BC')

        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('de')

        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('HL')

        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('sp')

        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('PC')

        with self.assertRaises(KeyError) as cm:
            self.cpu.get_reg8('x')

    def test_set_reg16(self):
        self.cpu.set_reg16('BC', 0x1234)
        self.cpu.set_reg16('DE', 0x3456)
        self.cpu.set_reg16('HL', 0x5678)
        self.assertEqual(self.cpu.get_reg8('f'), 0xb0)
        self.cpu.set_reg16('af', 0xabcd)

        self.assertEqual(self.cpu.get_reg8('B'), 0x12)
        self.assertEqual(self.cpu.get_reg8('C'), 0x34)
        self.assertEqual(self.cpu.get_reg8('D'), 0x34)
        self.assertEqual(self.cpu.get_reg8('E'), 0x56)
        self.assertEqual(self.cpu.get_reg8('H'), 0x56)
        self.assertEqual(self.cpu.get_reg8('L'), 0x78)
        self.assertEqual(self.cpu.get_reg8('a'), 0xab)
        # f is not writable, so should remain unchanged
        self.assertEqual(self.cpu.get_reg8('f'), 0xb0)

    def test_get_reg16(self):
        self.cpu.set_reg16('BC', 0x1234)
        self.cpu.set_reg16('DE', 0x3456)
        self.cpu.set_reg16('HL', 0x5678)
        self.cpu.sp = 0x7fff

        self.assertEqual(self.cpu.get_reg16('BC'), 0x1234)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x3456)
        self.assertEqual(self.cpu.get_reg16('HL'), 0x5678)
        self.assertEqual(self.cpu.get_reg16('sp'), 0x7fff)

    def test_set_sp(self):
        self.cpu.sp = 0x51234

        self.assertEqual(self.cpu.sp, 0x1234)

    def test_get_sp(self):
        self.cpu.sp = 0x1234

        self.assertEqual(self.cpu.sp, self.cpu.sp)

    def test_inc_sp(self):
        self.cpu.sp = 0x1234
        self.cpu.inc_sp()

        self.assertEqual(self.cpu.sp, 0x1235)

    def test_set_pc(self):
        self.cpu.pc = 0x1000

        self.assertEqual(self.cpu.pc, 0x1000)

    def test_get_pc(self):
        self.cpu.pc = 0x11000

        self.assertEqual(self.cpu.get_pc(), 0x1000)

    def test_inc_pc(self):
        self.cpu.pc = 0xffff
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

class TestZ80LoadStore(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()
        self.cpu.pc = 0

    def test_ld_imm8toreg8(self):
        self.cpu.mmu.rom = bytes([0, 1, 2, 3, 4, 5, 6])
        self.cpu.ld_imm8toreg8('B')()
        self.cpu.ld_imm8toreg8('C')()
        self.cpu.ld_imm8toreg8('D')()
        self.cpu.ld_imm8toreg8('E')()
        self.cpu.ld_imm8toreg8('H')()
        self.cpu.ld_imm8toreg8('L')()
        self.cpu.ld_imm8toreg8('A')()

        self.assertEqual(self.cpu.get_reg8('B'), 0)
        self.assertEqual(self.cpu.get_reg8('C'), 1)
        self.assertEqual(self.cpu.get_reg8('D'), 2)
        self.assertEqual(self.cpu.get_reg8('E'), 3)
        self.assertEqual(self.cpu.get_reg8('H'), 4)
        self.assertEqual(self.cpu.get_reg8('L'), 5)
        self.assertEqual(self.cpu.get_reg8('A'), 6)

    def test_ld_imm8toreg8_invalid_register(self):
        self.cpu.mmu.rom = bytes([0, 1, 2, 3, 4, 5, 6])
        with self.assertRaises(KeyError) as cm:
            self.cpu.ld_imm8toreg8('BC')()

    def test_ld_reg8toreg8(self):
        self.cpu.set_reg8('B', 0x00)
        self.cpu.set_reg8('C', 0x11)
        self.cpu.set_reg8('D', 0x22)
        self.cpu.set_reg8('E', 0x33)
        self.cpu.set_reg8('H', 0x44)
        self.cpu.set_reg8('L', 0x55)
        self.cpu.set_reg8('A', 0x66)

        self.cpu.ld_reg8toreg8('B', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x00)
        self.cpu.ld_reg8toreg8('C', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x11)
        self.cpu.ld_reg8toreg8('D', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x22)
        self.cpu.ld_reg8toreg8('E', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x33)
        self.cpu.ld_reg8toreg8('H', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x44)
        self.cpu.ld_reg8toreg8('L', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x55)
        self.cpu.ld_reg8toreg8('A', 'B')()
        self.assertEqual(self.cpu.get_reg8('B'), 0x66)

    def test_ld_reg8toreg8_invalid_register(self):
        with self.assertRaises(KeyError) as cm:
            self.cpu.ld_reg8toreg8('C', 'BC')()

        with self.assertRaises(KeyError) as cm:
            self.cpu.ld_reg8toreg8('BC', 'C')()

    def test_ld_reg8toreg16addr(self):
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.set_reg16('bc', 0xc000 + x)
            self.cpu.ld_reg8toreg16addr('a', 'bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xc000 + x), x)
            self.assertEqual(self.cpu.get_reg16('bc'), 0xc000 + x)

    def test_ld_reg8toreg16addr_inc(self):
        self.cpu.set_reg8('b', 0xfd)
        self.cpu.set_reg16('de', 0xcfff)
        self.cpu.ld_reg8toreg16addr_inc('b', 'de')()
        self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 0xfd)
        self.assertEqual(self.cpu.get_reg8('b'), 0xfd)
        self.assertEqual(self.cpu.get_reg16('de'), 0xd000)

    def test_ld_reg8toreg16addr_dec(self):
        self.cpu.set_reg8('b', 0xfd)
        self.cpu.set_reg16('de', 0xcfff)
        self.cpu.ld_reg8toreg16addr_dec('b', 'de')()
        self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 0xfd)
        self.assertEqual(self.cpu.get_reg8('b'), 0xfd)
        self.assertEqual(self.cpu.get_reg16('de'), 0xcffe)

    def test_ld_reg8toreg16addr_2(self):
        self.cpu.set_reg16('bc', 0xc000)
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.ld_reg8toreg16addr_inc('a', 'bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xc000 + x), x)

    def test_ld_reg8toreg16addr_3(self):
        self.cpu.set_reg16('bc', 0xc0ff)
        for x in range(256):
            self.cpu.set_reg8('a', x)
            self.cpu.ld_reg8toreg16addr_dec('a', 'bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xc0ff - x), x)

    def test_ld_reg8toimm16addr(self):
        self.cpu.set_reg8('a', 0xab)
        self.cpu.mmu.rom = bytes([0x00, 0xc0])
        self.cpu.ld_reg8toimm16addr('a')()
        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0xab)

    def test_ld_imm16addrtoreg8(self):
        self.cpu.mmu.set_addr(0xd000, 0xab)
        self.cpu.mmu.rom = bytes([0x00, 0xd0])
        self.cpu.ld_imm16addrtoreg8('c')()
        self.assertEqual(self.cpu.get_reg8('c'), 0xab)

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

    def test_ld_reg16addrtoreg8_3(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.set_reg16('hl', 0xd000)
            self.cpu.mmu.set_addr(0xd000, 3)
            self.cpu.ld_reg16addrtoreg8('hl', 'c', inc=True, dec=True)()

    def test_ld_reg16addrtoreg8_4(self):
        self.cpu.set_reg16('hl', 0xd000)
        self.cpu.mmu.set_addr(0xd000, 0x53)
        self.cpu.ld_reg16addrtoreg8('hl', 'c')()
        self.assertEqual(self.cpu.get_reg8('c'), 0x53)

    def test_ld_reg16toreg16(self):
        self.cpu.set_reg16('hl', 0x7654)

        self.cpu.ld_reg16toreg16('hl', 'sp')()

        self.assertEqual(self.cpu.sp, 0x7654)

    def test_ld_spimm8toregHL(self):
        self.cpu.sp = 0x7000
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x80])

        self.cpu.ld_spimm8toregHL()

        self.assertEqual(self.cpu.get_reg16('hl'), 0x7080)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_ld_spimm8toregHL_2(self):
        # Make sure carry and half-carry get set
        self.cpu.sp = 0x7001
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0xff])

        self.cpu.ld_spimm8toregHL()

        self.assertEqual(self.cpu.get_reg16('hl'), 0x7100)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)


    def test_ld_sptoimm16addr(self):
        self.cpu.sp = 0x1234
        self.cpu.mmu.rom = bytes([0x00, 0xd0])
        self.cpu.ld_sptoimm16addr()
        self.assertEqual(self.cpu.get_pc(), 2)
        self.assertEqual(self.cpu.mmu.get_addr(0xd000),
                self.cpu.sp >> 8)
        self.assertEqual(self.cpu.mmu.get_addr(0xd001),
                self.cpu.sp & 0xff)
        self.assertEqual(self.cpu.mmu.get_addr(0xd000), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(0xd001), 0x34)

    def test_ld_sptoaddr16_2(self):
        for x in range(2**10):
            self.cpu.sp = x
            self.cpu.set_reg16('bc', 0xd000 + 2*x)
            self.cpu.ld_sptoreg16addr('bc')()
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x),
                    self.cpu.sp >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1),
                    self.cpu.sp & 0xff)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x), x >> 8)
            self.assertEqual(self.cpu.mmu.get_addr(0xd000 + 2*x + 1), x & 0xff)

    def test_ld_imm8toaddrHL(self):
        self.cpu.mmu.rom = bytes([0, 255, 127])
        self.cpu.set_reg16('hl', 0xcfff)
        self.cpu.ld_imm8toaddrHL()
        self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 0)
        self.cpu.ld_imm8toaddrHL()
        self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 255)
        self.cpu.ld_imm8toaddrHL()
        self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 127)

    def test_ld_imm16toreg16(self):
        self.cpu.mmu.rom = bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xab])
        self.cpu.ld_imm16toreg16('BC')()
        self.cpu.ld_imm16toreg16('DE')()
        self.cpu.ld_imm16toreg16('HL')()

        self.assertEqual(self.cpu.get_reg16('BC'), 0x2301)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x6745)
        self.assertEqual(self.cpu.get_reg16('HL'), 0xab89)

    def test_push_reg16(self):
        self.cpu.set_reg16('sp', 0xc002)
        self.cpu.set_reg16('bc', 0x1234)

        self.cpu.push_reg16('bc')()

        self.assertEqual(self.cpu.sp, 0xc000)
        self.assertEqual(self.cpu.mmu.get_addr(0xc001), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x34)

    def test_pop_reg16(self):
        self.cpu.set_reg16('sp', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x34)
        self.cpu.mmu.set_addr(0xc001, 0x12)

        self.cpu.pop_reg16('bc')()

        self.assertEqual(self.cpu.sp, 0xc002)
        self.assertEqual(self.cpu.get_reg16('bc'), 0x1234)

    def test_ldh_regAtoaddr8(self):
        # JOYP register---bits 4 and 5 are writable
        self.cpu.pc = 0xc000
        self.cpu.mmu.set_addr(0xc000, 0x00)
        self.cpu.set_reg8('a', 0x30)

        self.cpu.ldh_regAtoaddr8()

        # Bits 0-3 indicate pressed buttons (active low)
        self.assertEqual(self.cpu.mmu.get_addr(0xff00), 0x30 | 0x0f)

    def test_ldh_addr8toregA(self):
        self.cpu.pc = 0xc000
        self.cpu.mmu.set_addr(0xc000, 0x00)
        # JOYP register---bits 4 and 5 are writable
        self.cpu.mmu.set_addr(0xff00, 0x30)

        self.cpu.ldh_addr8toregA()

        # Bits 0-3 indicate pressed buttons (active low)
        self.assertEqual(self.cpu.get_reg8('a'), 0x30 | 0x0f)

    def test_ldh_regAtoaddrC(self):
        # JOYP register---bits 4 and 5 are writable
        self.cpu.set_reg8('a', 0x30)
        self.cpu.set_reg8('c', 0x00)

        self.cpu.ldh_regAtoaddrC()

        # Bits 0-3 indicate pressed buttons (active low)
        self.assertEqual(self.cpu.mmu.get_addr(0xff00), 0x30 | 0x0f)

    def test_ldh_addrCtoregA(self):
        # JOYP register---bits 4 and 5 are writable
        self.cpu.mmu.set_addr(0xff00, 0x30)
        self.cpu.set_reg8('c', 0x00)

        self.cpu.ldh_addrCtoregA()

        # Bits 0-3 indicate pressed buttons (active low)
        self.assertEqual(self.cpu.get_reg8('a'), 0x30 | 0x0f)


class TestZ80ALU(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()
        self.cpu.pc = 0

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

        c = self.cpu.get_carry_flag()
        h = self.cpu.get_halfcarry_flag()
        s = self.cpu.get_sub_flag()
        z = self.cpu.get_zero_flag()
        self.assertEqual(self.cpu.get_reg16('bc'), 0xef00)
        self.assertEqual(self.cpu.get_carry_flag(), c)
        self.assertEqual(self.cpu.get_halfcarry_flag(), h)
        self.assertEqual(self.cpu.get_sub_flag(), s)
        self.assertEqual(self.cpu.get_zero_flag(), z)

    def test_inc_addrHL(self):
        # From the Game Boy Programming Manual
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x50)

        self.cpu.inc_addrHL()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x51)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_inc_addrHL_2(self):
        # Make sure half-carry and zero flags get set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0xff)

        self.cpu.inc_addrHL()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
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
        # Make sure zero flag gets set
        self.cpu.set_reg8('b', 0x01)

        self.cpu.dec_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)

    def test_dec_reg8_4(self):
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

    def test_dec_addrHL(self):
        # Example from the Game Boy Programming Manual
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x00)

        self.cpu.dec_addrHL()

        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0xff)

    def test_dec_addrHL_2(self):
        # Make sure zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x01)

        self.cpu.dec_addrHL()

        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)


    def test_add_imm8toreg8(self):
        self.cpu.set_reg8('a', 0xaf)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x11])

        self.cpu.add_imm8toreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xc0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)

    def test_add_imm8toreg8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x01])

        self.cpu.add_imm8toreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_add_imm8toreg8_3(self):
        self.cpu.set_reg8('a', 0xf0)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x10])

        self.cpu.add_imm8toreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_add_imm8toreg8_4(self):
        # add with carry
        self.cpu.set_reg8('a', 0xf0)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x10])
        self.cpu.set_carry_flag()

        self.cpu.add_imm8toreg8('a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0x01)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)

    def test_add_imm8toregSP(self):
        self.cpu.sp = 0x7000
        self.cpu.mmu.rom = bytes([0xfe])

        self.cpu.add_imm8toregSP()

        # Signed add
        self.assertEqual(self.cpu.sp, 0x6ffe)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_add_reg16addrtoreg8(self):
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x11)
        self.cpu.set_reg8('a', 0x3f)

        self.cpu.add_reg16addrtoreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x50)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_add_reg16addrtoreg8_2(self):
        # Make sure carry flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0xd0)
        self.cpu.set_reg8('a', 0x3f)

        self.cpu.add_reg16addrtoreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x0f)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_add_reg16addrtoreg8_3(self):
        # Make sure zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0xc1)
        self.cpu.set_reg8('a', 0x3f)

        self.cpu.add_reg16addrtoreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_add_reg16addrtoreg8_4(self):
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0xc0)
        self.cpu.set_reg8('a', 0x3f)

        self.cpu.add_reg16addrtoreg8('hl', 'a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_add_imm8toregSP_2(self):
        self.cpu.sp = 0x70fe
        self.cpu.mmu.rom = bytes([0x02])

        self.cpu.add_imm8toregSP()

        self.assertEqual(self.cpu.sp, 0x7100)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_add_reg16toregHL(self):
        self.cpu.set_reg16('bc', 0xffff)
        self.cpu.set_reg16('hl', 0x0001)
        self.cpu.add_reg16toregHL('bc')()
        self.assertEqual(self.cpu.get_reg16('hl'), 0x0000)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)

    def test_add_reg16toregHL_2(self):
        # Make sure carry and half-carry are not set
        self.cpu.set_reg16('bc', 0xffee)
        self.cpu.set_reg16('hl', 0x0011)

        self.cpu.add_reg16toregHL('bc')()

        self.assertEqual(self.cpu.get_reg16('hl'), 0xffff)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

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
        self.assertEqual(self.cpu.get_sub_flag(), 1)

        self.cpu.set_reg8('b', 0x00)
        self.cpu.set_reg8('c', 0x01)
        self.cpu.sub_reg8fromreg8('c', 'b')()
        self.assertEqual(self.cpu.get_reg8('c'), 0x01)
        self.assertEqual(self.cpu.get_reg8('b'), 0xff)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)

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

    def test_sub_reg8fromreg8_3(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3b)
        self.cpu.set_reg8('h', 0x2a)

        self.cpu.sub_reg8fromreg8('h', 'a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0x10)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm8fromreg8(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.rom = bytes([0x0f])

        self.cpu.sub_imm8fromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x2f)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm8fromreg8_2(self):
        # Make sure zero flag gets set
        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.rom = bytes([0x3e])

        self.cpu.sub_imm8fromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm8fromreg8_3(self):
        # Make sure carry flag gets set
        self.cpu.set_reg8('a', 0x00)
        self.cpu.mmu.rom = bytes([0x3e])

        self.cpu.sub_imm8fromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xc2)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_imm8fromreg8_4(self):
        self.cpu.set_reg8('a', 0x00)
        self.cpu.mmu.rom = bytes([0x3e])
        self.cpu.set_carry_flag()

        self.cpu.sub_imm8fromreg8('a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0xc1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_imm16addrfromreg8(self):
        """Example from the Gameboy Programming Manual"""

        u8 = self.cpu.get_reg8('a')
        self.cpu.mmu.rom = bytes([0x00, 0xc0])

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(0xc000, 0x40)
        self.cpu.sub_imm16addrfromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_imm16addrfromreg8_2(self):
        # Make sure the zero flag gets set
        u8 = self.cpu.get_reg8('a')
        self.cpu.mmu.rom = bytes([0x00, 0xc0])

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(0xc000, 0x3e)
        self.cpu.sub_imm16addrfromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_imm16addrfromreg8_3(self):
        # Make sure the half-carry flag gets set
        self.cpu.mmu.rom = bytes([0x00, 0xc0])

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(0xc000, 0x3f)
        self.cpu.sub_imm16addrfromreg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_imm16addrfromreg8_4(self):
        # Make sure the half-carry flag gets set
        u8 = self.cpu.get_reg8('a')
        self.cpu.mmu.rom = bytes([0x00, 0xc0])
        self.cpu.set_carry_flag()

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(0xc000, 0x3e)
        self.cpu.sub_imm16addrfromreg8('a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_reg16addrfromreg8(self):
        """Example from the Gameboy Programming Manual"""

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

    def test_sub_reg16addrfromreg8_2(self):
        # Make sure the zero flag gets set
        addr16 = 0xc000
        self.cpu.set_reg16('hl', addr16)

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(addr16, 0x3e)
        self.cpu.sub_reg16addrfromreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sub_reg16addrfromreg8_3(self):
        # Make sure the half-carry flag gets set
        addr16 = 0xc000
        self.cpu.set_reg16('hl', addr16)

        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(addr16, 0x3f)
        self.cpu.sub_reg16addrfromreg8('hl', 'a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sub_reg16addrfromreg8_4(self):
        addr16 = 0xc000
        self.cpu.set_reg16('hl', addr16)
        self.cpu.set_reg8('a', 0x3e)
        self.cpu.mmu.set_addr(addr16, 0x3e)

        self.cpu.sub_reg16addrfromreg8('hl', 'a', carry=True)()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_and_reg8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.set_reg8('b', 0x55)
        self.cpu.and_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
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
        self.cpu.mmu.rom = bytes([0x55])
        self.cpu.and_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_imm8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.mmu.rom = bytes([0x55])
        self.cpu.and_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
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
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_and_reg16addr_2(self):
        # Make sure the zero flag is not set
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xa1)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.set_reg16('bc', addr16)
        self.cpu.and_reg16addr('bc')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x1)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
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
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_reg8_2(self):
        self.cpu.set_reg8('a', 0xff)
        self.cpu.set_reg8('b', 0x55)
        self.cpu.or_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_reg8('b'), 0x55)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_reg8_3(self):
        self.cpu.set_reg8('a', 0x00)
        self.cpu.set_reg8('b', 0x00)
        self.cpu.or_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_or_imm8(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.rom = bytes([0x50])
        self.cpu.or_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfa)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_imm8_2(self):
        self.cpu.set_reg8('a', 0x00)
        self.cpu.mmu.rom = bytes([0x00])
        self.cpu.or_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_imm16addr(self):
        self.cpu.mmu.rom = bytes([0x00, 0xc0])

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(0xc000, 0x55)
        self.cpu.or_imm16addr()()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_imm16addr_2(self):
        self.cpu.mmu.rom = bytes([0x00, 0xc0])

        self.cpu.set_reg8('a', 0x00)
        self.cpu.mmu.set_addr(0xc000, 0x00)
        self.cpu.or_imm16addr()()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_reg16addr(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(addr16, 0x55)
        self.cpu.set_reg16('hl', addr16)
        self.cpu.or_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

    def test_or_reg16addr_2(self):
        addr16 = 0xc000

        self.cpu.set_reg8('a', 0x00)
        self.cpu.mmu.set_addr(addr16, 0x00)
        self.cpu.set_reg16('hl', addr16)
        self.cpu.or_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)

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
        self.cpu.mmu.rom = bytes([0xaa])
        self.cpu.xor_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_imm8_2(self):
        self.cpu.set_reg8('a', 0x55)
        self.cpu.mmu.rom = bytes([0x55])
        self.cpu.xor_imm8()()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_reg16addr(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(0xc000, 0x55)
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.xor_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0xff)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_xor_reg16addr_2(self):
        self.cpu.set_reg8('a', 0xaa)
        self.cpu.mmu.set_addr(0xc000, 0xaa)
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.xor_reg16addr('hl')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
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

    def test_cp_regAtoregHLaddr(self):
        """Example from the Gameboy Programming Manual"""

        addr16 = 0xc000

        self.cpu.set_reg8('a', 0x3c)
        self.cpu.mmu.set_addr(addr16, 0x40)
        self.cpu.set_reg16('hl', addr16)
        self.cpu.cp_regAtoregHLaddr()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.mmu.get_addr(addr16), 0x40)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_cp_regAtoregHLaddr_2(self):
        addr16 = 0xc000
        self.cpu.set_reg8('a', 0x3c)
        self.cpu.mmu.set_addr(addr16, 0x3c)
        self.cpu.set_reg16('hl', addr16)

        self.cpu.cp_regAtoregHLaddr()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.mmu.get_addr(addr16), 0x3c)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_cp_regAtoregHLaddr_3(self):
        addr16 = 0xc000
        self.cpu.set_reg8('a', 0x3c)
        self.cpu.mmu.set_addr(addr16, 0x2c)
        self.cpu.set_reg16('hl', addr16)

        self.cpu.cp_regAtoregHLaddr()

        self.assertEqual(self.cpu.get_reg8('a'), 0x3c)
        self.assertEqual(self.cpu.mmu.get_addr(addr16), 0x2c)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_cp_imm8toregA(self):
        # When the immediate is the same as the contents of register A, the
        # zero flag is set

        self.cpu.set_reg8('a', 0xfe)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0xfe])

        self.cpu.cp_imm8toregA()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_cp_imm8toregA_2(self):
        # When the immediate is greater than the contents of register A, the
        # carry flag is set

        self.cpu.set_reg8('a', 0xfe)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0xff])

        self.cpu.cp_imm8toregA()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_cp_imm8toregA_3(self):
        # When the immediate is less than the contents of register A, the
        # half-carry flag is set

        self.cpu.set_reg8('a', 0xfe)
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0xfc])

        self.cpu.cp_imm8toregA()

        self.assertEqual(self.cpu.get_reg8('a'), 0xfe)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_rl_reg8_1(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x95)
        self.cpu.set_carry_flag()
        self.cpu.rl_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x2b)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rl_reg8_2(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.reset_carry_flag()
        self.cpu.rl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x4a)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rl_reg8_3(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.set_carry_flag()
        self.cpu.rl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x4b)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rl_reg8_4(self):
        # Make sure the zero flag is set
        self.cpu.set_reg8('b', 0x00)
        self.cpu.reset_carry_flag()
        self.cpu.rl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rl_regHLaddr_1(self):
        # Make sure zero and carry flags are set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x80)
        self.cpu.reset_carry_flag()

        self.cpu.rl_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rl_regHLaddr_2(self):
        # Make sure zero and carry flags are not set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x08)
        self.cpu.set_carry_flag()

        self.cpu.rl_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x11)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rlc_reg8_1(self):
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

    def test_rlc_reg8_2(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.reset_carry_flag()
        self.cpu.rlc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x4b)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rlc_reg8_3(self):
        # Make sure the zero flag is set
        self.cpu.set_reg8('b', 0x00)
        self.cpu.set_zero_flag()

        self.cpu.rlc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_rlc_reg8_4(self):
        # Make sure the carry flag is not set
        self.cpu.set_reg8('b', 0x0a)
        self.cpu.set_carry_flag()

        self.cpu.rlc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x14)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)

    def test_rlc_regHLaddr_1(self):
        # Make sure the zero flag is set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x00)

        self.cpu.rlc_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_rlc_regHLaddr_2(self):
        # Make sure the carry flag is set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x88)

        self.cpu.rlc_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x11)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rr_reg8_1(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x81)
        self.cpu.reset_carry_flag()
        self.cpu.rr_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x40)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rr_reg8_2(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.reset_carry_flag()
        self.cpu.rr_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x52)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rr_reg8_3(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.set_carry_flag()
        self.cpu.rr_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rr_reg8_4(self):
        # Make sure zero flag gets set
        self.cpu.set_reg8('b', 0x01)
        self.cpu.set_zero_flag()
        self.cpu.reset_carry_flag()

        self.cpu.rr_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_rr_reg8_5(self):
        # Make sure carry flag does not get set
        self.cpu.set_reg8('b', 0x10)
        self.cpu.set_zero_flag()
        self.cpu.reset_carry_flag()

        self.cpu.rr_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x08)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 0)

    def test_rr_regHLaddr_1(self):
        # Make sure zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x01)
        self.cpu.reset_carry_flag()

        self.cpu.rr_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rr_regHLaddr_2(self):
        # Make sure carry flag does not get set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x10)
        self.cpu.reset_carry_flag()

        self.cpu.rr_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x08)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rrc_reg8_1(self):
        """Example from the Gameboy Programming Manual"""

        self.cpu.set_reg8('a', 0x3b)
        self.cpu.reset_carry_flag()
        self.cpu.rrc_reg8('a')()

        self.assertEqual(self.cpu.get_reg8('a'), 0x9d)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rrc_reg8_2(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.rrc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_rrc_reg8_3(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg8('b', 0x00)
        self.cpu.set_carry_flag()

        self.cpu.rrc_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rrc_regHLaddr(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x00)

        self.cpu.rrc_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_rrc_regHLaddr_2(self):
        # Make sure the carry flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x01)

        self.cpu.rrc_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x80)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_sla_reg8_1(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.sla_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x4a)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sla_reg8_2(self):
        self.cpu.set_reg8('b', 0x25)
        self.cpu.sla_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x4a)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sla_reg8_3(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg8('b', 0x80)

        self.cpu.sla_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_sla_regHLaddr_1(self):
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0xa5)
        self.cpu.set_reg16('hl', addr)
        self.cpu.sla_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x4a)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sla_regHLaddr_2(self):
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0x25)
        self.cpu.set_reg16('hl', addr)
        self.cpu.sla_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x4a)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sla_regHLaddr_3(self):
        # Make sure the zero flag gets set
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0x80)
        self.cpu.set_reg16('hl', addr)

        self.cpu.sla_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_sra_reg8_1(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.sra_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sra_reg8_2(self):
        self.cpu.set_reg8('b', 0xa4)
        self.cpu.sra_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sra_reg8_3(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg8('b', 0x01)

        self.cpu.sra_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_sra_addr16_1(self):
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0xa5)
        self.cpu.set_reg16('hl', addr)
        self.cpu.sra_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_sra_addr16_2(self):
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0xa4)
        self.cpu.set_reg16('hl', addr)
        self.cpu.sra_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0xd2)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_sra_addr16_3(self):
        addr = 0xc000
        self.cpu.mmu.set_addr(addr, 0x01)
        self.cpu.set_reg16('hl', addr)
        self.cpu.sra_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)

    def test_srl_reg8_1(self):
        self.cpu.set_reg8('b', 0xa5)
        self.cpu.srl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x52)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_srl_reg8_2(self):
        self.cpu.set_reg8('b', 0xa4)
        self.cpu.srl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x52)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_srl_reg8_3(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg8('b', 0x01)

        self.cpu.srl_reg8('b')()

        self.assertEqual(self.cpu.get_reg8('b'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_srl_regHLaddr_1(self):
        addr = 0xc000
        self.cpu.set_reg16('hl', addr)
        self.cpu.mmu.set_addr(addr, 0xa5)
        self.cpu.srl_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x52)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_srl_regHLaddr_2(self):
        addr = 0xc000
        self.cpu.set_reg16('hl', addr)
        self.cpu.mmu.set_addr(addr, 0xa4)
        self.cpu.srl_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.get_reg16('hl')), 0x52)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_srl_regHLaddr_3(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x01)

        self.cpu.srl_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_bit_reg8_1(self):
        # Make sure zero flag does not get set
        self.cpu.set_reg8('c', 0x10)
        self.cpu.set_zero_flag()

        self.cpu.bit_reg8(4, 'c')()

        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)

    def test_bit_reg8_2(self):
        # Make sure zero flag gets set
        self.cpu.set_reg8('c', 0x10)
        self.cpu.reset_zero_flag()

        self.cpu.bit_reg8(5, 'c')()

        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)

    def test_bit_regHLaddr_1(self):
        # Make sure zero flag does not get set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x10)
        self.cpu.set_zero_flag()

        self.cpu.bit_regHLaddr(4)()

        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)

    def test_bit_regHLaddr_2(self):
        # Make sure zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x10)
        self.cpu.reset_zero_flag()

        self.cpu.bit_regHLaddr(5)()

        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_sub_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 1)

    def test_res_reg8_1(self):
        self.cpu.set_reg8('d', 0x10)

        self.cpu.res_reg8(4, 'd')()

        self.assertEqual(self.cpu.get_reg8('d'), 0x00)

    def test_res_reg8_2(self):
        self.cpu.set_reg8('d', 0x00)

        self.cpu.res_reg8(4, 'd')()

        self.assertEqual(self.cpu.get_reg8('d'), 0x00)

    def test_res_regHLaddr(self):
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x10)

        self.cpu.res_regHLaddr(4)()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)

    def test_set__reg8_1(self):
        self.cpu.set_reg8('d', 0x00)

        self.cpu.set__reg8(4, 'd')()

        self.assertEqual(self.cpu.get_reg8('d'), 0x10)

    def test_set_reg8_2(self):
        self.cpu.set_reg8('d', 0x10)

        self.cpu.set__reg8(4, 'd')()

        self.assertEqual(self.cpu.get_reg8('d'), 0x10)

    def test_set_regHLaddr(self):
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x00)

        self.cpu.set_regHLaddr(4)()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x10)

    def test_swap_reg8_1(self):
        # Make sure the zero flag does not get set
        self.cpu.set_reg8('c', 0xb4)
        self.cpu.set_zero_flag()

        self.cpu.swap_reg8('c')()

        self.assertEqual(self.cpu.get_reg8('c'), 0x4b)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_swap_reg8_2(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg8('c', 0x00)
        self.cpu.reset_zero_flag()

        self.cpu.swap_reg8('c')()

        self.assertEqual(self.cpu.get_reg8('c'), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_swap_regHLaddr_1(self):
        # Make sure the zero flag does not get set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0xb4)
        self.cpu.set_zero_flag()

        self.cpu.swap_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x4b)
        self.assertEqual(self.cpu.get_zero_flag(), 0)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_swap_regHLaddr_2(self):
        # Make sure the zero flag gets set
        self.cpu.set_reg16('hl', 0xc000)
        self.cpu.mmu.set_addr(0xc000, 0x00)
        self.cpu.reset_zero_flag()

        self.cpu.swap_regHLaddr()

        self.assertEqual(self.cpu.mmu.get_addr(0xc000), 0x00)
        self.assertEqual(self.cpu.get_zero_flag(), 1)
        self.assertEqual(self.cpu.get_carry_flag(), 0)
        self.assertEqual(self.cpu.get_halfcarry_flag(), 0)
        self.assertEqual(self.cpu.get_sub_flag(), 0)

    def test_cpl(self):
        self.cpu.set_reg8('a', 0x55)

        self.cpu.cpl()

        self.assertEqual(self.cpu.get_reg8('a'), 0xaa)

    def test_daa_1(self):
        self.cpu.reset_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x88)

        self.cpu.daa()

        self.assertEqual(self.cpu.get_reg8('a'), 0x88)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_daa_2(self):
        # 28 = 0x1c
        self.cpu.set_reg8('a', 28)
        self.cpu.reset_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.reset_sub_flag()
        self.cpu.daa()

        self.assertEqual(self.cpu.get_reg8('a'), 34)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_daa_3(self):
        self.cpu.reset_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.set_halfcarry_flag()
        self.cpu.set_reg8('a', 0x82)

        self.cpu.daa()

        # add 0x06
        self.assertEqual(self.cpu.get_reg8('a'), 0x88)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_daa_4(self):
        self.cpu.reset_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0xa8)

        self.cpu.daa()

        # add 0x60
        self.assertEqual(self.cpu.get_reg8('a'), 0x08)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_5(self):
        self.cpu.reset_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x9a)

        self.cpu.daa()

        # add 0x66
        self.assertEqual(self.cpu.get_reg8('a'), 0x00)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_6(self):
        self.cpu.reset_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.set_halfcarry_flag()
        self.cpu.set_reg8('a', 0xa3)

        self.cpu.daa()

        # add 0x66
        self.assertEqual(self.cpu.get_reg8('a'), 0x09)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_7(self):
        self.cpu.reset_sub_flag()
        self.cpu.set_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x18)

        self.cpu.daa()

        # add 0x60
        self.assertEqual(self.cpu.get_reg8('a'), 0x78)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_8(self):
        self.cpu.reset_sub_flag()
        self.cpu.set_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x1a)

        self.cpu.daa()

        # add 0x66
        self.assertEqual(self.cpu.get_reg8('a'), 0x80)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_9(self):
        self.cpu.reset_sub_flag()
        self.cpu.set_carry_flag()
        self.cpu.set_halfcarry_flag()
        self.cpu.set_reg8('a', 0x33)

        self.cpu.daa()

        # add 0x66
        self.assertEqual(self.cpu.get_reg8('a'), 0x99)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_10(self):
        self.cpu.set_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x99)

        self.cpu.daa()

        # add 0x00
        self.assertEqual(self.cpu.get_reg8('a'), 0x99)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_daa_11(self):
        self.cpu.set_sub_flag()
        self.cpu.reset_carry_flag()
        self.cpu.set_halfcarry_flag()
        self.cpu.set_reg8('a', 0x88)

        self.cpu.daa()

        # add 0xfa
        self.assertEqual(self.cpu.get_reg8('a'), 0x82)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

    def test_daa_12(self):
        self.cpu.set_sub_flag()
        self.cpu.set_carry_flag()
        self.cpu.reset_halfcarry_flag()
        self.cpu.set_reg8('a', 0x77)

        self.cpu.daa()

        # add 0xa0
        self.assertEqual(self.cpu.get_reg8('a'), 0x17)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_13(self):
        self.cpu.set_sub_flag()
        self.cpu.set_carry_flag()
        self.cpu.set_halfcarry_flag()
        self.cpu.set_reg8('a', 0x77)

        self.cpu.daa()

        # add 0x9a
        self.assertEqual(self.cpu.get_reg8('a'), 0x11)
        self.assertEqual(self.cpu.get_carry_flag(), 1)

    def test_daa_14(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.reset_sub_flag()
            self.cpu.set_carry_flag()
            self.cpu.set_halfcarry_flag()
            self.cpu.set_reg8('a', 0x34)

            self.cpu.daa()

    def test_daa_15(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.set_sub_flag()
            self.cpu.set_carry_flag()
            self.cpu.set_halfcarry_flag()
            self.cpu.set_reg8('a', 0x56)

            self.cpu.daa()

    def test_daa_16(self):
        # Example from the Gameboy Programming Manual
        self.cpu.reset_halfcarry_flag()
        self.cpu.reset_carry_flag()
        self.cpu.set_reg8('a', 0x45)
        self.cpu.set_reg8('b', 0x38)
        self.cpu.add_reg8toreg8('b', 'a')() # 0x7d, c=0, h=0
        self.cpu.daa()
        self.assertEqual(self.cpu.get_reg8('a'), 0x83)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

        self.cpu.sub_reg8fromreg8('b', 'a')()
        self.cpu.daa()
        self.assertEqual(self.cpu.get_reg8('a'), 0x45)
        self.assertEqual(self.cpu.get_carry_flag(), 0)

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


class TestZ80Control(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()

    def test_jr_imm8(self):
        self.cpu.pc = 0x1000
        rom = [0 for _ in range(0x2000)]
        rom[0x1000] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.jr_imm8()()

        self.assertEqual(self.cpu.get_pc(), 0x1021)

    def test_jr_imm8_2(self):
        self.cpu.pc = 0x1000
        rom = [0 for _ in range(0x1001)]
        rom[0x1000] = 0xe0
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.jr_imm8()()

        self.assertEqual(self.cpu.get_pc(), 0x0fe1)

    def test_jr_imm8_nz(self):
        self.cpu.pc = 0x1000
        self.cpu.mmu.rom = bytes(0x20 for _ in range(0x1001))
        self.cpu.reset_zero_flag()
        self.cpu.jr_imm8('NZ')()

        self.assertEqual(self.cpu.get_pc(), 0x1021)

    def test_jr_imm8_z(self):
        self.cpu.pc = 0x1000
        self.cpu.mmu.rom = bytes(0x20 for _ in range(0x1001))
        self.cpu.set_zero_flag()
        self.cpu.jr_imm8('Z')()

        self.assertEqual(self.cpu.get_pc(), 0x1021)

    def test_jr_imm8_nc(self):
        self.cpu.pc = 0x1000
        self.cpu.mmu.rom = bytes(0x20 for _ in range(0x1001))
        self.cpu.reset_carry_flag()
        self.cpu.jr_imm8('NC')()

        self.assertEqual(self.cpu.get_pc(), 0x1021)

    def test_jr_imm8_c(self):
        self.cpu.pc = 0x1000
        self.cpu.mmu.rom = bytes(0x20 for _ in range(0x1001))
        self.cpu.set_carry_flag()
        self.cpu.jr_imm8('C')()

        self.assertEqual(self.cpu.get_pc(), 0x1021)

    def test_jr_imm8_c_2(self):
        self.cpu.pc = 0x1000
        # two's compl of 0x20 is 0xe0
        self.cpu.mmu.rom = bytes(0xe0 for _ in range(0x1001))
        self.cpu.set_carry_flag()
        self.cpu.jr_imm8('C')()

        # 0x1001 - 0x20 = 0x0fe1
        self.assertEqual(self.cpu.get_pc(), 0x0fe1)

    def test_jr_imm8_badcond(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.jr_imm8('A')()

    def test_jp_imm16addr(self):
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x00, 0xd0])
        self.cpu.jp_imm16addr()()

        self.assertEqual(self.cpu.get_pc(), 0xd000)

    def test_jp_reg16addr(self):
        self.cpu.pc = 0xc000
        self.cpu.set_reg16('hl', 0xd000)
        self.cpu.jp_reg16addr('hl')()

        self.assertEqual(self.cpu.get_pc(), 0xd000)

    def test_jp_imm16addr_nz(self):
        # TODO? provide consistent ROM for testing in setup
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x00, 0x20])
        self.cpu.reset_zero_flag()

        self.cpu.jp_imm16addr('NZ')()

        self.assertEqual(self.cpu.pc, 0x2000)

    def test_jp_imm16addr_z(self):
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x00, 0x20])
        self.cpu.set_zero_flag()

        self.cpu.jp_imm16addr('Z')()

        self.assertEqual(self.cpu.pc, 0x2000)

    def test_jp_imm16addr_nc(self):
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x00, 0x20])
        self.cpu.reset_carry_flag()

        self.cpu.jp_imm16addr('NC')()

        self.assertEqual(self.cpu.pc, 0x2000)

    def test_jp_imm16addr_c(self):
        self.cpu.pc = 0
        self.cpu.mmu.rom = bytes([0x00, 0x20])
        self.cpu.set_carry_flag()

        self.cpu.jp_imm16addr('C')()

        self.assertEqual(self.cpu.pc, 0x2000)

    def test_jp_imm16addr_badcond(self):
        self.pc = 0
        with self.assertRaises(ValueError) as cm:
            self.cpu.mmu.rom = bytes([0x00, 0x20])
            self.cpu.set_carry_flag()

            self.cpu.jp_imm16addr('B')()

    def test_ret(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.ret()()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_ret_cond_z(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.reset_zero_flag()
        self.cpu.ret(cond='z')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.sp, 0xd000)

        self.cpu.set_zero_flag()
        self.cpu.ret(cond='z')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_ret_cond_nz(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.set_zero_flag()
        self.cpu.ret(cond='nz')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.sp, 0xd000)

        self.cpu.reset_zero_flag()
        self.cpu.ret(cond='nz')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_ret_cond_2_c(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.reset_carry_flag()
        self.cpu.ret(cond='c')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.sp, 0xd000)

        self.cpu.set_carry_flag()
        self.cpu.ret(cond='c')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_ret_cond_2_nc(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.set_carry_flag()
        self.cpu.ret(cond='nc')()

        self.assertEqual(self.cpu.get_pc(), 0x1234)
        self.assertEqual(self.cpu.sp, 0xd000)

        self.cpu.reset_carry_flag()
        self.cpu.ret(cond='nc')()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_ret_cond_2_badcond(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.ret(cond='aa')()

    def test_reti(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        self.cpu.mmu.set_addr(0xd000, 0x00)
        self.cpu.mmu.set_addr(0xd001, 0xc0)

        self.cpu.reti()

        self.assertEqual(self.cpu.get_pc(), 0xc000)
        self.assertEqual(self.cpu.sp, 0xd002)

    def test_call_imm16addr(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        rom = [0 for _ in range(0x2000)]
        rom[0x1234] = 0x00
        rom[0x1235] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.call_imm16addr()()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.sp, 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x36)

    def test_call_imm16addr_z(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        rom = [0 for _ in range(0x2000)]
        rom[0x1234] = 0x00
        rom[0x1235] = 0x20
        rom[0x1236] = 0x00
        rom[0x1237] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.reset_zero_flag()
        self.cpu.call_imm16addr('z')()

        self.assertEqual(self.cpu.get_pc(), 0x1236)
        self.assertEqual(self.cpu.sp, 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x00)

        self.cpu.set_zero_flag()
        self.cpu.call_imm16addr('z')()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.sp, 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x38)

    def test_call_imm16addr_nz(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        rom = [0 for _ in range(0x2000)]
        rom[0x1234] = 0x00
        rom[0x1235] = 0x20
        rom[0x1236] = 0x00
        rom[0x1237] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.set_zero_flag()
        self.cpu.call_imm16addr('nz')()

        self.assertEqual(self.cpu.get_pc(), 0x1236)
        self.assertEqual(self.cpu.sp, 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x00)

        self.cpu.reset_zero_flag()
        self.cpu.call_imm16addr('nz')()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.sp, 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x38)

    def test_call_imm16addr_c(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        rom = [0 for _ in range(0x2000)]
        rom[0x1234] = 0x00
        rom[0x1235] = 0x20
        rom[0x1236] = 0x00
        rom[0x1237] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.reset_carry_flag()
        self.cpu.call_imm16addr('c')()

        self.assertEqual(self.cpu.get_pc(), 0x1236)
        self.assertEqual(self.cpu.sp, 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x00)

        self.cpu.set_carry_flag()
        self.cpu.call_imm16addr('c')()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.sp, 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x38)

    def test_call_imm16addr_nc(self):
        self.cpu.pc = 0x1234
        self.cpu.sp = 0xd000
        rom = [0 for _ in range(0x2000)]
        rom[0x1234] = 0x00
        rom[0x1235] = 0x20
        rom[0x1236] = 0x00
        rom[0x1237] = 0x20
        self.cpu.mmu.rom = bytes(rom)

        self.cpu.set_carry_flag()
        self.cpu.call_imm16addr('nc')()

        self.assertEqual(self.cpu.get_pc(), 0x1236)
        self.assertEqual(self.cpu.sp, 0xd000)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x00)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x00)

        self.cpu.reset_carry_flag()
        self.cpu.call_imm16addr('nc')()

        self.assertEqual(self.cpu.get_pc(), 0x2000)
        self.assertEqual(self.cpu.sp, 0xcffe)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp + 1), 0x12)
        self.assertEqual(self.cpu.mmu.get_addr(self.cpu.sp), 0x38)

    def test_rst(self):
        for addr in [0x00, 0x08, 0x10, 0x18, 0x20, 0x28, 0x30, 0x38]:
            self.cpu.pc = 0x1234
            self.cpu.sp = 0xd000

            self.cpu.rst(addr)()

            self.assertEqual(self.cpu.pc, addr)
            self.assertEqual(self.cpu.sp, 0xcffe)
            self.assertEqual(self.cpu.mmu.get_addr(0xcfff), 0x12)
            self.assertEqual(self.cpu.mmu.get_addr(0xcffe), 0x34)

    def test_call_imm16addr_badcond(self):
        with self.assertRaises(ValueError) as cm:
            self.cpu.call_imm16addr('aa')()

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


