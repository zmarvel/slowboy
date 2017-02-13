

from .mmu import MMU
from .z80 import Z80

class HeadlessUI():
    def __init__(self, romfile):
        with open(romfile, 'rb') as f:
            rom = f.read()
        mmu = MMU(rom)
        self.cpu = Z80(mmu)

    def start(self):
        self.cpu.go()
