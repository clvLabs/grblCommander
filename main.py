#!/usr/bin/python3
"""
grblCommander
=============
Allows to control a CNC driven by a grblShield
"""

import sys
import time
import pprint

import src.gc.utils as ut
import src.gc.ui as ui
import src.gc.keyboard as kb
import src.gc.serialport as sp
import src.gc.machine as mch
import src.gc.table as tbl
import src.gc.macro as mcr
import src.gc.test as test
from src.gc.config import cfg, loadedCfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
uiCfg = cfg['ui']
mchCfg = cfg['machine']
mcrCfg = cfg['macro']

# Current version
gVERSION = '0.4.2'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readyMsg(extraInfo=None):
  if extraInfo is None:
    extraInfo = mch.getSimpleMachineStatusStr()

  ui.readyMsg(extraInfo)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showHelp():
  ui.logBlock(
  """
  Available commands
  ---------------------------------------------------------------------
  hH?        - Show this help text
  qQ         - Exit
  rR         - Reset serial connection
  cC         - Clear screen

  sS         - Show current status (short/LONG)
  gG         - Send raw GCode command
  mM         - Macro (submenu)
  tT         - Tests (submenu)

  <F12>      - Copy MPos to SPos

  Rapids
  ---------------------------------------------------------------------
  <numpad>   - Safe relative rapid (XY) (including diagonals)
  */         - Relative rapid (Z) (-/+)

  0          - Safe go to X0Y0Z0
  .          - Safe absolute rapid (XY) to table position (submenu)

  Settings
  ---------------------------------------------------------------------
  -+         - Set rapid increment (XY) (-/+)
  <CTRL>x/y  - Set rapid increment (XY)

  zZ         - Set rapid increment (Z) (-/+)
  <CTRL>z    - Set rapid increment (Z)

  aA         - Set safe height (Z) (-/+)
  <CTRL>a    - Set safe height (Z)

  %          - Set table size percent (loop)
  <ALT>5     - Set table size percent

  vV         - Set verbose level (-/+) (loop)
  """)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineStatus():
  mch.getMachineStatus()

  ui.logBlock(
  """
  Current status:

  Machine {:}
  MPos    {:s}
  WPos    {:s}
  SPos    {:s}

  Software config:
  RapidIncrement_XY = {:}
  RapidIncrement_Z  = {:}
  SafeHeight        = {:}
  TableSize%        = {:d}%
  VerboseLevel      = {:d}/{:d} ({:s})
  """.format(
      mch.getColoredMachineStateStr(),
      mch.getMachinePosStr(),
      mch.getWorkPosStr(),
      mch.getSoftwarePosStr(),
      ui.coordStr(tbl.getRI_XY()),
      ui.coordStr(tbl.getRI_Z()),
      ui.coordStr(tbl.getSafeHeight()),
      tbl.getTableSizePercent(),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineLongStatus():
  machineStatus = mch.getMachineStatus()

  ui.logBlock(
  """
  Current status (LONG version):

  Machine {:}
  MPos    {:s}
  WPos    {:s}
  SPos    {:s}

  Machine FULL status:
  {:}

  Software config:
  RapidIncrement_XY = {:}
  RapidIncrement_Z  = {:}
  SafeHeight        = {:}
  TableSize%        = {:d}%
  VerboseLevel      = {:d}/{:d} ({:s})

  """.format(
      mch.getColoredMachineStateStr(),
      mch.getMachinePosStr(),
      mch.getWorkPosStr(),
      mch.getSoftwarePosStr(),
      pprint.pformat(machineStatus, indent=4, width=uiCfg['maxLineLen']),
      ui.coordStr(tbl.getRI_XY()),
      ui.coordStr(tbl.getRI_Z()),
      ui.coordStr(tbl.getSafeHeight()),
      tbl.getTableSizePercent(),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    )

  mcr.run(mcrCfg['machineLongStatus'], silent=True)

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
    elif(key == 134): # <F12>
      ui.keyPressMessage('<F12> - Copy MPos to SPos', key, char)
      mch.refreshSoftwarePos()

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

    elif(char in 'mM'):
      ui.keyPressMessage('mM - Macro', key, char)

      ui.logBlock(
      """
      Available commands:

      lL  - List macros
      rR  - Run macro
      sS  - Show macro
      xX  - Reload macros
      """)

      ui.inputMsg('Select command...')
      key = kb.readKey()
      char=chr(key)

      if(char in 'lL'):
        ui.keyPressMessage('lL - List macros', key, char)
        mcr.list()

      elif(char in 'rR'):
        ui.keyPressMessage('rR - Run macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=input()
        mcr.run(macroName)

      elif(char in 'sS'):
        ui.keyPressMessage('sS - Show macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=input()
        mcr.show(macroName)

      elif(char in 'xX'):
        ui.keyPressMessage('xX - Reload macros', key, char)
        ui.logTitle('Reloading macros')
        mcr.load()

      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif(char in 'gG'):
      ui.keyPressMessage('gG - Send raw GCode command', key, char)
      ui.inputMsg('Enter GCode command...')
      userCommand=input()
      sp.sendCommand(userCommand)
      mch.waitForMachineIdle()

    elif(char == 's'):
      ui.keyPressMessage('s - Show current status (short)', key, char)
      showMachineStatus()

    elif(char == 'S'):
      ui.keyPressMessage('S - Show current status (LONG)', key, char)
      showMachineLongStatus()

    elif(char in 'rR'):
      ui.keyPressMessage('rR - Reset serial connection', key, char)
      sp.connect()
      mch.getMachineStatus()

    elif(char in 'cC'):
      ui.keyPressMessage('cC - Clear screen', key, char)
      ui.clearScreen()

    elif(char in 'tT'):
      ui.keyPressMessage('tT - Tests', key, char)

      ui.logBlock(
      """
      Available commands:

      pP  - Point probe
      tT  - Table probing scan
      sS  - Table position scan
      lL  - Base levelling holes
      zZ  - Zig-zag pattern
      *   - DUMMY Test
      """)

      ui.inputMsg('Select command...')
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
        ui.keyPressMessage('Unknown command', key, char)

    elif(char == '/'):
      ui.keyPressMessage('/ - Relative rapid (Z)+', key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z())

    elif(char == '*'):
      ui.keyPressMessage('* - Relative rapid (Z)-', key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z()*-1)

    elif(char == '0'):
      ui.keyPressMessage('0 - Safe go to X0Y0Z0', key, char)
      mch.safeRapidAbsolute(x=0,y=0,z=0)

    elif(char == '1'):
      ui.keyPressMessage('1 - Safe relative rapid - [DL]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY()*-1)

    elif(char == '2'):
      ui.keyPressMessage('2 - Safe relative rapid - [D]', key, char)
      mch.safeRapidRelative(y=tbl.getRI_XY()*-1)

    elif(char == '3'):
      ui.keyPressMessage('3 - Safe relative rapid - [DR]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY()*-1)

    elif(char == '4'):
      ui.keyPressMessage('4 - Safe relative rapid - [L]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1)

    elif(char == '6'):
      ui.keyPressMessage('6 - Safe relative rapid - [R]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY())

    elif(char == '7'):
      ui.keyPressMessage('7 - Safe relative rapid - [UL]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY())

    elif(char == '8'):
      ui.keyPressMessage('8 - Safe relative rapid - [U]', key, char)
      mch.safeRapidRelative(y=tbl.getRI_XY())

    elif(char == '9'):
      ui.keyPressMessage('9 - Safe relative rapid - [UR]', key, char)
      mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY())

    elif(char == '.'):
      ui.keyPressMessage('. - Safe absolute rapid to table position', key, char)

      ui.logBlock(
      """
      Available commands:

      <numpad>  - Absolute table positions
      .         - One axis only (submenu)
      """)

      ui.inputMsg('Select command...')
      key = kb.readKey()
      char=chr(key)

      if(char == '.'):
        ui.keyPressMessage('. - ONE AXIS ONLY', key, char)

        ui.logBlock(
        """
        Available commands:

        <numpad>46  - Absolute X axis limits
        <numpad>28  - Absolute Y axis limits
        """)

        ui.inputMsg('Select command...')
        key = kb.readKey()
        char=chr(key)

        if(char == '2'):
          ui.keyPressMessage('2 - ONE AXIS ONLY - Safe absolute rapid to axis limits - [B]', key, char)
          mch.safeRapidAbsolute(y=0)
        elif(char == '4'):
          ui.keyPressMessage('4 - ONE AXIS ONLY - Safe absolute rapid to axis limits - [L]', key, char)
          mch.safeRapidAbsolute(x=0)
        elif(char == '6'):
          ui.keyPressMessage('6 - ONE AXIS ONLY - Safe absolute rapid to axis limits - [R]', key, char)
          mch.safeRapidAbsolute(x=tbl.getMaxX())
        elif(char == '8'):
          ui.keyPressMessage('8 - ONE AXIS ONLY - Safe absolute rapid to axis limits - [U]', key, char)
          mch.safeRapidAbsolute(y=tbl.getMaxY())
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif(char == '1'):
        ui.keyPressMessage('1 - Safe absolute rapid to table position - [BL]', key, char)
        mch.safeRapidAbsolute(x=0,y=0)
      elif(char == '2'):
        ui.keyPressMessage('2 - Safe absolute rapid to table position - [BC]', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=0)
      elif(char == '3'):
        ui.keyPressMessage('3 - Safe absolute rapid to table position - [BR]', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX(),y=0)
      elif(char == '4'):
        ui.keyPressMessage('4 - Safe absolute rapid to table position - [CL]', key, char)
        mch.safeRapidAbsolute(x=0,y=tbl.getMaxY()/2)
      elif(char == '5'):
        ui.keyPressMessage('5 - Safe absolute rapid to table position - [CC]', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY()/2)
      elif(char == '6'):
        ui.keyPressMessage('6 - Safe absolute rapid to table position - [CR]', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX(),y=tbl.getMaxY()/2)
      elif(char == '7'):
        ui.keyPressMessage('7 - Safe absolute rapid to table position - [UL]', key, char)
        mch.safeRapidAbsolute(x=0,y=tbl.getMaxY())
      elif(char == '8'):
        ui.keyPressMessage('8 - Safe absolute rapid to table position - [UC]', key, char)
        mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY())
      elif(char == '9'):
        ui.keyPressMessage('9 - Safe absolute rapid to table position - [UR]', key, char)
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
      showMachineStatus()

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
      showMachineStatus()

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
      showMachineStatus()

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
      showMachineStatus()

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage('Pressed unknown key {:d} {:s}'.format(key,char), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  if(processed):
    readyMsg()

  return True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
  ui.clearScreen()

  ui.logBlock('    grblCommander v{0}'.format(gVERSION), color='ui.header')

  ui.logTitle('Loading configuration')
  ui.log('Using configuration file: {:}'.format(loadedCfg))
  ui.log()

  ui.logTitle('Loading macros')
  mcr.load()
  ui.log()

  ui.logTitle('Serial connection')
  sp.connect()

  mch.viewBuildInfo()

  ui.logTitle('Sending startup macro')
  mcr.run(mcrCfg['startup'], silent=True)

  mch.viewGCodeParserState()
  ui.log('System ready!', color='ui.msg')

  showMachineStatus()
  ui.log('Type [hH?] for help', color='ui.msg')

  readyMsg()

  while(True):
    line = sp.readline()
    if(line):
      ui.log('<<<<< {:}'.format(line), color='comms.recv')

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
