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
	ui.debugLog("[ Entering sendGCodeInitSequence() ]", caller='sendGCodeInitSequence()', verbose='DEBUG')

	ui.debugLog("Sending GCode init sequence...", caller='sendGCodeInitSequence()', verbose='BASIC')
	ui.debugLog("", caller='sendGCodeInitSequence()', verbose='BASIC')

	ui.debugLog("Sending command [G21]: Programming in millimeters (mm)", caller='sendGCodeInitSequence()', verbose='WARNING')
	sp.sendSerialCommand("G21")

	ui.debugLog("Sending command [G90]: Absolute programming", caller='sendGCodeInitSequence()', verbose='WARNING')
	sp.sendSerialCommand("G90")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getMachineStatus():
	ui.debugLog("[ Entering getMachineStatus() ]", caller='getMachineStatus()', verbose='DEBUG')

	ui.debugLog("Querying machine status...", caller='getMachineStatus()', verbose='DEBUG')
	sp.gSerial.write( bytes("?\n", 'UTF-8') )

	startTime = time.time()
	receivedLines = 0
	responseArray=[]

	while( (time.time() - startTime) < sp.gSERIAL_RESPONSE_TIMEOUT ):
		line = sp.gSerial.readline()
		if(line):
			receivedLines += 1
			responseArray.append(line)
			if(receivedLines == 2):
				ui.debugLog("Successfully received machine status", caller='getMachineStatus()', verbose='DEBUG')
				break
	else:
		ui.debugLog("TIMEOUT Waiting for machine status", caller='getMachineStatus()', verbose='WARNING')

	return responseArray[0]


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showStatus():
	ui.debugLog("[ Entering showStatus() ]", caller='showStatus()', verbose='DEBUG')

	ui.debugLog("", caller='showStatus()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR, caller='showStatus()', verbose='BASIC')
	ui.debugLog("", caller='showStatus()', verbose='BASIC')
	ui.debugLog("Current status:", caller='showStatus()', verbose='BASIC')
	ui.debugLog("", caller='showStatus()', verbose='BASIC')

	ui.debugLog(
"""  Software XYZ:
    [X=%.3f Y=%.3f Z=%.3f]

  Machine XYZ:
    %s

  Software config:
    RapidIncrement_XY = %.2f
    RapidIncrement_Z  = %.2f
    SafeHeight        = %.2f
    TableSize%%        = %d%%
    VerboseLevel      = %d/%d (%s)"""
				% (	tbl.getX(), tbl.getY(), tbl.getZ(),
					getMachineStatus(),
					tbl.getRI_XY(), tbl.getRI_Z(),
					tbl.getSafeHeight(), tbl.getTableSizePercent(),
					ui.getVerboseLevel(), ui.gMAX_VERBOSE_LEVEL, ui.getVerboseLevelStr())
				, caller='showStatus()', verbose='BASIC' )

	ui.debugLog("", caller='showStatus()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR, caller='showStatus()', verbose='BASIC')
	ui.debugLog("", caller='showStatus()', verbose='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def waitForMachineIdle(verbose='WARNING'):
	ui.debugLog("[ Entering waitForMachineIdle() ]", caller='waitForMachineIdle()', verbose='DEBUG')

	ui.debugLog("Waiting for machine operation to finish...", caller='waitForMachineIdle()', verbose='SUPER')
	status = getMachineStatus()

	while( b'Idle' not in status ):
		if((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose))):
			print("\r" + repr(status), end="")
		time.sleep(0.1)
		status = getMachineStatus()

	if((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose))):
		print("\r" + repr(status) + "\n", end="")

	ui.debugLog("Machine operation finished", caller='waitForMachineIdle()', verbose='SUPER')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def feedAbsolute(x=None, y=None, z=None, speed=gDEFAULT_FEED_SPEED, verbose='WARNING'):
	ui.debugLog("[ Entering feedAbsolute() ]", caller='feedAbsolute()', verbose='DEBUG')

	if(	( (x is None) or ( x == tbl.getX() ) )
	and	( (y is None) or ( y == tbl.getY() ) )
	and	( (z is None) or ( z == tbl.getZ() ) ) ):
		ui.debugLog("Wouldn't move, doing nothing", caller='feedAbsolute()', verbose=verbose)
		return

	if( tbl.getZ() < tbl.getSafeHeight() ):
		if( x != None or y != None ):
			ui.debugLog("ERROR: Can't feed on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), caller='feedAbsolute()', verbose='ERROR')
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

	ui.debugLog("Sending command [%s]..." % repr(cmd), caller='feedAbsolute()', verbose='DETAIL')
	sp.sendSerialCommand(cmd, verbose=verbose)
	waitForMachineIdle(verbose=verbose)
	tbl.showCurrPos(verbose=verbose)
	return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
	ui.debugLog("[ Entering rapidAbsolute() ]", caller='rapidAbsolute()', verbose='DEBUG')

	if(	( (x is None) or ( x == tbl.getX() ) )
	and	( (y is None) or ( y == tbl.getY() ) )
	and	( (z is None) or ( z == tbl.getZ() ) ) ):
		ui.debugLog("Wouldn't move, doing nothing", caller='rapidAbsolute()', verbose=verbose)
		return

	if( tbl.getZ() < tbl.getSafeHeight() ):
		if( x != None or y != None ):
			ui.debugLog("ERROR: Can't rapid on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), caller='rapidAbsolute()', verbose='ERROR')
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

	ui.debugLog("Sending command [%s]..." % repr(cmd), caller='rapidAbsolute()', verbose='DETAIL')
	sp.sendSerialCommand(cmd, verbose=verbose)
	waitForMachineIdle(verbose=verbose)
	tbl.showCurrPos(verbose=verbose)
	return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def rapidRelative(x=None, y=None, z=None, verbose='WARNING'):
	ui.debugLog("[ Entering rapidRelative() ]", caller='rapidRelative()', verbose='DEBUG')

	lastX = tbl.getX()
	lastY = tbl.getY()
	lastZ = tbl.getZ()

	if( x is None and y is None and z is None ):
		ui.debugLog("No parameters provided, doing nothing", caller='rapidRelative()', verbose=verbose)
		return

	if( tbl.getZ() < tbl.getSafeHeight() ):
		if( x != None or y != None ):
			ui.debugLog("ERROR: Can't rapid on X/Y while Z < %d (SAFE_HEIGHT)!" % tbl.getSafeHeight(), caller='rapidRelative()', verbose='ERROR')
			return

	if(not tbl.checkRelativeXYZ(x, y, z)):
		# Error already shown
		return

	cmd = "G0 "

	if(x):
		newX = tbl.getX() + x
		if(newX<tbl.getMinX()):
			ui.debugLog("Adjusting X to MinX (%d)" % tbl.getMinX(), caller='rapidRelative()', verbose='DETAIL')
			newX=tbl.getMinX()
		elif(newX>tbl.getMaxX()):
			ui.debugLog("Adjusting X to MaxX (%d)" % tbl.getMaxX(), caller='rapidRelative()', verbose='DETAIL')
			newX=tbl.getMaxX()

		if(newX == tbl.getX()):
			ui.debugLog("X value unchanged, skipping", caller='rapidRelative()', verbose='DETAIL')
		else:
			tbl.setX(newX)
			cmd += "X" + "%.3f" % tbl.getX() + " "

	if(y):
		newY = tbl.getY() + y
		if(newY<tbl.getMinY()):
			ui.debugLog("Adjusting Y to MinY (%d)" % tbl.getMinY(), caller='rapidRelative()', verbose='DETAIL')
			newY=tbl.getMinY()
		elif(newY>tbl.getMaxY()):
			ui.debugLog("Adjusting Y to MaxY (%d)" % tbl.getMaxY(), caller='rapidRelative()', verbose='DETAIL')
			newY=tbl.getMaxY()

		if(newY == tbl.getY()):
			ui.debugLog("Y value unchanged, skipping", caller='rapidRelative()', verbose='DETAIL')
		else:
			tbl.setY(newY)
			cmd += "Y" + "%.3f" % tbl.getY() + " "

	if(z):
		newZ = tbl.getZ() + z
		if(newZ<tbl.gMIN_Z):
			ui.debugLog("Adjusting Z to MinZ (%d)" % tbl.gMIN_Z, caller='rapidRelative()', verbose='DETAIL')
			newZ=tbl.gMIN_Z
		elif(newZ>tbl.gMAX_Z):
			ui.debugLog("Adjusting Z to MaxZ (%d)" % tbl.gMAX_Z, caller='rapidRelative()', verbose='DETAIL')
			newZ=tbl.gMAX_Z

		if(newZ == tbl.getZ()):
			ui.debugLog("Z value unchanged, skipping", caller='rapidRelative()', verbose='DETAIL')
		else:
			tbl.setZ(newZ)
			cmd += "Z" + "%.3f" % tbl.getZ() + " "

	# If nothing changed in the relative move, don't send command
	if( lastX == tbl.getX() and	lastY == tbl.getY() and	lastZ == tbl.getZ() ):
		ui.debugLog("No position change, doing nothing", caller='rapidRelative()', verbose=verbose)
		return

	cmd = cmd.rstrip()

	ui.debugLog("Sending command [%s]..." % repr(cmd), caller='rapidRelative()', verbose='DETAIL')
	sp.sendSerialCommand(cmd, verbose=verbose)
	waitForMachineIdle(verbose=verbose)
	tbl.showCurrPos(verbose=verbose)
	return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidAbsolute(x=None, y=None, z=None, verbose='WARNING'):
	ui.debugLog("[ Entering safeRapidAbsolute() ]", caller='safeRapidAbsolute()', verbose='DEBUG')

	ui.debugLog("checking XYZ coordinates...", caller='safeRapidAbsolute()', verbose='DEBUG')
	if(not tbl.checkAbsoluteXYZ(x, y, z)):
		# Error already shown
		return

	# Avoid moving Z to safe area if params means no change
	if(	( (x is None) or ( x == tbl.getX() ) )
	and	( (y is None) or ( y == tbl.getY() ) )
	and	( (z is None) or ( z == tbl.getZ() ) ) ):
		ui.debugLog("Wouldn't move, doing nothing", caller='safeRapidAbsolute()', verbose=verbose)
		return

	if(	( x is None or x == tbl.getX() )
	and	( y is None or y == tbl.getY() ) ):
		ui.debugLog("Skipping move to safe Z due to no XY movement", caller='safeRapidAbsolute()', verbose='SUPER')
	elif( tbl.getZ() < tbl.getSafeHeight() ):
		ui.debugLog("Temporarily moving to safe Z...", caller='safeRapidAbsolute()', verbose='DETAIL')
		rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

	if(	( x != None and x != tbl.getX() )
	or	( y != None and y != tbl.getY() ) ):
		ui.debugLog("Applying rapid on XY...", caller='safeRapidAbsolute()', verbose='DETAIL')
		rapidAbsolute(x=x, y=y, verbose=verbose)

	if(z is None):
		ui.debugLog("Skipping rapid on Z (none specified)", caller='safeRapidAbsolute()', verbose='SUPER')
	elif(z == tbl.getZ()):
		ui.debugLog("Skipping rapid on Z (already at destination)", caller='safeRapidAbsolute()', verbose='SUPER')
	else:
		ui.debugLog("Applying rapid on Z...", caller='safeRapidAbsolute()', verbose='DETAIL')
		rapidAbsolute(z=z, verbose=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def safeRapidRelative(x=None, y=None, z=None, verbose='WARNING'):
	ui.debugLog("[ Entering safeRapidRelative() ]", caller='safeRapidRelative()', verbose='DEBUG')

	ui.debugLog("Checking XYZ offsets...", caller='safeRapidRelative()', verbose='DEBUG')
	if(not tbl.checkRelativeXYZ(x, y, z)):
		# Error already shown
		return

	savedZ = None

	if(	(not x) and (not y) ):
		ui.debugLog("Skipping move to safe Z due to no XY movement", caller='safeRapidRelative()', verbose='SUPER')
	elif(tbl.getZ() < tbl.getSafeHeight()):
		ui.debugLog("Temporarily moving to safe Z...", caller='safeRapidRelative()', verbose='DETAIL')
		savedZ = tbl.getZ()
		rapidAbsolute(z=tbl.getSafeHeight(), verbose=verbose)

	if(x or y):
		ui.debugLog("Applying rapid on XY...", caller='safeRapidRelative()', verbose='DETAIL')
		rapidRelative(x=x, y=y, verbose=verbose)

	if(savedZ != None):
		ui.debugLog("Restoring original Z...", caller='safeRapidRelative()', verbose='DETAIL')
		rapidAbsolute(z=savedZ, verbose=verbose)

	if(not z):
		ui.debugLog("Skipping rapid on Z (none specified)", caller='safeRapidRelative()', verbose='SUPER')
	else:
		ui.debugLog("Applying rapid on Z...", caller='safeRapidRelative()', verbose='DETAIL')
		rapidRelative(z=z, verbose=verbose)


