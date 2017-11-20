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
import src.gc.macro as macro
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

mcr = macro.Macro(mch)
tst = test.Test(mch)

# Jog distance
gXYJog = mchCfg['xyJogMm']
gZJog = mchCfg['zJogMm']

# Last GCode command
gLastGCodeCommand = ''

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readyMsg(extraInfo=None):
  if extraInfo is None:
    extraInfo = mch.getSimpleMachineStatusStr()

  ui.readyMsg(extraInfo)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def onParserStateChanged():
  if mch.status['machineState'] == 'Run':
    ui.log()
  ui.log(mch.getSimpleMachineStatusStr())

# Register
mch.onParserStateChanged.append(onParserStateChanged)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendCommand(command):
  if not command:
    return

  global gLastGCodeCommand
  gLastGCodeCommand = command

  # Special case for homing ($H)
  responseTimeout=None
  if command.rstrip(' ').upper() == '$H':
    responseTimeout=float(mchCfg['homingTimeout'])

  mch.sendWait(command, responseTimeout=responseTimeout)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showHelp():
  ui.logBlock(
  """
  Available commands
  ---------------------------------------------------------------------
  qQ         - Quit
  <CTRL>r    - Reset serial connection
  <CTRL>x    - grbl soft reset
  <ENTER>/?  - Force status re-query
  =          - Lock grblCommander

  cC         - Clear screen
  hH         - Show this help text
  s/S        - Show current status (short/LONG)
  @          - Show current status (FULL)
  gfxyz$     - Send raw GCode command
  [space]    - Send raw GCode command (start empty)
  º          - Repeat last GCode command
  mM         - Macro (submenu)
  tT         - Tests (submenu)
  rR         - Reset work coordinate (submenu)

  Jog
  ---------------------------------------------------------------------
  <numpad>         - XY jog (including diagonals)
  <SHIFT>+<numpad> - XY jog (double distance)
  <CTRL><numpad>   - XY jog (half distance)
  <numpad>-/+      - Z jog (up/down)

  <numpad>0        - Safe go to machine home
  <numpad>.        - Absolute rapid (XY) to table position (submenu)

  Settings
  ---------------------------------------------------------------------
  /          - Set jog distance (XY)
  *          - Set jog distance (Z)
  v/V        - Set verbose level (-/+) (loop)
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
  WCO     [{:s}]
  WPos    [{:s}]

  Software config:
  Jog distance (XY) = {:}
  Jog distance (Z)  = {:}
  VerboseLevel      = {:d}/{:d} ({:s})
  """.format(
      mch.getColoredMachineStateStr(),
      ui.setStrColor(mch.getAlarmStr(), 'ui.errorMsg'),
      ui.setStrColor(mch.getLastMessage(), 'ui.msg'),
      mch.getMachinePosStr(),
      mch.getWorkCoordinatesStr(),
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
def showMachineFullStatus():
  machineStatus=mch.getMachineStatus()

  ui.logBlock(
  """
  Machine FULL status: [{:}]

  {:s}
  """.format(
      mch.getColoredMachineStateStr(),
      pprint.pformat(machineStatus, indent=2, width=uiCfg['maxLineLen'])
    ))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def processUserInput():
  global gXYJog
  global gZJog

  if not kb.keyPressed():
    return True

  processed = True
  ps = mch.status['parserState']

  key = kb.readKey()
  char=chr(key)

  if key == kb.COMBO_0X:  # Combined code 0+x
    key = kb.readKey()
    char=chr(key)

    if key == 999999:
      pass
    elif key == kb.F1:
      if mcrCfg['hotKeys']['F1']:
        mcr.run(mcrCfg['hotKeys']['F1'], silent=True)
    elif key == kb.F2:
      if mcrCfg['hotKeys']['F2']:
        mcr.run(mcrCfg['hotKeys']['F2'], silent=True)
    elif key == kb.F3:
      if mcrCfg['hotKeys']['F3']:
        mcr.run(mcrCfg['hotKeys']['F3'], silent=True)
    elif key == kb.F4:
      if mcrCfg['hotKeys']['F4']:
        mcr.run(mcrCfg['hotKeys']['F4'], silent=True)
    elif key == kb.F5:
      if mcrCfg['hotKeys']['F5']:
        mcr.run(mcrCfg['hotKeys']['F5'], silent=True)
    elif key == kb.F6:
      if mcrCfg['hotKeys']['F6']:
        mcr.run(mcrCfg['hotKeys']['F6'], silent=True)
    elif key == kb.F7:
      if mcrCfg['hotKeys']['F7']:
        mcr.run(mcrCfg['hotKeys']['F7'], silent=True)
    elif key == kb.F8:
      if mcrCfg['hotKeys']['F8']:
        mcr.run(mcrCfg['hotKeys']['F8'], silent=True)
    elif key == kb.F9:
      if mcrCfg['hotKeys']['F9']:
        mcr.run(mcrCfg['hotKeys']['F9'], silent=True)
    elif key == kb.F10:
      if mcrCfg['hotKeys']['F10']:
        mcr.run(mcrCfg['hotKeys']['F10'], silent=True)

    elif key == kb.KP_END:
      ui.keyPressMessage('End - Jog - [DL] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-2,y=gXYJog*-2)

    elif key == kb.KP_DOWN:
      ui.keyPressMessage('Down - Jog - [D] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(y=gXYJog*-2)

    elif key == kb.KP_PGDN:
      ui.keyPressMessage('Pgdn - Jog - [DR] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*2,y=gXYJog*-2)

    elif key == kb.KP_LEFT:
      ui.keyPressMessage('Left - Jog - [L] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-2)

    elif key == kb.KP_RIGHT:
      ui.keyPressMessage('Right - Jog - [R] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*2)

    elif key == kb.KP_HOME:
      ui.keyPressMessage('Home - Jog - [UL] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-2,y=gXYJog*2)

    elif key == kb.KP_UP:
      ui.keyPressMessage('Up - Jog - [U] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(y=gXYJog*2)

    elif key == kb.KP_PGUP:
      ui.keyPressMessage('Pgup - Jog - [UR] [*2] ({:} {:})'.format(gXYJog*2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*2,y=gXYJog*2)


    elif key == kb.CTRL_KP_END:
      ui.keyPressMessage('End - Jog - [DL] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1,y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_DOWN:
      ui.keyPressMessage('Down - Jog - [D] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_PGDN:
      ui.keyPressMessage('Pgdn - Jog - [DR] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog/2,y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_LEFT:
      ui.keyPressMessage('Left - Jog - [L] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_RIGHT:
      ui.keyPressMessage('Right - Jog - [R] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog/2)

    elif key == kb.CTRL_KP_HOME:
      ui.keyPressMessage('Home - Jog - [UL] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1,y=gXYJog/2)

    elif key == kb.CTRL_KP_UP:
      ui.keyPressMessage('Up - Jog - [U] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(y=gXYJog/2)

    elif key == kb.CTRL_KP_PGUP:
      ui.keyPressMessage('Pgup - Jog - [UR] [/2] ({:} {:})'.format(gXYJog/2, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog/2,y=gXYJog/2)

    else:  # Rest of keys
      processed = False
      if ui.getVerboseLevelStr() == 'DEBUG':
        ui.keyPressMessage('Pressed unknown COMBINED key 0+{:d}'.format(key), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  elif key == kb.COMBO_224X:  # Combined code 224x
    key = kb.readKey()
    char=chr(key)

    if key == 999999:
      pass
    elif key == kb.F11:
      pass
    elif key == kb.F12:
      pass

    else:  # Rest of keys
      processed = False
      if ui.getVerboseLevelStr() == 'DEBUG':
        ui.keyPressMessage('Pressed unknown COMBINED key 224+{:d}'.format(key), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  else:  # Standard keys

    if char in 'qQ':
      ui.keyPressMessage('qQ - Quit', key, char)
      return False

    elif char in 'hH':
      ui.keyPressMessage('hH - Show help text', key, char)
      showHelp()

    elif char == '?' or key == kb.ENTER:
      ui.keyPressMessage('<ENTER>/? - Force status re-query', key, char)
      mch.viewMachineStatus()

    elif char == '=':
      ui.keyPressMessage('= - Lock grblCommander', key, char)
      while not ui.userConfirm(
        '================= grblCommander is LOCKED =================',
        'unlock'):
        pass

    elif char in 'mM':
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

      if char in 'lL':
        ui.keyPressMessage('lL - List macros', key, char)
        mcr.list()

      elif char in 'rR':
        ui.keyPressMessage('rR - Run macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=input()
        mcr.run(macroName)

      elif char in 'sS':
        ui.keyPressMessage('sS - Show macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=input()
        mcr.show(macroName)

      elif char in 'xX':
        ui.keyPressMessage('xX - Reload macros', key, char)
        ui.logTitle('Reloading macros')
        mcr.load()

      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif char in 'gfxyzGFXYZ$ ':
      ui.keyPressMessage(' - Send raw GCode command', key, char)
      ui.inputMsg('Enter GCode command...')
      if char == ' ':
        char = ''
      userCommand = char + input(char)
      sendCommand(userCommand)

    elif key == 167:   # º
      ui.keyPressMessage('F12 - Repeat last GCode command', key, char)
      sendCommand(gLastGCodeCommand)

    elif char == 's':
      ui.keyPressMessage('s - Show current status (short)', key, char)
      showMachineStatus()

    elif char == 'S':
      ui.keyPressMessage('S - Show current status (LONG)', key, char)
      showMachineLongStatus()

    elif char == '@':
      ui.keyPressMessage('@ - Show current status (FULL)', key, char)
      showMachineFullStatus()

    elif key == kb.CTRL_R:
      ui.keyPressMessage('<CTRL>r - Reset serial connection', key, char)
      mch.resetConnection()
      mch.queryMachineStatus()

    elif key == kb.CTRL_X:
      ui.keyPressMessage('<CTRL>x - grbl soft reset', key, char)
      mch.softReset()

    elif char in 'cC':
      ui.keyPressMessage('cC - Clear screen', key, char)
      ui.clearScreen()

    elif char in 'tT':
      ui.keyPressMessage('tT - Tests', key, char)

      ui.logBlock(
      """
      Available commands:

      sS  - Table position scan
      lL  - Base levelling holes
      zZ  - Zig-zag pattern
      *   - DUMMY Test
      """)

      ui.inputMsg('Select command...')
      key = kb.readKey()
      char=chr(key)

      if char in 'sS':
        ui.keyPressMessage('sS - Table position scan', key, char)
        tst.tablePositionScan()

      elif char in 'lL':
        ui.keyPressMessage('lL - Base levelling holes', key, char)
        tst.baseLevelingHoles()

      elif char in 'zZ':
        ui.keyPressMessage('zZ - Zig-zag pattern', key, char)
        tst.zigZagPattern()

      elif char == '*':
        ui.keyPressMessage('* - DUMMY Test', key, char)
        tst.dummy()

      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif char in 'rR':
      ui.keyPressMessage('rR - Reset work coordinate', key, char)

      ui.logBlock(
      """
      Available commands:

      xX  - Reset X to current position
      yY  - Reset Y to current position
      wW  - Reset XY to current position
      zZ  - Reset Z to current position
      aA  - Reset XYZ to current position
      -   - Reset XY to max machine travel
      *   - Reset XYZ to max machine travel
      """)

      ui.inputMsg('Select command...')
      key = kb.readKey()
      char=chr(key)

      if char in 'xX':
        ui.keyPressMessage('xX - Reset X to current position', key, char)
        mch.resetWCoord(char.lower())

      elif char in 'yY':
        ui.keyPressMessage('yY - Reset Y to current position', key, char)
        mch.resetWCoord(char.lower())

      elif char in 'wW':
        ui.keyPressMessage('wW - Reset XY to current position', key, char)
        mch.resetWCoord('x')
        mch.resetWCoord('y')

      elif char in 'zZ':
        ui.keyPressMessage('zZ - Reset Z to current position', key, char)
        mch.resetWCoord(char.lower())

      elif char in 'aA':
        ui.keyPressMessage('aA - Reset XYZ to current position', key, char)
        mch.resetWCoord('x')
        mch.resetWCoord('y')
        mch.resetWCoord('z')

      elif char == '-':
        ui.keyPressMessage('- - Reset XY to max machine travel', key, char)
        mch.resetWCoord('x','away')
        mch.resetWCoord('y','away')

      elif char == '*':
        ui.keyPressMessage('* - Reset XYZ to max machine travel', key, char)
        mch.resetWCoord('x','away')
        mch.resetWCoord('y','away')
        mch.resetWCoord('z','home')

      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif char == '-':
      ui.keyPressMessage('- - Jog (Z) up ({:} {:})'.format(gZJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=0,y=0,z=gZJog)

    elif char == '+':
      ui.keyPressMessage('+ - Jog (Z) down ({:} {:})'.format(gZJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=0,y=0,z=gZJog*-1)

    elif char == '0':
      ui.keyPressMessage('0 - Safe go to machine home', key, char)
      mch.goToMachineHome()

    elif char == '1':
      ui.keyPressMessage('1 - Jog - [DL] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-1,y=gXYJog*-1)

    elif char == '2':
      ui.keyPressMessage('2 - Jog - [D] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(y=gXYJog*-1)

    elif char == '3':
      ui.keyPressMessage('3 - Jog - [DR] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog,y=gXYJog*-1)

    elif char == '4':
      ui.keyPressMessage('4 - Jog - [L] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-1)

    elif char == '6':
      ui.keyPressMessage('6 - Jog - [R] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog)

    elif char == '7':
      ui.keyPressMessage('7 - Jog - [UL] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog*-1,y=gXYJog)

    elif char == '8':
      ui.keyPressMessage('8 - Jog - [U] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(y=gXYJog)

    elif char == '9':
      ui.keyPressMessage('9 - Jog - [UR] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=gXYJog,y=gXYJog)

    elif char == '.':
      ui.keyPressMessage('. - Absolute rapid to table position', key, char)

      minX = mch.getMin('x')
      minY = mch.getMin('y')
      maxX = mch.getMax('x')
      maxY = mch.getMax('y')
      wX = maxX-minX if minX<0 else minX-maxX
      wY = maxY-minY if minY<0 else minY-maxY
      cX = minX-(wX/2) if minX>0 else minX+(wX/2)
      cY = minY-(wY/2) if minX>0 else minY+(wY/2)

      ui.logBlock(
      """
      Available commands:

      <numpad>  - Absolute table positions
      .         - One axis only (submenu)
      """)

      ui.inputMsg('Select command...')
      key = kb.readKey()
      char=chr(key)

      if char == '.':
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

        if char == '2':
          ui.keyPressMessage('2 - ONE AXIS ONLY - Absolute rapid to axis limits - [B]', key, char)
          mch.rapidAbsolute(y=minY)
        elif char == '4':
          ui.keyPressMessage('4 - ONE AXIS ONLY - Absolute rapid to axis limits - [L]', key, char)
          mch.rapidAbsolute(x=minX)
        elif char == '6':
          ui.keyPressMessage('6 - ONE AXIS ONLY - Absolute rapid to axis limits - [R]', key, char)
          mch.rapidAbsolute(x=maxX)
        elif char == '8':
          ui.keyPressMessage('8 - ONE AXIS ONLY - Absolute rapid to axis limits - [U]', key, char)
          mch.rapidAbsolute(y=maxY)
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif char == '1':
        ui.keyPressMessage('1 - Absolute rapid to table position - [BL]', key, char)
        mch.rapidAbsolute(x=minX,y=minY)
      elif char == '2':
        ui.keyPressMessage('2 - Absolute rapid to table position - [BC]', key, char)
        mch.rapidAbsolute(x=cX,y=minY)
      elif char == '3':
        ui.keyPressMessage('3 - Absolute rapid to table position - [BR]', key, char)
        mch.rapidAbsolute(x=maxX,y=minY)
      elif char == '4':
        ui.keyPressMessage('4 - Absolute rapid to table position - [CL]', key, char)
        mch.rapidAbsolute(x=minX,y=cY)
      elif char == '5':
        ui.keyPressMessage('5 - Absolute rapid to table position - [CC]', key, char)
        mch.rapidAbsolute(x=cX,y=cY)
      elif char == '6':
        ui.keyPressMessage('6 - Absolute rapid to table position - [CR]', key, char)
        mch.rapidAbsolute(x=maxX,y=cY)
      elif char == '7':
        ui.keyPressMessage('7 - Absolute rapid to table position - [UL]', key, char)
        mch.rapidAbsolute(x=minX,y=maxY)
      elif char == '8':
        ui.keyPressMessage('8 - Absolute rapid to table position - [UC]', key, char)
        mch.rapidAbsolute(x=cX,y=maxY)
      elif char == '9':
        ui.keyPressMessage('9 - Absolute rapid to table position - [UR]', key, char)
        mch.rapidAbsolute(x=maxX,y=maxY)
      else:
        ui.keyPressMessage('Unknown command', key, char)

    elif char == '/':
      ui.keyPressMessage('/ - Set jog distance (XY)', key, char)
      gXYJog = ui.getUserInput(
        'Distance ({:})'.format(gXYJog),
        float,
        gXYJog)
      showMachineStatus()

    elif char == '*':
      ui.keyPressMessage('* - Set jog distance (Z)', key, char)
      gZJog = ui.getUserInput(
        'Distance ({:})'.format(gZJog),
        float,
        gZJog)
      showMachineStatus()

    elif char == 'V':
      ui.keyPressMessage('V - Set verbose level+', key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), +1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                            loop=True, valueName='Verbose level',
                            valueFormatter=lambda level : '{:d} {:s}'.format(level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    elif char == 'v':
      ui.keyPressMessage('v - Set verbose level-', key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), -1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                          loop=True, valueName='Verbose level',
                          valueFormatter=lambda level : '{:d} {:s}'.format(level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    else:  # Rest of keys
      processed = False
      if ui.getVerboseLevelStr() == 'DEBUG':
        ui.keyPressMessage('Pressed unknown key {:d} {:s}'.format(key,char), key, char)
      else:
        pass
        #ui.keyPressMessage('Unknown command', key, char)

  if processed:
    readyMsg()

  return True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
  ui.clearScreen()

  ui.logBlock('    grblCommander v{:}'.format(gVERSION), color='ui.header')

  ui.logTitle('Loading configuration')
  ui.log('Using configuration file: {:}'.format(loadedCfg))
  ui.log()

  ui.logTitle('Loading macros')
  mcr.load()
  ui.log()

  ui.logTitle('Grbl connection')
  mch.start()

  ui.logTitle('Sending startup macro')
  if mch.status['machineState'] == 'Idle':
    mcr.run(mcrCfg['startup'], silent=True)
  else:
    ui.log('WARNING: startup macro NOT executed (machine not ready)',c='ui.msg')
    ui.log()

  ui.log('System ready!', color='ui.successMsg')

  showMachineStatus()
  ui.log('Type [hH] for help', color='ui.msg')

  readyMsg()

  while True:
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
