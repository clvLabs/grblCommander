#!/usr/bin/python3
"""
grblCommander - table
=======================
Table boundaries management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

from . import ui as ui
from src.gc.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
mchCfg = cfg['machine']

# Current coordinates
gX = 0.0
gMIN_X = 0.0
gMAX_X = mchCfg['max']['X']

gY = 0.0
gMIN_Y = 0.0
gMAX_Y = mchCfg['max']['Y']

gZ = 0.0
gMIN_Z = 0.0
gMAX_Z = mchCfg['max']['Z']

# Rapid Increment (XY plane)
gRI_XY = mchCfg['xyJogMm']
gMIN_RI_XY = 0.1
gMAX_RI_XY = 100

# Rapid Increment (Z plane)
gRI_Z = mchCfg['zJogMm']
gMIN_RI_Z = 0.1
gMAX_RI_Z = 20

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

def getMinX():  return( gMIN_X )
def getMaxX():  return( gMAX_X )
def getMinY():  return( gMIN_Y )
def getMaxY():  return( gMAX_Y )
def getMinZ():  return( gMIN_Z )
def getMaxZ():  return( gMAX_Z )

def getRI_XY(): return( gRI_XY )
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
    ui.log( 'ERROR: RI_XY below {:} not allowed!'.format(ui.coordStr(gMIN_RI_XY)), color='ui.errorMsg', v='ERROR')
    return

  if( newRI > gMAX_RI_XY ):
    ui.log( 'ERROR: RI_XY over {:} not allowed!'.format(ui.coordStr(gMAX_RI_XY)), color='ui.errorMsg', v='ERROR')
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
    ui.log('ERROR: RI_Z below {:} not allowed!'.format(ui.coordStr(gMIN_RI_Z)), color='ui.errorMsg', v='ERROR')
    return

  if( newRI > gMAX_RI_Z ):
    ui.log('ERROR: RI_Z over {:} not allowed!'.format(ui.coordStr(gMAX_RI_Z)), color='ui.errorMsg', v='ERROR')
    return

  setRI_Z(newRI)
  ui.log('New Rapid Increment (Z): {:}'.format(ui.coordStr(newRI)), color='ui.info')
  return
