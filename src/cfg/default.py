#!/usr/bin/python3
"""
grblCommander - default configuration
=====================================
PLEASE DO NOT CHANGE config_default.py UNLESS YOU KNOW WHAT YOU'RE DOING

To change your personal settings please make a copy of this file,
  rename as user.py and edit as needed.
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
    'maxTravel': {
      'x': 280.0,            # Change to fit your machine
      'y': 280.0,            # Change to fit your machine
      'z': 80.0,             # Change to fit your machine
    },
    'softLimitsMargin': 1.0,
    'xyJogMm': 10.0,
    'zJogMm': 3.0,
    'seekSpeed': 2000,
    'feedSpeed': 400,
    'homingTimeout': 20,
    'probing': {
      'feedFast': 250,
      'feedMedium': 50,
      'feedSlow': 5,
      'interStagePulloff': 0.5,
      'pulloff': 1.0,
      'touchPlateHeight': 1.0,
      'timeout': 20,
    },
    'preferredParserState': {
      'coolant': 'M9',          # Change to fit your preferences
      'distanceMode': 'G90',    # Change to fit your preferences
      'feedRateMode': 'G94',    # Change to fit your preferences
      'motion': 'G0',           # Change to fit your preferences
      'plane': 'G17',           # Change to fit your preferences
      'spindle': 'M5',          # Change to fit your preferences
      'units': 'G21',           # Change to fit your preferences
      'wcs': 'G54',             # Change to fit your preferences
    },
  },

  # ---[Joystick configuration]--------------------------------------
  'joystick': {                 # Change to fit your joystick
    'name': 'joystickName',
    'axes': {
      0: {
        'axis': 'y',
        'invert': True,
      },
      1: {
        'axis': 'x',
        'invert': True,
      },
    },
    'buttons': {
      0: 'z-',
      1: 'extraD',
      3: 'extraU',
      4: 'z+',
    },
  },

  # ---[Macro configuration]--------------------------------------
  'macro': {
    'autoReload': True,
    'startup': 'def.start',
    'machineLongStatus': 'def.mls',
    'reservedNames': [ 'pause', 'startup', 'sleep' ],
    'blackList': [ ],
    'hotKeys': {
      'F1': '',
      'F2': '',
      'F3': '',
      'F4': '',
      'F5': '',
      'F6': '',
      'F7': '',
      'F8': '',
      'F9': '',
      'F10': '',
    },
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
    'maxLineLen': 100,
    'clearScreenLines': 100,
    'inputTitleWidth': 45,
    'readyMsg': '==========================[ Ready ]==========================',
    'simpleParserState': {
      'distanceMode': 'G90',    # Change to fit your preferences
      'motion': 'G0',           # Change to fit your preferences
      'units': 'G21',           # Change to fit your preferences
      'wcs': 'G54',             # Change to fit your preferences
    },
    'coordFormat': '{:8.3f}',
    'xyzFormat': '{:}/{:}/{:}',
    'msgSeparatorChar': '-',
    'titleSeparatorChar': '-',
    'blockSeparatorChar': '*',

    'colors': {
      'ui': {
        '':                  'white',    # Default
        'title':             'white+',
        'subtitle':          'white+',
        'header':            'cyan+',
        'onlineMachinePos':  'yellow+',
        'info':              'white',
        'msg':               'yellow+',
        'keyPressMsg':       'cyan+',
        'readyMsg':          'yellow+, magenta',
        'inputMsg':          'yellow+, magenta',
        'successMsg':        'green+',
        'errorMsg':          'yellow+, red',
        'cancelMsg':         'white+, red',
        'confirmMsg':        'magenta+',
        'finishedMsg':       'white+, green',
        'waiting':           'cyan+',
      },

      'macro': {
        '':             'white',    # Default
        'command':      'white+',
        'comment':      'green+',
        'macroCall':    'white+, blue',
        'reservedName': 'green+, blue',
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

}
