#grblCommander

## Synopsis

A handy tool for playing around with your grbl-controlled CNC.

Allows:

* Manually moving X/Y/Z axis at configurable steps
* Directly going to table corners / individual axis limits
* Sending raw g-code commands
* Running custom tests (read: configurable/programmable g-code)

Custom tests are currently stored on `src/test.py`:

* Point test
    * Finds current Z height at current X/Y using a custom probe (to be used with a Raspberry Pi or similar)
* Table test
    * Performs a grid check of the whole table using `Point test`
* Base levelling holes
    * Drills a series of holes targeted @ Z0 to manually level a wasteboard by sanding
* Zig-zag pattern
    * A couple tests to calculate feed and speed
    * Based on [this article](http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm)
* DUMMY
    * A test meant to be used as a sandbox

**PLEASE read the test code thoroughly before executing ANY of the tests**

## Setup

* Make sure you have Python3 installed.
* Edit `src/serialport.py` to update the `Serial configuration` section.

**TO-DO**: Add details about 3rd party library setup

## Usage

Run `python3 main.py` on the project folder and follow instructions.

**TO-DO**: Provide more details about usage
