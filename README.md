#grblCommander

## Synopsis

A handy tool for playing around with your grbl-controlled CNC.

Currently compatible with [grbl](https://github.com/gnea/grbl) v1.1

Allows:

* Manually moving X/Y/Z axis at configurable steps
* Directly going to table corners / individual axis limits
* Sending raw g-code commands
* Running custom macros, stored in the configuration file
* Running custom tests (read: configurable/programmable g-code)

Custom tests are currently stored on `src/test.py`:

* Point probe
    * Finds current Z height at current X/Y using a custom probe (to be used with a Raspberry Pi or similar)
* Table probing scan
    * Performs a grid check of the whole table using `Point probe`
* Table position scan
    * Moves the spindle around a 3x3 grid representing the coordinates:
        * [UL] [UC] [UR]
        * [CL] [CC] [CR]
        * [DL] [DC] [DR]
* Base levelling holes
    * Drills a series of holes targeted @ Z0 to manually level a wasteboard by sanding
* Zig-zag pattern
    * A couple tests to calculate feed and speed
    * Based on [this article](http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm)
* DUMMY
    * A test meant to be used as a sandbox

**PLEASE read the test code thoroughly before executing ANY of the tests**

## Setup

* Make sure you have Python3 installed
* Copy `src/config_default.py` as `src/config_user.py`
* Check the following sections in the new file for settings that need to be changed:
    * `[Serial configuration]`
    * `[GPIO configuration]`
    * `[Machine configuration]`

**TO-DO**: Add details about 3rd party library setup

## Usage

Run `python3 main.py` on the project folder and follow instructions.

**TO-DO**: Provide more details about usage
