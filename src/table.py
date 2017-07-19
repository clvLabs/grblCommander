#!/usr/bin/python3
"""
grblCommander - table
=======================
Table boundaries management
"""
#print("***[IMPORTING]*** grblCommander - table")

from . import ui as ui

# Current coordinates
gX = 0
gMIN_X = 0
gMAX_X = 291

gY = 0
gMIN_Y = 0
gMAX_Y = 295

gZ = 0
gMIN_Z = 0
gMAX_Z = 30

# Rapid Increment (XY plane)
gRI_XY = 25
gMIN_RI_XY = 0.1
gMAX_RI_XY = 100

# Rapid Increment (Z plane)
gRI_Z = 1
gMIN_RI_Z = 0.1
gMAX_RI_Z = 10

# Safe Z height
gSAFE_HEIGHT = 3
gMIN_SAFE_HEIGHT = 1
gMAX_SAFE_HEIGHT = 10

#Table size percent (divisor)
gTableSizePercent=100
gMIN_TABLE_SIZE_PERCENT = 10
gMAX_TABLE_SIZE_PERCENT = 100

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getX():	return(gX)
def setX(x):
	global gX
	gX = x

def getY():	return(gY)
def setY(y):
	global gY
	gY = y

def getZ():	return(gZ)
def setZ(z):
	global gZ
	gZ = z

def getTableSizePercent():		return(gTableSizePercent)
def setTableSizePercent(percent):
	global gTableSizePercent
	gTableSizePercent = percent


def getMinX():	return( (gMIN_X * gTableSizePercent) / 100 )
def getMaxX():	return( (gMAX_X * gTableSizePercent) / 100 )
def getMinY():	return( (gMIN_Y * gTableSizePercent) / 100 )
def getMaxY():	return( (gMAX_Y * gTableSizePercent) / 100 )
def getMinZ():	return( gMIN_Z )
def getMaxZ():	return( gMAX_Z )

def getRI_XY():	return( (gRI_XY * gTableSizePercent) / 100 )
def getRI_Z():	return( gRI_Z )

def setRI_XY(relativeIncrement):
	global gRI_XY
	gRI_XY = relativeIncrement

def setRI_Z(relativeIncrement):
	global gRI_Z
	gRI_Z = relativeIncrement

def getZ():	return(gZ)
def setZ(z):
	global gZ
	gZ = z

def getSafeHeight():	return gSAFE_HEIGHT

