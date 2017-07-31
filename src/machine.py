#!/usr/bin/python3
"""
grblCommander - machine
=======================
Machine (CNC) related code
"""
#print("***[IMPORTING]*** grblCommander - machine")

import time

from . import utils as ut
from . import ui as ui
from . import serialport as sp
from . import table as tbl

gDEFAULT_SEEK_SPEED = 2000
gDEFAULT_FEED_SPEED = 50

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendGCodeInitSequence():
  _k = 'mch.sendGCodeInitSequence()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Sending GCode init sequence...", k=_k, v='BASIC')
  ui.log("", k=_k, v='BASIC')

  ui.log("Sending command [G21]: Programming in millimeters (mm)", k=_k, v='WARNING')
  sp.sendSerialCommand("G21")

  ui.log("Sending command [G90]: Absolute programming", k=_k, v='WARNING')
  sp.sendSerialCommand("G90")

  ui.log("Sending command [F100]: Feed rate", k=_k, v='WARNING')
  sp.sendSerialCommand("F100")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getMachineStatus():
  _k = 'mch.getMachineStatus()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Querying machine status...", k=_k, v='DEBUG')
  sp.gSerial.write( bytes("?\n", 'UTF-8') )

  startTime = time.time()
  receivedLines = 0
  responseArray=[]

  while( (time.time() - startTime) < sp.gRESPONSE_TIMEOUT ):
    line = sp.gSerial.readline()
    if(line):
      receivedLines += 1
      responseArray.append(line)
      if(receivedLines == 2):
        ui.log("Successfully received machine status", k=_k, v='DEBUG')
        break
  else:
    ui.log("TIMEOUT Waiting for machine status", k=_k, v='WARNING')

  return responseArray[0]


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showStatus():
  _k = 'mch.showStatus()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.logBlock(
