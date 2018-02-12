#!/usr/bin/python3
'''
grblCommander
=============
Allows to control a CNC driven by a grblShield
'''

import sys
import time
import pprint

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

# UI manager
ui = ui.UI(cfg, kb)

# menu manager
mnu = menu.Menu(kb, ui)

# grbl machine manager
mch = grbl.Grbl(cfg, ui)

# grbl probe manager
prb = probe.Probe(cfg, ui, mch)

# joystick manager
joy = joystick.Joystick(cfg, ui)

mcr = macro.Macro(cfg, kb, ui, mch)
tst = test.Test(cfg, kb, ui, mch)

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
  homing = False
  if mch.stripCommand(command) == mch.GRBL_HOMING_CYCLE:
    homing = True

  mch.sendWait(command)

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
  statusStr += 'VerboseLevel      = {:d}/{:d} ({:s})\n'.format(ui.getVerboseLevel(), ui.MAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
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
      gXYJog = genericValueChanger(gXYJog, +1, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (+1) ({:})'.format(gXYJog))

    elif joy.status['x-']:
      gXYJog = genericValueChanger(gXYJog, -1, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (-1) ({:})'.format(gXYJog))

    elif joy.status['y+']:
      gXYJog = genericValueChanger(gXYJog, +10, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (+10) ({:})'.format(gXYJog))

    elif joy.status['y-']:
      gXYJog = genericValueChanger(gXYJog, -10, 1, 100, loop=True, valueName='xyJog')
      ui.keyPressMessage('Change jog distance (XY) (-10) ({:})'.format(gXYJog))

    elif joy.status['z+']:
      ui.keyPressMessage('Go to machine home Z')
      mch.goToMachineHome_Z()

    else:
      processed = False

  # Special actions with 'extraD' pushed
  elif joy.status['extraD']:
    if joy.status['x+']:
      gZJog = genericValueChanger(gZJog, +1, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (+1) ({:})'.format(gZJog))

    elif joy.status['x-']:
      gZJog = genericValueChanger(gZJog, -1, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (-1) ({:})'.format(gZJog))

    elif joy.status['y+']:
      gZJog = genericValueChanger(gZJog, +10, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (+10)] ({:})'.format(gZJog))

    elif joy.status['y-']:
      gZJog = genericValueChanger(gZJog, -10, 1, 20, loop=True, valueName='zJog')
      ui.keyPressMessage('Change jog distance (Z) (-10)] ({:})'.format(gZJog))

    elif joy.status['z+']:
      ui.keyPressMessage('Go to machine home')
      mch.goToMachineHome()

    else:
      processed = False

  # Normal actions
  elif joy.status['y-'] and joy.status['x-']:
    ui.keyPressMessage('JoyJog - [DL] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog*-1,y=gXYJog*-1)

  elif joy.status['y-'] and joy.status['x+']:
    ui.keyPressMessage('JoyJog - [DR] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog,y=gXYJog*-1)

  elif joy.status['y+'] and joy.status['x-']:
    ui.keyPressMessage('JoyJog - [UL] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog*-1,y=gXYJog)

  elif joy.status['y+'] and joy.status['x+']:
    ui.keyPressMessage('JoyJog - [UR] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog,y=gXYJog)

  elif joy.status['y-']:
    ui.keyPressMessage('JoyJog - [D] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(y=gXYJog*-1)

  elif joy.status['y+']:
    ui.keyPressMessage('JoyJog - [U] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(y=gXYJog)

  elif joy.status['x-']:
    ui.keyPressMessage('JoyJog - [L] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog*-1)

  elif joy.status['x+']:
    ui.keyPressMessage('JoyJog - [R] ({:} {:})'.format(gXYJog, unitsDesc))
    mch.moveRelative(x=gXYJog)

  elif joy.status['z+']:
    ui.keyPressMessage('JoyJog (Z) up ({:} {:})'.format(gZJog, unitsDesc))
    mch.moveRelative(x=0,y=0,z=gZJog)

  elif joy.status['z-']:
    ui.keyPressMessage('JoyJog (Z) down ({:} {:})'.format(gZJog, unitsDesc))
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


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def setZJogDistance():
  global gZJog
  gZJog = ui.getUserInput(
    'Distance ({:})'.format(gZJog),
    float,
    gZJog)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def genericValueChanger(value, direction, min, max, loop=False, valueName='', valueFormatter=None):
  newValue = 0
  increment = 0

  increment = direction

  if( direction > 0 ):  # Up
    if(  ( value < max )
    and  ( value + increment > max ) ):
      increment = max - value

  else:          # Down
    if(  ( value > min )
    and  ( value + increment  < min ) ):
      increment = min - value

  newValue = value + increment

  if(loop):
    if( newValue < min ):  newValue = max
    if( newValue > max ):  newValue = min
  else:
    if( newValue < min ):
      ui.log('ERROR: {:s} below {:d} not allowed!'.format(valueName, min), c='ui.errorMsg', v='ERROR')
      return value

    if( newValue > max ):
      ui.log('ERROR: {:s} over {:d} not allowed!'.format(valueName, max), c='ui.errorMsg', v='ERROR')
      return value

  if( valueFormatter != None ):
    formattedValue = valueFormatter( newValue )
  else:
    formattedValue = newValue

  ui.log('New {:s}: {:}'.format(valueName, formattedValue))
  return newValue


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeVerboseLevel(inc):
  tempVerboseLevel = genericValueChanger(  ui.getVerboseLevel(), inc, ui.MIN_VERBOSE_LEVEL, ui.MAX_VERBOSE_LEVEL,
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
def resetSerialConnection():
  mch.resetConnection()
  mch.queryMachineStatus()


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

  absoluteXYAxisLimitsSubmenu = mnu.subMenu([
    {'k':'2',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [D]',  'h':absoluteXYAxisLimits, 'ha':{'d':'D'}},
    {'k':'8',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [U]',  'h':absoluteXYAxisLimits, 'ha':{'d':'U'}},
    {'k':'4',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [L]',  'h':absoluteXYAxisLimits, 'ha':{'d':'L'}},
    {'k':'6',   'n':'ONE AXIS ONLY - Absolute move to axis limits - [R]',  'h':absoluteXYAxisLimits, 'ha':{'d':'R'}},
  ])

  absoluteTablePositionSubmenu = mnu.subMenu([
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

  machineHomeSubmenu = mnu.subMenu([
    {'k':'xX',  'n':'x',   'h':mch.goToMachineHome_X},
    {'k':'yY',  'n':'y',   'h':mch.goToMachineHome_Y},
    {'k':'zZ',  'n':'z',   'h':mch.goToMachineHome_Z},
    {'k':'wW',  'n':'xy',  'h':mch.goToMachineHome_XY},
    {'k':'aA',  'n':'xyz', 'h':mch.goToMachineHome},
  ])

  wcoHomeSubmenu = mnu.subMenu([
    {'k':'xX',  'n':'x',   'h':mch.sendWait, 'ha':{'command':'G0X0'}},
    {'k':'yY',  'n':'y',   'h':mch.sendWait, 'ha':{'command':'G0Y0'}},
    {'k':'zZ',  'n':'z',   'h':mch.sendWait, 'ha':{'command':'G0Z0'}},
    {'k':'wW',  'n':'xy',  'h':mch.sendWait, 'ha':{'command':'G0X0Y0'}},
    {'k':'aA',  'n':'xyz', 'h':goToWCHOHome},
  ])

  goHomeSubmenu = mnu.subMenu([
    {'k':'0',   'n':'Safe machine home (Z0 + X0Y0)', 'h':mch.goToMachineHome},
    {'k':'mM',  'n':'Machine home (*)',              'h':machineHomeSubmenu},
    {'k':'wW',  'n':'WCO home (*)',                  'h':wcoHomeSubmenu},
  ])

  macroSubmenu = mnu.subMenu([
    {'k':'lL',  'n':'List macros',   'h':mcr.list},
    {'k':'rR',  'n':'Run macro',     'h':runMacro},
    {'k':'sS',  'n':'Show macro',    'h':showMacro},
    {'k':'xX',  'n':'Reload macros', 'h':mcr.load},
  ])

  testsSubmenu = mnu.subMenu([
    {'k':'sS',  'n':'Table position scan',  'h':tst.tablePositionScan},
    {'k':'lL',  'n':'Base levelling holes', 'h':tst.baseLevelingHoles},
    {'k':'zZ',  'n':'Zig-zag pattern',      'h':tst.zigZagPattern},
    {'k':'*',   'n':'DUMMY Test',           'h':tst.dummy},
  ])

  resetSubmenu = mnu.subMenu([
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

  probeSubmenu = mnu.subMenu([
    {'k':'1',   'n':'Basic probe',       'h':prb.basic},
    {'k':'2',   'n':'Two stage probe',   'h':prb.twoStage},
    {'k':'3',   'n':'Three stage probe', 'h':prb.threeStage},
  ])

  mnu.setOptions([
    {'SECTION':1, 'n':'General commands'},
    {'k':'qQ',           'n':'Quit',                         'h':mnu.quit},
    {'k':'CTRL_R',       'n':'Reset serial connection',      'h':resetSerialConnection},
    {'k':'CTRL_X',       'n':'grbl soft reset',              'h':mch.softReset},
    {'k':'=',            'n':'Lock grblCommander',           'h':lockGrblCommander},
    {'k':'cC',           'n':'Clear screen',                 'h':ui.clearScreen},

    {'SECTION':1, 'n':'Info'},
    {'k':'hH',           'n':'Show help',                    'h':mnu.showOptions},
    {'k':['ENTER', '?'], 'n':'Force status re-query',        'h':mch.viewMachineStatus},
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
    {'k':'tT',           'n':'Tests (*)',                               'h':testsSubmenu},

    {'SECTION':1, 'n':'Macro'},
    {'k':'mM',           'n':'Macro (*)',                               'h':macroSubmenu},
    {'INFO':1, 'k':'<F1..F12>', 'n':'Run preconfigured macro'},
    {'HIDDEN':1, 'k':'F1', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F2', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F3', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F4', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F5', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F6', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F7', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F8', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F9', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F10', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F11', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},
    {'HIDDEN':1, 'k':'F12', 'n':'Preconfigured macro', 'h':mcr.runHotKeyMacro, 'xha':{'inName':'hotKey'}},

    {'SECTION':1, 'n':'Jog'},
    {'INFO':1, 'k':'<numpad>',             'n':'XY jog (including diagonals)'},
    {'INFO':1, 'k':'<cursor>',             'n':'XY jog'},
    {'INFO':1, 'k':'<SHIFT>+<cursor>',     'n':'XY jog (double distance)'},
    {'INFO':1, 'k':'<CTRL><cursor>',       'n':'XY jog (half distance)'},
    {'k':'-',  'n':'z jog [U]',            'h':jogZ,  'ha':{'d':'U'}},
    {'k':'+',  'n':'z jog [D]',            'h':jogZ,  'ha':{'d':'D'}},
    {'k':'/',  'n':'Set XY jog distance',  'h':setXYJogDistance},
    {'k':'*',  'n':'Set Z jog distance',   'h':setZJogDistance},

    {'HIDDEN':1, 'k':'1',   'n':'Jog - [DL]',          'h':jogXY, 'ha':{'d':'DL'}},
    {'HIDDEN':1, 'k':'2',   'n':'Jog - [D]',           'h':jogXY, 'ha':{'d':'D'}},
    {'HIDDEN':1, 'k':'3',   'n':'Jog - [DR]',          'h':jogXY, 'ha':{'d':'DR'}},
    {'HIDDEN':1, 'k':'4',   'n':'Jog - [L]',           'h':jogXY, 'ha':{'d':'L'}},
    {'HIDDEN':1, 'k':'6',   'n':'Jog - [R]',           'h':jogXY, 'ha':{'d':'R'}},
    {'HIDDEN':1, 'k':'7',   'n':'Jog - [UL]',          'h':jogXY, 'ha':{'d':'UL'}},
    {'HIDDEN':1, 'k':'8',   'n':'Jog - [U]',           'h':jogXY, 'ha':{'d':'U'}},
    {'HIDDEN':1, 'k':'9',   'n':'Jog - [UR]',          'h':jogXY, 'ha':{'d':'UR'}},

    {'HIDDEN':1, 'k':'CUR_U',   'n':'Jog - [U]',       'h':jogXY, 'ha':{'d':'U'}},
    {'HIDDEN':1, 'k':'CUR_D',   'n':'Jog - [D]',       'h':jogXY, 'ha':{'d':'D'}},
    {'HIDDEN':1, 'k':'CUR_L',   'n':'Jog - [L]',       'h':jogXY, 'ha':{'d':'L'}},
    {'HIDDEN':1, 'k':'CUR_R',   'n':'Jog - [R]',       'h':jogXY, 'ha':{'d':'R'}},

    {'HIDDEN':1, 'k':'SHIFT_CUR_U',   'n':'Jog - [U]*2', 'h':jogXY, 'ha':{'d':'U', 'tx': lambda x: x*2 }},
    {'HIDDEN':1, 'k':'SHIFT_CUR_D',   'n':'Jog - [D]*2', 'h':jogXY, 'ha':{'d':'D', 'tx': lambda x: x*2 }},
    {'HIDDEN':1, 'k':'SHIFT_CUR_L',   'n':'Jog - [L]*2', 'h':jogXY, 'ha':{'d':'L', 'tx': lambda x: x*2 }},
    {'HIDDEN':1, 'k':'SHIFT_CUR_R',   'n':'Jog - [R]*2', 'h':jogXY, 'ha':{'d':'R', 'tx': lambda x: x*2 }},

    {'HIDDEN':1, 'k':'CTRL_CUR_U',   'n':'Jog - [U]/2',  'h':jogXY, 'ha':{'d':'U', 'tx': lambda x: x/2 }},
    {'HIDDEN':1, 'k':'CTRL_CUR_D',   'n':'Jog - [D]/2',  'h':jogXY, 'ha':{'d':'D', 'tx': lambda x: x/2 }},
    {'HIDDEN':1, 'k':'CTRL_CUR_L',   'n':'Jog - [L]/2',  'h':jogXY, 'ha':{'d':'L', 'tx': lambda x: x/2 }},
    {'HIDDEN':1, 'k':'CTRL_CUR_R',   'n':'Jog - [R]/2',  'h':jogXY, 'ha':{'d':'R', 'tx': lambda x: x/2 }},

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
  mch.onParserStateChanged.append(onParserStateChanged)   # Register parserStateChanged listener
  mch.start()     # Start connection

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
    ui.log('Closing grbl connection...')
    mch.stop()

    ui.log('Stopping keyboard hook...')
    kb.stop()

    ui.log('Closing program...')

