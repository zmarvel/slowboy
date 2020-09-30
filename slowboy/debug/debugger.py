import asyncio
import bisect
import dataclasses
import functools
import sys
import io
from functools import partial
from typing import Callable, List, Dict, Type, Optional

import numpy as np
from PIL import Image

from slowboy.debug.exceptions import UnrecognizedCommandException
from slowboy.debug.message_handler import MessageHandler
from slowboy.debug.message_protocol import MessageProtocol
from slowboy.debug.messages import (Response, responses, ShutdownCommand, StepCommand,
                                    ContinueCommand, SetBreakpointCommand, ReadRegisterCommand,
                                    ReadMemoryCommand, REGISTERS, HitBreakpointResponse,
                                    ReadRegisterResponse, ReadMemoryResponse, SetWatchpointCommand,
                                    HitWatchpointResponse)


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
    return reg.lower() in REGISTERS


def int_or_hex(s: str) -> int:
    return int(s, 16 if s.startswith('0x') else 10)


# Keep these in an sorted list for now. Since things are only inserted when
# this module is initially loaded, the cost of insertion sort probably doesn't
# matter. If needed, we could use a trie or something (since I'd like to support
# e.g. `c` and `cont` as shorthand for `continue`.
_cli_commands = []  # List[str]
_cli_command_attrs = []  # List[CLICommandAttributes]


def cli_command_search(name, *args):
    # TODO this only handles subcommand depth of at most 1
    name = tuple(p for p in name.split(' ') if p != '')
    i = bisect.bisect_left(_cli_commands, name[0])
    if _cli_commands[i] != name[0]:
        raise KeyError(f'Command {name} not found')

    attrs = _cli_command_attrs[i]
    if len(name) > 1 and name[1] in attrs.subcommands:
        return attrs.subcommands[name[1]].func(*(name[2:]))
    else:
        return attrs.func(*(name[1:] + args))


@dataclasses.dataclass
class CLICommandAttributes:
    func: Callable
    nargs: int
    arg_types: List[Type]
    description: str
    help: str
    subcommands: Dict[str, 'CLICommandAttributes'] = dataclasses.field(
        default_factory=dict)


def cli_command(command: str, nargs: int = 0, arg_types: Optional[List] = None,
                description: str = '', help: str = ''):
    """Decorator for registering CLI commands.

    Args:
        command: Command name.
        nargs: Number of arguments.
        arg_types: List of argument types.
        description: Summary of command.
        help: Detailed help.
    """
    if arg_types is None:
        arg_types = []
    # Register the command
    i = bisect.bisect_left(_cli_commands, command)
    if i < len(_cli_commands) and _cli_commands[i] == command:
        raise UnrecognizedCommandException(
            f'{command} already exists in command dictionary')
    _cli_commands.insert(i, command)
    if help == '':
        help = description

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args):
            # noinspection PyShadowingNames
            converted_args = tuple(arg_types[i](arg) for i, arg in enumerate(args))
            return func(*converted_args)

        _cli_command_attrs.insert(i, CLICommandAttributes(
            func=wrapper,
            nargs=nargs,
            arg_types=arg_types,
            description=description,
            help=help
        ))
        return wrapper
    return decorator


def cli_subcommand(command: str, parent: str, nargs: int = 0,
                   arg_types: Optional[List] = None, description: str = '', help: str = ''):
    """Decorator for registering subcommands under existing CLI commands.

    Args:
        command: Subcommand name.
        parent: Name of parent command.
        nargs: Number of arguments.
        arg_types: List of argument types.
        description: Command brief.
        help: Detailed description.
    """
    if arg_types is None:
        arg_types = []

    i = bisect.bisect_left(_cli_commands, parent)
    if help == '':
        help = description

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args):
            # noinspection PyShadowingNames
            converted_args = tuple(arg_types[i](arg) for i, arg in enumerate(args))
            return func(*converted_args)

        _cli_command_attrs[i].subcommands[command] = CLICommandAttributes(
            func=wrapper,
            nargs=nargs,
            arg_types=arg_types,
            description=description,
            help=help
        )
        return wrapper
    return decorator


def cli_help():
    for cmd, attrs in zip(_cli_commands, _cli_command_attrs):
        print(f'{cmd} - {attrs.description}')
        if attrs.help:
            print(f'  {attrs.help}')
        for subcmd, subattrs in attrs.subcommands.items():
            print(f'    {subcmd} - {subattrs.description}')
            if subattrs.help:
                print(f'      {subattrs.help}')


@cli_command('help')
def command_help():
    cli_help()


@cli_command('quit', description='Quit the debugger.')
def command_quit():
    return [ShutdownCommand()]


@cli_command('step', description='In trace mode, steps forward one instruction.')
def command_step():
    return [StepCommand()]


@cli_command('continue', description=('In trace mode, continue until a breakpoint is hit or the '
                                      'system halts on its own.'))
def command_continue():
    return [ContinueCommand()]


@cli_command('breakpoint', nargs=1, arg_types=[int_or_hex], description='Add a breakpoint.')
def command_breakpoint(addr: int):
    return [SetBreakpointCommand(addr)]


