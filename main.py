#!/usr/bin/python3
"""
grblCommander
=============
Allows to control a CNC driven by a grblShield
"""

import sys
import time

import src.utils as ut
import src.ui as ui
import src.keyboard as kb
import src.serialport as sp
import src.machine as mch
import src.table as tbl
import src.test as test
from src.config import loadedCfg

# Current version
gVERSION = '0.3.0'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showHelp():
  ui.logBlock(
  """
  Available commands:

  qQ             - Exit
  hH?            - Show this help text
  s/S            - Show current status (short/LONG)
  rR             - Reset serial connection
  cC             - Clear screen
  tT             - Tests (submenu)
  gG             - Send raw GCode command

  <numpad>       - Safe relative rapid (XY) (including diagonals)
  /*             - Relative rapid (Z) +/-
  <numpad>0      - Safe go to X0Y0Z0
  .              - Safe absolute rapid (XY) to table corners (submenu)

  +-             - Set rapid increment (XY) +/-
  <CTRL>x/y      - Set rapid increment (XY)
  Zz             - Set rapid increment (Z) +/-
  <CTRL>z        - Set rapid increment (Z)
  Aa             - Set safe height (Z) +/-
  <CTRL>a        - Set safe height (Z)
  %              - Set table size percent (loop)
  <ALT>5         - Set table size percent
  Vv             - Set verbose level +/- (loop)
  """)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def processUserInput():
  if not kb.keyPressed():
    return True

  processed = True

  key = kb.readKey()
  char=chr(key)

  if(key == 0):  # Combined code 0+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage('Pressed unknown COMBINED key 0+{:d}'.format(key), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  elif(key == 224):  # Combined code 224+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass
    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage('Pressed unknown COMBINED key 224+{:d}'.format(key), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  else:  # Standard keys

    if(char in 'qQ'):
      ui.keyPressMessage('qQ - Exit', key, char)
      return False

    elif(char in 'hH?'):
      ui.keyPressMessage('hH? - Show help text', key, char)
      showHelp()

    elif(char in 'gG'):
      ui.keyPressMessage('gG - Send raw GCode command', key, char)
      ui.inputMsg('Enter command...')
      userCommand=input()
      sp.sendCommand(userCommand)
      mch.waitForMachineIdle()

    elif(char == 's'):
      ui.keyPressMessage('s - Show current status (short)', key, char)
      mch.showStatus()

    elif(char == 'S'):
      ui.keyPressMessage('S - Show current status (LONG)', key, char)
      mch.showLongStatus()

    elif(char in 'rR'):
      ui.keyPressMessage('rR - Reset serial connection', key, char)
      sp.connect()

    elif(char in 'cC'):
      ui.keyPressMessage('cC - Clear screen', key, char)
      ui.clearScreen()

    elif(char in 'tT'):
      ui.keyPressMessage('tT - Tests', key, char)

      ui.logBlock(
      """
      Available tests:

      pP             - Point probe
      tT             - Table probing scan
      sS             - Table position scan
      lL             - Base levelling holes
      zZ             - Zig-zag pattern
      *              - DUMMY Test
      """)

      ui.inputMsg('Select test to run...')
      key = kb.readKey()
      char=chr(key)

      if(char in 'pP'):
        ui.keyPressMessage('pP - Point probe', key, char)
        test.pointProbe()

      elif(char in 'tT'):
        ui.keyPressMessage('tT - Table probing scan', key, char)
        test.tableProbingScan()

      elif(char in 'sS'):
        ui.keyPressMessage('sS - Table position scan', key, char)
        test.tablePositionScan()

      elif(char in 'lL'):
        ui.keyPressMessage('lL - Base levelling holes', key, char)
        test.baseLevelingHoles()

      elif(char in 'zZ'):
        ui.keyPressMessage('zZ - Zig-zag pattern', key, char)
        test.zigZagPattern()

      elif(char == '*'):
        ui.keyPressMessage('* - DUMMY Test', key, char)
        test.dummy()

      else:
        ui.keyPressMessage('Unknown test', key, char)

    elif(char == '/'):
      ui.keyPressMessage('/ - Relative rapid (Z)+', key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z())

    elif(char == '*'):
      ui.keyPressMessage('* - Relative rapid (Z)-', key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z()*-1)

    elif(char == '0'):
      ui.keyPressMessage('<numpad>0 - Safe go to X0Y0Z0', key, char)
      mch.safeRapidAbsolute(x=0,y=0,z=0)

    elif(char == '1'):
      ui.keyPressMessage('<numpad>1 - Safe relative rapid - DL', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY()*-1)

    elif(char == '2'):
      ui.keyPressMessage('<numpad>2 - Safe relative rapid - D', key, char)
      mch.safeRapidRelative(y=tbl.getRI_XY()*-1)

    elif(char == '3'):
      ui.keyPressMessage('<numpad>3 - Safe relative rapid - DR', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY()*-1)

    elif(char == '4'):
      ui.keyPressMessage('<numpad>4 - Safe relative rapid - L', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1)

    elif(char == '6'):
      ui.keyPressMessage('<numpad>6 - Safe relative rapid - R', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY())

    elif(char == '7'):
      ui.keyPressMessage('<numpad>7 - Safe relative rapid - UL', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY())

    elif(char == '8'):
      ui.keyPressMessage('<numpad>8 - Safe relative rapid - U', key, char)
      mch.safeRapidRelative(y=tbl.getRI_XY())

    elif(char == '9'):
      ui.keyPressMessage('<numpad>9 - Safe relative rapid - UR', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY())

    elif(char == '.'):
      ui.keyPressMessage('* - Safe absolute rapid to table corners', key, char)

      ui.logBlock(
      """
      Available commands:

      <numpad>1..9   - Absolute table positions
      .              - One axis only (submenu)
      """)

      ui.inputMsg('Use <numpad> to select corner...')
      key = kb.readKey()
      char=chr(key)

      if(char == '.'):
        ui.keyPressMessage('* - ONE AXIS ONLY', key, char)

        ui.logBlock(
        """
        Available commands:

        <numpad>2468   - Absolute table positions
        """)

        ui.inputMsg('Use <numpad> to select corner...')
        key = kb.readKey()
        char=chr(key)

        if(char == '2'):
          ui.keyPressMessage('2 - ONE AXIS ONLY - Safe absolute rapid to table corners - BC', key, char)
          mch.safeRapidAbsolute(y=0)
        elif(char == '4'):
          ui.keyPressMessage('4 - ONE AXIS ONLY - Safe absolute rapid to table corners - CL', key, char)
          mch.safeRapidAbsolute(x=0)
        elif(char == '6'):
          ui.keyPressMessage('6 - ONE AXIS ONLY - Safe absolute rapid to table corners - CR', key, char)
          mch.safeRapidAbsolute(x=tbl.getMaxX())
        elif(char == '8'):
          ui.keyPressMessage('8 - ONE AXIS ONLY - Safe absolute rapid to table corners - UC', key, char)
          mch.safeRapidAbsolute(y=tbl.getMaxY())
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif(char == '1'):
        ui.keyPressMessage('1 - Safe absolute rapid to table corners - BL', key, char)
        mch.safeRapidAbsolute(x=0,y=0)
      elif(char == '2'):
        ui.keyPressMessage('2 - Safe absolute rapid to table corners - BC', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=0)
      elif(char == '3'):
        ui.keyPressMessage('3 - Safe absolute rapid to table corners - BR', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX(),y=0)
      elif(char == '4'):
        ui.keyPressMessage('4 - Safe absolute rapid to table corners - CL', key, char)
        mch.safeRapidAbsolute(x=0,y=tbl.getMaxY()/2)
      elif(char == '5'):
        ui.keyPressMessage('5 - Safe absolute rapid to table corners - CC', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY()/2)
      elif(char == '6'):
        ui.keyPressMessage('6 - Safe absolute rapid to table corners - CR', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX(),y=tbl.getMaxY()/2)
      elif(char == '7'):
        ui.keyPressMessage('7 - Safe absolute rapid to table corners - UL', key, char)
        mch.safeRapidAbsolute(x=0,y=tbl.getMaxY())
      elif(char == '8'):
        ui.keyPressMessage('8 - Safe absolute rapid to table corners - UC', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY())
      elif(char == '9'):
        ui.keyPressMessage('9 - Safe absolute rapid to table corners - UR', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX(),y=tbl.getMaxY())
      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif(char == '+'):
      ui.keyPressMessage('+ - Set rapid increment (XY)+', key, char)
      tbl.changeRI_XY(+1)

    elif(char == '-'):
      ui.keyPressMessage('- - Set rapid increment (XY)-', key, char)
      tbl.changeRI_XY(-1)

    elif(key in [24, 25]):  # <CTRL>x/y
      ui.keyPressMessage('<CTRL>x/y - Set rapid increment (XY)', key, char)
      tbl.setRI_XY(
        ui.getUserInput(
          'Increment ({:})'.format(tbl.getRI_XY()),
          float,
          tbl.getRI_XY()))
      mch.showStatus()

    elif(char == 'Z'):
      ui.keyPressMessage('Z - Set rapid increment (Z)+', key, char)
      tbl.changeRI_Z(+1)

    elif(char == 'z'):
      ui.keyPressMessage('z - Set rapid increment (Z)-', key, char)
      tbl.changeRI_Z(-1)

    elif(key == 26):  # <CTRL>z
      ui.keyPressMessage('<CTRL>z - Set rapid increment (Z)', key, char)
      tbl.setRI_Z(
        ui.getUserInput(
          'Increment ({:})'.format(tbl.getRI_Z()),
          float,
          tbl.getRI_Z()))
      mch.showStatus()

    elif(char == '%'):
      ui.keyPressMessage('% - Set table size percent (loop)', key, char)
      tmpTableSizePercent = ut.genericValueChanger(  tbl.getTableSizePercent(), +10, tbl.gMIN_TABLE_SIZE_PERCENT, tbl.gMAX_TABLE_SIZE_PERCENT,
                              loop=True, valueName='Table size percent')

      tbl.setTableSizePercent(tmpTableSizePercent)

    elif(key == 53):  # <ALT>5
      ui.keyPressMessage('<ALT>5 - Set table size percent', key, char)
      tbl.setTableSizePercent(
        ui.getUserInput(
          'Table size % ({:})'.format(tbl.getTableSizePercent()),
          int,
          tbl.getTableSizePercent()))
      mch.showStatus()

    elif(char == 'V'):
      ui.keyPressMessage('V - Set verbose level+', key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), +1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                            loop=True, valueName='Verbose level',
                            valueFormatter=lambda level : '{:d} {:s}'.format(level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    elif(char == 'v'):
      ui.keyPressMessage('v - Set verbose level-', key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), -1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                          loop=True, valueName='Verbose level',
                          valueFormatter=lambda level : '{:d} {:s}'.format(level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    elif(char == 'A'):
      ui.keyPressMessage('A - Set safe height (Z)+', key, char)
      tempSafeHeight = ut.genericValueChanger(  tbl.getSafeHeight(), +1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
                            loop=False, valueName='Safe Height' )
      tbl.setSafeHeight(tempSafeHeight)

    elif(char == 'a'):
      ui.keyPressMessage('a - Set safe height (Z)-', key, char)
      tempSafeHeight = ut.genericValueChanger(  tbl.getSafeHeight(), -1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
                            loop=False, valueName='Safe Height' )
      tbl.setSafeHeight(tempSafeHeight)

    elif(key == 1):  # <CTRL>a
      ui.keyPressMessage('<CTRL>a - Set safe height (Z)', key, char)
      tbl.setSafeHeight(
        ui.getUserInput(
          'Safe height ({:})'.format(tbl.getSafeHeight()),
          int,
          tbl.getSafeHeight()))
      mch.showStatus()

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage('Pressed unknown key {:d} {:s}'.format(key,char), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  if(processed):
    ui.readyMsg(extraInfo=mch.getSimpleMachineStatusStr())

  return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
  ui.clearScreen()

  ui.logBlock('    grblCommander v{0}'.format(gVERSION), color='ui.header')

  ui.log('Using configuration file: {:}'.format(loadedCfg))
  ui.log()

  sp.connect()
  mch.sendGCodeInitSequence()
  ui.log()

  mch.viewGCodeParameters()
  ui.log()

  ui.log('System ready!')

  mch.showStatus()

  ui.log('Type "H" for help')

  ui.readyMsg(extraInfo=mch.getSimpleMachineStatusStr())

  while(True):

    line = sp.readline()
    if(line):
      ui.log('<<<<< {:}'.format(line))

    if not processUserInput():
      break

  ui.log('Closing serial port...')
  sp.close()

  ui.log('Closing program...')



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def execTestCode():

  print(ui.charLine('*'))
  print('  TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE')
  print(ui.charLine('*'))
  print('\n\n')

  # <TEST CODE>
  pass
  # </TEST CODE>

  sys.exit(0)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':

  # execTestCode()

  try:
    main()
  finally:
    pass
#    ui.log('Press any key to exit...')
#    readKey()
