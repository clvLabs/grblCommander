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
def getX():  return(gX)
def setX(x):
  global gX
  gX = x

def getY():  return(gY)
def setY(y):
  global gY
  gY = y

def getZ():  return(gZ)
def setZ(z):
  global gZ
  gZ = z

def getTableSizePercent():    return(gTableSizePercent)
def setTableSizePercent(percent):
  global gTableSizePercent
  gTableSizePercent = percent


def getMinX():  return( (gMIN_X * gTableSizePercent) / 100 )
def getMaxX():  return( (gMAX_X * gTableSizePercent) / 100 )
def getMinY():  return( (gMIN_Y * gTableSizePercent) / 100 )
def getMaxY():  return( (gMAX_Y * gTableSizePercent) / 100 )
def getMinZ():  return( gMIN_Z )
def getMaxZ():  return( gMAX_Z )

def getRI_XY(): return( (gRI_XY * gTableSizePercent) / 100 )
def getRI_Z():  return( gRI_Z )

def setRI_XY(relativeIncrement):
  global gRI_XY
  gRI_XY = relativeIncrement

def setRI_Z(relativeIncrement):
  global gRI_Z
  gRI_Z = relativeIncrement

def getZ():  return(gZ)
def setZ(z):
  global gZ
  gZ = z

def getSafeHeight():  return gSAFE_HEIGHT

def setSafeHeight(height):
  global gSAFE_HEIGHT
  gSAFE_HEIGHT = height

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeRI_XY(direction):
  _k = 'tbl.changeRI_XY()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  newRI = 0
  increment = 0

  if( direction > 0 ):  # Up
    if( gRI_XY < 1 ):    increment = +0.05
    elif( gRI_XY < 10 ):  increment = +1
    elif( gRI_XY < 30 ):  increment = +5
    else:
      increment = +10
      if( gRI_XY+increment > gMAX_RI_XY ):
        increment = gMAX_RI_XY - gRI_XY

  else:          # Down
    if( gRI_XY > 30 ):    increment = -10
    elif( gRI_XY > 10 ):  increment = -5
    elif( gRI_XY >= 2 ):  increment = -1
    else:
      increment = -0.05
      if( gRI_XY+increment < gMIN_RI_XY ):
        increment = gMIN_RI_XY - gRI_XY

  newRI = gRI_XY + increment

  if( newRI < gMIN_RI_XY ):
    ui.log( "ERROR: RI_XY below %.3f not allowed!" % gMIN_RI_XY , k=_k, v='BASIC')
    return

  if( newRI > gMAX_RI_XY ):
    ui.log( "ERROR: RI_XY over %.3f not allowed!" % gMAX_RI_XY , k=_k, v='BASIC')
    return

  setRI_XY(newRI)
  ui.log("New Rapid Increment (XY): %.3f" % newRI, k=_k, v='BASIC')
  return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeRI_Z(direction):
  _k = 'tbl.changeRI_Z()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  newRI = 0
  increment = 0

  if( direction > 0 ):  # Up
    if( gRI_Z < 1 ):  increment = +0.05
    else:
      increment = +1
      if( gRI_Z+increment > gMAX_RI_Z ):
        increment = gMAX_RI_Z - gRI_Z

  else:          # Down
    if( gRI_Z >= 2 ):  increment = -1
    else:
      increment = -0.05
      if( gRI_Z+increment < gMIN_RI_Z ):
        increment = gMIN_RI_Z - gRI_Z

  newRI = gRI_Z + increment

  if( newRI < gMIN_RI_Z ):
    ui.log( "ERROR: RI_Z below %.3f not allowed!" % gMIN_RI_Z , k=_k, v='BASIC')
    return

  if( newRI > gMAX_RI_Z ):
    ui.log( "ERROR: RI_Z over %.3f not allowed!" % gMAX_RI_Z , k=_k, v='BASIC')
    return

  setRI_Z(newRI)
  ui.log("New Rapid Increment (Z): %.3f" % newRI, k=_k, v='BASIC')
  return


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showCurrPos(verbose='WARNING'):
  _k = 'tbl.showCurrPos()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("[X=%.3f Y=%.3f Z=%.3f]" % (getX(), getY(), getZ()), k=_k, v=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkAbsoluteXYZ(x=None, y=None, z=None):
  _k = 'tbl.checkAbsoluteXYZ()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Calculating result...", k=_k, v='DEBUG')
  result = (checkAbsoluteX(x) and checkAbsoluteY(y) and checkAbsoluteZ(z))

  ui.log(  "checkAbsoluteXYZ() - Absolute coordinates are %s"
        % ("OK" if result else "WRONG")
        , k=_k, v='DEBUG')
  return(result)


