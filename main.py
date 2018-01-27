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
import src.gc.joystick as joystick
import src.gc.grbl.grbl as grbl
import src.gc.grbl.probe as probe
import src.gc.macro as macro
import src.gc.test as test
from src.gc.config import cfg, loadedCfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
uiCfg = cfg['ui']
mchCfg = cfg['machine']
mcrCfg = cfg['macro']

# Current version
gVERSION = '0.9.0'

# grbl machine manager
mch = grbl.Grbl(cfg)

# grbl probe manager
prb = probe.Probe(mch)

# joystick manager
joy = joystick.Joystick(cfg)

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
  # While running, machine is already displaying status
  if not mch.isRunning():
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
  responseTimeout = None
  homing = False
  if command.rstrip(' ').upper() == '$H':
    homing = True
    responseTimeout=float(mchCfg['homingTimeout'])

  mch.sendWait(command, responseTimeout=responseTimeout)

  if homing:
    sendStartupMacro()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendStartupMacro():
  ui.logTitle('Sending startup macro')
  if mch.status['machineState'] == 'Idle':
    mcr.run(mcrCfg['startup'], silent=True)
  else:
    ui.log('WARNING: startup macro NOT executed (machine not ready)',c='ui.msg')
    ui.log()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showHelp():
  ui.logBlock(
  """
  General commands
  ---------------------------------------------------------------------
  qQ         - Quit
  <CTRL>r    - Reset serial connection
  <CTRL>x    - grbl soft reset
  =          - Lock grblCommander
  cC         - Clear screen
  v/V        - Set verbose level (-/+) (loop)

  Info
  ---------------------------------------------------------------------
  hH         - Show this help text
  s/S        - Show current status (short/LONG)
  @          - Show current status (FULL)

  Machine control
  ---------------------------------------------------------------------
  gfxyz$     - Send raw GCode command
  [space]    - Send raw GCode command (start empty)
  lL         - Send raw GCode command (FORCE RELATIVE)
  <ENTER>/?  - Force status re-query
  º          - Repeat last GCode command
  pP         - Probe (submenu)
  mM         - Macro (submenu)
  tT         - Tests (submenu)
  rR         - Reset work coordinate (submenu)

  Jog
  ---------------------------------------------------------------------
  <numpad>         - XY jog (including diagonals)
  <SHIFT>+<numpad> - XY jog (double distance)
  <CTRL><numpad>   - XY jog (half distance)
  <numpad>-/+      - Z jog (up/down)
  /                - Set jog distance (XY)
  *                - Set jog distance (Z)
  <numpad>0        - Go home (submenu)
  <numpad>.        - Absolute move (XY) to table position (submenu)

  Joystick
  ---------------------------------------------------------------------
  j                - Enable/disable joystick
  J                - Restart joystick connection
  <xy>             - XY jog (including diagonals)
  <z>-/+           - Z jog (up/down)
  <extraU><z+>     - Go to machine home Z
  <extraD><z+>     - Go to machine home
  <extraU><x>      - Change jog distance (XY) (+-1)
  <extraU><y>      - Change jog distance (XY) (+-10)
  <extraD><x>      - Change jog distance (Z) (+-1)
  <extraD><y>      - Change jog distance (Z) (+-10)
  """)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineStatus():
  mch.getMachineStatus()

  statusStr = ''

  statusStr += 'Current status: [{:}]\n'.format(mch.getColoredMachineStateStr())
  statusStr += '\n'
  statusStr += 'Alarm    [{:s}]\n'.format(ui.setStrColor(mch.getAlarmStr(), 'ui.errorMsg'))
  statusStr += 'Msg      [{:s}]\n'.format(ui.setStrColor(mch.getLastMessage(), 'ui.msg'))
  statusStr += '\n'
  statusStr += 'MPos     [{:s}]\n'.format(mch.getMachinePosStr())
  statusStr += 'WCO      [{:s}]\n'.format(mch.getWorkCoordinatesStr())
  statusStr += 'WPos     [{:s}]\n'.format(mch.getWorkPosStr())
  statusStr += 'PRB      {:s}\n'.format(mch.getProbePosStr())
  statusStr += '\n'
  statusStr += 'INPins   {:s}\n'.format(mch.getInputPinStateLongStr())
  statusStr += 'Parser   [{:s}]\n'.format(mch.getSimpleSettingsStr())

  statusStr += 'Joystick [{:s}] [{:s}]\n'.format(
    ui.setStrColor('CONNECTED', 'ui.successMsg') if joy.connected else ui.setStrColor('DISCONNECTED', 'ui.errorMsg'),
    ui.setStrColor('ENABLED', 'ui.successMsg') if joy.enabled else ui.setStrColor('DISABLED', 'ui.errorMsg')
  )

  statusStr += '\n'
  statusStr += 'Software config:\n'
  statusStr += 'Jog distance (XY) = {:}\n'.format(ui.coordStr(gXYJog))
  statusStr += 'Jog distance (Z)  = {:}\n'.format(ui.coordStr(gZJog))
  statusStr += 'VerboseLevel      = {:d}/{:d} ({:s})\n'.format(ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
  # statusStr += '\n'.format()

  ui.logBlock(statusStr)


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

  char = kb.getch()
  key=kb.ch2key(char)

  if key == kb.COMBO_0X:  # Combined code 0+x
    char = kb.getch()
    key=kb.ch2key(char)

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
        ui.keyPressMessage('Unknown command', key, char)
        pass

  elif key == kb.COMBO_224X:  # Combined code 224x
    char = kb.getch()
    key=kb.ch2key(char)

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
        ui.keyPressMessage('Unknown command', key, char)
        pass

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

    elif char in 'pP':
      ui.keyPressMessage('pP - Probe', key, char)

      ui.logBlock(
      """
      Available commands:

      1   - Basic probe
      2   - Two stage probe
      3   - Three stage probe
      """)

      ui.inputMsg('Select command...')
      char = kb.getch()
      key=kb.ch2key(char)

      if char == '1':
        ui.keyPressMessage('1 - Basic probe', key, char)
        prb.basic()

      elif char == '2':
        ui.keyPressMessage('2 - Two stage probe', key, char)
        prb.twoStage()

      elif char == '3':
        ui.keyPressMessage('3 - Three stage probe', key, char)
        prb.threeStage()

      else:
        ui.keyPressMessage('Unknown command', key, char)


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
      char = kb.getch()
      key=kb.ch2key(char)

      if char in 'lL':
        ui.keyPressMessage('lL - List macros', key, char)
        mcr.list()

      elif char in 'rR':
        ui.keyPressMessage('rR - Run macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=kb.input()
        mcr.run(macroName)

      elif char in 'sS':
        ui.keyPressMessage('sS - Show macro', key, char)
        ui.inputMsg('Enter macro name...')
        macroName=kb.input()
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
      userCommand = char + kb.input(char)
      sendCommand(userCommand)

    elif char in 'lL':
      ui.keyPressMessage('lL - Send raw GCode command (FORCE RELATIVE)', key, char)
      savedDistanceMode = mch.status['parserState']['distanceMode']['val']
      ui.inputMsg('Enter GCode command...')
      userCommand = kb.input()
      if savedDistanceMode != 'G91':
        userCommand = 'G91 ' + userCommand
      sendCommand(userCommand)
      if savedDistanceMode != 'G91':
        sendCommand(savedDistanceMode)


    elif char == 'º':
      ui.keyPressMessage('º - Repeat last GCode command', key, char)
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
      char = kb.getch()
      key=kb.ch2key(char)

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
      pP  - Reset Z to current PRB:Z
      mM  - Manual [XYZ] reset
      -   - Reset XY to machine home
      +   - Reset XY to max machine travel
      /   - Reset XYZ to machine home
      *   - Reset XY to max machine travel, Z to home
      gG  - Get GCode command for current WCO
      """)

      ui.inputMsg('Select command...')
      char = kb.getch()
      key=kb.ch2key(char)
      processed = True

      if char in 'xX':
        ui.keyPressMessage('xX - Reset X to current position', key, char)
        mch.resetWCOAxis(char.lower(), 'curr')

      elif char in 'yY':
        ui.keyPressMessage('yY - Reset Y to current position', key, char)
        mch.resetWCOAxis(char.lower(), 'curr')

      elif char in 'wW':
        ui.keyPressMessage('wW - Reset XY to current position', key, char)
        mch.resetWCO('curr','curr')

      elif char in 'zZ':
        ui.keyPressMessage('zZ - Reset Z to current position', key, char)
        mch.resetWCOAxis(char.lower(), 'curr')

      elif char in 'aA':
        ui.keyPressMessage('aA - Reset XYZ to current position', key, char)
        mch.resetWCO('curr', 'curr', 'curr')

      elif char in 'pP':
        ui.keyPressMessage('pP - Reset Z to current PRB:Z', key, char)
        mch.resetWCOAxis('z', prb.axisPos('z'))

      elif char in 'mM':
        ui.keyPressMessage('mM - Manual [XYZ] reset', key, char)
        ui.inputMsg('Enter GCode command...')
        prefix = mch.getResetWCOStr()
        userCommand = prefix + kb.input(prefix)
        sendCommand(userCommand)

      elif char == '-':
        ui.keyPressMessage('- - Reset XY to machine home', key, char)
        mch.resetWCO('home','home')

      elif char == '+':
        ui.keyPressMessage('+ - Reset XY to max machine travel', key, char)
        mch.resetWCO('away','away')

      elif char == '/':
        ui.keyPressMessage('/ - Reset XYZ to machine home', key, char)
        mch.resetWCO('home','home','home')

      elif char == '*':
        ui.keyPressMessage('* - Reset XY to max machine travel, Z to home', key, char)
        mch.resetWCO('away','away','away')

      elif char in 'gG':
        ui.keyPressMessage('gG - Get GCode command for current WCO', key, char)
        cmd = mch.getResetWCOStr('wco','wco','wco')
        ui.log(cmd, c='ui.msg')

      else:
        processed = False
        ui.keyPressMessage('Unknown command', key, char)

      if processed:
        mch.getMachineStatus()

    elif char == 'j':
      ui.keyPressMessage('j - Enable/disable joystick', key, char)
      joy.enabled = not joy.enabled

      ui.log('Joystick [{:s}] [{:s}]\n'.format(
        ui.setStrColor('CONNECTED', 'ui.successMsg') if joy.connected else ui.setStrColor('DISCONNECTED', 'ui.errorMsg'),
        ui.setStrColor('ENABLED', 'ui.successMsg') if joy.enabled else ui.setStrColor('DISABLED', 'ui.errorMsg')
      ))

    elif char == 'J':
      ui.keyPressMessage('J - Restart joystick connection', key, char)
      joy.restart()

      ui.log()
      ui.log('Joystick [{:s}] [{:s}]\n'.format(
        ui.setStrColor('CONNECTED', 'ui.successMsg') if joy.connected else ui.setStrColor('DISCONNECTED', 'ui.errorMsg'),
        ui.setStrColor('ENABLED', 'ui.successMsg') if joy.enabled else ui.setStrColor('DISABLED', 'ui.errorMsg')
      ))

    elif char == '-':
      ui.keyPressMessage('- - Jog (Z) up ({:} {:})'.format(gZJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=0,y=0,z=gZJog)

    elif char == '+':
      ui.keyPressMessage('+ - Jog (Z) down ({:} {:})'.format(gZJog, ps['units']['desc']), key, char)
      mch.moveRelative(x=0,y=0,z=gZJog*-1)

    elif char == '0':
      ui.keyPressMessage('0 - Go home', key, char)

      ui.logBlock(
      """
      Available commands:

      <numpad>0 - Safe machine home (Z0 + X0Y0)
      mM        - Machine home (submenu)
      wW        - WCO home (submenu)
      """)

      ui.inputMsg('Select command...')
      char = kb.getch()
      key=kb.ch2key(char)

      if char == '0':
        ui.keyPressMessage('<numpad>0 - Safe machine home (Z0 + X0Y0)', key, char)
        mch.goToMachineHome()


      elif char in 'mM':
        ui.keyPressMessage('m - Machine home', key, char)

        ui.logBlock(
        """
        Available commands:

        xX        - x
        yY        - y
        zZ        - z
        wW        - xy
        aA        - xyz
        """)

        ui.inputMsg('Select command...')
        char = kb.getch()
        key=kb.ch2key(char)

        if char in 'xX':
          ui.keyPressMessage('x - x', key, char)
          mch.goToMachineHome_X()
        elif char in 'yY':
          ui.keyPressMessage('y - y', key, char)
          mch.goToMachineHome_Y()
        elif char in 'zZ':
          ui.keyPressMessage('z - z', key, char)
          mch.goToMachineHome_Z()
        elif char in 'wW':
          ui.keyPressMessage('w - xy', key, char)
          mch.goToMachineHome_XY()
        elif char in 'aA':
          ui.keyPressMessage('a - xyz', key, char)
          mch.goToMachineHome()
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif char in 'wW':
        ui.keyPressMessage('w - WCO home', key, char)

        ui.logBlock(
        """
        Available commands:

        xX        - x
        yY        - y
        zZ        - z
        wW        - xy
        aA        - xyz
        """)

        ui.inputMsg('Select command...')
        char = kb.getch()
        key=kb.ch2key(char)

        if char in 'xX':
          ui.keyPressMessage('x - x', key, char)
          mch.sendWait('G0X0')
        elif char in 'yY':
          ui.keyPressMessage('y - y', key, char)
          mch.sendWait('G0Y0')
        elif char in 'zZ':
          ui.keyPressMessage('z - z', key, char)
          mch.sendWait('G0Z0')
        elif char in 'wW':
          ui.keyPressMessage('w - xy', key, char)
          mch.sendWait('G0X0Y0')
        elif char in 'aA':
          ui.keyPressMessage('a - xyz', key, char)
          mch.sendWait('G0X0Y0Z0')
        else:
          ui.keyPressMessage('Unknown command', key, char)

      else:
        ui.keyPressMessage('Unknown command', key, char)

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
      ui.keyPressMessage('. - Absolute move to table position', key, char)

      minX = mch.getMin('x')
      minY = mch.getMin('y')
      maxX = mch.getMax('x')
      maxY = mch.getMax('y')
      wX = abs(maxX-minX) if minX<0 else abs(minX-maxX)
      wY = abs(maxY-minY) if minY<0 else abs(minY-maxY)
      cX = minX-(wX/2) if minX>0 else minX+(wX/2)
      cY = minY-(wY/2) if minX>0 else minY+(wY/2)

      ui.logBlock(
      """
      Available commands:

      <numpad>  - Absolute table positions
      .         - One axis only (submenu)
      """)

      ui.inputMsg('Select command...')
      char = kb.getch()
      key=kb.ch2key(char)

      if char == '.':
        ui.keyPressMessage('. - ONE AXIS ONLY', key, char)

        ui.logBlock(
        """
        Available commands:

        <numpad>46  - Absolute X axis limits
        <numpad>28  - Absolute Y axis limits
        """)

        ui.inputMsg('Select command...')
        char = kb.getch()
        key=kb.ch2key(char)

        if char == '2':
          ui.keyPressMessage('2 - ONE AXIS ONLY - Absolute move to axis limits - [B]', key, char)
          mch.moveAbsolute(y=minY)
        elif char == '4':
          ui.keyPressMessage('4 - ONE AXIS ONLY - Absolute move to axis limits - [L]', key, char)
          mch.moveAbsolute(x=minX)
        elif char == '6':
          ui.keyPressMessage('6 - ONE AXIS ONLY - Absolute move to axis limits - [R]', key, char)
          mch.moveAbsolute(x=maxX)
        elif char == '8':
          ui.keyPressMessage('8 - ONE AXIS ONLY - Absolute move to axis limits - [U]', key, char)
          mch.moveAbsolute(y=maxY)
        else:
          ui.keyPressMessage('Unknown command', key, char)

      elif char == '1':
        ui.keyPressMessage('1 - Absolute move to table position - [BL]', key, char)
        mch.moveAbsolute(x=minX,y=minY)
      elif char == '2':
        ui.keyPressMessage('2 - Absolute move to table position - [BC]', key, char)
        mch.moveAbsolute(x=cX,y=minY)
      elif char == '3':
        ui.keyPressMessage('3 - Absolute move to table position - [BR]', key, char)
        mch.moveAbsolute(x=maxX,y=minY)
      elif char == '4':
        ui.keyPressMessage('4 - Absolute move to table position - [CL]', key, char)
        mch.moveAbsolute(x=minX,y=cY)
      elif char == '5':
        ui.keyPressMessage('5 - Absolute move to table position - [CC]', key, char)
        mch.moveAbsolute(x=cX,y=cY)
      elif char == '6':
        ui.keyPressMessage('6 - Absolute move to table position - [CR]', key, char)
        mch.moveAbsolute(x=maxX,y=cY)
      elif char == '7':
        ui.keyPressMessage('7 - Absolute move to table position - [UL]', key, char)
        mch.moveAbsolute(x=minX,y=maxY)
      elif char == '8':
        ui.keyPressMessage('8 - Absolute move to table position - [UC]', key, char)
        mch.moveAbsolute(x=cX,y=maxY)
      elif char == '9':
        ui.keyPressMessage('9 - Absolute move to table position - [UR]', key, char)
        mch.moveAbsolute(x=maxX,y=maxY)
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
      ui.keyPressMessage('Unknown command {:s} ({:d})'.format(char, key), key, char)

  if processed:
    readyMsg()

  return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def processJoystickInput():
  global gXYJog
  global gZJog

  joy.process()

  processed = True

  # see: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Jogging#joystick-implementation
  # for key in joy.status:
  #   status = joy.status[key]
  #   if status:
  #     print('jog: {:s}'.format(key))
  ps = mch.status['parserState']
  unitsDesc = ps['units']['desc']

  # Special actions with 'extraU' pushed
  if joy.status['extraU']:
    if joy.status['x+']:
      gXYJog = ut.genericValueChanger(gXYJog, +1, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (+1) ({:})'.format(gXYJog), 0, '')

    elif joy.status['x-']:
      gXYJog = ut.genericValueChanger(gXYJog, -1, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (-1) ({:})'.format(gXYJog), 0, '')

    elif joy.status['y+']:
      gXYJog = ut.genericValueChanger(gXYJog, +10, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (+10) ({:})'.format(gXYJog), 0, '')

    elif joy.status['y-']:
      gXYJog = ut.genericValueChanger(gXYJog, -10, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (-10) ({:})'.format(gXYJog), 0, '')

    elif joy.status['z+']:
      ui.keyPressMessage('Go to machine home Z', 0, '')
      mch.goToMachineHome_Z()

    else:
      processed = False

  # Special actions with 'extraD' pushed
  elif joy.status['extraD']:
    if joy.status['x+']:
      gZJog = ut.genericValueChanger(gZJog, +1, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (+1) ({:})'.format(gZJog), 0, '')

    elif joy.status['x-']:
      gZJog = ut.genericValueChanger(gZJog, -1, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (-1) ({:})'.format(gZJog), 0, '')

    elif joy.status['y+']:
      gZJog = ut.genericValueChanger(gZJog, +10, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (+10)] ({:})'.format(gZJog), 0, '')

    elif joy.status['y-']:
      gZJog = ut.genericValueChanger(gZJog, -10, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (-10)] ({:})'.format(gZJog), 0, '')

    elif joy.status['z+']:
      ui.keyPressMessage('Go to machine home', 0, '')
      mch.goToMachineHome()

    else:
      processed = False

  # Normal actions
  elif joy.status['y-'] and joy.status['x-']:
    ui.keyPressMessage('JoyJog - [DL] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog*-1,y=gXYJog*-1)

  elif joy.status['y-'] and joy.status['x+']:
    ui.keyPressMessage('JoyJog - [DR] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog,y=gXYJog*-1)

  elif joy.status['y+'] and joy.status['x-']:
    ui.keyPressMessage('JoyJog - [UL] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog*-1,y=gXYJog)

  elif joy.status['y+'] and joy.status['x+']:
    ui.keyPressMessage('JoyJog - [UR] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog,y=gXYJog)

  elif joy.status['y-']:
    ui.keyPressMessage('JoyJog - [D] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(y=gXYJog*-1)

  elif joy.status['y+']:
    ui.keyPressMessage('JoyJog - [U] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(y=gXYJog)

  elif joy.status['x-']:
    ui.keyPressMessage('JoyJog - [L] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog*-1)

  elif joy.status['x+']:
    ui.keyPressMessage('JoyJog - [R] ({:} {:})'.format(gXYJog, unitsDesc), 0, '')
    mch.moveRelative(x=gXYJog)

  elif joy.status['z+']:
    ui.keyPressMessage('JoyJog (Z) up ({:} {:})'.format(gZJog, unitsDesc), 0, '')
    mch.moveRelative(x=0,y=0,z=gZJog)

  elif joy.status['z-']:
    ui.keyPressMessage('JoyJog (Z) down ({:} {:})'.format(gZJog, unitsDesc), 0, '')
    mch.moveRelative(x=0,y=0,z=gZJog*-1)

  else:
    processed = False

  if processed:
    readyMsg()


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

  ui.logTitle('Joystick connection')
  joy.start()
  ui.log()

  sendStartupMacro()

  ui.log('System ready!', color='ui.successMsg')

  showMachineStatus()
  ui.log('Type [hH] for help', color='ui.msg')

  readyMsg()

  while True:
    mch.process()

    processJoystickInput()

    if not processUserInput():
      break

  ui.log('Closing grbl connection...')
  mch.stop()

  ui.log('Closing program...')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def execTestCode():

  ui.logBlock('  TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE', color='ui.cancelMsg')

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
#    kb.getch()
