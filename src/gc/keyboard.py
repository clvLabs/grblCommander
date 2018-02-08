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

from . import ui as ui    # [DBG] !!!!!

def DBG(msg):
  ui.log('[DBG] {:}'.format(msg), c='red, yellow')


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
# Key list (defined here, redeclared & filled below)

KEY_LIST = {}


# ------------------------------------------------------------------
# Key class

class Key:

  def __init__(self, n=None, k=None, c=None, c0x=None, c224x=None):

    # Make sure we have both key and char
    assert k or c
    if not k:      k = ord(c)
    try:
      if not c:      c = chr(k)
    except ValueError:
      c = '?'

    self.n = n          # name
    self.k = k          # key
    self.c = c          # char
    self.c0x = c0x      # combo 0X
    self.c224x = c224x  # comgo 224x


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _in(self, coll):
    ''' Checks if key is the provided collection.
        Collection can be:
          - A string representing a key name => 'CTRL_X'
          - A string representing a list of chars => 'yYnN'
          - A list of strings in any of the above formats
    '''
    if type(coll) is str:
      if coll in KEY_LIST:
        return coll == self.n

      if self.c in coll:
        return True

    elif type(coll) is list:

      for c in coll:
        if self._in(c):
          return True

    else:
      print('Unknown collection type')
      assert False

    return False

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
  def _getch(self, display=False):
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
    ''' Returns a Key object. '''
    char = self._getch()
    charVal = ord(char)
    DBG('k[{:}] c[{:}]'.format(charVal, char))

    key = None
    c0x = None
    c224x = None

    # 'COMBO_0X'
    if charVal == 0:
      DBG('c0x!')
      c0x = 1
      # Get next code
      char = self._getch()
      charVal = ord(char)

      for name in self.k:
        k = self.k[name]
        if k.c0x and k.k == charVal:
          key = k
          break

    # 'COMBO_224X'
    elif charVal == 224:
      DBG('c224x!')
      c224x = 1

      # Get next code
      char = self._getch()
      charVal = ord(char)

      for name in self.k:
        k = self.k[name]
        if k.c224x and k.k == charVal:
          key = k
          break

    # 'Normal' keys
    else:
      for name in self.k:
        k = self.k[name]
        if k.k == charVal:
          key = k
          break

    if not key:
      key = Key(n=char, k=charVal, c0x=c0x, c224x=c224x)

    return key


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def input(self, prompt=''):
    ''' Substitution for python's input(), switching terminals '''

    sys.stdout.write(prompt)

    # Set non-blocking flag for stdio
    os.set_blocking(self.fd, False)

    # Flush keyboard buffer into return value
    kbBuffer = ''
    enterBuffered = False
    char = self._getch(True)

    while char:
      kbBuffer += char

      if ord(char) == 10:
        enterBuffered = True

      char = self._getch(True)

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
      DBG('SetOwnTerm! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetTerm(self):
    ''' Resets to normal terminal.  On Windows this is a no-op. '''

    if os.name == 'nt':
      pass
    else:
      termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)
      DBG('RESETTerm! <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def initKeyValueConstants(self):
    ''' Shares a few common key codes '''
    self.noKey = Key(n='NONE', k=-1)

    self.k = KEY_LIST


# ------------------------------------------------------------------
# Key list

KEY_LIST = {
  'ENTER': Key(n='ENTER', k=10),
  'CR': Key(n='CR', k=13),
  'ESC': Key(n='ESC', k=27),

  'CTRL_R': Key(n='CTRL_R', k=18),
  'CTRL_X': Key(n='CTRL_X', k=24),
  'CTRL_Y': Key(n='CTRL_Y', k=25),
  'CTRL_Z': Key(n='CTRL_Z', k=26),

  'F1': Key(n='F1', k=59, c0x=1),
  'F2': Key(n='F2', k=60, c0x=1),
  'F3': Key(n='F3', k=61, c0x=1),
  'F4': Key(n='F4', k=62, c0x=1),
  'F5': Key(n='F5', k=63, c0x=1),
  'F6': Key(n='F6', k=64, c0x=1),
  'F7': Key(n='F7', k=65, c0x=1),
  'F8': Key(n='F8', k=66, c0x=1),
  'F9': Key(n='F9', k=67, c0x=1),
  'F10': Key(n='F10', k=68, c0x=1),
  'F11': Key(n='F11', k=133, c224x=1),
  'F12': Key(n='F12', k=134, c224x=1),

  'INS': Key(n='INS', k=82, c224x=1),
  'DEL': Key(n='DEL', k=83, c224x=1),
  'HOME': Key(n='HOME', k=71, c224x=1),
  'END': Key(n='END', k=79, c224x=1),
  'PGUP': Key(n='PGUP', k=73, c224x=1),
  'PGDN': Key(n='PGDN', k=81, c224x=1),
  'LEFT': Key(n='LEFT', k=75, c224x=1),
  'RIGHT': Key(n='RIGHT', k=77, c224x=1),
  'UP': Key(n='UP', k=72, c224x=1),
  'DOWN': Key(n='DOWN', k=80, c224x=1),

  'KP_INS': Key(n='KP_INS', k=82, c0x=1),
  'KP_DEL': Key(n='KP_DEL', k=83, c0x=1),
  'KP_HOME': Key(n='KP_HOME', k=71, c0x=1),
  'KP_END': Key(n='KP_END', k=79, c0x=1),
  'KP_PGUP': Key(n='KP_PGUP', k=73, c0x=1),
  'KP_PGDN': Key(n='KP_PGDN', k=81, c0x=1),
  'KP_LEFT': Key(n='KP_LEFT', k=75, c0x=1),
  'KP_RIGHT': Key(n='KP_RIGHT', k=77, c0x=1),
  'KP_UP': Key(n='KP_UP', k=72, c0x=1),
  'KP_DOWN': Key(n='KP_DOWN', k=80, c0x=1),

  'CTRL_KP_INS': Key(n='CTRL_KP_INS', k=146, c0x=1),
  'CTRL_KP_DEL': Key(n='CTRL_KP_DEL', k=147, c0x=1),
  'CTRL_KP_HOME': Key(n='CTRL_KP_HOME', k=119, c0x=1),
  'CTRL_KP_END': Key(n='CTRL_KP_END', k=117, c0x=1),
  'CTRL_KP_PGUP': Key(n='CTRL_KP_PGUP', k=132, c0x=1),
  'CTRL_KP_PGDN': Key(n='CTRL_KP_PGDN', k=118, c0x=1),
  'CTRL_KP_LEFT': Key(n='CTRL_KP_LEFT', k=115, c0x=1),
  'CTRL_KP_RIGHT': Key(n='CTRL_KP_RIGHT', k=116, c0x=1),
  'CTRL_KP_UP': Key(n='CTRL_KP_UP', k=141, c0x=1),
  'CTRL_KP_DOWN': Key(n='CTRL_KP_DOWN', k=145, c0x=1),
}
