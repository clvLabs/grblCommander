#grblCommander

## Synopsis

A handy tool for playing around with your grbl-controlled CNC.

Currently compatible with [grbl](https://github.com/gnea/grbl) v1.1

Allows:

* Manually moving X/Y/Z axis at configurable steps
* Directly going to table corners / individual axis limits
* Sending raw g-code commands
* Running custom macros, stored in separate files in a folder tree
* Running custom tests (read: configurable/programmable g-code)

Custom tests are currently stored on `src/test.py`:

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
* Make sure you have dependencies installed
    * **TO-DO**: Add details about 3rd party library setup
* Clone this repo or download and extract the .ZIP file in a local folder

### Settings
grblcommander comes with some default settings that might not suit your needs.

* Serial port configuration, machine configuration and some other general settings are stored in a configuration file.
* Some configurable features are stored as macros:
    * **Startup sequence** : GCode commands to execute at grblCommander startup
        * If you work in inches or in relative mode, make sure you check this out!
    * **Machine Long Status** : Extra commands used to gather machine status in its long version

To change the configuration file:

* Copy `src/cfg/default.py` as `src/cfg/user.py`
* Check the following sections in the new file for settings that might need to be changed:
    * `[Serial configuration]`
    * `[Machine configuration]`
* Feel free to experiment with the rest of settings!

To change the macros used in grblCommander:

* Copy the macro files in `src/macro/def` to `src/macro/u/def` (create folder)
* Edit the new macro files
* Edit `src/cfg/user.py` to:
    * Set the new macro names to be used
    * Put `def.` in th macro blackList so it's not loaded anymore
```
    'macro': {
      'startup': 'u.def.start',
      'machineLongStatus': 'u.def.mls',
      ...
      'blackList': [ 'def.' ],
```

## Usage

Run `python3 main.py` or `./main.py` on the project folder and follow instructions.

**TO-DO**: Provide more details about usage
