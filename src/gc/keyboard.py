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
import threading
import queue

# Windows
if os.name == 'nt':
  import msvcrt

# Posix (Linux, OS X)
else:
  import termios
  import atexit
  from select import select

# ------------------------------------------------------------------
# Key list (defined here, redeclared & filled below)

KEY_LIST = {}


# ------------------------------------------------------------------
# Key class

class Key:

  def __init__(self, n=None, k=None, c=None):

    if not k:
      k = ord(c)

    try:
      if not c:
        if type(k) is int:
          c = chr(k)
        else:
          c= '<?>'
    except ValueError:
      c = '<?>'

    if not n:
      n = '{:} (key {:})'.format(c, k)

    self.n = n      # name
    self.k = k      # key
    self.c = c      # char

    self.keyList = KEY_LIST

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _in(self, coll):
    ''' Checks if key is the provided collection.
      Collection can be:
        - A string representing a key name => 'CTRL_X'
        - A string representing a list of chars => 'yYnN'
        - A list of strings in any of the above formats
    '''
    if type(coll) is str:
      if coll in self.keyList:
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
# KBThread class

class KBThread(threading.Thread):
  ''' Keyboard watcher thread '''

  SLEEP_TIME = 0.0005
  outQueue = None    # Queue for char output
  lastTime = 0

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def __init__(self, fd, outQueue):
    super().__init__()
    self.fd = fd
    self.outQueue = outQueue
    self._stopEvent = threading.Event()
    self._runningEvent = threading.Event()
    self.resume()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stop(self):
      self._stopEvent.set()
      self.resume()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stopped(self):
      return self._stopEvent.is_set()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def pause(self):
      self._runningEvent.clear()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resume(self):
      self._runningEvent.set()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def paused(self):
      return not self._runningEvent.is_set()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def run(self):
    while True:

      c = None
      while not c:
        self._runningEvent.wait()
        if self.stopped():
          return
        c = self._getch()
        if not c:
          time.sleep(self.SLEEP_TIME)

      curTime = time.time()
      elapsed = curTime - self.lastTime
      self.lastTime = curTime

      self.outQueue.put((c, elapsed,))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _getch(self):
    ''' Returns a keyboard character. '''
    try:
      if os.name == 'nt':
        return msvcrt.getch().decode('utf-8')

      else:
        os.set_blocking(self.fd, False)
        char = sys.stdin.read(1)
        os.set_blocking(self.fd, True)
        return char

    except Exception as e:
      print(
        'keyboard.py: EXCEPTION reading keyboard: {:}'.format(str(e)))
      return '\0'


# ------------------------------------------------------------------
# Keyboard class

class Keyboard:

  MBTIME = 0.001 # MultiByte threshold time
  nextChar = None

  def __init__(self):
    ''' Construct a Keyboard object. '''
    self.initKeyValueConstants()

    # Setup keyboard
    if os.name == 'nt':
      pass
    else:
      # Save the terminal settings
      self.fd = sys.stdin.fileno()
      self.old_term = termios.tcgetattr(self.fd)

      # New terminal setting unbuffered
      self.new_term = termios.tcgetattr(self.fd)
      self.new_term[3] = (self.new_term[3] & ~
                termios.ICANON & ~termios.ECHO)

      self.setOwnTerm()

      # Support normal-terminal reset at exit
      atexit.register(self.resetTerm)

    # Setup listener thread
    self.charQueue = queue.Queue()
    self.listener = KBThread(self.fd, self.charQueue)
    self.listener.start()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stop(self):
    self.listener.stop()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def keyPressed(self):
    ''' Returns True if keyboard character was hit, False otherwise. '''
    return not self.charQueue.empty()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getKey(self):
    ''' Returns a Key object. '''

    # Wait for a key !!!!
    while not self.keyPressed() and not self.nextChar:
      pass

    if self.nextChar:
      char, elapsed = self.nextChar, 0
      self.nextChar = None
    else:
      char, elapsed = self.charQueue.get_nowait()

    charVal = ord(char)

    cmd = ''

    if charVal == 27:
      time.sleep(self.MBTIME)
      if self.keyPressed():
        cmd += char
        cmdLen = self.charQueue.qsize()
        for i in range(cmdLen):
          char, elapsed = self.charQueue.get_nowait()
          if elapsed < self.MBTIME:
            cmd += char
          else:
            self.nextChar = char
            break

    if cmd == '':
      cmd = None

    key = None

    for name in self.keyList:
      k = self.keyList[name]

      if not cmd and type(k.k) is int:
        if k.k == charVal:
          key = k
          break
      elif type(k.k) is str:
        if k.k == cmd:
          key = k
          break
      else:
        pass

    if not key:
      if cmd:
        key = Key(n='UNKNOWN: <ESC>[{:}]'.format(cmd[1:]), k=cmd)
      else:
        key = Key(c=char, k=charVal)

    return key

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def input(self, prompt=''):
    ''' Substitution for python's input(), switching terminals '''

    self.listener.pause()
    sys.stdout.write(prompt)

    # Flush keyboard buffer into return value
    kbBuffer = ''
    enterBuffered = False

    if False:   # TODO: Fix (not working)

      # Set non-blocking flag for stdio
      os.set_blocking(self.fd, False)

      key = self.getKey()

      while key.c:
        kbBuffer += key.c

        if key.k == 10:
          enterBuffered = True

        key = self.getKey()

      # Reet blocking flag for stdio
      os.set_blocking(self.fd, True)

    if enterBuffered:
      retVal = kbBuffer
    else:
      self.resetTerm()
      retVal = kbBuffer + input()
      self.setOwnTerm()

    self.listener.resume()

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
    ''' Shares a few common key codes '''
    self.noKey = Key(n='NONE', k=-1)

    self.keyList = {}

    for k in KEY_LIST:
      self.keyList[k] = Key(n=k, **KEY_LIST[k])


