import abc
import struct
import enum


class Message(metaclass=abc.ABCMeta):
    code = 0x00

    def __init__(self, payload=bytes()):
        self.payload = payload

    def serialize(self):
        return self.serialize_header() + self.payload

    def serialize_header(self):
        return struct.pack('!LL', self.code, len(self.payload))

    @classmethod
    def deserialize(cls, payload):
        """Default implementation. May be overridden for messages with non-empty
        payloads.
        """
        return cls()


# ------------------------------------------------------------------------------

class Commands(enum.Enum):
    INVALID_COMMAND = 0x00
    SHUTDOWN_COMMAND = 0x01
    STEP_COMMAND = 0x02
    CONTINUE_COMMAND = 0x03
    SET_BREAKPOINT_COMMAND = 0x04
    READ_REGISTER_COMMAND = 0x05
    READ_MEMORY_COMMAND = 0x06
    DUMP_TILES_COMMAND = 0x07
    UPDATE_TILES_COMMAND = 0x08
    SET_WATCHPOINT_COMMAND = 0x09

class Command(Message):
    code = Commands.INVALID_COMMAND.value


class ShutdownCommand(Command):
    code = Commands.SHUTDOWN_COMMAND.value


class StepCommand(Command):
    code = Commands.STEP_COMMAND.value


class ContinueCommand(Command):
    code = Commands.CONTINUE_COMMAND.value


class SetBreakpointCommand(Command):
    code = Commands.SET_BREAKPOINT_COMMAND.value

    def __init__(self, addr: int):
        super().__init__(struct.pack('!H', addr))

    @classmethod
    def deserialize(cls, payload):
        return cls(struct.unpack('!H', payload)[0])

    @property
    def address(self):
        return struct.unpack('!H', self.payload)[0]


SINGLE_REGISTERS = ('a', 'b', 'c', 'd', 'e', 'f', 'h', 'l')
DOUBLE_REGISTERS = ('bc', 'de', 'hl', 'sp', 'pc')
REGISTERS = SINGLE_REGISTERS + DOUBLE_REGISTERS


class ReadRegisterCommand(Command):
    code = Commands.READ_REGISTER_COMMAND.value

    def __init__(self, reg: str):
        super(Command, self).__init__(
            ReadRegisterCommand.encode_register(reg))
        self.register = reg

    @classmethod
    def deserialize(cls, payload):
        return cls(ReadRegisterCommand.decode_register(payload))

    @staticmethod
    def encode_register(reg: str) -> bytes:
        if reg in SINGLE_REGISTERS:
            return reg.encode('ascii') + b'\x00'
        elif reg in DOUBLE_REGISTERS:
            return reg.encode('ascii')
        else:
            raise ValueError(f'Invalid register {reg}')

    @staticmethod
    def decode_register(breg: bytes) -> str:
        if breg[1] == b'\x00':
            breg = breg[:1]
        decoded = breg.decode('ascii')
        if decoded not in REGISTERS:
            raise ValueError(f'Invalid register {decoded}')
        else:
            return decoded

class ReadMemoryCommand(Command):
    code = Commands.READ_MEMORY_COMMAND.value

    def __init__(self, addr: int, length: int):
        super(Command, self).__init__(struct.pack('!HH', addr, length))

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


class DumpTilesCommand(Command):
    code = Commands.DUMP_TILES_COMMAND.value


class UpdateTilesCommand(Command):
    code = Commands.UPDATE_TILES_COMMAND.value


class SetWatchpointCommand(Command):
    code = Commands.SET_WATCHPOINT_COMMAND.value

    def __init__(self, addr: int, read=False):
        """Watch a region of memory. By default, only watch writes.

        Args:
            addr: Address to watch.
            read: Also watch for reads.
        """
        super().__init__(struct.pack('!HH', addr, 1 if read else 0))
        self.addr = addr
        self.read = read

    @classmethod
    def deserialize(cls, payload):
        addr, read = struct.unpack('!HH', payload)
        return cls(addr, read == 1)


commands = [
    ShutdownCommand,
    StepCommand,
    ContinueCommand,
    SetBreakpointCommand,
    ReadRegisterCommand,
    ReadMemoryCommand,
    DumpTilesCommand,
    UpdateTilesCommand,
    SetWatchpointCommand,
]


# ------------------------------------------------------------------------------

class Response(Message):
    pass

class HitBreakpointResponse(Response):
    code = 0x01

    def __init__(self, addr: int):
        super(Response, self).__init__(struct.pack('!H', addr))

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
        super().__init__(self.encode_register(reg) + struct.pack('!H', value))
        self.register = reg
        self.value = value

    @classmethod
    def deserialize(cls, payload):
        reg = payload[:2].decode('ascii').rstrip('\x00')
        value, = struct.unpack('!H', payload[2:])
        if reg not in REGISTERS:
            raise ValueError(f'Invalid register {reg}')
        return cls(reg, value)

    @staticmethod
    def encode_register(reg: str) -> bytes:
        if reg in SINGLE_REGISTERS:
            return reg.encode('ascii') + b'\x00'
        elif reg in DOUBLE_REGISTERS:
            return reg.encode('ascii')
        else:
            raise ValueError(f'Invalid register {reg}')


class ReadMemoryResponse(Response):
    code = 0x03

    def __init__(self, addr: int, values: bytes):
        super(Response, self).__init__(
            struct.pack('!H{}B'.format(len(values)), addr, *values))

    @classmethod
    def deserialize(cls, payload):
        nvalues = len(payload) - 2
        unpacked = struct.unpack('!H{}B'.format(nvalues), payload)
        addr = unpacked[0]
        values = unpacked[1:]
        return cls(addr, values)

    @property
    def address(self):
        return struct.unpack_from('!H', self.payload)[0]

    @property
    def values(self):
        return self.payload[2:]


class HitWatchpointResponse(Response):
    code = 0x04

    def __init__(self, addr: int, value: int, read=False):
        super().__init__(struct.pack('!HHH', addr, value, 1 if read else 0))
        self.addr = addr
        self.value = value
        self.read = read

    @classmethod
    def deserialize(cls, payload):
        addr, value, read = struct.unpack('!HHH', payload)
        return cls(addr, value, read == 1)


responses = [
    HitBreakpointResponse,
    ReadRegisterResponse,
    ReadMemoryResponse,
    HitWatchpointResponse,
]
