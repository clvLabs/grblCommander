#!/usr/bin/python3
"""
grblCommander - machine
=======================
Machine (CNC) related code
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
import pprint

from . import utils as ut
from . import ui as ui
from . import keyboard as kb
from . import serialport as sp
from . import table as tbl
from src.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
uiCfg = cfg['ui']
spCfg = cfg['serial']
macroCfg = cfg['macro']
macroCfgScripts = macroCfg['scripts']
mchCfg = cfg['machine']

gStatusStr = ''
gStatus = {}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def listGCodeMacros():
  maxNameLen = 0
  for macroName in macroCfgScripts:
    if len(macroName) > maxNameLen:
      maxNameLen = len(macroName)

  block = ''
  block += '{:}   {:} {:}\n\n'.format(
    'NAME'.ljust(maxNameLen),
    'LINES'.ljust(5),
    'DESCRIPTION'
    )

  for macroName in macroCfgScripts:
    macro = macroCfgScripts[macroName]
    description = macro['description']
    commands = macro['commands']

    block += '{:}   {:} {:}\n'.format(
      macroName.ljust(maxNameLen),
      str(len(commands)).ljust(5),
      description
      )

  ui.logBlock(block)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendGCodeMacro(name, silent=False):
  if not name in macroCfgScripts:
    ui.log('ERROR: Macro [{:}] does not exist, please check config file.'.format(name),
      color='ui.errorMsg')
    return

  macro = macroCfgScripts[name]
  description = macro['description']
  commands = macro['commands']

  if not silent:
    showGCodeMacro(name)

    ui.inputMsg('Press y/Y to execute, any other key to cancel...')
    key=kb.readKey()
    char=chr(key)

    if not char in 'yY':
      testCancelled = True
      ui.logBlock('MACRO EXECUTION CANCELLED', color='ui.cancelMsg')
      return

  for command in commands:
    sp.sendCommand(command[0])
    if not silent:
      waitForMachineIdle()

  if not silent:
    ui.logBlock('MACRO EXECUTION FINISHED', color='ui.finishedMsg')

  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showGCodeMacro(name):
  if not name in macroCfgScripts:
    ui.log('ERROR: Macro [{:}] does not exist, check config file.'.format(name),
      color='ui.errorMsg')
    return

  macro = macroCfgScripts[name]
  description = macro['description']
  commands = macro['commands']

  block = 'Macro [{:}] - {:} ({:} commands)\n\n'.format(
    name, description, len(commands))

  maxCommandLen = 0
  for command in commands:
    if len(command[0]) > maxCommandLen:
      maxCommandLen = len(command[0])

  for command in commands:
    block += '{:}   {:}\n'.format(
      ui.setStrColor(command[0].ljust(maxCommandLen), 'macro.command'),
      ui.setStrColor(command[1], 'macro.comment') )

  ui.logBlock(block)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def viewBuildInfo():
  ui.logTitle('Requesting build info')
  ui.log('Sending command [$I]...', v='DETAIL')
  sp.sendCommand('$I')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def viewGCodeParserState():
  ui.logTitle('Requesting GCode parser state')
  ui.log('Sending command [$G]...', v='DETAIL')
  sp.sendCommand('$G')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def viewGCodeParameters():
  ui.logTitle('Requesting GCode parameters')
  ui.log('Sending command [$#]...', v='DETAIL')
  sp.sendCommand('$#')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def viewGrblConfig():
  ui.logTitle('Requesting grbl config')
  ui.log('Sending command [$$]...', v='DETAIL')
  sp.sendCommand('$$')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def viewStartupBlocks():
  ui.logTitle('Requesting startup blocks')
  ui.log('Sending command [$N]...', v='DETAIL')
  sp.sendCommand('$N')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def enableSleepMode():
  ui.logTitle('Requesting sleep mode enable')
  ui.log('Sending command [$SLP]...', v='DETAIL')
  sp.sendCommand('$SLP')
  ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def parseMachineStatus(status):
  global gStatus

  if status[0] == '<':
    status = status[1:-1]

  # Separe parameter groups
  params = status.split('|')

  # Status is always the first field
  gStatus['machineState'] = params.pop(0)

  # Get the rest of fields
  while len(params):
    param = params.pop(0).split(':')
    paramName = param[0]
    paramValue = param[1]

    if paramName == 'MPos' or paramName == 'WPos' or paramName == 'WCO':
      coords = paramValue.split(',')
      x = float(coords[0])
      y = float(coords[1])
      z = float(coords[2])

      gStatus[paramName] = {
        'x':x,
        'y':y,
        'z':z
      }

      if paramName == 'MPos':
        gStatus[paramName]['desc'] = 'machinePos'
      elif paramName == 'WPos':
        gStatus[paramName]['desc'] = 'workPos'
      elif paramName == 'WCO':
        gStatus[paramName]['desc'] = 'workCoordinates'

    elif paramName == 'Bf':
      blocks = paramValue.split(',')
      planeBufferBlocks = int(blocks[0])
      serialRXBufferBlocks = int(blocks[1])
      gStatus[paramName] = {
        'desc': 'buffer',
        'planeBufferBlocks': planeBufferBlocks,
        'serialRXBufferBlocks': serialRXBufferBlocks
      }

    elif paramName == 'Ln':
      gStatus[paramName] = {
        'desc': 'lineNumber',
        'value': paramValue
      }

    elif paramName == 'F':
      gStatus[paramName] = {
        'desc': 'feed',
        'value': int(paramValue)
      }

    elif paramName == 'FS':
      values = paramValue.split(',')
      feed = int(values[0])
      speed = int(values[1])

      gStatus['F'] = {
        'desc': 'feed',
        'value': int(feed)
      }

      gStatus['S'] = {
        'desc': 'speed',
        'value': int(speed)
      }

    elif paramName == 'Pn':
      gStatus[paramName] = {
        'desc': 'inputPinState',
        'value': paramValue
      }

    elif paramName == 'Ov':
      values = paramValue.split(',')
      feed = values[0]
      rapid = values[1]
      speed = values[2]
      gStatus[paramName] = {
        'desc': 'override',
        'feed': int(feed),
        'rapid': int(rapid),
        'speed': int(speed)
      }

    elif paramName == 'A':
      gStatus[paramName] = {
        'desc': 'accesoryState',
        'value': paramValue
      }

    else:
      gStatus[paramName] = {
        'desc': 'UNKNOWN',
        'value': paramValue
      }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getMachineStatus():
  global gStatusStr

  ui.log('Querying machine status...', v='DEBUG')
  sp.write('?\n')

  startTime = time.time()
  receivedLines = 0
  responseArray=[]

  while( (time.time() - startTime) < spCfg['responseTimeout'] ):
    line = sp.readline()
    if(line):
      receivedLines += 1
      responseArray.append(line)
      if(receivedLines == 2):
        ui.log('Successfully received machine status', v='DEBUG')
        gStatusStr = responseArray[0]
        parseMachineStatus(gStatusStr)
        break
  else:
    gStatusStr = ''
    ui.log('TIMEOUT Waiting for machine status', v='WARNING')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getSimpleMachineStatusStr():
  return '{:} - MPos {:}'.format(
    getColoredMachineStateStr(),
    getMachinePosStr()
  )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getColoredMachineStateStr():
  machineStateStr = gStatus['machineState']
  return ui.setStrColor(machineStateStr, 'machineState.{:}'.format(machineStateStr))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getMachinePosStr():
  mPos = gStatus['MPos'] if 'MPos' in gStatus else None
  return ui.xyzStr(mPos['x'], mPos['y'], mPos['z']) if mPos else '<NONE>'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getWorkPosStr():
  wPos = gStatus['WPos'] if 'WPos' in gStatus else None
  return ui.xyzStr(wPos['x'], wPos['y'], wPos['z']) if wPos else '<NONE>'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getSoftwarePosStr():
  return ui.xyzStr(
    tbl.getX(),
    tbl.getY(),
    tbl.getZ(),
    'ui.machinePosDiff' if tbl.getX() != gStatus['MPos']['x'] else '',
    'ui.machinePosDiff' if tbl.getY() != gStatus['MPos']['y'] else '',
    'ui.machinePosDiff' if tbl.getZ() != gStatus['MPos']['z'] else '',
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showStatus():
  getMachineStatus()

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
      getColoredMachineStateStr(),
      getMachinePosStr(),
      getWorkPosStr(),
      getSoftwarePosStr(),
      ui.coordStr(tbl.getRI_XY()),
      ui.coordStr(tbl.getRI_Z()),
      ui.coordStr(tbl.getSafeHeight()),
      tbl.getTableSizePercent(),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showLongStatus():
  getMachineStatus()

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
      getColoredMachineStateStr(),
      getMachinePosStr(),
      getWorkPosStr(),
      getSoftwarePosStr(),
      pprint.pformat(gStatus, indent=4, width=uiCfg['maxLineLen']),
      ui.coordStr(tbl.getRI_XY()),
      ui.coordStr(tbl.getRI_Z()),
      ui.coordStr(tbl.getSafeHeight()),
      tbl.getTableSizePercent(),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    )

  viewBuildInfo()
  viewStartupBlocks()
  viewGCodeParserState()
  viewGrblConfig()
  viewGCodeParameters()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def waitForMachineIdle(verbose='WARNING'):
  ui.log('Waiting for machine operation to finish...', v='SUPER')
  getMachineStatus()

  showStatus = ((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose)))

  while gStatus['machineState'] != 'Idle' and gStatus['machineState'] != 'Check':
    if showStatus:
      ui.clearLine()
      coloredMachineStatusStr = ui.setStrColor(gStatusStr, 'ui.onlineMachineStatus')
      ui.log('\r[{:}] {:}'.format(getColoredMachineStateStr(), coloredMachineStatusStr), end='')
    time.sleep(0.2)
    getMachineStatus()

  if showStatus:
    ui.clearLine()
    coloredMachineStatusStr = ui.setStrColor(gStatusStr, 'ui.onlineMachineStatus')
    ui.log('\r[{:}] {:}'.format(getColoredMachineStateStr(), coloredMachineStatusStr), end='')

  ui.log(' - ', end='')
  ui.log(getSoftwarePosStr(), v=verbose)

  ui.log('Machine operation finished', v='SUPER')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def feedAbsolute(x=None, y=None, z=None, speed=mchCfg['feedSpeed'], verbose='WARNING'):
  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", color='ui.msg', v=verbose)
    return

  cmd = 'G1 '

  if( x != None and x != tbl.getX() ):
    tbl.setX(x)
    cmd += 'X{:} '.format(ui.coordStr(tbl.getX()))

  if( y != None and y != tbl.getY() ):
    tbl.setY(y)
    cmd += 'Y{:} '.format(ui.coordStr(tbl.getY()))

  if( z != None and z != tbl.getZ() ):
    tbl.setZ(z)
    cmd += 'Z{:} '.format(ui.coordStr(tbl.getZ()))

  cmd += 'F{:} '.format(speed)

  cmd = cmd.rstrip()

  ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
  sp.sendCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", color='ui.msg', v=verbose)
    return

  if( tbl.getZ() < tbl.getSafeHeight() ):
    if( x != None or y != None ):
      ui.log("ERROR: Can't rapid on X/Y while Z < {:} (SAFE_HEIGHT)!".format(tbl.getSafeHeight()), color='ui.errorMsg', v='ERROR')
      return

  if(not tbl.checkAbsoluteXYZ(x, y, z)):
    # Error already shown
    return

  cmd = 'G0 '

  if( x != None and x != tbl.getX() ):
    tbl.setX(x)
    cmd += 'X{:} '.format(ui.coordStr(tbl.getX()))

  if( y != None and y != tbl.getY() ):
    tbl.setY(y)
    cmd += 'Y{:} '.format(ui.coordStr(tbl.getY()))

  if( z != None and z != tbl.getZ() ):
    tbl.setZ(z)
    cmd += 'Z{:} '.format(ui.coordStr(tbl.getZ()))

  cmd = cmd.rstrip()

  ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
  sp.sendCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidRelative(x=None, y=None, z=None, verbose='WARNING'):
  lastX = tbl.getX()
  lastY = tbl.getY()
  lastZ = tbl.getZ()

  if( x is None and y is None and z is None ):
    ui.log('No parameters provided, doing nothing', v=verbose)
    return

  if( tbl.getZ() < tbl.getSafeHeight() ):
    if( x != None or y != None ):
      ui.log("ERROR: Can't rapid on X/Y while Z < {:} (SAFE_HEIGHT)!".format(tbl.getSafeHeight()), color='ui.errorMsg', v='ERROR')
      return

  if(not tbl.checkRelativeXYZ(x, y, z)):
    # Error already shown
    return

  cmd = 'G0 '

  if(x):
    newX = tbl.getX() + x
    if(newX<tbl.getMinX()):
      ui.log('Adjusting X to MinX ({:})'.format(tbl.getMinX()), v='DETAIL')
      newX=tbl.getMinX()
    elif(newX>tbl.getMaxX()):
      ui.log('Adjusting X to MaxX ({:})'.format(tbl.getMaxX()), v='DETAIL')
      newX=tbl.getMaxX()

    if(newX == tbl.getX()):
      ui.log('X value unchanged, skipping', v='DETAIL')
    else:
      tbl.setX(newX)
      cmd += 'X{:} '.format(ui.coordStr(tbl.getX()))

  if(y):
    newY = tbl.getY() + y
    if(newY<tbl.getMinY()):
      ui.log('Adjusting Y to MinY ({:})'.format(tbl.getMinY()), v='DETAIL')
      newY=tbl.getMinY()
    elif(newY>tbl.getMaxY()):
      ui.log('Adjusting Y to MaxY ({:})'.format(tbl.getMaxY()), v='DETAIL')
      newY=tbl.getMaxY()

    if(newY == tbl.getY()):
      ui.log('Y value unchanged, skipping', v='DETAIL')
    else:
      tbl.setY(newY)
      cmd += 'Y{:} '.format(ui.coordStr(tbl.getY()))

  if(z):
    newZ = tbl.getZ() + z
    if(newZ<tbl.getMinZ()):
      ui.log('Adjusting Z to MinZ ({:})'.format(tbl.getMinZ()), v='DETAIL')
      newZ=tbl.getMinZ()
    elif(newZ>tbl.getMaxZ()):
      ui.log('Adjusting Z to MaxZ ({:})'.format(tbl.getMaxZ()), v='DETAIL')
      newZ=tbl.getMaxZ()

    if(newZ == tbl.getZ()):
      ui.log('Z value unchanged, skipping', v='DETAIL')
    else:
      tbl.setZ(newZ)
      cmd += 'Z{:} '.format(ui.coordStr(tbl.getZ()))

  # If nothing changed in the relative move, don't send command
  if( lastX == tbl.getX() and  lastY == tbl.getY() and  lastZ == tbl.getZ() ):
    ui.log('No position change, doing nothing', v=verbose)
    return

  cmd = cmd.rstrip()

  ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
  sp.sendCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
  ui.log('checking XYZ coordinates...', v='DEBUG')
  if(not tbl.checkAbsoluteXYZ(x, y, z)):
    # Error already shown
    return

  savedZ = None

  # Avoid moving Z to safe area if params means no change
  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", color='ui.msg', v=verbose)
    return

  if(  ( x is None or x == tbl.getX() )
  and  ( y is None or y == tbl.getY() ) ):
    ui.log('Skipping move to safe Z due to no XY movement', v='SUPER')
  elif( tbl.getZ() < tbl.getSafeHeight() ):
    ui.log('Temporarily moving to safe Z...', v='DETAIL')
    savedZ = tbl.getZ()
    rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

  if(  ( x != None and x != tbl.getX() )
  or  ( y != None and y != tbl.getY() ) ):
    ui.log('Applying rapid on XY...', v='DETAIL')
    rapidAbsolute(x=x, y=y, verbose=verbose)

  if(z is None):
    z = savedZ

  if(z is None):
    ui.log('Skipping rapid on Z (none specified)', v='SUPER')
  elif(z == tbl.getZ()):
    ui.log('Skipping rapid on Z (already at destination)', v='SUPER')
  else:
    ui.log('Applying rapid on Z...', v='DETAIL')
    rapidAbsolute(z=z, verbose=verbose)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidRelative(x=None, y=None, z=None, verbose='WARNING'):
  ui.log('Checking XYZ offsets...', v='DEBUG')
  if(not tbl.checkRelativeXYZ(x, y, z)):
    # Error already shown
    return

  savedZ = None

  if(  (not x) and (not y) ):
    ui.log('Skipping move to safe Z due to no XY movement', v='SUPER')
  elif(tbl.getZ() < tbl.getSafeHeight()):
    ui.log('Temporarily moving to safe Z...', v='DETAIL')
    savedZ = tbl.getZ()
    rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

  if(x or y):
    ui.log('Applying rapid on XY...', v='DETAIL')
    rapidRelative(x=x, y=y, verbose=verbose)

  if(savedZ != None):
    ui.log('Restoring original Z...', v='DETAIL')
    rapidAbsolute(z=savedZ, verbose=verbose)

  if(not z):
    ui.log('Skipping rapid on Z (none specified)', v='SUPER')
  else:
    ui.log('Applying rapid on Z...', v='DETAIL')
    rapidRelative(z=z, verbose=verbose)
