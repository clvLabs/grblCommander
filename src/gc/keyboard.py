#!/usr/bin/python3
'''
grblCommander - keyboard
========================
Keyboard management

Derived from kbhit:
A Python class implementing KBHIT, the standard keyboard-interrupt poller.
Works transparently on Windows and Posix (Linux, Mac OS X).  Doesn't work
with IDLE.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
import sys
import os

# Windows
if os.name == 'nt':
  import msvcrt

# Posix (Linux, OS X)
else:
  import sys
  import termios
  import atexit
  from select import select

# ------------------------------------------------------------------
# Keyboard class

class Keyboard:

  def __init__(self):
    ''' Construct a Keyboard object. '''
    self.initKeyValueConstants()

    if os.name == 'nt':
      pass
    else:
      # Save the terminal settings
      self.fd = sys.stdin.fileno()
      self.old_term = termios.tcgetattr(self.fd)

      # New terminal setting unbuffered
      self.new_term = termios.tcgetattr(self.fd)
      self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)

      self.setOwnTerm()

      # Support normal-terminal reset at exit
      atexit.register(self.resetTerm)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def keyPressed(self):
    ''' Returns True if keyboard character was hit, False otherwise. '''
    if os.name == 'nt':
      return msvcrt.kbhit()

    else:
      dr,dw,de = select([sys.stdin], [], [], 0)
      return dr != []


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def ch2key(self, ch):
    return ord(ch)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getch(self, display=False):
    ''' Returns a keyboard character. '''
    try:
      if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')

      else:
        char = sys.stdin.read(1)
        if display:
          sys.stdout.write(char)
        return char

    except Exception as e:
      print('keyboard.py: EXCEPTION reading keyboard: {:}'.format(str(e)))
      return 0

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getKey(self):
    return self.ch2key(self.getch())
    ''' Returns a Key object. '''


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def input(self, prompt=''):
    ''' Substitution for python's input(), switching terminals '''

    sys.stdout.write(prompt)

    # Set non-blocking flag for stdio
    os.set_blocking(self.fd, False)

    # Flush keyboard buffer into return value
    kbBuffer = ''
    enterBuffered = False
    char = self.getch(True)

    while char:
      kbBuffer += char

      if ord(char) == 10:
        enterBuffered = True

      char = self.getch(True)

    # Reet blocking flag for stdio
    os.set_blocking(self.fd, True)

    if enterBuffered:
      retVal = kbBuffer
    else:
      self.resetTerm()
      retVal = kbBuffer + input()
      self.setOwnTerm()

    return retVal


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def setOwnTerm(self):
    ''' Activate own terminal.  On Windows this is a no-op. '''

    if os.name == 'nt':
      pass
    else:
      termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetTerm(self):
    ''' Resets to normal terminal.  On Windows this is a no-op. '''

    if os.name == 'nt':
      pass
    else:
      termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def initKeyValueConstants(self):
    self.LF = 10
    self.CR  = 13
    self.ENTER = self.LF
    self.CTRL_R = 18
    self.CTRL_X = 24
    self.CTRL_Y = 25
    self.CTRL_Z = 26
    self.ESC = 27

    self.COMBO_0X = 0

    self.F1 = 59
    self.F2 = 60
    self.F3 = 61
    self.F4 = 62
    self.F5 = 63
    self.F6 = 64
    self.F7 = 65
    self.F8 = 66
    self.F9 = 67
    self.F10 = 68

    self.KP_INS = 82
    self.KP_DEL = 83
    self.KP_HOME = 71
    self.KP_END = 79
    self.KP_PGUP = 73
    self.KP_PGDN = 81
    self.KP_LEFT = 75
    self.KP_RIGHT = 77
    self.KP_UP = 72
    self.KP_DOWN = 80

    self.CTRL_KP_INS = 146
    self.CTRL_KP_DEL = 147
    self.CTRL_KP_HOME = 119
    self.CTRL_KP_END = 117
    self.CTRL_KP_PGUP = 132
    self.CTRL_KP_PGDN = 118
    self.CTRL_KP_LEFT = 115
    self.CTRL_KP_RIGHT = 116
    self.CTRL_KP_UP = 141
    self.CTRL_KP_DOWN = 145

    self.COMBO_224X = 224

    self.F11 = 133
    self.F12 = 134

    self.INS = 82
    self.DEL = 83
    self.HOME = 71
    self.END = 79
    self.PGUP = 73
    self.PGDN = 81
    self.LEFT = 75
    self.RIGHT = 77
    self.UP = 72
    self.DOWN = 80
    ''' Shares a few common key codes '''
