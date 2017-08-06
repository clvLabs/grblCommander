#!/usr/bin/python3
"""
grblCommander - table
=======================
Table boundaries management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

from . import ui as ui
from src.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
mchCfg = cfg['machine']

# Current coordinates
gX = 0.0
gMIN_X = 0.0
gMAX_X = mchCfg['maxX']

gY = 0.0
gMIN_Y = 0.0
gMAX_Y = mchCfg['maxY']

gZ = 0.0
gMIN_Z = 0.0
gMAX_Z = mchCfg['maxX']

# Rapid Increment (XY plane)
gRI_XY = mchCfg['rapidXY']
gMIN_RI_XY = 0.1
gMAX_RI_XY = 100

# Rapid Increment (Z plane)
gRI_Z = mchCfg['rapidZ']
gMIN_RI_Z = 0.1
gMAX_RI_Z = 20

# Safe Z height
gSAFE_HEIGHT = mchCfg['zSafeHeight']
gMIN_SAFE_HEIGHT = 0
gMAX_SAFE_HEIGHT = 30

# Table size percent (divisor)
gTableSizePercent = mchCfg['tableSizePercent']
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
    ui.log( 'ERROR: RI_XY below {:} not allowed!'.format(ui.coordStr(gMIN_RI_XY)), color='ui.msg')
    return

  if( newRI > gMAX_RI_XY ):
    ui.log( 'ERROR: RI_XY over {:} not allowed!'.format(ui.coordStr(gMAX_RI_XY)), color='ui.msg')
    return

  setRI_XY(newRI)
  ui.log('New Rapid Increment (XY): {:}'.format(ui.coordStr(newRI)), color='ui.info')
  return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def changeRI_Z(direction):
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
    ui.log('ERROR: RI_Z below {:} not allowed!'.format(ui.coordStr(gMIN_RI_Z)), color='ui.msg')
    return

  if( newRI > gMAX_RI_Z ):
    ui.log('ERROR: RI_Z over {:} not allowed!'.format(ui.coordStr(gMAX_RI_Z)), color='ui.msg')
    return

  setRI_Z(newRI)
  ui.log('New Rapid Increment (Z): {:}'.format(ui.coordStr(newRI)), color='ui.info')
  return

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkAbsoluteXYZ(x=None, y=None, z=None):
  ui.log('Calculating result...', v='DEBUG')
  result = (checkAbsoluteX(x) and checkAbsoluteY(y) and checkAbsoluteZ(z))

  ui.log(  'checkAbsoluteXYZ() - Absolute coordinates are {:s}'.format(
        'OK' if result else 'WRONG'), v='DEBUG')
  return(result)


def checkAbsoluteX(x=None):
  if(x is None):
    ui.log('Empty value', v='DEBUG')
    return True
  elif(x < getMinX()):
    ui.log('ERROR: X below {:} not allowed!'.format(ui.coordStr(getMinX())), v='ERROR')
    return False

  elif(x > getMaxX()):
    ui.log('ERROR: X over {:} not allowed!'.format(ui.coordStr(getMaxX())), v='ERROR')
    return False

  ui.log('Absolute value is OK', v='DEBUG')
  return True


def checkAbsoluteY(y=None):
  if(y is None):
    ui.log('Empty value is OK', v='DEBUG')
    return True

  elif(y < getMinY()):
    ui.log('ERROR: Y below {:} not allowed!'.format(ui.coordStr(getMinY())), v='ERROR')
    return False

  elif(y > getMaxY()):
    ui.log('ERROR: Y over {:} not allowed!'.format(ui.coordStr(getMaxY())), v='ERROR')
    return False

  ui.log('Absolute value is OK', v='DEBUG')
  return True


def checkAbsoluteZ(z=None):
  if(z is None):
    ui.log('Empty value is OK', v='DEBUG')
    return True

  elif(z < getMinZ()):
    ui.log('ERROR: Z below {:} not allowed!'.format(ui.coordStr(getMinZ())), color='ui.msg', v='ERROR')
    return False

  elif(z > getMaxZ()):
    ui.log('ERROR: Z over {:} not allowed!'.format(ui.coordStr(getMaxZ())), color='ui.msg', v='ERROR')
    return False

  ui.log('Absolute value is OK', v='DEBUG')
  return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkRelativeXYZ(x=None, y=None, z=None):
  result = (checkRelativeX(x) or checkRelativeY(y) or checkRelativeZ(z))

  ui.log(  'Relative coordinates are {:s}'.format(
        'OK' if result else 'WRONG'), v='DEBUG')
  return(result)


def checkRelativeX(x=None):
  if(not x):  # No X provided or X==0
    ui.log('Empty or 0 means no change', v='DEBUG')
    return False

  elif(x>0):  # Up
    if(getX()==getMaxX()):
      ui.log('X is already at MAX_X ({:})'.format(ui.coordStr(getMaxX())), color='ui.msg', v='ERROR')
      return False
  else:    # Down
    if(getX()==getMinX()):
      ui.log('X is already at MIN_X ({:})'.format(ui.coordStr(getMinX())), color='ui.msg', v='ERROR')
      return False

  ui.log('Relative value means change', v='DEBUG')
  return True


def checkRelativeY(y=None):
  if(not y):  # No Y provided or Y==0
    ui.log('Empty or 0 means no change', v='DEBUG')
    return False

  elif(y>0):  # Up
    if(getY()==getMaxY()):
      ui.log('Y is already at MAX_Y ({:})'.format(ui.coordStr(getMaxY())), color='ui.msg', v='ERROR')
      return False
  else:    # Down
    if(getY()==getMinY()):
      ui.log('Y is already at MIN_Y ({:})'.format(ui.coordStr(getMinY())), color='ui.msg', v='ERROR')
      return False

  ui.log('Relative value means change', v='DEBUG')
  return True


def checkRelativeZ(z=None):
  if(not z):  # No Z provided or Z==0
    ui.log('Empty or 0 means no change', v='DEBUG')
    return False

  elif(z>0):  # Up
    if(getZ()==getMaxZ()):
      ui.log('Z is already at MAX_Z ({:})'.format(ui.coordStr(getMaxZ())), color='ui.msg', v='ERROR')
      return False
  else:    # Down
    if(getZ()==getMinZ()):
      ui.log('Z is already at MIN_Z ({:})'.format(ui.coordStr(getMinZ())), color='ui.msg', v='ERROR')
      return False

  ui.log('Relative value means change', v='DEBUG')
  return True
