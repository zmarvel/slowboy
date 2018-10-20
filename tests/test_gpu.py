
import unittest

import slowboy.gpu
import slowboy.interrupts

from tests.mock_interrupt_controller import MockInterruptController


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

    def test__update_vram(self):
        # TODO
        self.fail('Not implemented: test__update_vram')

    def test_colorto8bit(self):
        self.assertRaises(ValueError, slowboy.gpu.colorto8bit, 4)

        self.assertEqual(slowboy.gpu.colorto8bit(0), 0xff)
        self.assertEqual(slowboy.gpu.colorto8bit(1), 0xaa)
        self.assertEqual(slowboy.gpu.colorto8bit(2), 0x55)
        self.assertEqual(slowboy.gpu.colorto8bit(3), 0x00)

    def test_bgp(self):
        # 11 11 11 00
        self.assertEqual(self.gpu.bgp, 0xfc)
        self.assertEqual(self.gpu._palette, [0xff, 0x00, 0x00, 0x00])

        # 00 01 10 11
        self.gpu.bgp = 0x1b
        self.assertEqual(self.gpu.bgp, 0x1b)
        self.assertEqual(self.gpu._palette, [0x00, 0x55, 0xaa, 0xff])

    def test_obp(self):
        self.assertEqual(self.gpu.obp0, 0xff)
        self.assertEqual(self.gpu._sprite_palette0, [0xff, 0x00, 0x00, 0x00])
        self.assertEqual(self.gpu.obp1, 0xff)
        self.assertEqual(self.gpu._sprite_palette1, [0xff, 0x00, 0x00, 0x00])

        # 00 01 10 11
        self.gpu.obp0 = 0x1b
        self.assertEqual(self.gpu.obp0, 0x1b)
        self.assertEqual(self.gpu._sprite_palette0, [0xff, 0x55, 0xaa, 0xff])
        # 11 10 01 00
        self.gpu.obp1 = 0xe4
        self.assertEqual(self.gpu.obp1, 0xe4)
        self.assertEqual(self.gpu._sprite_palette1, [0xff, 0xaa, 0x55, 0x00])

    def test_ly_lyc(self):
        self.assertEqual(self.gpu.ly, 0)

        # Changing LYC so that LYC != LY should clear STAT LYC flag
        self.gpu.lyc = 5
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_LYC_FLAG_MASK, 0)
        # Make LY = LYC -- STAT LYC flag should be set
        self.gpu.ly = 5
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_LYC_FLAG_MASK,
                         slowboy.gpu.STAT_LYC_FLAG_MASK)
        # Changing LY so that LYC != LY should *also* clear STAT LYC flag
        self.gpu.ly = 6
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_LYC_FLAG_MASK, 0)
        # Make LYC = LY -- should also set STAT LYC flag
        self.gpu.lyc = 6
        self.assertEqual(self.gpu.stat & slowboy.gpu.STAT_LYC_FLAG_MASK,
                         slowboy.gpu.STAT_LYC_FLAG_MASK)

    def test_wx_wy(self):
        self.assertEqual(self.gpu.wx, 0)
        self.assertEqual(self.gpu.wy, 0)

        self.gpu.wx = 7
        self.assertEqual(self.gpu._wx, 0)

        self.gpu.wy = 0
        self.assertEqual(self.gpu._wy, 0)
