
import abc
from typing import Callable
import asyncio
import struct
import enum
from collections import deque

from slowboy.debug.exceptions import *




class Message(metaclass=abc.ABCMeta):
    def __init__(self, payload=bytes()):
        self.payload = payload

    def serialize(self):
        return self.serialize_header() + self.payload

    def serialize_header(self):
        return struct.pack('!LL', self.code, len(self.payload))

    @classmethod
    def deserialize(cls, payload=bytes()):
        """Default implementation. May be overridden for messages with non-empty
        payloads.
        """
        return cls()


# ------------------------------------------------------------------------------

class Command(Message):
    pass


class ShutdownCommand(Command):
    code = 0x01


class StepCommand(Command):
    code = 0x02


class ContinueCommand(Command):
    code = 0x03


class SetBreakpointCommand(Command):
    code = 0x04

    def __init__(self, addr: int):
        self.payload = struct.pack('!H', addr)

    @classmethod
    def deserialize(cls, payload):
        return cls(struct.unpack('!H', payload)[0])

    @property
    def address(self):
        return struct.unpack('!H', self.payload)[0]


registers = [
    'a', 'b', 'c', 'd', 'e', 'f', 'h', 'l', # 8-bit registers
    'bc', 'de', 'hl', 'sp', 'pc',           # 16-bit registers
]
class ReadRegisterCommand(Command):
    code = 0x05

    def __init__(self, reg: str):
        self.payload = struct.pack('!B', ReadRegisterCommand.encode_register(reg))

    @classmethod
    def deserialize(cls, payload):
        regid = struct.unpack('!B', payload)[0]
        return cls(ReadRegisterCommand.decode_register(regid))

    @staticmethod
    def encode_register(reg):
        return registers.index(reg)

    @staticmethod
    def decode_register(regid):
        return registers[regid]

    @property
    def register(self):
        return struct.unpack('!B', self.payload)[0]

class ReadMemoryCommand(Command):
    code = 0x06

    def __init__(self, addr: int, length: int):
        self.payload = struct.pack('!HH', addr, length)

    @classmethod
    def deserialize(cls, payload):
        addr, length = struct.unpack('!HH', payload)
        return cls(addr, length)

    @property
    def address(self):
        return struct.unpack('!HH', self.payload)[0]

    @property
    def length(self):
        return struct.unpack('!HH', self.payload)[1]

commands = [
    ShutdownCommand,
    StepCommand,
    ContinueCommand,
    SetBreakpointCommand,
    ReadRegisterCommand,
    ReadMemoryCommand,
]


# ------------------------------------------------------------------------------

class Response(Message):
    pass

class HitBreakpointResponse(Response):
    code = 0x01

    def __init__(self, addr: int):
        self.payload = struct.pack('!H', addr)

    @classmethod
    def deserialize(cls, payload):
        addr = struct.unpack('!H', payload)[0]
        return cls(addr)

    @property
    def address(self):
        return struct.unpack('!H', self.payload)[0]

class ReadRegisterResponse(Response):
    code = 0x02

    def __init__(self, reg: str, value: int):
        self.payload = struct.pack('!BB', reg, value)

    @classmethod
    def deserialize(cls, payload):
        reg, value = struct.unpack('!BB', payload)
        return cls(reg, value)

    @property
    def register(self):
        return struct.unpack('!BB', self.payload)[0]

    @property
    def value(self):
        return struct.unpack('!BB', self.payload)[1]

class ReadMemoryResponse(Response):
    code = 0x03

    def __init__(self, addr: int, values: bytes):
        self.payload = struct.pack('!H{}B'.format(len(values)), addr, *values)

    @classmethod
    def deserialize(cls, payload):
        nvalues = len(payload) - 2
        unpacked = struct.unpack('!H{}B'.format(nvalues), payload)
        addr = unpacked[0]
        values = unpacked[1:]
        return cls(addr, values)

    @property
    def address(self):
        nvalues = len(self.payload) - 2
        return struct.unpack('!H{}B'.format(nvalues), self.payload)[0]

    @property
    def values(self):
        nvalues = len(self.payload) - 2
        return struct.unpack('!H{}B'.format(nvalues), self.payload)[1:]


responses = [
    HitBreakpointResponse,
    ReadRegisterResponse,
    ReadMemoryResponse,
]
