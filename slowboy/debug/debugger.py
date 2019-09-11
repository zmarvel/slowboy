import asyncio
import sys
from functools import partial
import io

from messages import *
from exceptions import *
from message_protocol import MessageProtocol
from message_handler import MessageHandler

# ------------------------------------------------------------------------------
class ClientProtocol(MessageProtocol):
    messages = responses

    def __init__(self, resp_queue: asyncio.Queue):
        super().__init__(resp_queue)


# ------------------------------------------------------------------------------
def split_command(cmd: str):
    """Split `cmd` at its spaces. Additionally, strip whitespace from the ends.
    """
    return list(filter(lambda x: x != '', cmd.strip().split(' ')))


# ------------------------------------------------------------------------------
def validate_register(reg: str):
    return reg.lower() in registers


def get_command(cmd: str):
    """Turns input from stdin into Command objects
    """
    if cmd.startswith('q'):
        return ShutdownCommand()
    elif cmd.startswith('s'):
        return StepCommand()
    elif cmd.startswith('c'):
        return ContinueCommand()
    elif cmd.startswith('b'):
        cmd, addr = split_command(cmd)
        return SetBreakpointCommand(int(addr))
    elif cmd.startswith('reg'):
        cmd, reg = split_command(cmd)
        if not validate_register(reg):
            print("Unrecognized register: {}".format(reg))
        return ReadRegisterCommand(reg)
    elif cmd.startswith('x') or cmd.startswith('ex'):
        cmd, addr, length = split_command(cmd)
        return ReadMemoryCommand(int(addr), int(length))
    else:
        raise UnrecognizedCommandException(cmd)


# ------------------------------------------------------------------------------
def stdin_handler(readable: io.IOBase, transport: asyncio.Transport,
                  protocol: asyncio.Protocol, close_cb: Callable[[], None]):
    line = readable.readline().rstrip()

    cmd = get_command(line) if line else ShutdownCommand()
    protocol.send_message(cmd)

    if cmd.code == ShutdownCommand.code:
        transport.write_eof()
        close_cb()


# ------------------------------------------------------------------------------
class ResponseReceiver(MessageHandler):
    def __init__(self, loop: asyncio.BaseEventLoop, resp_queue: asyncio.Queue):
        super().__init__(loop, resp_queue)

    def handle_message(self, response: Response):
        """Overridden method called by message handler
        """
        if response.code == HitBreakpointResponse.code:
            print('Hit breakpoint at {:#0x}'.format(response.address))
        elif response.code == ReadRegisterResponse.code:
            print('Register {}: {:#0x}'.format(response.register, response.value))
        elif response.code == ReadMemoryResponse.code:
            formatted_values = ' '.join('{:#0x}'.format(value) for value in response.values)
            print('Address {:#0x}: {}'.format(response.address,
                                                  formatted_values))


# ------------------------------------------------------------------------------



loop = asyncio.get_event_loop()
# Connect to the server
resp_queue = asyncio.Queue()
receiver = ResponseReceiver(loop, resp_queue)

transport, protocol = loop.run_until_complete(
    loop.create_connection(partial(ClientProtocol, resp_queue),
                           host='127.0.0.1', port=9099))

receiver_task = receiver.start()

def shutdown_callback():
    receiver.stop()
    loop.stop()
    print('event loop shutdown')

loop.add_reader(sys.stdin, stdin_handler, sys.stdin,
                transport, protocol, shutdown_callback)
try:
    loop.run_forever()
except KeyboardInterrupt:
    print('Shutdown signal received')
    receiver.stop()
finally:
    tasks = asyncio.Task.all_tasks(loop=loop)
    loop.run_until_complete(*tasks)
    loop.stop()
    loop.close()