@cli_command('reg', nargs=1, arg_types=[str], description='Get the value of a register')
def command_reg(reg: str):
    if not validate_register(reg):
        print("Unrecognized register: {}".format(reg))
    return [ReadRegisterCommand(reg)]


@cli_command('examine', nargs=2, arg_types=[int_or_hex, int],
             description='Examine a region of memory',
             help='examine <addr> <length>')
def command_examine(addr, length):
    return [ReadMemoryCommand(int(addr), int(length))]


@cli_command('gpu')
def command_gpu():
    pass


@cli_subcommand('dump', 'gpu', description='Dump GPU tiles and memory')
def command_gpu_dump():
    return [ReadMemoryCommand(0x8000, 0x2000)]


@cli_command('watchw', nargs=1, arg_types=[int_or_hex],
             description='Watch a byte in memory for writes')
def command_watchw(addr):
    return [SetWatchpointCommand(addr, False)]


@cli_command('watchrw', nargs=1, arg_types=[int_or_hex],
             description='Watch a byte in memory for reads or writes')
def command_watchrw(addr):
    return [SetWatchpointCommand(addr, True)]


# ------------------------------------------------------------------------------
def stdin_handler(readable: io.IOBase, transport: asyncio.Transport,
                  protocol: asyncio.Protocol, close_cb: Callable[[], None]):
    line = readable.readline().rstrip()

    cmds = cli_command_search(line) if line else [ShutdownCommand()]
    for cmd in cmds:
        protocol.send_message(cmd)

    if any(cmd.code == ShutdownCommand.code for cmd in cmds):
        transport.write_eof()
        close_cb()


# ------------------------------------------------------------------------------
class ResponseReceiver(MessageHandler):
    def __init__(self, loop: asyncio.BaseEventLoop, resp_queue: asyncio.Queue):
        super().__init__(loop, resp_queue)

    def handle_message(self, response: Response):
        """Overridden method called by message handler
        """
        if isinstance(response, HitBreakpointResponse):
            print('Hit breakpoint at {:#0x}'.format(response.address))
        elif isinstance(response, ReadRegisterResponse):
            print('Register {}: {:#0x}'.format(response.register, response.value))
        elif isinstance(response, ReadMemoryResponse):
            mem = response.values
            addr = response.address
            if addr == 0x8000 and len(mem) == 0x2000:
                # Dump GPU memory
                tile_data = mem[:0x1800]
                tile_map = mem[0x1800:]
                self._save_tile_data(tile_data, 'tiledata.bmp')
                print('Saved tiles to tiledata.bmp')
                self._save_tile_map(tile_map, 'tilemap.bin')
                print('Saved tile map to tilemap.bin')
            else:
                print(f'Address {addr:#0x}: {mem.hex()}')
        elif isinstance(response, HitWatchpointResponse):
            if response.read:
                print(f'Read watchpoint {response.addr:x}: {response.value:x}')
            else:
                print(f'Wrote watchpoint {response.addr:x}: {response.value:x}')
        else:
            print(f'Unrecognized response: {response}')

    _DEFAULT_PALETTE = [0, 0xff // 4, (0xff // 4) * 2, 0xff]

    @staticmethod
    def _decode_tile_data(tile_data: bytes) -> np.ndarray:
        from slowboy.gfx import decode_tile
        tiles = np.frombuffer(tile_data, dtype=np.uint8) \
            .reshape((-1, 16))
        decoded_tiles = np.empty((tiles.shape[0], 8, 8), dtype=np.uint32)
        for i in range(tiles.shape[0]):
            encoded_tile = tiles[i, :]
            tile = decode_tile(encoded_tile, ResponseReceiver._DEFAULT_PALETTE)
            # "convert" to RGBA
            tile = np.repeat(tile, 4)
            # set alpha=0xff
            tile[3::4] = 0xff
            tile = np.frombuffer(tile, dtype=np.uint32).reshape((8, 8))
            decoded_tiles[i, :, :] = tile[:, :]
        return decoded_tiles

    _SHEET_WIDTH = 16

    @staticmethod
    def _save_tile_data(tile_data: bytes, filename: str):
        decoded_tiles = ResponseReceiver._decode_tile_data(tile_data)
        # Make the tiles into an image
        # Number of rows of tiles in the tile sheet
        sheet_cols = ResponseReceiver._SHEET_WIDTH
        sheet_rows = decoded_tiles.shape[0] // sheet_cols
        out_image = np.empty(0, dtype=np.uint32)
        for row in range(sheet_rows):
            for tile_row in range(decoded_tiles[0].shape[1]):
                row_of_tiles = decoded_tiles[row*sheet_cols:(row+1)*sheet_cols, tile_row, :]
                out_image = np.append(out_image, row_of_tiles.flatten())
        print(set(out_image))
        img = Image.frombytes('RGBA', (sheet_cols * 8, sheet_rows * 8), out_image.tobytes())
        img.save(filename)

    @staticmethod
    def _save_tile_map(tile_map: bytes, filename: str):
        with open(filename, 'wb') as f:
            f.write(tile_map)

# ------------------------------------------------------------------------------


def main():
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


if __name__ == '__main__':
    main()
