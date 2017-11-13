#!/usr/bin/python3
"""
grblCommander - keyboard
========================
Keyboard management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
import sys
from . import kbhit

if 'win' in sys.platform:
  import msvcrt
else:
  import getch

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Keyboard manager
gKey = kbhit.KBHit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressed():
  return gKey.kbhit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readKey():
  if 'win' in sys.platform:
    return ord(msvcrt.getch())
  else:
    return ord(getch.getch())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Key value constants

LF=10
CR=13
CTRL_X = 24
CTRL_Y = 25
CTRL_Z = 26
ESC = 27

COMBO_0X = 0

F1 = 59
F2 = 60
F3 = 61
F4 = 62
F5 = 63
F6 = 64
F7 = 65
F8 = 66
F9 = 67
F10 = 68

KP_INS = 82
KP_DEL = 83
KP_HOME = 71
KP_END = 79
KP_PGUP = 73
KP_PGDN = 81
KP_LEFT = 75
KP_RIGHT = 77
KP_UP = 72
KP_DOWN = 80

CTRL_KP_INS = 146
CTRL_KP_DEL = 147
CTRL_KP_HOME = 119
CTRL_KP_END = 117
CTRL_KP_PGUP = 132
CTRL_KP_PGDN = 118
CTRL_KP_LEFT = 115
CTRL_KP_RIGHT = 116
CTRL_KP_UP = 141
CTRL_KP_DOWN = 145

COMBO_224X = 224

F11 = 133
F12 = 134

INS = 82
DEL = 83
HOME = 71
END = 79
PGUP = 73
PGDN = 81
LEFT = 75
RIGHT = 77
UP = 72
DOWN = 80
