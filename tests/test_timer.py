

import unittest

import slowboy.timer
import slowboy.interrupts

from tests.mock_interrupt_controller import MockInterruptController


class TimerTest(unittest.TestCase):
    def setUp(self):
        self.timer = slowboy.timer.Timer()
        self.interrupt_listener = MockInterruptController()
        self.timer.register_interrupt_listener(self.interrupt_listener)

    def tearDown(self):
        pass

    def test_init(self):
        self.assertEqual(self.timer.div, 0)
        self.assertEqual(self.timer.tima, 0)
        self.assertEqual(self.timer.tma, 0)
        self.assertEqual(self.timer.div, 0)

    def test_div(self):
        # enable timer
        self.timer.tac |= 0x4

        self.timer.notify(0, 490)
        self.assertEqual(self.timer._div_cycles, 2)
        self.assertEqual(self.timer.div, 1)

    def test_tima_0(self):
        # enable timer at 4096 Hz
        self.timer.tac |= 0x4

        self.timer.notify(0, 1955)
        self.assertEqual(self.timer.tima, 1)
        self.assertEqual(self.timer._cycles, 2)
        self.assertEqual(self.interrupt_listener.last_interrupt,
                         slowboy.interrupts.InterruptType.timer)

    def test_tima_1(self):
        # enable timer at 16384 Hz
        self.timer.tac |= 0x4 | 0x3

        self.timer.notify(0, 490)
        self.assertEqual(self.timer.tima, 1)
        self.assertEqual(self.timer._cycles, 2)
        self.assertEqual(self.interrupt_listener.last_interrupt,
                         slowboy.interrupts.InterruptType.timer)

    def test_tima_2(self):
        # enable timer at 65536 Hz
        self.timer.tac |= 0x4 | 0x2

        self.timer.notify(0, 130)
        self.assertEqual(self.timer.tima, 1)
        self.assertEqual(self.timer._cycles, 8)
        self.assertEqual(self.interrupt_listener.last_interrupt,
                         slowboy.interrupts.InterruptType.timer)

    def test_tima_3(self):
        # enable timer at 262144 Hz
        self.timer.tac |= 0x4 | 0x1

        self.timer.notify(0, 31)
        self.assertEqual(self.timer.tima, 1)
        self.assertEqual(self.timer._cycles, 1)
        self.assertEqual(self.interrupt_listener.last_interrupt,
                         slowboy.interrupts.InterruptType.timer)