"""
Current status:

  Software XYZ:
    [X=%.3f Y=%.3f Z=%.3f]

  Machine XYZ:
    %s

  Software config:
    RapidIncrement_XY = %.2f
    RapidIncrement_Z  = %.2f
    SafeHeight        = %.2f
    TableSize%%        = %d%%
    VerboseLevel      = %d/%d (%s)
"""
    % (  tbl.getX(), tbl.getY(), tbl.getZ(),
      getMachineStatus(),
      tbl.getRI_XY(), tbl.getRI_Z(),
      tbl.getSafeHeight(), tbl.getTableSizePercent(),
      ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
    , k=_k, v='BASIC' )


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def waitForMachineIdle(verbose='WARNING'):
  _k = 'mch.waitForMachineIdle()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Waiting for machine operation to finish...", k=_k, v='SUPER')
  status = getMachineStatus()

  while( b'Idle' not in status ):
    if((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose))):
      print("\r" + (" " * 80), end="")
      print("\r" + repr(status), end="")
    time.sleep(0.1)
    status = getMachineStatus()

  if((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose))):
    print("\r" + (" " * 80), end="")
    print("\r" + repr(status) + "\n", end="")

  ui.log("Machine operation finished", k=_k, v='SUPER')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def feedAbsolute(x=None, y=None, z=None, speed=gDEFAULT_FEED_SPEED, verbose='WARNING'):
  _k = 'mch.feedAbsolute()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", k=_k, v=verbose)
    return

  if( tbl.getZ() < tbl.getSafeHeight() ):
    if( x != None or y != None ):
      ui.log("ERROR: Can't feed on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), k=_k, v='ERROR')
      return

  cmd = "G1 "

  if( x != None and x != tbl.getX() ):
    tbl.setX(x)
    cmd += "X" + "%.3f" % tbl.getX() + " "

  if( y != None and y != tbl.getY() ):
    tbl.setY(y)
    cmd += "Y" + "%.3f" % tbl.getY() + " "

  if( z != None and z != tbl.getZ() ):
    tbl.setZ(z)
    cmd += "Z" + "%.3f" % tbl.getZ() + " "

  cmd += "F%d " % speed

  cmd = cmd.rstrip()

  ui.log("Sending command [%s]..." % repr(cmd), k=_k, v='DETAIL')
  sp.sendSerialCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  tbl.showCurrPos(verbose=verbose)
  return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
  _k = 'mch.rapidAbsolute()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", k=_k, v=verbose)
    return

  if( tbl.getZ() < tbl.getSafeHeight() ):
    if( x != None or y != None ):
      ui.log("ERROR: Can't rapid on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), k=_k, v='ERROR')
      return

  if(not tbl.checkAbsoluteXYZ(x, y, z)):
    # Error already shown
    return

  cmd = "G0 "

  if( x != None and x != tbl.getX() ):
    tbl.setX(x)
    cmd += "X" + "%.3f" % tbl.getX() + " "

  if( y != None and y != tbl.getY() ):
    tbl.setY(y)
    cmd += "Y" + "%.3f" % tbl.getY() + " "

  if( z != None and z != tbl.getZ() ):
    tbl.setZ(z)
    cmd += "Z" + "%.3f" % tbl.getZ() + " "

  cmd = cmd.rstrip()

  ui.log("Sending command [%s]..." % repr(cmd), k=_k, v='DETAIL')
  sp.sendSerialCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  tbl.showCurrPos(verbose=verbose)
  return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidRelative(x=None, y=None, z=None, verbose='WARNING'):
  _k = 'mch.rapidRelative()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  lastX = tbl.getX()
  lastY = tbl.getY()
  lastZ = tbl.getZ()

  if( x is None and y is None and z is None ):
    ui.log("No parameters provided, doing nothing", k=_k, v=verbose)
    return

  if( tbl.getZ() < tbl.getSafeHeight() ):
    if( x != None or y != None ):
      ui.log("ERROR: Can't rapid on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), k=_k, v='ERROR')
      return

  if(not tbl.checkRelativeXYZ(x, y, z)):
    # Error already shown
    return

  cmd = "G0 "

  if(x):
    newX = tbl.getX() + x
    if(newX<tbl.getMinX()):
      ui.log("Adjusting X to MinX (%d)" % tbl.getMinX(), k=_k, v='DETAIL')
      newX=tbl.getMinX()
    elif(newX>tbl.getMaxX()):
      ui.log("Adjusting X to MaxX (%d)" % tbl.getMaxX(), k=_k, v='DETAIL')
      newX=tbl.getMaxX()

    if(newX == tbl.getX()):
      ui.log("X value unchanged, skipping", k=_k, v='DETAIL')
    else:
      tbl.setX(newX)
      cmd += "X" + "%.3f" % tbl.getX() + " "

  if(y):
    newY = tbl.getY() + y
    if(newY<tbl.getMinY()):
      ui.log("Adjusting Y to MinY (%d)" % tbl.getMinY(), k=_k, v='DETAIL')
      newY=tbl.getMinY()
    elif(newY>tbl.getMaxY()):
      ui.log("Adjusting Y to MaxY (%d)" % tbl.getMaxY(), k=_k, v='DETAIL')
      newY=tbl.getMaxY()

    if(newY == tbl.getY()):
      ui.log("Y value unchanged, skipping", k=_k, v='DETAIL')
    else:
      tbl.setY(newY)
      cmd += "Y" + "%.3f" % tbl.getY() + " "

  if(z):
    newZ = tbl.getZ() + z
    if(newZ<tbl.getMinZ()):
      ui.log("Adjusting Z to MinZ (%d)" % tbl.getMinZ(), k=_k, v='DETAIL')
      newZ=tbl.getMinZ()
    elif(newZ>tbl.getMaxZ()):
      ui.log("Adjusting Z to MaxZ (%d)" % tbl.getMaxZ(), k=_k, v='DETAIL')
      newZ=tbl.getMaxZ()

    if(newZ == tbl.getZ()):
      ui.log("Z value unchanged, skipping", k=_k, v='DETAIL')
    else:
      tbl.setZ(newZ)
      cmd += "Z" + "%.3f" % tbl.getZ() + " "

  # If nothing changed in the relative move, don't send command
  if( lastX == tbl.getX() and  lastY == tbl.getY() and  lastZ == tbl.getZ() ):
    ui.log("No position change, doing nothing", k=_k, v=verbose)
    return

  cmd = cmd.rstrip()

  ui.log("Sending command [%s]..." % repr(cmd), k=_k, v='DETAIL')
  sp.sendSerialCommand(cmd, verbose=verbose)
  waitForMachineIdle(verbose=verbose)
  tbl.showCurrPos(verbose=verbose)
  return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
  _k = 'mch.safeRapidAbsolute()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("checking XYZ coordinates...", k=_k, v='DEBUG')
  if(not tbl.checkAbsoluteXYZ(x, y, z)):
    # Error already shown
    return

  savedZ = None

  # Avoid moving Z to safe area if params means no change
  if(  ( (x is None) or ( x == tbl.getX() ) )
  and  ( (y is None) or ( y == tbl.getY() ) )
  and  ( (z is None) or ( z == tbl.getZ() ) ) ):
    ui.log("Wouldn't move, doing nothing", k=_k, v=verbose)
    return

  if(  ( x is None or x == tbl.getX() )
  and  ( y is None or y == tbl.getY() ) ):
    ui.log("Skipping move to safe Z due to no XY movement", k=_k, v='SUPER')
  elif( tbl.getZ() < tbl.getSafeHeight() ):
    ui.log("Temporarily moving to safe Z...", k=_k, v='DETAIL')
    savedZ = tbl.getZ()
    rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

  if(  ( x != None and x != tbl.getX() )
  or  ( y != None and y != tbl.getY() ) ):
    ui.log("Applying rapid on XY...", k=_k, v='DETAIL')
    rapidAbsolute(x=x, y=y, verbose=verbose)

  if(z is None):
    z = savedZ

  if(z is None):
    ui.log("Skipping rapid on Z (none specified)", k=_k, v='SUPER')
  elif(z == tbl.getZ()):
    ui.log("Skipping rapid on Z (already at destination)", k=_k, v='SUPER')
  else:
    ui.log("Applying rapid on Z...", k=_k, v='DETAIL')
    rapidAbsolute(z=z, verbose=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidRelative(x=None, y=None, z=None, verbose='WARNING'):
  _k = 'mch.safeRapidRelative()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Checking XYZ offsets...", k=_k, v='DEBUG')
  if(not tbl.checkRelativeXYZ(x, y, z)):
    # Error already shown
    return

  savedZ = None

  if(  (not x) and (not y) ):
    ui.log("Skipping move to safe Z due to no XY movement", k=_k, v='SUPER')
  elif(tbl.getZ() < tbl.getSafeHeight()):
    ui.log("Temporarily moving to safe Z...", k=_k, v='DETAIL')
    savedZ = tbl.getZ()
    rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

  if(x or y):
    ui.log("Applying rapid on XY...", k=_k, v='DETAIL')
    rapidRelative(x=x, y=y, verbose=verbose)

  if(savedZ != None):
    ui.log("Restoring original Z...", k=_k, v='DETAIL')
    rapidAbsolute(z=savedZ, verbose=verbose)

  if(not z):
    ui.log("Skipping rapid on Z (none specified)", k=_k, v='SUPER')
  else:
    ui.log("Applying rapid on Z...", k=_k, v='DETAIL')
    rapidRelative(z=z, verbose=verbose)


