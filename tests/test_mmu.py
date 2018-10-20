

import unittest

import slowboy.mmu
import slowboy.gpu
import slowboy.interrupts

from tests.mock_interrupt_controller import MockInterruptController


class TestMMU(unittest.TestCase):
    def setUp(self):
        self.mmu = slowboy.mmu.MMU()
        self.rom_filename = 'blank_rom.gb'
        self.mmu.load_rom_from_file(self.rom_filename)

        self.mmu.load_gpu(slowboy.gpu.GPU())
        self.mmu.load_interrupt_controller(MockInterruptController())

    def test_load_rom(self):
        self.mmu.unload_rom()

        with open(self.rom_filename, 'rb') as f:
            romdata = f.read()

            self.mmu.load_rom(romdata)

        with open(self.rom_filename, 'rb') as f:
            rom = f.read()

            for addr, byte in enumerate(rom):
                self.assertEqual(byte, self.mmu.get_addr(addr))

        self.assertEqual(len(self.mmu.rom), 32*1024)

    def test_load_rom_bad(self):
        self.mmu.unload_rom()

        with self.assertRaises(FileNotFoundError) as cm:
            self.mmu.load_rom_from_file('bad_filename.gb')

    def test_get_addr(self):
        pass

    def test_set_addr_bad(self):
        with self.assertRaises(ValueError) as cm:
            self.mmu.set_addr(-1, 255)

    def test_set_addr_bad_2(self):
        self.skipTest('writes to invalid memory no longer raise ValueError')
        for x in range(0xfea0, 0xff00):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, 255)

    def test_set_addr_bad_3(self):
        with self.assertRaises(ValueError) as cm:
            self.mmu.set_addr(0x10000, 255)

    def test_set_addr_rom(self):
        self.skipTest('writes to invalid memory no longer raise ValueError')
        for x in range(0x4000):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, x**2)

        for x in range(0x4000, 0x8000):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, x**3)

    def test_set_addr_vram(self):
        for x in range(0x8000, 0xa000):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.gpu.vram[x - 0x8000])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0x8000, 0xa000):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.gpu.vram[x - 0x8000])
            self.assertEqual(self.mmu.get_addr(x), 0)
    
    def test_set_addr_cartridge_ram(self):
        for x in range(0xa000, 0xc000):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.cartridge_ram[x - 0xa000])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xa000, 0xc000):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.cartridge_ram[x - 0xa000])
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_wram(self):
        for x in range(0xc000, 0xe000):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.wram[x - 0xc000])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xc000, 0xe000):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.wram[x - 0xc000])
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_echo_ram(self):
        for x in range(0xe000, 0xfe00):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.wram[x - 0xe000])
            self.assertEqual(self.mmu.get_addr(x), self.mmu.get_addr(x - 0x2000))
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xe000, 0xfe00):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.wram[x - 0xe000])
            self.assertEqual(self.mmu.get_addr(x), self.mmu.get_addr(x - 0x2000))
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_sprite_table(self):
        for x in range(0xfe00, 0xfea0):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.gpu.oam[x - 0xfe00])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xfe00, 0xfea0):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.gpu.oam[x - 0xfe00])
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_io(self):
        # TODO
        self.fail('not implemented: memory-mapped IO tests')

    def test_set_addr_hram(self):
        for x in range(0xff80, 0xffff):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.hram[x - 0xff80])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xff80, 0xffff):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.hram[x - 0xff80])
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_interrupt_enable_register(self):
        self.mmu.set_addr(0xffff, 255)
        self.assertEqual(self.mmu.get_addr(0xffff),
                         self.mmu.interrupt_controller.ie)
        self.assertEqual(self.mmu.get_addr(0xffff), 255)

class TestDMA(unittest.TestCase):
    def setUp(self):
        self.mmu = slowboy.mmu.MMU(gpu=slowboy.gpu.GPU())
        self.rom = bytearray(0x300)
        for i in range(0x200):
            self.rom[i] = 0
        for i in range(0x200, 0x300):
            self.rom[i] = (i * 2) & 0xff
        self.mmu.load_rom(self.rom)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertEqual(self.mmu.dma, 0)

    def test_dma(self):
        # Source: 0x200
        self.mmu.dma = 0x02
        self.assertEqual(self.mmu.dma, 0x02)
        for i in range(0xa0):
            self.assertEqual(self.mmu.get_addr(0xfe00+i), ((0x200+i) * 2) & 0xff)