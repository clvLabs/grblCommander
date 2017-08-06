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
def keyPressed():
  return kbhit.KBHit().kbhit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readKey():
  if(ut.isWindows()):
    return ord(msvcrt.getch())
  else:
    return ord(getch.getch())
