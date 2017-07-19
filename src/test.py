#!/usr/bin/python3
"""
grblCommander - test
=====================
Test code
"""
#print("***[IMPORTING]*** grblCommander - test")

import sys
import time

from . import utils as ut
from . import ui as ui
from . import table as tbl
from . import machine as mch
from . import serialport as sp
from . import keyboard as kb

if(not ut.isWindows()):
  from . import rpigpio as gpio
  gpio.setup()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def automaticContactTest(iterations = 3):
  _k = 'test.automaticContactTest()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if(ut.isWindows()):
    ui.log("ERROR: Automatic contact test not available under Windows", k=_k, v='BASIC')
    return False

  ui.log("Saving original Z", k=_k, v='DETAIL')
  savedZ = tbl.getZ()

  downStep = 0.1
  upStep = 0.01
  touchZList = []
  nextStartPoint = 0
  touchZ = 0

  ui.log("Starting contact test (%d iterations)..." % iterations, k=_k, v='BASIC')

  for curIteration in range(iterations):

    # Prepare Z position
    ui.log("Moving to Z to last known touch point +1 step to start test...", k=_k, v='DETAIL')
    mch.feedAbsolute(z=nextStartPoint, speed=mch.gDEFAULT_SEEK_SPEED, v='NONE')

    # Step down until contact
    exit = False
    testCancelled = False
    z = tbl.getZ()

    ui.log("---[Iteration %d]-----------------------" % (curIteration+1,), k=_k, v='BASIC')
    while(not exit):
      ui.log("Seeking CONTACT point (Z=%.3f)\r" % (z,), end='', k=_k, v='BASIC')

      mch.feedAbsolute(z=z, v='NONE')

      if(kb.keyPressed()):
        key=kb.readKey()

        if( key == 27 ):  # <ESC>
          exit = True
          testCancelled = True
          break

      if(gpio.isContactActive()):
        ui.log("", k=_k, v='BASIC')
        exit = True
        touchZ = z
        nextStartPoint = touchZ+downStep
        break

      z -= downStep

    # Step up until contact lost
    if(testCancelled):
      break
    else:
      exit = False
      lastZ = z

      while(not exit):
        z += upStep
        ui.log("Seeking RELEASE point (Z=%.3f)\r" % (z,), end='', k=_k, v='BASIC')

        mch.feedAbsolute(z=z, v='NONE')

        if(kb.keyPressed()):
          key=kb.readKey()

          if( key == 27 ):  # <ESC>
            exit = True
            testCancelled = True
            break

        if(not gpio.isContactActive()):
          ui.log("", k=_k, v='BASIC')
          ui.log("*** TOUCH POINT at Z=%.3f ***" % (lastZ,), k=_k, v='BASIC')
          exit = True
          touchZ = lastZ
          break

        lastZ = z

      touchZList.append(touchZ)

    ui.log("---------------------------------------", k=_k, v='BASIC')

  if(testCancelled):
    ui.log("", k=_k, v='BASIC')
    ui.log("*"*40, k=_k, v='BASIC')
    ui.log("POINT CONTACT TEST CANCELLED", k=_k, v='BASIC')
    ui.log("*"*40, k=_k, v='BASIC')

  ui.log("Restoring original Z...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=savedZ, v='NONE')

  averageTouchZ = float(sum(touchZList))/len(touchZList) if len(touchZList) > 0 else 0

  minTouchZ = 9999
  for tz in touchZList:
    if( tz < minTouchZ ): minTouchZ = tz

  maxTouchZ = -9999
  for tz in touchZList:
    if( tz > maxTouchZ ): maxTouchZ = tz

  maxDevTouchZ = maxTouchZ - minTouchZ

  ui.log(  "RESULTS:", k=_k, v='BASIC')
  ui.log(  "--------", k=_k, v='BASIC')
  ui.log(  "- TOUCH POINTS at Z=%s" % (touchZList,), k=_k, v='BASIC')
  ui.log(  "- Average=%.3f - Min=%.3f - Max=%.3f - MaxDev=%.3f"
          % (  averageTouchZ
            , minTouchZ
            , maxTouchZ
            , maxDevTouchZ)
          , k=_k, v='BASIC')

  if(testCancelled):  return False
  else:        return { 'z':averageTouchZ, 'iter':iterations, 'max':maxTouchZ, 'min':minTouchZ, 'dev':maxDevTouchZ }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def manualContactTest():
  _k = 'test.manualContactTest()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Saving original Z", k=_k, v='DETAIL')
  savedZ = tbl.getZ()
  ui.log("Moving to Z0 to start test...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=0, v='NONE')

  ui.log("Starting contact test...", k=_k, v='BASIC')

  # 0.1 step down until contact
  exit = False
  testCancelled = False
  touchZ = 0
  z = tbl.getZ()

  while(not exit):
    z -= 0.1
    ui.log("[%d] Seeking CONTACT point (Z=%.3f)\r" % (curIteration+1,z), end='', k=_k, v='BASIC')

    mch.feedAbsolute(z=z, v='NONE')

    ui.log("<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...", k=_k, v='BASIC')
    key=0
    while( key != 13 and key != 10 and key != 32 and key != 27 ):
      key=kb.readKey()

    if( key == 27 ):  # <ESC>
      exit = True
      testCancelled = True
      break
    elif( key == 13 or key == 10 ):  # <ENTER>
      ui.log("Stopping at Z=%.3f" % z, k=_k, v='BASIC')
      exit = True
      touchZ = z
      break
    elif( key == 32 ):  # <SPACE>
      pass

    if( exit ):
      break

  # 0.025 step up until contact lost
  if(not testCancelled):
    exit = False
    lastZ = z

    while(not exit):
      z += 0.025
      ui.log("[%d] Seeking RELEASE point (Z=%.3f)\r" % (curIteration+1,z), end='', k=_k, v='BASIC')

      mch.feedAbsolute(z=z, v='NONE')

      ui.log("PHASE2 : Seeking RELEASE point", k=_k, v='BASIC')
      ui.log("<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...", k=_k, v='BASIC')
      key=0
      while( key != 13 and key != 10 and key != 32 and key != 27 ):
        key=kb.readKey()

      if( key == 27 ):  # <ESC>
        exit = True
        testCancelled = True
        break
      elif( key == 13 or key == 10 ):  # <ENTER>
        ui.log("TOUCH POINT at Z=%.3f" % lastZ, k=_k, v='BASIC')
        exit = True
        touchZ = lastZ
        break
      elif( key == 32 ):  # <SPACE>
        pass

      if( exit ):
        break

      lastZ = z

  if(testCancelled):
    ui.log("*"*40, k=_k, v='BASIC')
    ui.log("POINT CONTACT TEST CANCELLED", k=_k, v='BASIC')
    ui.log("*"*40, k=_k, v='BASIC')

  ui.log("Restoring original Z...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=savedZ)

  if(testCancelled):  return False
  else:        return { 'z':touchZ, 'iter':1, 'max':touchZ, 'min':touchZ, 'dev':0 }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def gridContactTest():
  _k = 'test.gridContactTest()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log("Enter number of (inner) lines...", k=_k, v='BASIC')
  userLines=input("[0-n]\n")

  if(not userLines.isnumeric()):
    ui.log("Invalid number of lines", k=_k, v='BASIC')
    return

  gridLines = int(userLines) + 2

  result = [[None for i in range(gridLines)] for j in range(gridLines)]

  ui.log("Saving original XYZ", k=_k, v='DETAIL')
  savedX, savedY, savedZ = tbl.getX(), tbl.getY(), tbl.getZ()

  if(tbl.getZ() < tbl.getSafeHeight()):
    ui.log("Temporarily moving to safe Z...", k=_k, v='DETAIL')
    mch.rapidAbsolute(z=tbl.getSafeHeight(), v='NONE')

  gridIncrementX = tbl.getMaxX() / (gridLines-1)
  gridIncrementY = tbl.getMaxY() / (gridLines-1)

  gridX = [gridIncrementX * pos for pos in range(gridLines)]
  gridY = [gridIncrementY * pos for pos in range(gridLines)]

  ui.log("tbl.getMaxX() = [%.3f]" % (tbl.getMaxX(),), k=_k, v='DEBUG')
  ui.log("tbl.getMaxY() = [%.3f]" % (tbl.getMaxY(),), k=_k, v='DEBUG')
  ui.log("gridIncrementX = [%.3f]" % (gridIncrementX,), k=_k, v='DEBUG')
  ui.log("gridIncrementY = [%.3f]" % (gridIncrementY,), k=_k, v='DEBUG')
  ui.log("gridX = [%s]" % (repr(gridX),), k=_k, v='DEBUG')
  ui.log("gridY = [%s]" % (repr(gridY),), k=_k, v='DEBUG')

  ui.log(  "Starting test (%d*%d lines / %d points)..."
        %  ( gridLines
          , gridLines
          , gridLines*gridLines )
        , k=_k, v='BASIC')

  testCancelled = False
  curGridPoint = 0

  rangeY = range(len(gridY))

  for indexY in rangeY:
    if( indexY % 2 == 0 ):  rangeX = range(len(gridX))
    else:          rangeX = range(len(gridX)-1,-1,-1)

    for indexX in rangeX:
      ui.log("*"*40, k=_k, v='BASIC')
      ui.log(  "Testing[%d][%d] Y=%.3f X=%.3f (%d/%d)..."
            %  ( indexY
              , indexX
              , gridY[indexY]
              , gridX[indexX]
              , curGridPoint+1
              , gridLines*gridLines )
            , k=_k, v='BASIC')
      ui.log("*"*40, k=_k, v='BASIC')

      ui.log("mch.rapidAbsolute(Y=%.3f X=%.3f)..." % (gridY[indexY],gridX[indexX],), k=_k, v='DEBUG')
      mch.rapidAbsolute(y=gridY[indexY], x=gridX[indexX], v='NONE')

      if kb.keyPressed():
        if(kb.readKey() == 27):    # <ESC>
          testCancelled = True
          break

      curGridPoint+=1

      # Make a contact test
      if(ut.isWindows()):
        testResult = manualContactTest()
      else:
        testResult = automaticContactTest()

      if( testResult is False ):
        testCancelled = True
        break

      result[indexY][indexX] = { 'X':gridX[indexX], 'Y':gridY[indexY], 'Z':testResult['z'], 'Zmaz':testResult['max'], 'Zmin':testResult['min'], 'Zdev':testResult['dev'] }

    if(testCancelled): break

  if(testCancelled):
    ui.log("*"*40, k=_k, v='BASIC')
    ui.log("GRID CONTACT TEST CANCELLED", k=_k, v='BASIC')
    ui.log("*"*40, k=_k, v='BASIC')
    if(tbl.getZ() < tbl.getSafeHeight()):
      ui.log("Temporarily moving to safe Z...", k=_k, v='DETAIL')
      mch.rapidAbsolute(z=tbl.getSafeHeight(), v='NONE')
    ui.log("Restoring original XYZ...", k=_k, v='DETAIL')
    mch.safeRapidAbsolute(x=savedX, y=savedY, v='NONE')
    mch.safeRapidAbsolute(z=savedZ, v='NONE')
    return
  else:
    ui.log("*"*40, k=_k, v='BASIC')
    ui.log("Test finished.", k=_k, v='BASIC')
    ui.log("*"*40, k=_k, v='BASIC')

  # Test results - normal
  ui.log("*"*40, k=_k, v='BASIC')
  ui.log("Test tesults (normalized) = ", k=_k, v='BASIC')

  rangeY = range(len(gridY))
  rangeX = range(len(gridX))

  for indexY in rangeY:
    for indexX in rangeX:
      if(result[indexY][indexX] is None):
        ui.log(  "Y[%02d][%07.3f] X[%02d][%07.3f] Z[ERROR]"
              %  (  indexY
                , 0.0
                , indexX
                , 0.0 )
              , k=_k, v='BASIC')
      else:
        ui.log(  "Y[%02d][%07.3f] X[%02d][%07.3f] Z[%07.3f]-dev[%07.3f]"
              % (  indexY
                , result[indexY][indexX]['Y']
                , indexX
                , result[indexY][indexX]['X']
                , (result[indexY][indexX]['Z'] - result[0][0]['Z'])
                , result[indexY][indexX]['Zdev'] )
              , k=_k, v='BASIC')


  # Test results - Excel formatted
  # Create output file
  t=time.localtime()
  fileName =  "logs/GridContactTest %d%02d%02d%02d%02d%02d.txt" % (t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)
  outFile = open(fileName, 'w')

  outFile.write(" grblCommander Grid Contact Test \n")
  outFile.write("=================================\n")
  outFile.write("\n")
  outFile.write("TimeStamp: %d/%02d/%02d %02d:%02d:%02d\n" % (t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec) )
  outFile.write("\n")
  outFile.write(
"""  Software config:
    RapidIncrement_XY = %.2f
    RapidIncrement_Z  = %.2f
    TableSize%%        = %d%%
"""
    % (  tbl.getRI_XY(), tbl.getRI_Z(), tbl.getTableSizePercent() ) )
  outFile.write("\n")

  outFile.write("Test results (real Z):\n")
  outFile.write("----------------------\n")
  outFile.write("\n")

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = "%07.3f\t" % result[indexY][0]['Y']

    for indexX in rangeX:
      if(result[indexY][indexX] is None):
        line += "ERROR\t"
      else:
        line += "%07.3f\t" % result[indexY][indexX]['Z']

    outFile.write(line.rstrip('\t')+'\n')

  line = "\t"

  for indexX in rangeX:
    line += "%07.3f\t" % result[0][indexX]['X']

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write("\n")


  outFile.write("Test results (normalized Z):\n")
  outFile.write("----------------------------\n")
  outFile.write("\n")

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = "%07.3f\t" % result[indexY][0]['Y']

    for indexX in rangeX:
      if(result[indexY][indexX] is None):
        line += "ERROR\t"
      else:
        line += "%07.3f\t" % (result[indexY][indexX]['Z'] - result[0][0]['Z'])

    outFile.write(line.rstrip('\t')+'\n')

  line = "\t"

  for indexX in rangeX:
    line += "%07.3f\t" % result[0][indexX]['X']

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write("\n")


  outFile.write("Test results (Z deviations):\n")
  outFile.write("----------------------------\n")
  outFile.write("\n")

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = "%07.3f\t" % result[indexY][0]['Y']

    for indexX in rangeX:
      if(result[indexY][indexX] is None):
        line += "ERROR\t"
      else:
        line += "%07.3f\t" % (result[0][0]['Zdev'],)

    outFile.write(line.rstrip('\t')+'\n')

  line = "\t"

  for indexX in rangeX:
    line += "%07.3f\t" % result[0][indexX]['X']

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write("\n")



  outFile.close()

  ui.log("", k=_k, v='BASIC')
  ui.log("Excel version saved to %s" % fileName, k=_k, v='BASIC')
  ui.log("*"*40, k=_k, v='BASIC')

  ui.log("Restoring original XYZ...", k=_k, v='BASIC')
  mch.safeRapidAbsolute(x=savedX, y=savedY, v='NONE')
  mch.safeRapidAbsolute(z=savedZ, v='NONE')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
