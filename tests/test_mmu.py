

import unittest

import slowboy.mmu

class TestMMU(unittest.TestCase):
    def setUp(self):
        self.mmu = slowboy.mmu.MMU()
        self.rom_filename = 'blank_rom.gb'
        self.mmu.load_rom(self.rom_filename)

    def test_load_rom(self):
        self.mmu.unload_rom()

        self.mmu.load_rom(self.rom_filename)

        with open(self.rom_filename, 'rb') as f:
            rom = f.read()

            for addr, byte in enumerate(rom):
                self.assertEqual(byte, self.mmu.get_addr(addr))

    def test_load_rom_bad(self):
        self.mmu.unload_rom()

        with self.assertRaises(FileNotFoundError) as cm:
            self.mmu.load_rom('bad_filename.gb')

    def test_get_addr(self):
        pass

    def test_set_addr_bad(self):
        with self.assertRaises(ValueError) as cm:
            self.mmu.set_addr(-1, 255)

    def test_set_addr_bad_2(self):
        for x in range(0xfea0, 0xff00):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, 255)

    def test_set_addr_bad_3(self):
        with self.assertRaises(ValueError) as cm:
            self.mmu.set_addr(0x10000, 255)

    def test_set_addr_rom(self):
        for x in range(0x4000):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, x**2)

        for x in range(0x4000, 0x8000):
            with self.assertRaises(ValueError) as cm:
                self.mmu.set_addr(x, x**3)

    def test_set_addr_vram(self):
        for x in range(0x8000, 0xa000):
            self.mmu.set_addr(x, x**2)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.vram[x - 0x8000])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0x8000, 0xa000):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.vram[x - 0x8000])
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
            self.assertEqual(self.mmu.get_addr(x), self.mmu.vram[x - 0xfe00])
            self.assertEqual(self.mmu.get_addr(x), x**2 % 256)

        for x in range(0xfe00, 0xfea0):
            self.mmu.set_addr(x, 0)
            self.assertEqual(self.mmu.get_addr(x), self.mmu.vram[x - 0xfe00])
            self.assertEqual(self.mmu.get_addr(x), 0)

    def test_set_addr_io(self):
        raise NotImplementedError('memory-mapped IO tests')

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
        self.assertEqual(self.mmu.get_addr(0xffff), self.mmu.interrupt_enable)
        self.assertEqual(self.mmu.get_addr(0xffff), 255)
