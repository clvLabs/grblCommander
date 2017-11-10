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
    'max': {
      'X': 280.0,            # Change to fit your machine
      'Y': 280.0,            # Change to fit your machine
      'Z': 80.0,             # Change to fit your machine
    },
    'xyJogMm': 25.0,
    'zJogMm': 10.0,
    'seekSpeed': 2000,
    'feedSpeed': 50,
  },

  # ---[Macro configuration]--------------------------------------
  'macro': {
    'autoReload': True,
    'startup': 'def.start',
    'machineLongStatus': 'def.mls',
    'reservedNames': [ 'PAUSE', 'STARTUP' ],
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
    'readyMsg': '===========[ Ready ]===========',
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

}
