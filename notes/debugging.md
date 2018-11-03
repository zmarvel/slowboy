# Debugging

## Notes

- pass `--debug` to slowboy to get logs of the instruction being executed and
  the CPU state
- use `--trace` with gnuboy to get similar output
- I used https://github.com/mmuszkow/gb-disasm to disassemble a ROM which was
  also useful

## Implementing a debugger

The `SDLUI` class already contains some rudimentary debugging functionality:
- breakpoints
- step/continue
- memory watchpoints
- register dumps
- memory dumps

The code is admittedly a hacked-together mess, but it works. Beyond a refactor,
a proper debugger would almost certainly save some time developing the emulator,
but it would take some work on multiple levels.

### Interface

Either a curses- or GTK-based interface is my first thought. Considering
Python's threading limitations, it would have to run in a different process.
Fortunately, heavy IPC wouldn't be necessary. Interface components I picture
are:

- Source display like GDB's TUI mode
- Visually setting breakpoints
- Register display
- Displaying tile data would be neat
- Disassembling a range of memory would also be neat

A third option is implementing a GDB server, but see the next section.

### Mapping source to the current instruction

A good disassembly Python API would be a start, but for symbol information and
tracking the location in the actual source, the ability to emit debug info
from the assembler is crucial. I don't know of any GB assemblers with that
feature, but it seems doable.

Using GDB as an interface appeals to me, but it requires some investigation.
Can a GDB server provide debugging information to GDB, or does it have to
read it from the binary itself?

### Architecture

As I stated, running the debugger in another process is a must (the emulator
keeps the CPU very busy). A couple of message queues (or sockets?) seem like
a good solution. The debugger subscribes to certain events (like hit
breakpoints) and can issue commands over a socket, and the CPU sends the
debugger updated state information like register values.
