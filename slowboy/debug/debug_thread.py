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
                                    Response, ReadRegisterResponse,
                                    commands)
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

    def handle_message(self, msg: Command):
        print('DebugMessageReceiver got', msg)
        if msg.code == ShutdownCommand.code:
            # TODO
            pass
        elif msg.code == StepCommand.code:
            # TODO this is probably not atomic
            self.cpu.trace = True
        elif msg.code == ContinueCommand.code:
            self.cpu.trace = False
        elif msg.code == SetBreakpointCommand.code:
            self.cpu.set_breakpoint(msg.address)
        elif msg.code == ReadRegisterCommand.code:
            value = self.cpu.read_register(ReadRegisterCommand.decode_register(
                msg.register))
            self.resp_queue.put_nowait(
                ReadRegisterResponse(msg.register, value))
        elif msg.code == ReadMemoryCommand.code:
            addr = msg.address
            length = msg.length
            for i in range(addr, length):
                print(self.cpu.mmu.get_addr(addr))
        else:
            raise UnrecognizedCommandException()





class DebugMessageSender(MessageHandler):
    def __init__(self, loop, tx_queue, protocol_list):
        super().__init__(loop, tx_queue)
        self.protocol_list = protocol_list

    def handle_message(self, msg: Response):
        print('DebugMessageSender got', msg)
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

    def run(self):
        print('DebugThread started')
        loop = self.loop

        host, port = self.debug_address
        protocols = []

        coro = loop.create_server(partial(DebugServerProtocol, self.cmd_q,
                                          lambda p: protocols.append(p)),
                                  host=host, port=port,
                                  reuse_address=True)
        server = loop.run_until_complete(coro)
        self.server = server

        receiver = DebugMessageReceiver(loop, self.cmd_q, self.resp_q, self.cpu)
        receiver_task = receiver.start()
        #receiver_task = self.start()
        #register_shutdown_callback(lambda: self.server.close())
        #register_shutdown_callback(lambda: self.loop.stop())
        sender = DebugMessageSender(loop, self.resp_q, protocols)
        sender_task = sender.start()
        sender.register_shutdown_callback(lambda: server.close())
        sender.register_shutdown_callback(lambda: loop.stop())
        self.sender = sender

        print('DebugServer started on {}'.format(self.debug_address))

        #loop.run_forever()
        asyncio.gather(sender_task, receiver_task, loop=loop)
        loop.run_until_complete(server.wait_closed())

        print('DebugThread finished')


