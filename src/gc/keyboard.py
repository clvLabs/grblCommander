#!/usr/bin/python3
"""
grblCommander - keyboard
========================
Keyboard management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
from . import kbhit
from . import utils as ut

if(ut.isWindows()):      import msvcrt
if(not ut.isWindows()):  import getch

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Keyboard manager
gKey = kbhit.KBHit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressed():
  return gKey.kbhit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readKey():
  if(ut.isWindows()):
    return ord(msvcrt.getch())
  else:
    return ord(getch.getch())

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Key value constants

CTRL_X = 24
CTRL_Y = 25
CTRL_Z = 26

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

COMBO_224X = 224

F12 = 134
