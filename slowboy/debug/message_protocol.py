import asyncio
import enum
import struct

from slowboy.debug.messages import *

class MessageProtocol(asyncio.Protocol):
    class RxState(enum.Enum):
        WAITING = 1
        GOT_CODE = 2
        GOT_SIZE = 3
        GOT_PAYLOAD = 4

    def __init__(self, rx_queue: asyncio.Queue):
        self.rx_queue = rx_queue
        self.rx_state = self.RxState.WAITING
        self._rx_buffer = bytes()
        self._rx_code = -1
        self._rx_size = -1

    def connection_made(self, transport):
        """Overridden method from asyncio.Protocol. Print out who we connected
        with and store away the transport argument in an attribute.
        """
        print('MessageProtocol: connection made with {}'.format(
            transport.get_extra_info('peername')))
        self.transport = transport

    def connection_lost(self, exc):
        """Overridden method from asyncio.Protocol. Calls any connection-lost
        callbacks.
        """
        print('MessageProtocol: Connection lost with {}',
              self.transport.get_extra_info('peername'))

    def decode_message(self, code: int, size: int, payload: bytes):
        """`self.messages` should be defined by subclasses. Decodes the received
        message into an object that should subclass Message.
        """
        for cls in self.messages:
            if cls.code == code:
                return cls.deserialize(payload)
        raise UnrecognizedMessageException(code)

    def data_received(self, data: bytes):
        """Overridden method from asyncio.Protocol. Handles partial receipt of
        a message. Calls decode_message to get an object from the serialized
        data, and adds the object to the queue.
        """
        print('received {} bytes: {}'.format(len(data), data))
        if self.rx_state == self.RxState.WAITING and len(data) > 0:
            # The message could be segmented
            buffered_len = len(self._rx_buffer)
            if buffered_len < 4:
                self._rx_buffer += data[0:4-buffered_len]
                data = data[len(self._rx_buffer):]
            if len(self._rx_buffer) == 4:
                self._rx_code, = struct.unpack('!L', self._rx_buffer)
                print('got code {}'.format(self._rx_code))
                self.rx_state = self.RxState.GOT_CODE
                self._rx_buffer = bytes()
        if self.rx_state == self.RxState.GOT_CODE and len(data) > 0:
            buffered_len = len(self._rx_buffer)
            if buffered_len < 4:
                self._rx_buffer += data[0:4-buffered_len]
                data = data[len(self._rx_buffer):]
            if len(self._rx_buffer) == 4:
                self._rx_size, = struct.unpack('!L', self._rx_buffer)
                print('got size', self._rx_size)
                self.rx_state = self.RxState.GOT_SIZE
                self._rx_buffer = bytes()
        if self.rx_state == self.RxState.GOT_SIZE:
            size = self._rx_size
            if len(self._rx_buffer) < size:
                self._rx_buffer += data[0:size]
                data = data[size:]
            if len(self._rx_buffer) == size:
                # Copy rx_buffer into response_payload
                self._rx_payload = self._rx_buffer[:]
                self.rx_state = self.RxState.GOT_PAYLOAD
                self._rx_buffer = bytes()
        if self.rx_state == self.RxState.GOT_PAYLOAD:
            resp = self.decode_message(self._rx_code, self._rx_size,
                                        self._rx_payload)
            print('got payload {}'.format(resp))
            self.rx_queue.put_nowait(resp)
            self.rx_state = self.RxState.WAITING
            self._rx_code = -1
            self._rx_size = -1

    def eof_received(self):
        """Overridden method from asyncio.Protocol.
        """
        print('EOF received')

    def send_message(self, msg: Message):
        """Serializes and sends a message over self.transport.
        """
        print('Sending {}'.format(msg))
        serialized = msg.serialize()
        self.transport.write(serialized)
