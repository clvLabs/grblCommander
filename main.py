#!/usr/bin/python3
'''
grblCommander
=============
Allows to control a CNC driven by a grblShield
'''

import sys
import time
import pprint

import src.gc.utils as ut
import src.gc.ui as ui
import src.gc.menu as menu
import src.gc.keyboard as keyboard
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
gVERSION = '0.11.0'

# keyboard manager
kb = keyboard.Keyboard()

# menu manager
mnu = menu.Menu(kb)

# grbl machine manager
mch = grbl.Grbl(cfg)

# grbl probe manager
prb = probe.Probe(mch)

# joystick manager
joy = joystick.Joystick(cfg)

mcr = macro.Macro(mch, kb)
tst = test.Test(mch, kb)

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
    responseTimeout = float(mchCfg['homingTimeout'])

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
  '''
  General commands
  ---------------------------------------------------------------------
  qQ         - Quit
  <CTRL>r    - Reset serial connection
  <CTRL>x    - grbl soft reset
  =          - Lock grblCommander
  cC         - Clear screen

  Info
  ---------------------------------------------------------------------
  hH         - Show this help text
  <ENTER>/?  - Force status re-query
  s/S        - Show current status (short/LONG)
  @          - Show current status (FULL)
  eE         - Show grbl settings
  v/V        - Set verbose level (-/+) (loop)

  Machine control
  ---------------------------------------------------------------------
  <numpad>0  - Go home (submenu)
  <numpad>.  - Absolute move (XY) to table position (submenu)
  gfxyz$     - Send raw GCode command
  [space]    - Send raw GCode command (start empty)
  lL         - Send raw GCode command (FORCE RELATIVE)
  º          - Repeat last GCode command
  rR         - Reset work coordinate (submenu)
  pP         - Probe (submenu)
  mM         - Macro (submenu)
  tT         - Tests (submenu)

  Jog
  ---------------------------------------------------------------------
  <numpad>         - XY jog (including diagonals)
  <SHIFT>+<numpad> - XY jog (double distance)
  <CTRL><numpad>   - XY jog (half distance)
  <numpad>-/+      - Z jog (up/down)
  /                - Set jog distance (XY)
  *                - Set jog distance (Z)

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
  ''')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineStatus():
  mch.getMachineStatus()

  statusStr = ''

  statusStr += 'Current status: [{:}]\n'.format(mch.getColoredMachineStateStr())
  statusStr += '\n'
  statusStr += 'Alarm    [{:s}]\n'.format(ui.color(mch.getAlarmStr(), 'ui.errorMsg'))
  statusStr += 'Msg      [{:s}]\n'.format(ui.color(mch.getLastMessage(), 'ui.msg'))
  statusStr += '\n'
  statusStr += 'MPos     [{:s}]\n'.format(mch.getMachinePosStr())
  statusStr += 'WCO      [{:s}]\n'.format(mch.getWorkCoordinatesStr())
  statusStr += 'WPos     [{:s}]\n'.format(mch.getWorkPosStr())
  statusStr += 'PRB      {:s}\n'.format(mch.getProbePosStr())
  statusStr += '\n'
  statusStr += 'INPins   {:s}\n'.format(mch.getInputPinStateLongStr())

  statusStr += 'Parser:\n'
  settings = mch.getCompleteParserState()
  for s in settings:
    statusStr += '  - {:}\n'.format(s)
  statusStr += '\n'

  statusStr += 'Joystick [{:s}] [{:s}]\n'.format(
    ui.color('CONNECTED', 'ui.successMsg') if joy.connected else ui.color('DISCONNECTED', 'ui.errorMsg'),
    ui.color('ENABLED', 'ui.successMsg') if joy.enabled else ui.color('DISABLED', 'ui.errorMsg')
  )

  statusStr += '\n'
  statusStr += 'Software config:\n'
  statusStr += 'Jog distance (XY) = {:}\n'.format(ui.coordStr(gXYJog))
  statusStr += 'Jog distance (Z)  = {:}\n'.format(ui.coordStr(gZJog))
  statusStr += 'VerboseLevel      = {:d}/{:d} ({:s})\n'.format(ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
  # statusStr += '\n'.format()

  ui.logBlock(statusStr)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showGrblSettings():

  settingsStr = ''

  settingsStr += 'grbl settings:\n'
  settingsStr += '\n'
  settings = mch.getCompleteGrblSettings()
  for s in settings:
    settingsStr += '  - {:}\n'.format(s)
  settingsStr += '\n'

  ui.logBlock(settingsStr)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineLongStatus():
  showMachineStatus()
  mcr.run(mcrCfg['machineLongStatus'], silent=True)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMachineFullStatus():
  machineStatus=mch.getMachineStatus()

  ui.logBlock(
  '''
  Machine FULL status: [{:}]

  {:s}
  '''.format(
      mch.getColoredMachineStateStr(),
      pprint.pformat(machineStatus, indent=2, width=uiCfg['maxLineLen'])
    ))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def lockGrblCommander():
  while not ui.userConfirm(
    '================= grblCommander is LOCKED =================',
    'unlock'):
    pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def _processUserInput():
  global gXYJog
  global gZJog

  if not kb.keyPressed():
    return True

  processed = True
  ps = mch.status['parserState']

  char = kb.getch()
  key = kb.ch2key(char)

  if key == kb.COMBO_0X:  # Combined code 0+x
    char = kb.getch()
    key = kb.ch2key(char)
    unitsDesc = ps['units']['desc']

    if key == 999999:
      pass
    elif key == kb.F1:
      mcr.runHotKeyMacro('F1')
    elif key == kb.F2:
      mcr.runHotKeyMacro('F2')
    elif key == kb.F3:
      mcr.runHotKeyMacro('F3')
    elif key == kb.F4:
      mcr.runHotKeyMacro('F4')
    elif key == kb.F5:
      mcr.runHotKeyMacro('F5')
    elif key == kb.F6:
      mcr.runHotKeyMacro('F6')
    elif key == kb.F7:
      mcr.runHotKeyMacro('F7')
    elif key == kb.F8:
      mcr.runHotKeyMacro('F8')
    elif key == kb.F9:
      mcr.runHotKeyMacro('F9')
    elif key == kb.F10:
      mcr.runHotKeyMacro('F10')

    elif key == kb.KP_END:
      ui.keyPressMessage('End - Jog - [DL] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*-2,y=gXYJog*-2)

    elif key == kb.KP_DOWN:
      ui.keyPressMessage('Down - Jog - [D] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(y=gXYJog*-2)

    elif key == kb.KP_PGDN:
      ui.keyPressMessage('Pgdn - Jog - [DR] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*2,y=gXYJog*-2)

    elif key == kb.KP_LEFT:
      ui.keyPressMessage('Left - Jog - [L] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*-2)

    elif key == kb.KP_RIGHT:
      ui.keyPressMessage('Right - Jog - [R] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*2)

    elif key == kb.KP_HOME:
      ui.keyPressMessage('Home - Jog - [UL] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*-2,y=gXYJog*2)

    elif key == kb.KP_UP:
      ui.keyPressMessage('Up - Jog - [U] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(y=gXYJog*2)

    elif key == kb.KP_PGUP:
      ui.keyPressMessage('Pgup - Jog - [UR] [*2] ({:} {:})'.format(gXYJog*2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog*2,y=gXYJog*2)

    elif key == kb.CTRL_KP_END:
      ui.keyPressMessage('End - Jog - [DL] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1,y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_DOWN:
      ui.keyPressMessage('Down - Jog - [D] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_PGDN:
      ui.keyPressMessage('Pgdn - Jog - [DR] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog/2,y=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_LEFT:
      ui.keyPressMessage('Left - Jog - [L] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1)

    elif key == kb.CTRL_KP_RIGHT:
      ui.keyPressMessage('Right - Jog - [R] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(x=gXYJog/2)

    elif key == kb.CTRL_KP_HOME:
      ui.keyPressMessage('Home - Jog - [UL] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(x=(gXYJog/2)*-1,y=gXYJog/2)

    elif key == kb.CTRL_KP_UP:
      ui.keyPressMessage('Up - Jog - [U] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
      mch.moveRelative(y=gXYJog/2)

    elif key == kb.CTRL_KP_PGUP:
      ui.keyPressMessage('Pgup - Jog - [UR] [/2] ({:} {:})'.format(gXYJog/2, unitsDesc), key, char)
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
    key = kb.ch2key(char)

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

    if False:
      pass

    elif char == '?' or key == kb.ENTER:
      ui.keyPressMessage('<ENTER>/? - Force status re-query', key, char)
      mch.viewMachineStatus()

    elif key == kb.CTRL_R:
      ui.keyPressMessage('<CTRL>r - Reset serial connection', key, char)
      mch.resetConnection()
      mch.queryMachineStatus()

    elif key == kb.CTRL_X:
      ui.keyPressMessage('<CTRL>x - grbl soft reset', key, char)
      mch.softReset()

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
def onParserStateChanged():
  # While running, machine is already displaying status
  if not mch.isRunning():
    ui.log(mch.getSimpleMachineStatusStr())


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def jogXY(d, tx=None):
  ''' Machine relative jog XY.
      - d : direction(string) 'UDLR'
      - t : transform (lambda)
  '''
  d = d.upper()
  x = 0
  y = 0

  if 'U' in d:  y = gXYJog
  if 'D' in d:  y = gXYJog * -1
  if 'L' in d:  x = gXYJog * -1
  if 'R' in d:  x = gXYJog

  if tx:
    x = tx(x)
    y = tx(y)

  mch.moveRelative(x=x, y=y)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def jogZ(d, tx=None):
  ''' Machine relative jog XY.
      - d : direction(string) 'UDLR'
      - t : transform (lambda)
  '''
  d = d.upper()
  z = 0

  if 'U' in d:  z = gZJog
  if 'D' in d:  z = gZJog * -1

  if tx:
    z = tx(z)

  mch.moveRelative(z=z)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def runMacro():
  ui.inputMsg('Enter macro name...')
  macroName=kb.input()
  mcr.run(macroName)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showMacro():
  ui.inputMsg('Enter macro name...')
  macroName=kb.input()
  mcr.show(macroName)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def goToWCHOHome():
  mch.sendWait('G0X0Y0')
  mch.sendWait('G0Z0')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def repeatLastGCodeCommand():
  sendCommand(gLastGCodeCommand)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def resetZToCurrProbeZ():
  mch.resetWCOAxis('z', prb.axisPos('z'))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def manualXYZReset():
  ui.inputMsg('Enter GCode command...')
  prefix = mch.getResetWCOStr()
  userCommand = prefix + kb.input(prefix)
  sendCommand(userCommand)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getWCOResetCommand():
  cmd = mch.getResetWCOStr('wco','wco','wco')
  ui.log(cmd, c='ui.msg')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendRawGCodeCommand(char=''):
  ui.inputMsg('Enter GCode command...')
  userCommand = char + kb.input(char)
  sendCommand(userCommand)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendRawGCodeCommandRELATIVE():
  savedDistanceMode = mch.status['parserState']['distanceMode']['val']
  ui.inputMsg('Enter GCode command...')
  userCommand = kb.input()
  if savedDistanceMode != 'G91':
    userCommand = 'G91 ' + userCommand
  sendCommand(userCommand)
  if savedDistanceMode != 'G91':
    sendCommand(savedDistanceMode)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def toggleJoystickEnable():
  joy.enabled = not joy.enabled

  ui.log('Joystick [{:s}] [{:s}]\n'.format(
    ui.color('CONNECTED', 'ui.successMsg') if joy.connected else ui.color('DISCONNECTED', 'ui.errorMsg'),
    ui.color('ENABLED', 'ui.successMsg') if joy.enabled else ui.color('DISABLED', 'ui.errorMsg')
  ))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def restartJoystickConnection():
  joy.restart()

  ui.log()
  ui.log('Joystick [{:s}] [{:s}]\n'.format(
    ui.color('CONNECTED', 'ui.successMsg') if joy.connected else ui.color('DISCONNECTED', 'ui.errorMsg'),
    ui.color('ENABLED', 'ui.successMsg') if joy.enabled else ui.color('DISABLED', 'ui.errorMsg')
  ))


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def setXYJogDistance():
  global gXYJog
  gXYJog = ui.getUserInput(
    'Distance ({:})'.format(gXYJog),
    float,
    gXYJog)
  showMachineStatus()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def setZJogDistance():
  global gZJog
  gZJog = ui.getUserInput(
    'Distance ({:})'.format(gZJog),
    float,
    gZJog)
  showMachineStatus()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeVerboseLevel(inc):
  tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), inc, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                        loop=True, valueName='Verbose level',
                        valueFormatter=lambda level : '{:d} {:s}'.format(level,ui.getVerboseLevelStr(level)) )
  ui.setVerboseLevel(tempVerboseLevel)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def absoluteXYAxisLimits(d):
  minX = mch.getMin('x')
  minY = mch.getMin('y')
  maxX = mch.getMax('x')
  maxY = mch.getMax('y')

  d = d.upper()
  x = None
  y = None

  if 'U' in d:  y = maxY
  if 'D' in d:  y = minY
  if 'L' in d:  x = minX
  if 'R' in d:  x = maxX

  mch.moveAbsolute(x=x, y=y)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def absoluteTablePosition(p):
  minX = mch.getMin('x')
  minY = mch.getMin('y')
  maxX = mch.getMax('x')
  maxY = mch.getMax('y')
  wX = abs(maxX-minX) if minX<0 else abs(minX-maxX)
  wY = abs(maxY-minY) if minY<0 else abs(minY-maxY)
  cX = minX-(wX/2) if minX>0 else minX+(wX/2)
  cY = minY-(wY/2) if minX>0 else minY+(wY/2)

  p = p.upper()
  yPos = p[0]
  xPos = p[1]

  x = None
  y = None

  if yPos == 'U':   y = maxY
  elif yPos == 'C': y = cY
  elif yPos == 'D': y = minY

  if xPos == 'L':   y = minX
  elif xPos == 'C': y = cX
  elif xPos == 'R': y = maxX

  mch.moveAbsolute(x=x, y=y)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def dummy():
  pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def dummy():
  pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def dummy():
  pass


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def NOT_IMPLEMENTED():
  ui.log('Not implemented yet...', c='ui.errorMsg')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def setupMenu():

  absoluteXYAxisLimitsSubmenu = menu.Menu(kb, [
    {'k':'2',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [D]',  'h':absoluteXYAxisLimits, 'ha':{'d':'D'}},
    {'k':'8',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [U]',  'h':absoluteXYAxisLimits, 'ha':{'d':'U'}},
    {'k':'4',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [L]',  'h':absoluteXYAxisLimits, 'ha':{'d':'L'}},
    {'k':'6',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [R]',  'h':absoluteXYAxisLimits, 'ha':{'d':'R'}},
  ])

  absoluteTablePositionSubmenu = menu.Menu(kb, [
    {'k':'.',   'n':'One axis only (*)',                       'h':absoluteXYAxisLimitsSubmenu},
    {'k':'1',   'n':'Absolute move to table position - [DL]',  'h':absoluteTablePosition, 'ha':{'p':'DL'}},
    {'k':'2',   'n':'Absolute move to table position - [DC]',  'h':absoluteTablePosition, 'ha':{'p':'DC'}},
    {'k':'3',   'n':'Absolute move to table position - [DR]',  'h':absoluteTablePosition, 'ha':{'p':'DR'}},
    {'k':'4',   'n':'Absolute move to table position - [CL]',  'h':absoluteTablePosition, 'ha':{'p':'CL'}},
    {'k':'5',   'n':'Absolute move to table position - [CC]',  'h':absoluteTablePosition, 'ha':{'p':'CC'}},
    {'k':'6',   'n':'Absolute move to table position - [CR]',  'h':absoluteTablePosition, 'ha':{'p':'CR'}},
    {'k':'7',   'n':'Absolute move to table position - [UL]',  'h':absoluteTablePosition, 'ha':{'p':'UL'}},
    {'k':'8',   'n':'Absolute move to table position - [UC]',  'h':absoluteTablePosition, 'ha':{'p':'UC'}},
    {'k':'9',   'n':'Absolute move to table position - [UR]',  'h':absoluteTablePosition, 'ha':{'p':'UR'}},
  ])

  machineHomeSubmenu = menu.Menu(kb, [
    {'k':'xX',  'n':'x',   'h':mch.goToMachineHome_X},
    {'k':'yY',  'n':'y',   'h':mch.goToMachineHome_Y},
    {'k':'zZ',  'n':'z',   'h':mch.goToMachineHome_Z},
    {'k':'wW',  'n':'xy',  'h':mch.goToMachineHome_XY},
    {'k':'aA',  'n':'xyz', 'h':mch.goToMachineHome},
  ])

  wcoHomeSubmenu = menu.Menu(kb, [
    {'k':'xX',  'n':'x',   'h':mch.sendWait, 'ha':{'command':'G0X0'}},
    {'k':'yY',  'n':'y',   'h':mch.sendWait, 'ha':{'command':'G0Y0'}},
    {'k':'zZ',  'n':'z',   'h':mch.sendWait, 'ha':{'command':'G0Z0'}},
    {'k':'wW',  'n':'xy',  'h':mch.sendWait, 'ha':{'command':'G0X0Y0'}},
    {'k':'aA',  'n':'xyz', 'h':goToWCHOHome},
  ])

  goHomeSubmenu = menu.Menu(kb, [
    {'k':'0',   'n':'Safe machine home (Z0 + X0Y0)', 'h':mch.goToMachineHome},
    {'k':'mM',  'n':'Machine home (*)',              'h':machineHomeSubmenu},
    {'k':'wW',  'n':'WCO home (*)',                  'h':wcoHomeSubmenu},
  ])

  macroSubmenu = menu.Menu(kb, [
    {'k':'lL',  'n':'List macros',   'h':mcr.list},
    {'k':'rR',  'n':'Run macro',     'h':runMacro},
    {'k':'sS',  'n':'Show macro',    'h':showMacro},
    {'k':'xX',  'n':'Reload macros', 'h':mcr.load},
  ])

  testsSubmenu = menu.Menu(kb, [
    {'k':'sS',  'n':'Table position scan',  'h':tst.tablePositionScan},
    {'k':'lL',  'n':'Base levelling holes', 'h':tst.baseLevelingHoles},
    {'k':'zZ',  'n':'Zig-zag pattern',      'h':tst.zigZagPattern},
    {'k':'*',   'n':'DUMMY Test',           'h':tst.dummy},
  ])

  resetSubmenu = menu.Menu(kb, [
    {'SECTION':1, 'n':'Reset to current position'},
    {'k':'xX',   'n':'X',    'h':mch.resetWCO,      'ha':{'x':'curr'}},
    {'k':'yY',   'n':'Y',    'h':mch.resetWCO,      'ha':{'y':'curr'}},
    {'k':'zZ',   'n':'Z',    'h':mch.resetWCO,      'ha':{'z':'curr'}},
    {'k':'wW',   'n':'XY',   'h':mch.resetWCO,      'ha':{'x':'curr', 'y':'curr'}},
    {'k':'aA',   'n':'XYZ',  'h':mch.resetWCO,      'ha':{'x':'curr', 'y':'curr', 'z':'curr'}},

    {'SECTION':1, 'n':'Reset to machine limits'},
    {'k':'-',    'n':'XY to machine home',                  'h':mch.resetWCO, 'ha':{'x':'home', 'y':'home'}},
    {'k':'+',    'n':'XY to max machine travel',            'h':mch.resetWCO, 'ha':{'x':'away', 'y':'away'}},
    {'k':'/',    'n':'XYZ to machine home',                 'h':mch.resetWCO, 'ha':{'x':'home', 'y':'home', 'z':'home'}},
    {'k':'*',    'n':'XY to max machine travel, Z to home', 'h':mch.resetWCO, 'ha':{'x':'away', 'y':'away', 'z':'home'}},

    {'SECTION':1, 'n':'Misc.'},
    {'k':'pP',   'n':'Reset Z to current PRB:Z',          'h':resetZToCurrProbeZ},
    {'k':'mM',   'n':'Manual [XYZ] reset',                'h':manualXYZReset},
    {'k':'gG',   'n':'Get GCode command for current WCO', 'h':getWCOResetCommand},
  ])

  probeSubmenu = menu.Menu(kb, [
    {'k':'1',   'n':'Basic probe',       'h':prb.basic},
    {'k':'2',   'n':'Two stage probe',   'h':prb.twoStage},
    {'k':'3',   'n':'Three stage probe', 'h':prb.threeStage},
  ])

  mnu.setOptions([
    {'SECTION':1, 'n':'General commands'},
    {'k':'qQ',           'n':'Quit',                         'h':mnu.quit},
    {'k':'',             'n':'***Reset serial connection',   'h':NOT_IMPLEMENTED},
    {'k':'',             'n':'***grbl soft reset',           'h':NOT_IMPLEMENTED},
    {'k':'=',            'n':'Lock grblCommander',           'h':lockGrblCommander},
    {'k':'cC',           'n':'Clear screen',                 'h':ui.clearScreen},

    {'SECTION':1, 'n':'Info'},
    {'k':'hH',           'n':'Show help',                    'h':mnu.showOptions},
    {'k':'',             'n':'***Force status re-query',     'h':NOT_IMPLEMENTED},
    {'k':'s',            'n':'Show current status (short)',  'h':showMachineStatus},
    {'k':'S',            'n':'Show current status (LONG)',   'h':showMachineLongStatus},
    {'k':'@',            'n':'Show current status (FULL)',   'h':showMachineFullStatus},
    {'k':'eE',           'n':'Show grbl settings',           'h':showGrblSettings},
    {'k':'v',            'n':'Set verbose level -',          'h':changeVerboseLevel, 'ha':{'inc':-1}},
    {'k':'V',            'n':'Set verbose level +',          'h':changeVerboseLevel, 'ha':{'inc':+1}},

    {'SECTION':1, 'n':'Machine control'},
    {'k':'0',            'n':'Go home (*)',                             'h':goHomeSubmenu},
    {'k':'.',            'n':'Absolute move to table position (*)',     'h':absoluteTablePositionSubmenu},
    {'k':'gGfFxXyYzZ$',  'n':'Send raw GCode command',                  'h':sendRawGCodeCommand, 'xha':{'inChar':'char'}},
    {'k':' ',            'n':'Send raw GCode command (start EMPTY)',    'h':sendRawGCodeCommand},
    {'k':'lL',           'n':'Send raw GCode command (FORCE RELATIVE)', 'h':sendRawGCodeCommandRELATIVE},
    {'k':'º',            'n':'Repeat last GCode command',               'h':repeatLastGCodeCommand},
    {'k':'rR',           'n':'Reset work coordinate (*)',               'h':resetSubmenu},
    {'k':'pP',           'n':'Probe (*)',                               'h':probeSubmenu},
    {'k':'mM',           'n':'Macro (*)',                               'h':macroSubmenu},
    {'k':'tT',           'n':'Tests (*)',                               'h':testsSubmenu},

    {'SECTION':1, 'n':'Jog'},
    {'INFO':1, 'k':'<numpad>',         'n':'XY jog (including diagonals)'},
    {'INFO':1, 'k':'<SHIFT>+<numpad>', 'n':'XY jog (double distance)'},
    {'INFO':1, 'k':'<CTRL><numpad>',   'n':'XY jog (half distance)'},
    {'k':'/',   'n':'Set XY jog distance', 'h':setXYJogDistance},
    {'k':'*',   'n':'Set Z jog distance',  'h':setZJogDistance},

    {'HIDDEN':1, 'k':'1',   'n':'Jog - [DL]',          'h':jogXY, 'ha':{'d':'DL'}},
    {'HIDDEN':1, 'k':'2',   'n':'Jog - [D]',           'h':jogXY, 'ha':{'d':'D'}},
    {'HIDDEN':1, 'k':'3',   'n':'Jog - [DR]',          'h':jogXY, 'ha':{'d':'DR'}},
    {'HIDDEN':1, 'k':'4',   'n':'Jog - [L]',           'h':jogXY, 'ha':{'d':'L'}},
    {'HIDDEN':1, 'k':'6',   'n':'Jog - [R]',           'h':jogXY, 'ha':{'d':'R'}},
    {'HIDDEN':1, 'k':'7',   'n':'Jog - [UL]',          'h':jogXY, 'ha':{'d':'UL'}},
    {'HIDDEN':1, 'k':'8',   'n':'Jog - [U]',           'h':jogXY, 'ha':{'d':'U'}},
    {'HIDDEN':1, 'k':'9',   'n':'Jog - [UR]',          'h':jogXY, 'ha':{'d':'UR'}},
    {'HIDDEN':1, 'k':'-',   'n':'Jog - (Z) [U]',       'h':jogZ,  'ha':{'d':'U'}},
    {'HIDDEN':1, 'k':'+',   'n':'Jog - (Z) [D]',       'h':jogZ,  'ha':{'d':'D'}},

    {'SECTION':1, 'n':'Joystick'},
    {'k':'j',   'n':'Enable/disable joystick',     'h':toggleJoystickEnable},
    {'k':'J',   'n':'Restart joystick connection', 'h':restartJoystickConnection},

    {'INFO':1, 'k':'<xy>',             'n':'XY jog (including diagonals)'},
    {'INFO':1, 'k':'<z>-/+',           'n':'Z jog (up/down)'},
    {'INFO':1, 'k':'<extraU><z+>',     'n':'Go to machine home Z'},
    {'INFO':1, 'k':'<extraD><z+>',     'n':'Go to machine home'},
    {'INFO':1, 'k':'<extraU><x>',      'n':'Change jog distance (XY) (+-1)'},
    {'INFO':1, 'k':'<extraU><y>',      'n':'Change jog distance (XY) (+-10)'},
    {'INFO':1, 'k':'<extraD><x>',      'n':'Change jog distance (Z) (+-1)'},
    {'INFO':1, 'k':'<extraD><y>',      'n':'Change jog distance (Z) (+-10)'},


  ])

  #   ui.keyPressMessage('9 - Jog - [UR] ({:} {:})'.format(gXYJog, ps['units']['desc']), key, char)

  mnu.setSettings({
    'readyMsg': readyMsg,
  })

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
  ui.clearScreen()

  ui.logBlock('    grblCommander v{:}'.format(gVERSION), c='ui.header')

  ui.logTitle('Loading configuration')
  ui.log('Using configuration file: {:}'.format(loadedCfg))
  ui.log()

  ui.logTitle('Loading macros')
  mcr.load()
  ui.log()

  ui.logTitle('Grbl connection')
  # Register parserStateChanged listener
  mch.onParserStateChanged.append(onParserStateChanged)
  # Start connection
  mch.start()

  ui.logTitle('Joystick connection')
  joy.start()
  ui.log()

  sendStartupMacro()

  setupMenu()

  ui.log('System ready!', c='ui.successMsg')

  showMachineStatus()
  ui.log('Type [hH] for help', c='ui.msg')

  readyMsg()

  while True:
    mch.process()

    processJoystickInput()

    if not mnu.process():
      break

  ui.log('Closing grbl connection...')
  mch.stop()

  ui.log('Closing program...')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def execTestCode():

  ui.logBlock('  TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE - TEST ACTIVE', c='ui.cancelMsg')

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
