import asyncio
import threading
from functools import partial
from time import sleep

from slowboy.z80 import Z80

from slowboy.debug.message_handler import MessageHandler
from slowboy.debug.message_protocol import MessageProtocol 
from slowboy.debug.messages import (Command, ShutdownCommand, StepCommand,
                                    ContinueCommand, SetBreakpointCommand,
                                    ReadRegisterCommand, ReadMemoryCommand,
                                    DumpTilesCommand, UpdateTilesCommand,
                                    Response, ReadRegisterResponse,
                                    commands, ReadMemoryResponse, SetWatchpointCommand,
                                    HitWatchpointResponse)
from slowboy.debug.exceptions import UnrecognizedCommandException 



class DebugServerProtocol(MessageProtocol):
    """Thin subclass over `MessageProtocol`. Just enqueues received messages.

    Args:
        cmd_q (asyncio.Queue): Queue, shared with :obj:`Z80`, for storing
            received messages.
        register_cb ([MessageProtocol] -> None): Callback for registering newly
            opened connections, represented by an instance of this class, with
            the "outside world" (other classes). This way, we can actively send
            messages rather than just respond to them.
    """
    messages = commands

    def __init__(self, cmd_q, register_cb):
        super().__init__(cmd_q)
        register_cb(self)


class DebugMessageReceiver(MessageHandler):
    def __init__(self, loop, rx_queue: asyncio.Queue, resp_queue: asyncio.Queue,
                 z80: Z80):
        super().__init__(loop, rx_queue)
        self.resp_queue = resp_queue
        self.cpu = z80

    @staticmethod
    def dump_mem(mem, start=0): 
        cols = 16 
        rows = len(mem) // cols 
        addr = 0 
        for row in range(rows): 
            print('[{:04x}] '.format(start+addr), end='') 
            for col in range(cols): 
                print(' {:02x}'.format(mem[addr+col]), end='') 
            addr += cols 
            print('') 

    def handle_message(self, msg: Command):
        print('DebugMessageReceiver got', msg)
        if msg.code == ShutdownCommand.code:
            # TODO
            pass
        elif msg.code == StepCommand.code:
            # TODO this is probably not atomic
            self.cpu.step = True
            self.cpu.trace = True
        elif msg.code == ContinueCommand.code:
            self.cpu.step = False
            self.cpu.trace = False
        elif isinstance(msg, SetBreakpointCommand):
            self.cpu.set_breakpoint(msg.address)
        elif isinstance(msg, ReadRegisterCommand):
            value = self.cpu.read_register(msg.register)
            self.resp_queue.put_nowait(
                ReadRegisterResponse(msg.register, value))
        elif isinstance(msg, ReadMemoryCommand):
            addr = msg.address
            length = msg.length
            buf = bytearray(length)
            for i in range(length):
                buf[i] = self.cpu.mmu.get_addr(addr+i)
            self.resp_queue.put_nowait(
                ReadMemoryResponse(addr, bytes(buf)))
        elif msg.code == DumpTilesCommand.code:
            print('Dumping GPU tiles')
            # self.cpu.gpu.dump_tileset('tileset.bmp')
            # self.cpu.gpu.dump_background('background.bmp')
            # self.cpu.gpu.dump_foreground('foreground.bmp')
            # buf = bytearray(0x1800)
            # self.cpu.gpu.dump_tile_memory(buf)
            # self.dump_mem(buf, 0x8000)
            self.cpu.gpu.dump_regs()
        elif msg.code == UpdateTilesCommand.code:
            for i in range(128):
                self.cpu.gpu._update_tile(i)
        elif isinstance(msg, SetWatchpointCommand):
            self.cpu.mmu.add_watchpoint(msg.addr, msg.read, partial(self.hit_watchpoint, msg.addr))
        else:
            raise UnrecognizedCommandException()

    def hit_watchpoint(self, addr, value, read=False):
        # Called from the "main" (UI) thread's context, so we can't just touch resp_queue directly
        self.loop.call_soon_threadsafe(
            lambda: self.resp_queue.put_nowait(HitWatchpointResponse(addr, value, read)))
        # Now put the CPU in trace mode
        self.cpu.trace = True


class DebugMessageSender(MessageHandler):
    def __init__(self, loop, tx_queue, protocol_list):
        super().__init__(loop, tx_queue)
        self.protocol_list = protocol_list

    def handle_message(self, msg: Response):
        for protocol in self.protocol_list:
            protocol.send_message(msg)


class DebugThread(threading.Thread):
    def __init__(self, debug_address, cpu):
        super().__init__()
        self.loop = asyncio.new_event_loop()
        self.loop.set_debug(True)
        self.cmd_q = asyncio.Queue(loop=self.loop)
        self.resp_q = asyncio.Queue(loop=self.loop)
        self.debug_address = debug_address
        self.cpu = cpu

    @property
    def command_queue(self):
        return self.cmd_q

    @property
    def response_queue(self):
        return self.resp_q

    def stop(self):
        print('DebugThread begins shutdown')
        self.loop.call_soon_threadsafe(self.sender.stop)
        self.loop.call_soon_threadsafe(self.receiver.stop)
        self.loop.call_soon_threadsafe(self.server.close)

    def run(self):
        print('DebugThread started')
        loop = self.loop

        host, port = self.debug_address
        protocols = []

        coro = loop.create_server(partial(DebugServerProtocol, self.cmd_q,
                                          lambda p: protocols.append(p)),
                                  host=host, port=port,
                                  reuse_address=True)
        self.server = loop.run_until_complete(coro)

        self.receiver = DebugMessageReceiver(loop, self.cmd_q, self.resp_q, self.cpu)
        receiver_task = self.receiver.start()
        self.sender = DebugMessageSender(loop, self.resp_q, protocols)
        sender_task = self.sender.start()

        print('DebugServer started on {}'.format(self.debug_address))

        asyncio.gather(sender_task, receiver_task, loop=loop)
        loop.run_until_complete(self.server.wait_closed())

        print('DebugThread finished')

