
import abc
from collections import namedtuple

Op = namedtuple('Op', ['function', 'cycles', 'description'])

class ClockListener(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def notify(self, clock: int, cycles: int):
        """Notify the listener that the clock has advanced.

        :param clock: The new value of the CPU clock.
        :param cycles: The number of cycles that have passed since the last
            notification."""
        pass

def uint8toBCD(uint8):
    """Convert an 8-bit unsigned integer to binary-coded decimal."""

    d1 = uint8 // 10
    d0 = uint8 % 10

    return (d1 << 4) | d0

def torgba(c):
    assert c < 4
    return ((c << 6) | (c << 4) | (c << 2) | c)

def sub_s8(x, y):
    """Subtract two 8-bit integers stored in two's complement."""

    return (x + twoscompl8(y)) & 0xff

def sub_s16(x, y):
    """Subtract two 16-bit integers stored in two's complement."""

    return (x + twoscompl16(y)) & 0xffff

def add_s8(x, y):
    """Add two 8-bit integers stored in two's complement."""

    return (x + y) & 0xff

def add_s16(x, y):
    """Add two 16-bit integers stored in two's complement."""

    return (x + y) & 0xffff

def twoscompl8(x):
    """Returns the reciprocal of 8-bit x in two's complement."""

    return ((x ^ 0xff) + 1) & 0xff

def twoscompl16(x):
    """Returns the reciprocal of 16-bit x in two's complement."""

    return ((x ^ 0xffff) + 1) & 0xffff
