
import unittest

import slowboy.gpu
import slowboy.interrupts

class MockInterruptController(slowboy.interrupts.InterruptListener):
    def __init__(self):
        self.last_interrupt = None

    def notify_interrupt(self, interrupt):
        self.last_interrupt = interrupt

    def acknowledge_interrupt(self, interrupt):
        pass

STAT_IE_ALL_MASK = (slowboy.gpu.STAT_LYC_IE_MASK |
                    slowboy.gpu.STAT_OAM_IE_MASK |
                    slowboy.gpu.STAT_HBLANK_IE_MASK |
                    slowboy.gpu.STAT_VBLANK_IE_MASK)

class TestGPU(unittest.TestCase):
    def setUp(self):
        self.gpu = slowboy.gpu.GPU()
        self.interrupt_controller = MockInterruptController()

    def test_constructor(self):
        self.assertEqual(len(self.gpu.vram), 0x2000)
        self.assertEqual(len(self.gpu.oam), 0xa0)

        self.assertEqual(self.gpu.lcdc, 0x91)
        self.assertEqual(self.gpu.scy, 0x00)
        self.assertEqual(self.gpu.scx, 0x00)
        self.assertEqual(self.gpu.ly, 0x00)
        self.assertEqual(self.gpu.lyc, 0x00)
        self.assertEqual(self.gpu.bgp, 0xfc)
        self.assertEqual(self.gpu.obp0, 0xff)
        self.assertEqual(self.gpu.obp1, 0xff)
        self.assertEqual(self.gpu.wy, 0x00)
        self.assertEqual(self.gpu.wx, 0x00)

        # LYC=LY, Mode.OAM_READ
        self.assertEqual(self.gpu.stat, 0x04 | 0x02)

        self.assertEqual(self.gpu.mode, slowboy.gpu.Mode.OAM_READ)
        self.assertEqual(self.gpu.mode_clock, 0)

    def test_mode(self):
        # Force ClockListener.notify and verify mode state transitions
        for i in range(144):
            # OAM_READ (2)
            self.assertEqual(self.gpu.mode, slowboy.gpu.Mode.OAM_READ)
            self.assertEqual(self.gpu.mode_clock, 0)
            self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                             slowboy.gpu.Mode.OAM_READ.value)

            # OAM_VRAM_READ (3)
            self.gpu.notify(0, 80)
            self.assertEqual(self.gpu.mode, slowboy.gpu.Mode.OAM_VRAM_READ)
            self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                             slowboy.gpu.Mode.OAM_VRAM_READ.value)
            self.assertEqual(self.gpu.mode_clock, 0)
            
            # HBLANK (0)
            self.gpu.notify(0, 172)
            self.assertEqual(self.gpu.mode, slowboy.gpu.Mode.H_BLANK)
            self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                             slowboy.gpu.Mode.H_BLANK.value)
            self.assertEqual(self.gpu.mode_clock, 0)

            self.gpu.notify(0, 204)

        # VBLANK (1)
        self.assertEqual(self.gpu.mode, slowboy.gpu.Mode.V_BLANK)
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                         slowboy.gpu.Mode.V_BLANK.value)
        self.assertEqual(self.gpu.mode_clock, 0)

    def test_stat_mode(self):
        # Initial mode is OAM_READ
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                         slowboy.gpu.Mode.OAM_READ.value)

        self.gpu.mode = slowboy.gpu.Mode.OAM_VRAM_READ
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                         slowboy.gpu.Mode.OAM_VRAM_READ.value)

        self.gpu.mode = slowboy.gpu.Mode.H_BLANK
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                         slowboy.gpu.Mode.H_BLANK.value)

        self.gpu.mode = slowboy.gpu.Mode.V_BLANK
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_MODE_MASK,
                         slowboy.gpu.Mode.V_BLANK.value)

    def test_stat_oam_interrupt(self):
        self.gpu.load_interrupt_controller(self.interrupt_controller)

        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_OAM_IE_MASK, 0)
        self.gpu.stat |= slowboy.gpu.STAT_OAM_IE_MASK
        self.gpu.mode = slowboy.gpu.Mode.OAM_READ
        self.assertEqual(self.interrupt_controller.last_interrupt,
                         slowboy.interrupts.InterruptType.stat) 

    def test_stat_lyc_interrupt(self):
        self.gpu.load_interrupt_controller(self.interrupt_controller)

        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_LYC_IE_MASK, 0)
        self.gpu.stat |= slowboy.gpu.STAT_LYC_IE_MASK
        self.gpu.ly = self.gpu.lyc
        self.assertEqual(self.interrupt_controller.last_interrupt,
                         slowboy.interrupts.InterruptType.stat) 

    def test_stat_hblank_interrupt(self):
        self.gpu.load_interrupt_controller(self.interrupt_controller)

        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_HBLANK_IE_MASK, 0)
        self.gpu.stat |= slowboy.gpu.STAT_HBLANK_IE_MASK
        self.gpu.mode = slowboy.gpu.Mode.H_BLANK
        self.assertEqual(self.interrupt_controller.last_interrupt,
                         slowboy.interrupts.InterruptType.stat) 

    def test_stat_vblank_interrupt(self):
        self.gpu.load_interrupt_controller(self.interrupt_controller)

        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_VBLANK_IE_MASK, 0)
        self.gpu.stat |= slowboy.gpu.STAT_VBLANK_IE_MASK
        self.gpu.mode = slowboy.gpu.Mode.V_BLANK
        self.assertEqual(self.interrupt_controller.last_interrupt,
                         slowboy.interrupts.InterruptType.stat) 
