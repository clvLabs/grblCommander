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
  },

  # ---[Test configuration]--------------------------------------
  'test': {
    'password': 'IAmSure',
    'autoProbeIterations': 3,
  },

  # ---[GPIO configuration (Raspberry Pi)]----------------------------
  'gpio': {
    'probePin': 12,   # Change to match your Raspberry's probe GPIO
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
        '':             'white',    # Default
        'command':      'white+',
        'comment':      'green+',
        'macroCall':    'white+, blue',
        'reservedName': 'yellow+, blue',
        'subCallStart': 'white+, green',
        'subCallEnd':   'white+, red',
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

    'reservedNames': [ 'PAUSE' ],

    'scripts': {

      # ---[GC Macros: used by grblCommander]---------------------------------------------

      'gc.start': {
        'title': 'grblCommander - Startup sequence',
        'description': """
        This macro is called by default each time grlbCommander starts.
        Usually you will call other macros from here.
        """,
        'commands': [
          ['gc.mbs',   'Basic machine settings'],
        ],
      },

      'gc.mbs': {
        'title': 'grblCommander - Machine Basic Settings',
        'description': """
        This macro is called by default from gc.start.
        Set your preferred modal settings here.
        """,
        'commands': [
          ['G0',      'Rapid positioning'],
          ['G54',     'Machine coordinate system G54'],
          ['G17',     'XY Plane selection'],
          ['G90',     'Absolute programming'],
          ['G21',     'Programming in millimeters (mm)'],
          ['F100',    'Feed rate'],
        ],
      },

      'gc.mls': {
        'title': 'grblCommander - Machine Long Status',
        'description': """
        This macro is used by grblCommander to display extended
        machine settings in the 'Show current status (LONG)' option.
        You can customize the settings being shown and their display order here.
        """,
        'commands': [
          ['$I',      'Build info'],
          ['$N',      'Startup blocks'],
          ['$G',      'GCode parser state'],
          ['$#',      'GCode parameters'],
          ['$$',      'grbl config'],
        ],
      },

      # ---[SAMPLE Macros: You can delete these in config_user.py]----------------------------------

      'sample.1': {
        'title': 'Macro sample - 1mm feeds XYZ',
        'description': """
        This is an example on using grblCommanders' macros:
        - Each line can contain a command and/or a comment
        - Empty lines are allowed as display spacers
        - Macros can be called from macros
        - 'PAUSE' command can be used to pause execution
        """,
        'commands': [
          ['',              'Prepare machine modal settings'],
          ['G21',           'Programming in millimeters (mm)'],
          ['G91',           'Relative programming'],
          [],
          ['PAUSE',         'Pause before X axis'],
          [],
          ['',              'X axis travel'],
          ['G1 X+1 F100',   'X - Right'],
          ['G1 X-2 F100',   'X - Left'],
          ['G1 X+1 F100',   'X - Center'],
          [],
          ['PAUSE',         'Pause before Y axis'],
          [],
          ['',              'Y axis travel'],
          ['G1 Y+1 F100',   'Y - Right'],
          ['G1 Y-2 F100',   'Y - Left'],
          ['G1 Y+1 F100',   'Y - Center'],
          [],
          ['PAUSE',         'Pause before Z axis'],
          [],
          ['',              'Z axis travel'],
          ['G1 Z+1 F100',   'Z - Right'],
          ['G1 Z-2 F100',   'Z - Left'],
          ['G1 Z+1 F100',   'Z - Center'],
          [],
          ['gc.mbs',         'Restore machine modal settings'],
        ],
      },

      'sample.2': {
        'title': 'Macro example - simple X0Y0Z0 rapid',
        'commands': [
          ['G0 X0Y0'],
          ['G0 Z0'],
        ],
      },

      # ---[USER Macros]--------------------------------------

    },
  },

}
