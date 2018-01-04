

import abc
from enum import Enum
from typing import Sequence
import logging


IF_VBLANK_OFFSET = 0
IF_VBLANK_MASK = (1 << IF_VBLANK_OFFSET)
IF_STAT_OFFSET = 1
IF_STAT_MASK = (1 << IF_STAT_OFFSET)
IF_TIMER_OFFSET = 2
IF_TIMER_MASK = (1 << IF_TIMER_OFFSET)
IF_SERIAL_OFFSET = 3
IF_SERIAL_MASK = (1 << IF_SERIAL_OFFSET)
IF_JOYPAD_OFFSET = 4
IF_JOYPAD_MASK = (1 << IF_JOYPAD_OFFSET)


class InterruptType(Enum):
    vblank = IF_VBLANK_OFFSET
    stat = IF_STAT_OFFSET
    timer = IF_TIMER_OFFSET
    serial = IF_SERIAL_OFFSET
    joypad = IF_JOYPAD_OFFSET


class InterruptListener(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify_interrupt(self, interrupt: InterruptType):
        pass

    @abc.abstractmethod
    def acknowledge_interrupt(self, interrupt: InterruptType):
        pass


class InterruptController(InterruptListener):
    def __init__(self, logger:logging.Logger=None, log_level=logging.DEBUG):
        self.enabled = True
        self._if = 0
        self._ie = 0
        if logger is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger.getChild(__class__.__name__)

        if log_level is not None:
            self.logger.setLevel(log_level)

    @property
    def if_(self):
        return self._if

    @if_.setter
    def if_(self, value):
        self.logger.debug('set IF to %#x', value)
        self._if = value

    @property
    def ie(self):
        return self._ie

    @ie.setter
    def ie(self, value):
        self.logger.debug('set IE to %#x', value)
        self._ie = value

    def ei(self):
        self.enabled = True

    def di(self):
        self.enabled = False

    @property
    def has_interrupt(self) -> bool:
        return (self.if_ & 0x1f) > 0

    def get_interrupts(self) -> Sequence[InterruptType]:
        for i in range(5):
            if self.if_ & (1 << i):
                yield InterruptType(i)

    def get_interrupt(self) -> InterruptType:
        for i in range(5):
            if self.if_ & (1 << i):
                return InterruptType(i)

    def notify_interrupt(self, interrupt: InterruptType):
        if self.ie & (1 << interrupt.value) == 0:
            # interrupt disabled
            return

        self.logger.debug('notified: %s', interrupt)
        self.if_ |= 1 << interrupt.value

    def acknowledge_interrupt(self, interrupt: InterruptType):
        self.logger.debug('acknowledged: %s', interrupt)
        self.if_ &= (1 << interrupt.value) ^ 0xff
