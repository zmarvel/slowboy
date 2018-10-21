
import logging

from slowboy.util import ClockListener
from slowboy.interrupts import InterruptType, InterruptListener


class Timer(ClockListener):
    def __init__(self, logger=None, log_level=logging.WARNING):
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger.getChild(__class__.__name__)
        self.logger.propagate = True
        self.logger.setLevel(log_level)

        self._div = 0
        self.div = 0
        self._tima = 0
        self.tima = 0
        self._tma = 0
        self.tma = 0
        self._tac = 0
        self.tac = 0
        self._div_cycles = 0
        self._cycles = 0

        self.interrupt_listeners = []

    def register_interrupt_listener(self, obj: InterruptListener):
        self.interrupt_listeners.append(obj)

    def notify_interrupt_listeners(self):
        for listener in self.interrupt_listeners:
            listener.notify_interrupt(InterruptType.timer)

    def notify(self, clock, cycles):
        if self.tac & 0x4 == 0:
            return

        self._cycles += cycles
        if self._cycles >= self._period:
            self.tima += 1
            self._cycles %= self._period

        self._div_cycles += cycles
        if self._div_cycles >= 488:
            self.div += 1
            self._div_cycles %= 488

    @property
    def div(self):
        return self._div

    @div.setter
    def div(self, value):
        self._div = value & 0xff

    @property
    def tima(self):
        return self._tima

    @tima.setter
    def tima(self, value):
        tmp = self._tima
        self._tima = value & 0xff

        if self._tima > tmp:
            self.notify_interrupt_listeners()

    @property
    def tma(self):
        return self._tma

    @tma.setter
    def tma(self, value):
        self._tma = value & 0xff

    @property
    def tac(self):
        return self._tac

    @tac.setter
    def tac(self, value):
        self._tac = value & 0x7

        clock_select = value & 0x3
        if clock_select == 0:
            self._period = 8000000 // 4096
        elif clock_select == 1:
            self._period = 8000000 // 262144
        elif clock_select == 2:
            self._period = 8000000 // 65536
        elif clock_select == 3:
            self._period = 8000000 // 16384
