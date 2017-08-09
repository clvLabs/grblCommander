#!/usr/bin/python3
"""
grblCommander - default configuration
=====================================
PLEASE DO NOT CHANGE config_default.py UNLESS YOU KNOW WHAT YOU'RE DOING

To change your personal settings please make a copy of this file,
  rename as config_user.py and edit as needed.
"""

if __name__ == '__main__':
  print('This is a configuration file, it should not be executed directly')

# Configuration object
cfg = {

  # ---[Serial configuration]--------------------------------------
  'serial': {
    'baudRate': 115200,
    'portWindows': 3,              # Change to match your Arduino's COM port
    'portLinux': '/dev/ttyACM0',   # Change to match your Arduino's COM port
    'timeout': 0.1,
    'responseTimeout': 2,
  },

  # ---[GPIO configuration (Raspberry Pi)]----------------------------
  'gpio': {
    'probePin': 12,   # Change to match your Raspberry's probe GPIO
  },

  # ---[Machine configuration]--------------------------------------
  'machine': {
    'maxX': 280.0,            # Change to fit your machine
    'maxY': 280.0,            # Change to fit your machine
    'maxZ': 80.0,             # Change to fit your machine
    'zSafeHeight': 5.0,
    'rapidXY': 25.0,
    'rapidZ': 10.0,
    'tableSizePercent': 100,
    'seekSpeed': 2000,
    'feedSpeed': 50,

    'startupMacro': 'startup',
  },

  # ---[Test configuration]--------------------------------------
  'test': {
    'password': 'IAmSure',
    'autoProbeIterations': 3,
  },

  # ---[Interface configuration]--------------------------------------
  'ui': {
    'verboseLevel': 'WARNING',
    'maxLineLen': 80,
    'clearScreenLines': 100,
    'inputTitleWidth': 45,
    'readyMsg': '==================[ Ready ]==================',
    'coordFormat': '{:.3f}',
    'xyzFormat': '[{:}/{:}/{:}]',
    'msgSeparatorChar': '-',
    'titleSeparatorChar': '-',
    'blockSeparatorChar': '*',

    'colors': {
      'ui': {
        '':                     'white',    # Default
        'title':                'white+',
        'subtitle':             'white+',
        'header':               'cyan+',
        'onlineMachineStatus':  'yellow+',
        'machinePosDiff':       'yellow+, red',
        'info':                 'white',
        'msg':                  'yellow+',
        'keyPressMsg':          'cyan+',
        'readyMsg':             'yellow+, magenta',
        'inputMsg':             'yellow+, magenta',
        'errorMsg':             'yellow+, red',
        'cancelMsg':            'white+, red',
        'confirmMsg':           'magenta+',
        'finishedMsg':          'white+, green',
        'waiting':              'cyan+',
      },

      'macro': {
        '':         'white',    # Default
        'command':  'white+',
        'comment':  'green+',
      },

      'comms': {
        '':         'white',    # Default
        'send':     'yellow+, blue',
        'recv':     'green+, blue',
      },

      'machineState': {
        '':         'red+',    # Default
        'Idle':     'green',
        'Run':      'white+, green',
        'Hold':     'red',
        'Jog':      'cyan+',
        'Alarm':    'yellow+, red',
        'Door':     'yellow+, red',
        'Check':    'yellow+, red',
        'Home':     'yellow+',
        'Sleep':    'yellow+',
      },
    },
  },

  # ---[Macro configuration]--------------------------------------
  'macro': {

    'scripts': {

      'startup': {
        'description': 'Startup sequence for grblCommander',
        'commands': [
          ['G0',      'Rapid positioning'],
          ['G54',     'Machine coordinate system G54'],
          ['G17',     'XY Plane selection'],
          ['G90',     'Absolute programming'],
          ['G21',     'Programming in millimeters (mm)'],
          ['F100',    'Feed rate'],
        ],
      },

      'demo': {
        'description': 'Macro example - star pattern XYZ',
        'commands': [
          ['',              'This is a sample macro used to demonstrate'],
          ['',              'the use of macros in grblCommander.'],
          ['',              ''],
          ['',              'It will move the bit with a speed of 100 for 1mm'],
          ['',              'in XYZ axis in both directions from the current spot.'],
          ['',              ''],
          ['',              'WARNING: This macro will leave your machine working in mm (G21)'],
          ['',              ''],
          ['G21',           'Make sure we work in mm'],
          ['G91',           'Set relative programming (TEMPORARY)'],
          ['',              ''],
          ['G1 X+1 F100',   'X - Right'],
          ['G1 X-2 F100',   'X - Left'],
          ['G1 X+1 F100',   'X - Center'],
          ['',              ''],
          ['G1 Y+1 F100',   'Y - Right'],
          ['G1 Y-2 F100',   'Y - Left'],
          ['G1 Y+1 F100',   'Y - Center'],
          ['',              ''],
          ['G1 Z+1 F100',   'Z - Right'],
          ['G1 Z-2 F100',   'Z - Left'],
          ['G1 Z+1 F100',   'Z - Center'],
          ['',              ''],
          ['G90',           'Restore absolute programming'],
        ],
      },

      'simple': {
        'description': 'Simple macro example - X0Y0Z0 rapid',
        'commands': [
          ['G0 X0Y0'],
          ['G0 Z0'],
        ],
      },

      # ---[OWN Macros]--------------------------------------

    },
  },

}
