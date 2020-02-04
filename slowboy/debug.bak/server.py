import asyncio
from functools import partial
import threading
from time import sleep

from slowboy.debug.messages import *
from slowboy.debug.exceptions import *
from slowboy.debug.message_protocol import MessageProtocol
from slowboy.debug.message_handler import MessageHandler


# ------------------------------------------------------------------------------
class ServerProtocol(MessageProtocol):
    messages = commands

    def __init__(self, cmd_queue, sender):
        super().__init__(cmd_queue)
        sender.register_protocol(self)

# ------------------------------------------------------------------------------
class CommandReceiver(MessageHandler):
    def __init__(self, loop, cmd_queue, resp_queue):
        super().__init__(loop, cmd_queue)
        self.resp_queue = resp_queue

    def handle_message(self, command):
        """Overridden method called by message handler task
        """
        if command.code == ShutdownCommand.code:
            print('Received shutdown')
            self.stop()
        elif command.code == StepCommand.code:
            print('Step')
        elif command.code == ContinueCommand.code:
            print('Continue')
        elif command.code == SetBreakpointCommand.code:
            print('Breakpoint at {:#0x}'.format(command.address))
        elif command.code == ReadRegisterCommand.code:
            regid = command.register
            print('Read register {}'.format(ReadRegisterCommand.decode_register(regid)))
            resp = ReadRegisterResponse(regid, 42)
            self.resp_queue.put_nowait(resp)
        elif command.code == ReadMemoryCommand.code:
            print('Read memory at {:#0x}'.format(command.address))
            values = bytes([42] * command.length)
            resp = ReadMemoryResponse(command.address, values)
            self.resp_queue.put_nowait(resp)
        else:
            print('Unrecognized command {}'.format(command))

class ResponseSender(MessageHandler):
    def __init__(self, loop, resp_queue, protocols=[]):
        super().__init__(loop, resp_queue)
        self.protocols = protocols

    def register_protocol(self, protocol):
        self.protocols.append(protocol)

    def handle_message(self, response):
        for protocol in self.protocols:
            protocol.send_message(response)


class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def stop(self):
        #self.receiver_task.cancel()
        #self.sender_task.cancel()

        self.loop.call_soon_threadsafe(self.loop.stop)
        for task in asyncio.Task.all_tasks(loop=self.loop):
            task.cancel()

    def run(self):
        self.loop = asyncio.new_event_loop()
        self.cmd_q = asyncio.Queue(loop=self.loop)
        self.resp_q = asyncio.Queue(loop=self.loop)
        loop = self.loop

        receiver = CommandReceiver(loop, self.cmd_q, self.resp_q)
        #sender = ResponseSender(loop, self.resp_q)

        # Set up the listening server. This will enqueue commands as they arrive.
        #coro = loop.create_server(partial(ServerProtocol, self.cmd_q, sender),
        #                        '127.0.0.1', 9099, reuse_address=True)
        #server = loop.run_until_complete(coro)


        receiver_task = receiver.start()
        #sender_task = sender.start()
        self.receiver_task = receiver_task
        #self.sender_task = sender_task

        #receiver.register_shutdown_callback(lambda: server.close())
        #receiver.register_shutdown_callback(lambda: sender.stop())
        #sender.register_shutdown_callback(lambda: loop.stop())

        #print('Serving on {}'.format(server.sockets[0].getsockname()))
        #loop.run_forever()
        loop.run_until_complete(receiver_task)


server_thread = ServerThread()
server_thread.start()

try:
    while True:
        sleep(0.4)
except KeyboardInterrupt:
    server_thread.stop()
