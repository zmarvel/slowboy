# slowboy

slowboy aims to be the slowest Gameboy emulator. Just kidding---but the goal of
this project isn't to create a fast emulator, since those already exist. The
goal is twofold: can a reasonably performant Gameboy emulator be build in
Python, and can it serve as an easy-to-read codebase for others who want to
emulate this system?

## TODO

* Audio
* Handle different bank controller configurations

See `notes/performance.md` for some thoughts on speeding up the emulator.

An eventual goal is improving the debugger---see `notes/debugging.md`.

### Test ROMs

* Test interrupts

## Installation

If you install this emulator, it probably won't play very many games. Here are
some things you *could* do:

- Try running games and create an issue if they don't run, especially if it
  crashes.
- Try running or writing the test "games" in `test_roms/` and create an issue if
  they don't work or crash on your system.

If hacking on it is what you're interested in, please forge ahead!


## Development

### Dependencies

This program uses SDL2 for graphics, and eventually the unit tests will require
some of the SDL2 data structures. Currently, it requires at least libsdl2
version 2.0.5 or greater. I'd like to eventually relax the requirement to at
most 2.0.2 to support Debian 8 and Ubuntu 16.04.

On the following distributions, the SDL2 package is too old, so you'll need to
build it from source:
- Debian 8 (2.0.2)
- Ubuntu 14.04 (2.0.2) and 16.04 (2.0.4)

I develop on Linux---these Linux distributions package at least libsdl2 version
2.0.5:
- Debian 9: `libsdl2-2.0-0` (2.0.5)
- Ubuntu 18.04: `libsdl2-2.0-0` (2.0.8)
- CentOS 7: `SDL2` (2.0.8, from EPEL---install `epel-release`)

### Installation

After cloning the repository, you can install the project for development with

```
$ pip install --editable .
```

You can run the tests from the root of the project with

```
$ pytest
```

Additionally, if you have [coverage][coverage] installed, you can use that:

```
$ coverage run --source slowboy -m unittest discover tests
$ coverage html
```

[coverage]: https://pypi.python.org/pypi/coverage/

## Known Issues

Running the unit tests with `pytest` on my system causes a segfault for some
reason. The workaround is just running the tests with `unittest`:

```
$ python -m unittest discover tests
```