def checkAbsoluteX(x=None):
  _k = 'tbl.checkAbsoluteX()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(x is None):
    ui.log("Empty value", k=_k, v='DEBUG')
    return True
  elif(x < getMinX()):
    ui.log("ERROR: X below %.3f not allowed!" % getMinX(), k=_k, v='ERROR')
    return False

  elif(x > getMaxX()):
    ui.log("ERROR: X over %.3f not allowed!" % getMaxX(), k=_k, v='ERROR')
    return False

  ui.log("Absolute value is OK", k=_k, v='DEBUG')
  return True


def checkAbsoluteY(y=None):
  _k = 'tbl.checkAbsoluteY()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(y is None):
    ui.log("Empty value is OK", k=_k, v='DEBUG')
    return True

  elif(y < getMinY()):
    ui.log("ERROR: Y below %.3f not allowed!" % getMinY(), k=_k, v='ERROR')
    return False

  elif(y > getMaxY()):
    ui.log("ERROR: Y over %.3f not allowed!" % getMaxY(), k=_k, v='ERROR')
    return False

  ui.log("Absolute value is OK", k=_k, v='DEBUG')
  return True


def checkAbsoluteZ(z=None):
  _k = 'tbl.checkAbsoluteZ()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(z is None):
    ui.log("Empty value is OK", k=_k, v='DEBUG')
    return True

  elif(z < getMinZ()):
    ui.log("ERROR: Z below %.3f not allowed!" % getMinZ(), k=_k, v='ERROR')
    return False

  elif(z > getMaxZ()):
    ui.log("ERROR: Z over %.3f not allowed!" % getMaxZ(), k=_k, v='ERROR')
    return False

  ui.log("Absolute value is OK", k=_k, v='DEBUG')
  return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkRelativeXYZ(x=None, y=None, z=None):
  _k = 'tbl.checkRelativeXYZ()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  result = (checkRelativeX(x) or checkRelativeY(y) or checkRelativeZ(z))

  ui.log(  "Relative coordinates are %s"

        % ("OK" if result else "WRONG")
        , k=_k, v='DEBUG')
  return(result)


def checkRelativeX(x=None):
  _k = 'tbl.checkRelativeX()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(not x):  # No X provided or X==0
    ui.log("Empty or 0 means no change", k=_k, v='DEBUG')
    return False

  elif(x>0):  # Up
    if(getX()==getMaxX()):
      ui.log("X is already at MAX_X (%.3f)" % getMaxX(), k=_k, v='ERROR')
      return False
  else:    # Down
    if(getX()==getMinX()):
      ui.log("X is already at MIN_X (%.3f)" % getMinX(), k=_k, v='ERROR')
      return False

  ui.log("Relative value means change", k=_k, v='DEBUG')
  return True


def checkRelativeY(y=None):
  _k = 'tbl.checkRelativeY()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(not y):  # No Y provided or Y==0
    ui.log("Empty or 0 means no change", k=_k, v='DEBUG')
    return False

  elif(y>0):  # Up
    if(getY()==getMaxY()):
      ui.log("Y is already at MAX_Y (%.3f)" % getMaxY(), k=_k, v='ERROR')
      return False
  else:    # Down
    if(getY()==getMinY()):
      ui.log("Y is already at MIN_Y (%.3f)" % getMinY(), k=_k, v='ERROR')
      return False

  ui.log("Relative value means change", k=_k, v='DEBUG')
  return True


def checkRelativeZ(z=None):
  _k = 'tbl.checkRelativeZ()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(not z):  # No Z provided or Z==0
    ui.log("Empty or 0 means no change", k=_k, v='DEBUG')
    return False

  elif(z>0):  # Up
    if(getZ()==getMaxZ()):
      ui.log("Z is already at MAX_Z (%.3f)" % getMaxZ(), k=_k, v='ERROR')
      return False
  else:    # Down
    if(getZ()==getMinZ()):
      ui.log("Z is already at MIN_Z (%.3f)" % getMinZ(), k=_k, v='ERROR')
      return False

  ui.log("Relative value means change", k=_k, v='DEBUG')
  return True

