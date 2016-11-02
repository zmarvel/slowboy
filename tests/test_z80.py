
import unittest

import slowboy.z80

class TestZ80(unittest.TestCase):
    def setUp(self):
        self.cpu = slowboy.z80.Z80()

    def test_set_reg8(self):
        self.cpu.set_reg8('B', 0)
        self.cpu.set_reg8('C', 1)
        self.cpu.set_reg8('D', 3)
        self.cpu.set_reg8('E', 4)
        self.cpu.set_reg8('H', 5)
        self.cpu.set_reg8('L', 6)
        self.cpu.set_reg8('A', 7)

        registers = self.cpu.get_registers()

        self.assertEqual(registers['b'], 0)
        self.assertEqual(registers['c'], 1)
        self.assertEqual(registers['d'], 2)
        self.assertEqual(registers['e'], 3)
        self.assertEqual(registers['h'], 4)
        self.assertEqual(registers['l'], 5)
        self.assertEqual(registers['a'], 6)

    def test_set_reg8(self):
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
        self.cpu.set_reg16('SP', 0x789a)

        self.assertEqual(self.cpu.get_reg8('B'), 0x12)
        self.assertEqual(self.cpu.get_reg8('C'), 0x34)
        self.assertEqual(self.cpu.get_reg8('D'), 0x34)
        self.assertEqual(self.cpu.get_reg8('E'), 0x56)
        self.assertEqual(self.cpu.get_reg8('H'), 0x56)
        self.assertEqual(self.cpu.get_reg8('L'), 0x78)
        self.assertEqual(self.cpu.get_reg16('SP'), 0x789a)

    def test_get_reg16(self):
        self.cpu.set_reg16('BC', 0x1234)
        self.cpu.set_reg16('DE', 0x3456)
        self.cpu.set_reg16('HL', 0x5678)
        self.cpu.set_reg16('SP', 0x789a)

        self.assertEqual(self.cpu.get_reg16('BC'), 0x1234)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x3456)
        self.assertEqual(self.cpu.get_reg16('HL'), 0x5678)
        self.assertEqual(self.cpu.get_reg16('SP'), 0x789a)

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
        self.cpu.ld_imm8toreg8(0, 'B')
        self.cpu.ld_imm8toreg8(1, 'C')
        self.cpu.ld_imm8toreg8(2, 'D')
        self.cpu.ld_imm8toreg8(3, 'E')
        self.cpu.ld_imm8toreg8(4, 'H')
        self.cpu.ld_imm8toreg8(5, 'L')
        self.cpu.ld_imm8toreg8(6, 'A')

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

        self.cpu.ld_reg8toreg8('B', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 0)
        self.cpu.ld_reg8toreg8('C', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 1)
        self.cpu.ld_reg8toreg8('D', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 2)
        self.cpu.ld_reg8toreg8('E', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 3)
        self.cpu.ld_reg8toreg8('H', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 4)
        self.cpu.ld_reg8toreg8('L', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 5)
        self.cpu.ld_reg8toreg8('A', 'B')
        self.assertEqual(self.cpu.get_reg8('B'), 6)

        self.cpu.ld_reg8toreg8('C', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 1)
        self.cpu.ld_reg8toreg8('D', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 2)
        self.cpu.ld_reg8toreg8('E', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 3)
        self.cpu.ld_reg8toreg8('H', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 4)
        self.cpu.ld_reg8toreg8('L', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 5)
        self.cpu.ld_reg8toreg8('A', 'C')
        self.assertEqual(self.cpu.get_reg8('C'), 6)

    def test_ld_imm16toreg16(self):
        self.cpu.ld_imm16toreg16(0x0123, 'BC')
        self.cpu.ld_imm16toreg16(0x4567, 'DE')
        self.cpu.ld_imm16toreg16(0x89ab, 'HL')
        self.cpu.ld_imm16toreg16(0xcdef, 'SP')

        self.assertEqual(self.cpu.get_reg16('BC'), 0x0123)
        self.assertEqual(self.cpu.get_reg16('DE'), 0x4567)
        self.assertEqual(self.cpu.get_reg16('HL'), 0x89ab)
        self.assertEqual(self.cpu.get_reg16('SP'), 0xcdef)

    def test_inc_reg8(self):
        self.cpu.set_reg8('b', 0x04)
        self.cpu.inc_reg8('b')
        self.assertEqual(self.cpu.get_reg8('b'), 0x05)

    def test_inc_reg16(self):
        self.cpu.set_reg16('bc', 0xee)
        self.cpu.inc_reg16('bc')
        self.assertEqual(self.cpu.get_reg16('bc'), 0xef)

    def test_dec_reg8(self):
        self.cpu.set_reg8('b', 0x04)
        self.cpu.dec_reg8('b')
        self.assertEqual(self.cpu.get_reg8('b'), 0x03)

    def test_dec_reg16(self):
        self.cpu.set_reg16('bc', 0xee)
        self.cpu.dec_reg16('bc')
        self.assertEqual(self.cpu.get_reg16('bc'), 0xed)