# ------------------------------------------------------------------
# Key list

KEY_LIST = {
  'ENTER': {'k': 10},
  'CR': {'k': 13},
  'ESC': {'k': 27},

  'CTRL_R': {'k': 18},
  'CTRL_X': {'k': 24},
  'CTRL_Y': {'k': 25},
  'CTRL_Z': {'k': 26},

  'CUR_UP': {'k': '\x1b[A'},
  'CUR_DOWN': {'k': '\x1b[B'},
  'CUR_RIGHT': {'k': '\x1b[C'},
  'CUR_LEFT': {'k': '\x1b[D'},

  'SHIFT_CUR_UP': {'k': '\x1b[1;2A'},
  'SHIFT_CUR_DOWN': {'k': '\x1b[1;2B'},
  'SHIFT_CUR_RIGHT': {'k': '\x1b[1;2C'},
  'SHIFT_CUR_LEFT': {'k': '\x1b[1;2D'},

  'CTRL_CUR_UP': {'k': '\x1b[1;5A'},
  'CTRL_CUR_DOWN': {'k': '\x1b[1;5B'},
  'CTRL_CUR_RIGHT': {'k': '\x1b[1;5C'},
  'CTRL_CUR_LEFT': {'k': '\x1b[1;5D'},

  'F1': {'k': '\x1bOP'},
  'F2': {'k': '\x1bOQ'},
  'F3': {'k': '\x1bOR'},
  'F4': {'k': '\x1bOS'},
  'F5': {'k': '\x1b[15~'},
  'F6': {'k': '\x1b[17~'},
  'F7': {'k': '\x1b[18~'},
  'F8': {'k': '\x1b[19~'},
  'F9': {'k': '\x1b[20~'},
  'F10': {'k': '\x1b[21~'},
  'F11': {'k': '\x1b[23~'},
  'F12': {'k': '\x1b[24~'},

  'SHIFT_F1': {'k': '\x1bO1;2P'},
  'SHIFT_F2': {'k': '\x1bO1;2Q'},
  'SHIFT_F3': {'k': '\x1bO1;2R'},
  'SHIFT_F4': {'k': '\x1bO1;2S'},
  'SHIFT_F5': {'k': '\x1b[15;2~'},
  'SHIFT_F6': {'k': '\x1b[17;2~'},
  'SHIFT_F7': {'k': '\x1b[18;2~'},
  'SHIFT_F8': {'k': '\x1b[19;2~'},
  'SHIFT_F9': {'k': '\x1b[20;2~'},
  'SHIFT_F10': {'k': '\x1b[21;2~'},
  'SHIFT_F11': {'k': '\x1b[23;2~'},
  'SHIFT_F12': {'k': '\x1b[24;2~'},

  'ALT_F1': {'k': '\x1bO1;3P'},
  'ALT_F2': {'k': '\x1bO1;3Q'},
  'ALT_F3': {'k': '\x1bO1;3R'},
  'ALT_F4': {'k': '\x1bO1;3S'},
  'ALT_F5': {'k': '\x1b[15;3~'},
  'ALT_F6': {'k': '\x1b[17;3~'},
  'ALT_F7': {'k': '\x1b[18;3~'},
  'ALT_F8': {'k': '\x1b[19;3~'},
  'ALT_F9': {'k': '\x1b[20;3~'},
  'ALT_F10': {'k': '\x1b[21;3~'},
  'ALT_F11': {'k': '\x1b[23;3~'},
  'ALT_F12': {'k': '\x1b[24;3~'},

  'CTRL_F1': {'k': '\x1bO1;5P'},
  'CTRL_F2': {'k': '\x1bO1;5Q'},
  'CTRL_F3': {'k': '\x1bO1;5R'},
  'CTRL_F4': {'k': '\x1bO1;5S'},
  'CTRL_F5': {'k': '\x1b[15;5~'},
  'CTRL_F6': {'k': '\x1b[17;5~'},
  'CTRL_F7': {'k': '\x1b[18;5~'},
  'CTRL_F8': {'k': '\x1b[19;5~'},
  'CTRL_F9': {'k': '\x1b[20;5~'},
  'CTRL_F10': {'k': '\x1b[21;5~'},
  'CTRL_F11': {'k': '\x1b[23;5~'},
  'CTRL_F12': {'k': '\x1b[24;5~'},

  'CTRL_SHIFT_F1': {'k': '\x1bO1;6P'},
  'CTRL_SHIFT_F2': {'k': '\x1bO1;6Q'},
  'CTRL_SHIFT_F3': {'k': '\x1bO1;6R'},
  'CTRL_SHIFT_F4': {'k': '\x1bO1;6S'},
  'CTRL_SHIFT_F5': {'k': '\x1b[15;6~'},
  'CTRL_SHIFT_F6': {'k': '\x1b[17;6~'},
  'CTRL_SHIFT_F7': {'k': '\x1b[18;6~'},
  'CTRL_SHIFT_F8': {'k': '\x1b[19;6~'},
  'CTRL_SHIFT_F9': {'k': '\x1b[20;6~'},
  'CTRL_SHIFT_F10': {'k': '\x1b[21;6~'},
  'CTRL_SHIFT_F11': {'k': '\x1b[23;6~'},
  'CTRL_SHIFT_F12': {'k': '\x1b[24;6~'},


  'INS': {'k': '\x1b[2~'},
  'DEL': {'k': '\x1b[3~'},
  'HOME': {'k': '\x1bOH'},
  'END': {'k': '\x1bOF'},
  'PGUP': {'k': '\x1b[5~'},
  'PGDN': {'k': '\x1b[6~'},

  'SHIFT_INS': {'k': '\x1b[2;2~'},
  'SHIFT_DEL': {'k': '\x1b[3;2~'},
  'SHIFT_HOME': {'k': '\x1bO1;2H'},
  'SHIFT_END': {'k': '\x1bO1;2F'},
  'SHIFT_PGUP': {'k': '\x1b[5;2~'},
  'SHIFT_PGDN': {'k': '\x1b[6;2~'},

  'CTRL_INS': {'k': '\x1b[2;5~'},
  'CTRL_DEL': {'k': '\x1b[3;5~'},
  'CTRL_HOME': {'k': '\x1bO1;5H'},
  'CTRL_END': {'k': '\x1bO1;5F'},
  'CTRL_PGUP': {'k': '\x1b[5;5~'},
  'CTRL_PGDN': {'k': '\x1b[6;5~'},

  'CTRL_SHIFT_INS': {'k': '\x1b[2;6~'},
  'CTRL_SHIFT_DEL': {'k': '\x1b[3;6~'},
  'CTRL_SHIFT_HOME': {'k': '\x1bO1;6H'},
  'CTRL_SHIFT_END': {'k': '\x1bO1;6F'},
  'CTRL_SHIFT_PGUP': {'k': '\x1b[5;6~'},
  'CTRL_SHIFT_PGDN': {'k': '\x1b[6;6~'},

  'KP_HOME': {'k': '\x1b[1~'},
  'KP_END': {'k': '\x1b[4~'},
  'KP_PGUP': {'k': '\x1b[5~'},
  # 'KP_PGDN': {'k': '\x1b[6~'},
  'KP_CENTER': {'k': '\x1b[E'},
}
