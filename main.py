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
import src.gc.grbl.grbl as grbl
import src.gc.macro as mcr
import src.gc.test as test
from src.gc.config import cfg, loadedCfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
uiCfg = cfg['ui']
mchCfg = cfg['machine']
mcrCfg = cfg['macro']

# Current version
gVERSION = '0.5.0'

# grbl machine manager
mch = grbl.Grbl(cfg)
mcr.setGrbl(mch)

# Table limits
gMIN_X = 0.0
gMAX_X = mchCfg['max']['X']

gMIN_Y = 0.0
gMAX_Y = mchCfg['max']['Y']

gMIN_Z = 0.0
gMAX_Z = mchCfg['max']['Z']

# Rapid Increment
gXYJog = mchCfg['xyJogMm']
gZJog = mchCfg['zJogMm']

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
  hH         - Show this help text
  qQ         - Exit
  rR         - Reset serial connection
  <CTRL>x    - grbl soft reset
  cC         - Clear screen

  ?          - Force status re-query
  sS         - Show current status (short/LONG)
  gG$        - Send raw GCode command
  mM         - Macro (submenu)
  tT         - Tests (submenu)

  Rapids
  ---------------------------------------------------------------------
  <numpad>   - Relative rapid (XY) (including diagonals)
  -+         - Relative rapid (Z) (up/down)

  0          - Safe go to X0Y0Z0
  .          - Absolute rapid (XY) to table position (submenu)

  Settings
  ---------------------------------------------------------------------
  xX         - Set rapid increment (XY)
  zZ         - Set rapid increment (Z)
  vV         - Set verbose level (-/+) (loop)
  """)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineStatus():
  mch.getMachineStatus()

  ui.logBlock(
  """
  Current status: [{:}]

  Alarm   [{:s}]
  Msg     [{:s}]

  MPos    [{:s}]
  WPos    [{:s}]

  Software config:
  RapidIncrement_XY = {:}
  RapidIncrement_Z  = {:}
  VerboseLevel      = {:d}/{:d} ({:s})
  """.format(
      mch.getColoredMachineStateStr(),
      ui.setStrColor(mch.getAlarmStr(), 'ui.errorMsg'),
      ui.setStrColor(mch.getLastMessage(), 'ui.msg'),
      mch.getMachinePosStr(),
      mch.getWorkPosStr(),
      ui.coordStr(gXYJog),
      ui.coordStr(gZJog),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineLongStatus():
  showMachineStatus()
  mcr.run(mcrCfg['machineLongStatus'], silent=True)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def processUserInput():
  if not kb.keyPressed():
    return True

  processed = True

  key = kb.readKey()
  char=chr(key)

  if(key == kb.COMBO_0X):  # Combined code 0+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass
    elif(key == kb.F1):
      if mcrCfg['hotKeys']['F1']:
        mcr.run(mcrCfg['hotKeys']['F1'], silent=True)
    elif(key == kb.F2):
      if mcrCfg['hotKeys']['F2']:
        mcr.run(mcrCfg['hotKeys']['F2'], silent=True)
    elif(key == kb.F3):
      if mcrCfg['hotKeys']['F3']:
        mcr.run(mcrCfg['hotKeys']['F3'], silent=True)
    elif(key == kb.F4):
      if mcrCfg['hotKeys']['F4']:
        mcr.run(mcrCfg['hotKeys']['F4'], silent=True)
    elif(key == kb.F5):
      if mcrCfg['hotKeys']['F5']:
        mcr.run(mcrCfg['hotKeys']['F5'], silent=True)
    elif(key == kb.F6):
      if mcrCfg['hotKeys']['F6']:
        mcr.run(mcrCfg['hotKeys']['F6'], silent=True)
    elif(key == kb.F7):
      if mcrCfg['hotKeys']['F7']:
        mcr.run(mcrCfg['hotKeys']['F7'], silent=True)
    elif(key == kb.F8):
      if mcrCfg['hotKeys']['F8']:
        mcr.run(mcrCfg['hotKeys']['F8'], silent=True)
    elif(key == kb.F9):
      if mcrCfg['hotKeys']['F9']:
        mcr.run(mcrCfg['hotKeys']['F9'], silent=True)
    elif(key == kb.F10):
      if mcrCfg['hotKeys']['F10']:
        mcr.run(mcrCfg['hotKeys']['F10'], silent=True)

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage('Pressed unknown COMBINED key 0+{:d}'.format(key), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  elif(key == kb.COMBO_224X):  # Combined code 224+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass
    elif(key == kb.F12):
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

    elif(char in 'hH'):
      ui.keyPressMessage('hH - Show help text', key, char)
      showHelp()

    elif(char in '?'):
      ui.keyPressMessage('? - Force status re-query', key, char)
      mch.queryMachineStatus()

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

    elif(char in 'gG$'):
      ui.keyPressMessage('gG$ - Send raw GCode command', key, char)
      ui.inputMsg('Enter GCode command...')
      userCommand = char + input(char)
      mch.sendCommand(userCommand)
      mch.waitForMachineIdle()

    elif(char == 's'):
      ui.keyPressMessage('s - Show current status (short)', key, char)
      showMachineStatus()

    elif(char == 'S'):
      ui.keyPressMessage('S - Show current status (LONG)', key, char)
      showMachineLongStatus()

    elif(char in 'rR'):
      ui.keyPressMessage('rR - Reset serial connection', key, char)
      mch.resetConnection()
      mch.queryMachineStatus()

    elif(key == kb.CTRL_X):
      ui.keyPressMessage('<CTRL>x - grbl soft reset', key, char)
      mch.softReset()

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

    elif(char == '-'):
      ui.keyPressMessage('- - Relative rapid (Z) up', key, char)
      mch.rapidRelative(x=0,y=0,z=gZJog)

    elif(char == '+'):
      ui.keyPressMessage('+ - Relative rapid (Z) down', key, char)
      mch.rapidRelative(x=0,y=0,z=gZJog*-1)

    elif(char == '0'):
      ui.keyPressMessage('0 - Safe go to X0Y0Z0', key, char)
      ui.log('TEMPORARILY DISABLED', c='ui.msg')
      # mch.rapidAbsolute(x=0,y=0,z=0)

    elif(char == '1'):
      ui.keyPressMessage('1 - Relative rapid - [DL]', key, char)
      mch.rapidRelative(x=gXYJog*-1,y=gXYJog*-1)

    elif(char == '2'):
      ui.keyPressMessage('2 - Relative rapid - [D]', key, char)
      mch.rapidRelative(y=gXYJog*-1)

    elif(char == '3'):
      ui.keyPressMessage('3 - Relative rapid - [DR]', key, char)
      mch.rapidRelative(x=gXYJog,y=gXYJog*-1)

    elif(char == '4'):
      ui.keyPressMessage('4 - Relative rapid - [L]', key, char)
      mch.rapidRelative(x=gXYJog*-1)

    elif(char == '6'):
      ui.keyPressMessage('6 - Relative rapid - [R]', key, char)
      mch.rapidRelative(x=gXYJog)

    elif(char == '7'):
      ui.keyPressMessage('7 - Relative rapid - [UL]', key, char)
      mch.rapidRelative(x=gXYJog*-1,y=gXYJog)

    elif(char == '8'):
      ui.keyPressMessage('8 - Relative rapid - [U]', key, char)
      mch.rapidRelative(y=gXYJog)

    elif(char == '9'):
      ui.keyPressMessage('9 - Relative rapid - [UR]', key, char)
      mch.rapidRelative(x=gXYJog,y=gXYJog)

    elif(char == '.'):
      ui.keyPressMessage('. - Absolute rapid to table position', key, char)

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
          ui.keyPressMessage('2 - ONE AXIS ONLY - Absolute rapid to axis limits - [B]', key, char)
          mch.rapidAbsolute(y=gMIN_Y)
        elif(char == '4'):
          ui.keyPressMessage('4 - ONE AXIS ONLY - Absolute rapid to axis limits - [L]', key, char)
          mch.rapidAbsolute(x=gMIN_X)
        elif(char == '6'):
          ui.keyPressMessage('6 - ONE AXIS ONLY - Absolute rapid to axis limits - [R]', key, char)
          mch.rapidAbsolute(x=gMAX_X)
        elif(char == '8'):
          ui.keyPressMessage('8 - ONE AXIS ONLY - Absolute rapid to axis limits - [U]', key, char)
          mch.rapidAbsolute(y=gMAX_Y)
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif(char == '1'):
        ui.keyPressMessage('1 - Absolute rapid to table position - [BL]', key, char)
        mch.rapidAbsolute(x=gMIN_X,y=gMIN_Y)
      elif(char == '2'):
        ui.keyPressMessage('2 - Absolute rapid to table position - [BC]', key, char)
        mch.rapidAbsolute(x=gMAX_X/2,y=gMIN_Y)
      elif(char == '3'):
        ui.keyPressMessage('3 - Absolute rapid to table position - [BR]', key, char)
        mch.rapidAbsolute(x=gMAX_X,y=gMIN_Y)
      elif(char == '4'):
        ui.keyPressMessage('4 - Absolute rapid to table position - [CL]', key, char)
        mch.rapidAbsolute(x=gMIN_X,y=gMAX_Y/2)
      elif(char == '5'):
        ui.keyPressMessage('5 - Absolute rapid to table position - [CC]', key, char)
        mch.rapidAbsolute(x=gMAX_X/2,y=gMAX_Y/2)
      elif(char == '6'):
        ui.keyPressMessage('6 - Absolute rapid to table position - [CR]', key, char)
        mch.rapidAbsolute(x=gMAX_X,y=gMAX_Y/2)
      elif(char == '7'):
        ui.keyPressMessage('7 - Absolute rapid to table position - [UL]', key, char)
        mch.rapidAbsolute(x=gMIN_X,y=gMAX_Y)
      elif(char == '8'):
        ui.keyPressMessage('8 - Absolute rapid to table position - [UC]', key, char)
        mch.rapidAbsolute(x=gMAX_X/2,y=gMAX_Y)
      elif(char == '9'):
        ui.keyPressMessage('9 - Absolute rapid to table position - [UR]', key, char)
        mch.rapidAbsolute(x=gMAX_X,y=gMAX_Y)
      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif(char in 'xX'):
      ui.keyPressMessage('xX - Set rapid increment (XY)', key, char)
      global gXYJog
      gXYJog = ui.getUserInput(
        'Increment ({:})'.format(gXYJog),
        float,
        gXYJog)
      showMachineStatus()

    elif(char in 'zZ'):
      ui.keyPressMessage('<CTRL>z - Set rapid increment (Z)', key, char)
      global gZJog
      gZJog = ui.getUserInput(
        'Increment ({:})'.format(gZJog),
        float,
        gZJog)
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

  ui.logTitle('Grbl connection')
  mch.start()

  # ui.logTitle('Sending startup macro')
  # mcr.run(mcrCfg['startup'], silent=True)

  ui.log('System ready!', color='ui.successMsg')

  showMachineStatus()
  ui.log('Type [hH] for help', color='ui.msg')

  readyMsg()

  while(True):
    mch.process()

    if not processUserInput():
      break

  ui.log('Closing grbl connection...')
  mch.stop()

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