def setSafeHeight(height):
	global gSAFE_HEIGHT
	gSAFE_HEIGHT = height

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeRI_XY(direction):
	ui.debugLog("[ Entering changeRI_XY() ]", caller='changeRI_XY()', verbose='DEBUG')

	newRI = 0
	increment = 0

	if( direction > 0 ):	# Up
		if( gRI_XY < 1 ):		increment = +0.05
		elif( gRI_XY < 10 ):	increment = +1
		elif( gRI_XY < 30 ):	increment = +5
		else:
			increment = +10
			if( gRI_XY+increment > gMAX_RI_XY ):
				increment = gMAX_RI_XY - gRI_XY

	else:					# Down
		if( gRI_XY > 30 ):		increment = -10
		elif( gRI_XY > 10 ):	increment = -5
		elif( gRI_XY >= 2 ):	increment = -1
		else:
			increment = -0.05
			if( gRI_XY+increment < gMIN_RI_XY ):
				increment = gMIN_RI_XY - gRI_XY

	newRI = gRI_XY + increment

	if( newRI < gMIN_RI_XY ):
		ui.debugLog( "ERROR: RI_XY below %.3f not allowed!" % gMIN_RI_XY , caller='changeRI_XY()', verbose='BASIC')
		return

	if( newRI > gMAX_RI_XY ):
		ui.debugLog( "ERROR: RI_XY over %.3f not allowed!" % gMAX_RI_XY , caller='changeRI_XY()', verbose='BASIC')
		return

	setRI_XY(newRI)
	ui.debugLog("New Rapid Increment (XY): %.3f" % newRI, caller='changeRI_XY()', verbose='BASIC')
	return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeRI_Z(direction):
	ui.debugLog("[ Entering changeRI_Z() ]", caller='changeRI_Z()', verbose='DEBUG')

	newRI = 0
	increment = 0

	if( direction > 0 ):	# Up
		if( gRI_Z < 1 ):	increment = +0.05
		else:
			increment = +1
			if( gRI_Z+increment > gMAX_RI_Z ):
				increment = gMAX_RI_Z - gRI_Z

	else:					# Down
		if( gRI_Z >= 2 ):	increment = -1
		else:
			increment = -0.05
			if( gRI_Z+increment < gMIN_RI_Z ):
				increment = gMIN_RI_Z - gRI_Z

	newRI = gRI_Z + increment

	if( newRI < gMIN_RI_Z ):
		ui.debugLog( "ERROR: RI_Z below %.3f not allowed!" % gMIN_RI_Z , caller='changeRI_Z()', verbose='BASIC')
		return

	if( newRI > gMAX_RI_Z ):
		ui.debugLog( "ERROR: RI_Z over %.3f not allowed!" % gMAX_RI_Z , caller='changeRI_Z()', verbose='BASIC')
		return

	setRI_Z(newRI)
	ui.debugLog("New Rapid Increment (Z): %.3f" % newRI, caller='changeRI_Z()', verbose='BASIC')
	return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showCurrPos(verbose='WARNING'):
	ui.debugLog("[ Entering showCurrPos() ]", caller='showCurrPos()', verbose='DEBUG')

	ui.debugLog("[X=%.3f Y=%.3f Z=%.3f]" % (getX(), getY(), getZ()), caller='showCurrPos()', verbose=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkAbsoluteXYZ(x=None, y=None, z=None):
	ui.debugLog("[ Entering checkAbsoluteXYZ() ]", caller='checkAbsoluteXYZ()', verbose='DEBUG')

	ui.debugLog("Calculating result...", caller='checkAbsoluteXYZ()', verbose='DEBUG')
	result = (checkAbsoluteX(x) and checkAbsoluteY(y) and checkAbsoluteZ(z))

	ui.debugLog(	"checkAbsoluteXYZ() - Absolute coordinates are %s"
				% ("OK" if result else "WRONG")
				, caller='checkAbsoluteXYZ()', verbose='DEBUG')
	return(result)


def checkAbsoluteX(x=None):
	ui.debugLog("[ Entering checkAbsoluteX() ]", caller='checkAbsoluteX()', verbose='DEBUG')

	if(x is None):
		ui.debugLog("Empty value", caller='checkAbsoluteX()', verbose='DEBUG')
		return True
	elif(x < getMinX()):
		ui.debugLog("ERROR: X below %.3f not allowed!" % getMinX(), caller='checkAbsoluteX()', verbose='ERROR')
		return False

	elif(x > getMaxX()):
		ui.debugLog("ERROR: X over %.3f not allowed!" % getMaxX(), caller='checkAbsoluteX()', verbose='ERROR')
		return False

	ui.debugLog("Absolute value is OK", caller='checkAbsoluteX()', verbose='DEBUG')
	return True


def checkAbsoluteY(y=None):
	ui.debugLog("[ Entering checkAbsoluteY() ]", caller='checkAbsoluteY()', verbose='DEBUG')

	if(y is None):
		ui.debugLog("Empty value is OK", caller='checkAbsoluteY()', verbose='DEBUG')
		return True

	elif(y < getMinY()):
		ui.debugLog("ERROR: Y below %.3f not allowed!" % getMinY(), caller='checkAbsoluteY()', verbose='ERROR')
		return False

	elif(y > getMaxY()):
		ui.debugLog("ERROR: Y over %.3f not allowed!" % getMaxY(), caller='checkAbsoluteY()', verbose='ERROR')
		return False

	ui.debugLog("Absolute value is OK", caller='checkAbsoluteY()', verbose='DEBUG')
	return True


def checkAbsoluteZ(z=None):
	ui.debugLog("[ Entering checkAbsoluteZ() ]", caller='checkAbsoluteZ()', verbose='DEBUG')

	if(z is None):
		ui.debugLog("Empty value is OK", caller='checkAbsoluteZ()', verbose='DEBUG')
		return True

	elif(z < getMinZ()):
		ui.debugLog("ERROR: Z below %.3f not allowed!" % getMinZ(), caller='checkAbsoluteZ()', verbose='ERROR')
		return False

	elif(z > getMaxZ()):
		ui.debugLog("ERROR: Z over %.3f not allowed!" % getMaxZ(), caller='checkAbsoluteZ()', verbose='ERROR')
		return False

	ui.debugLog("Absolute value is OK", caller='checkAbsoluteZ()', verbose='DEBUG')
	return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkRelativeXYZ(x=None, y=None, z=None):
	ui.debugLog("[ Entering checkRelativeXYZ() ]", caller='checkRelativeXYZ()', verbose='DEBUG')

	result = (checkRelativeX(x) or checkRelativeY(y) or checkRelativeZ(z))

	ui.debugLog(	"Relative coordinates are %s"

				% ("OK" if result else "WRONG")
				, caller='checkRelativeXYZ()', verbose='DEBUG')
	return(result)


def checkRelativeX(x=None):
	ui.debugLog("[ Entering checkRelativeX() ]", caller='checkRelativeX()', verbose='DEBUG')

	if(not x):	# No X provided or X==0
		ui.debugLog("Empty or 0 means no change", caller='checkRelativeX()', verbose='DEBUG')
		return False

	elif(x>0):	# Up
		if(getX()==getMaxX()):
			ui.debugLog("X is already at MAX_X (%.3f)" % getMaxX(), caller='checkRelativeX()', verbose='ERROR')
			return False
	else:		# Down
		if(getX()==getMinX()):
			ui.debugLog("X is already at MIN_X (%.3f)" % getMinX(), caller='checkRelativeX()', verbose='ERROR')
			return False

	ui.debugLog("Relative value means change", caller='checkRelativeX()', verbose='DEBUG')
	return True


def checkRelativeY(y=None):
	ui.debugLog("[ Entering checkRelativeY() ]", caller='checkRelativeY()', verbose='DEBUG')

	if(not y):	# No Y provided or Y==0
		ui.debugLog("Empty or 0 means no change", caller='checkRelativeY()', verbose='DEBUG')
		return False

	elif(y>0):	# Up
		if(getY()==getMaxY()):
			ui.debugLog("Y is already at MAX_Y (%.3f)" % getMaxY(), caller='checkRelativeY()', verbose='ERROR')
			return False
	else:		# Down
		if(getY()==getMinY()):
			ui.debugLog("Y is already at MIN_Y (%.3f)" % getMinY(), caller='checkRelativeY()', verbose='ERROR')
			return False

	ui.debugLog("Relative value means change", caller='checkRelativeY()', verbose='DEBUG')
	return True


def checkRelativeZ(z=None):
	ui.debugLog("[ Entering checkRelativeZ() ]", caller='checkRelativeZ()', verbose='DEBUG')

	if(not z):	# No Z provided or Z==0
		ui.debugLog("Empty or 0 means no change", caller='checkRelativeZ()', verbose='DEBUG')
		return False

	elif(z>0):	# Up
		if(getZ()==getMaxZ()):
			ui.debugLog("Z is already at MAX_Z (%.3f)" % getMaxZ(), caller='checkRelativeZ()', verbose='ERROR')
			return False
	else:		# Down
		if(getZ()==getMinZ()):
			ui.debugLog("Z is already at MIN_Z (%.3f)" % getMinZ(), caller='checkRelativeZ()', verbose='ERROR')
			return False

	ui.debugLog("Relative value means change", caller='checkRelativeZ()', verbose='DEBUG')
	return True

