# slowboy

slowboy aims to be the slowest Game Boy emulator. Just kidding—but the goal of
this project isn't to create a fast emulator, since those already exist. The
goal of the project is simple: try to write an emulator in Python that will
perform reasonably on modern low-end hardware. If performance is one of the
goals, why Python? Well, another goal of the project is to provide an
easy-to-read codebase for others who want to emulate this system.

## TODO

* complete instruction set
* Graphics
* Audio

## Installation

After installing this emulator, you currently won't have anything interesting
unless you want to hack on it. If that's what you're interested in, forge ahead!


## Development

After cloning the repository, you can install the project for development with

```
$ pip install --editable .
```

You can run the tests from the root of the project with

```
$ python -m unittest discover tests
```

Additionally, if you have [coverage][coverage] installed, you can use that:

```
$ coverage --source slowboy -m unittest discover tests
```

[![Build Status](https://travis-ci.org/zmarvel/slowboy.svg?branch=master)](https://travis-ci.org/zmarvel/slowboy)

[coverage]: https://pypi.python.org/pypi/coverage/
