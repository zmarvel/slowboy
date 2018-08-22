# slowboy

slowboy aims to be the slowest Gameboy emulator. Just kidding---but the goal of
this project isn't to create a fast emulator, since those already exist. The
goal is twofold: can a reasonably performant Gameboy emulator be build in
Python, and can it serve as an easy-to-read codebase for others who want to
emulate this system?

## TODO

* Graphics
* Audio

## Installation

After installing this emulator, you currently won't be able to do much unless
you want to hack on it. If that's what you're interested in, forge ahead!


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
$ coverage --source slowboy -m unittest discover tests
```

[coverage]: https://pypi.python.org/pypi/coverage/
