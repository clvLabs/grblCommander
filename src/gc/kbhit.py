#!/usr/bin/python3
"""
grblCommander - kbhit
=======================
(copied) Keyboard hit detector
"""

# if __name__ == '__main__':
#   print('This file is a module, it should not be executed directly')

'''
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

NOTES:
- Modified on 2015/01/11 -> Code reorganized
'''

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
# KBHit class

class KBHit:

  def __init__(self):
    ''' Construct a KBHit object.
    '''

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
  def kbhit(self):
    ''' Returns True if keyboard character was hit, False otherwise.
    '''
    if os.name == 'nt':
      return msvcrt.kbhit()

    else:
      dr,dw,de = select([sys.stdin], [], [], 0)
      return dr != []


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getch(self, display=False):
    ''' Returns a keyboard character after kbhit() has been called.
    '''

    if os.name == 'nt':
      return msvcrt.getch().decode('utf-8')

    else:
      char = sys.stdin.read(1)
      if display:
        sys.stdout.write(char)
      return char


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def input(self, prompt=''):
    ''' Substitution for python's input(), switching terminals
    '''

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
    ''' Activate own terminal.  On Windows this is a no-op.
    '''

    if os.name == 'nt':
      pass
    else:
      termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetTerm(self):
    ''' Resets to normal terminal.  On Windows this is a no-op.
    '''

    if os.name == 'nt':
      pass
    else:
      termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Test
if __name__ == '__main__':

  kb = KBHit()

  print('Hit any key, or ESC to exit')

  while True:
    if kb.kbhit():
      c = kb.getch()
      if ord(c) == 27: # ESC
        break
      print(c)
