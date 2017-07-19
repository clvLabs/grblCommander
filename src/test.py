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
  ui.debugLog("[ Entering automaticContactTest() ]", caller='automaticContactTest()', verbose='DEBUG')

  if(ut.isWindows()):
    ui.debugLog("ERROR: Automatic contact test not available under Windows", caller='automaticContactTest()', verbose='BASIC')
    return False

  ui.debugLog("Saving original Z", caller='automaticContactTest()', verbose='DETAIL')
  savedZ = tbl.getZ()

  downStep = 0.1
  upStep = 0.01
  touchZList = []
  nextStartPoint = 0
  touchZ = 0

  ui.debugLog("Starting contact test (%d iterations)..." % iterations, caller='automaticContactTest()', verbose='BASIC')

  for curIteration in range(iterations):

    # Prepare Z position
    ui.debugLog("Moving to Z to last known touch point +1 step to start test...", caller='automaticContactTest()', verbose='DETAIL')
    mch.feedAbsolute(z=nextStartPoint, speed=mch.gDEFAULT_SEEK_SPEED, verbose='NONE')

    # Step down until contact
    exit = False
    testCancelled = False
    z = tbl.getZ()

    ui.debugLog("---[Iteration %d]-----------------------" % (curIteration+1,), caller='automaticContactTest()', verbose='BASIC')
    while(not exit):
      ui.debugLog("Seeking CONTACT point (Z=%.3f)\r" % (z,), end='', caller='automaticContactTest()', verbose='BASIC')

      mch.feedAbsolute(z=z, verbose='NONE')

      if(kb.keyPressed()):
        key=kb.readKey()

        if( key == 27 ):  # <ESC>
          exit = True
          testCancelled = True
          break

      if(gpio.isContactActive()):
        ui.debugLog("", caller='automaticContactTest()', verbose='BASIC')
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
        ui.debugLog("Seeking RELEASE point (Z=%.3f)\r" % (z,), end='', caller='automaticContactTest()', verbose='BASIC')

        mch.feedAbsolute(z=z, verbose='NONE')

        if(kb.keyPressed()):
          key=kb.readKey()

          if( key == 27 ):  # <ESC>
            exit = True
            testCancelled = True
            break

        if(not gpio.isContactActive()):
          ui.debugLog("", caller='automaticContactTest()', verbose='BASIC')
          ui.debugLog("*** TOUCH POINT at Z=%.3f ***" % (lastZ,), caller='automaticContactTest()', verbose='BASIC')
          exit = True
          touchZ = lastZ
          break

        lastZ = z

      touchZList.append(touchZ)

    ui.debugLog("---------------------------------------", caller='automaticContactTest()', verbose='BASIC')

  if(testCancelled):
    ui.debugLog("", caller='automaticContactTest()', verbose='BASIC')
    ui.debugLog("*"*40, caller='automaticContactTest()', verbose='BASIC')
    ui.debugLog("POINT CONTACT TEST CANCELLED", caller='automaticContactTest()', verbose='BASIC')
    ui.debugLog("*"*40, caller='automaticContactTest()', verbose='BASIC')

  ui.debugLog("Restoring original Z...", caller='automaticContactTest()', verbose='DETAIL')
  mch.safeRapidAbsolute(z=savedZ, verbose='NONE')

  averageTouchZ = float(sum(touchZList))/len(touchZList) if len(touchZList) > 0 else 0

  minTouchZ = 9999
  for tz in touchZList:
    if( tz < minTouchZ ): minTouchZ = tz

  maxTouchZ = -9999
  for tz in touchZList:
    if( tz > maxTouchZ ): maxTouchZ = tz

  maxDevTouchZ = maxTouchZ - minTouchZ

  ui.debugLog(  "RESULTS:", caller='automaticContactTest()', verbose='BASIC')
  ui.debugLog(  "--------", caller='automaticContactTest()', verbose='BASIC')
  ui.debugLog(  "- TOUCH POINTS at Z=%s" % (touchZList,), caller='automaticContactTest()', verbose='BASIC')
  ui.debugLog(  "- Average=%.3f - Min=%.3f - Max=%.3f - MaxDev=%.3f"
          % (  averageTouchZ
            , minTouchZ
            , maxTouchZ
            , maxDevTouchZ)
          , caller='automaticContactTest()', verbose='BASIC')

  if(testCancelled):  return False
  else:        return { 'z':averageTouchZ, 'iter':iterations, 'max':maxTouchZ, 'min':minTouchZ, 'dev':maxDevTouchZ }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def manualContactTest():
  ui.debugLog("[ Entering manualContactTest() ]", caller='manualContactTest()', verbose='DEBUG')

  ui.debugLog("Saving original Z", caller='manualContactTest()', verbose='DETAIL')
  savedZ = tbl.getZ()
  ui.debugLog("Moving to Z0 to start test...", caller='manualContactTest()', verbose='DETAIL')
  mch.safeRapidAbsolute(z=0, verbose='NONE')

  ui.debugLog("Starting contact test...", caller='manualContactTest()', verbose='BASIC')

  # 0.1 step down until contact
  exit = False
  testCancelled = False
  touchZ = 0
  z = tbl.getZ()

  while(not exit):
    z -= 0.1
    ui.debugLog("[%d] Seeking CONTACT point (Z=%.3f)\r" % (curIteration+1,z), end='', caller='manualContactTest()', verbose='BASIC')

    mch.feedAbsolute(z=z, verbose='NONE')

    ui.debugLog("<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...", caller='manualContactTest()', verbose='BASIC')
    key=0
    while( key != 13 and key != 10 and key != 32 and key != 27 ):
      key=kb.readKey()

    if( key == 27 ):  # <ESC>
      exit = True
      testCancelled = True
      break
    elif( key == 13 or key == 10 ):  # <ENTER>
      ui.debugLog("Stopping at Z=%.3f" % z, caller='manualContactTest()', verbose='BASIC')
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
      ui.debugLog("[%d] Seeking RELEASE point (Z=%.3f)\r" % (curIteration+1,z), end='', caller='manualContactTest()', verbose='BASIC')

      mch.feedAbsolute(z=z, verbose='NONE')

      ui.debugLog("PHASE2 : Seeking RELEASE point", caller='manualContactTest()', verbose='BASIC')
      ui.debugLog("<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...", caller='manualContactTest()', verbose='BASIC')
      key=0
      while( key != 13 and key != 10 and key != 32 and key != 27 ):
        key=kb.readKey()

      if( key == 27 ):  # <ESC>
        exit = True
        testCancelled = True
        break
      elif( key == 13 or key == 10 ):  # <ENTER>
        ui.debugLog("TOUCH POINT at Z=%.3f" % lastZ, caller='manualContactTest()', verbose='BASIC')
        exit = True
        touchZ = lastZ
        break
      elif( key == 32 ):  # <SPACE>
        pass

      if( exit ):
        break

      lastZ = z

  if(testCancelled):
    ui.debugLog("*"*40, caller='manualContactTest()', verbose='BASIC')
    ui.debugLog("POINT CONTACT TEST CANCELLED", caller='manualContactTest()', verbose='BASIC')
    ui.debugLog("*"*40, caller='manualContactTest()', verbose='BASIC')

  ui.debugLog("Restoring original Z...", caller='manualContactTest()', verbose='DETAIL')
  mch.safeRapidAbsolute(z=savedZ)

  if(testCancelled):  return False
  else:        return { 'z':touchZ, 'iter':1, 'max':touchZ, 'min':touchZ, 'dev':0 }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def gridContactTest():
  ui.debugLog("[ Entering gridContactTest() ]", caller='gridContactTest()', verbose='DEBUG')

  ui.debugLog("Enter number of (inner) lines...", caller='gridContactTest()', verbose='BASIC')
  userLines=input("[0-n]\n")

  if(not userLines.isnumeric()):
    ui.debugLog("Invalid number of lines", caller='gridContactTest()', verbose='BASIC')
    return

  gridLines = int(userLines) + 2

  result = [[None for i in range(gridLines)] for j in range(gridLines)]

  ui.debugLog("Saving original XYZ", caller='gridContactTest()', verbose='DETAIL')
  savedX, savedY, savedZ = tbl.getX(), tbl.getY(), tbl.getZ()

  if(tbl.getZ() < tbl.getSafeHeight()):
    ui.debugLog("Temporarily moving to safe Z...", caller='gridContactTest()', verbose='DETAIL')
    mch.rapidAbsolute(z=tbl.getSafeHeight(), verbose='NONE')

  gridIncrementX = tbl.getMaxX() / (gridLines-1)
  gridIncrementY = tbl.getMaxY() / (gridLines-1)

  gridX = [gridIncrementX * pos for pos in range(gridLines)]
  gridY = [gridIncrementY * pos for pos in range(gridLines)]

  ui.debugLog("tbl.getMaxX() = [%.3f]" % (tbl.getMaxX(),), caller='gridContactTest()', verbose='DEBUG')
  ui.debugLog("tbl.getMaxY() = [%.3f]" % (tbl.getMaxY(),), caller='gridContactTest()', verbose='DEBUG')
  ui.debugLog("gridIncrementX = [%.3f]" % (gridIncrementX,), caller='gridContactTest()', verbose='DEBUG')
  ui.debugLog("gridIncrementY = [%.3f]" % (gridIncrementY,), caller='gridContactTest()', verbose='DEBUG')
  ui.debugLog("gridX = [%s]" % (repr(gridX),), caller='gridContactTest()', verbose='DEBUG')
  ui.debugLog("gridY = [%s]" % (repr(gridY),), caller='gridContactTest()', verbose='DEBUG')

  ui.debugLog(  "Starting test (%d*%d lines / %d points)..."
        %  ( gridLines
          , gridLines
          , gridLines*gridLines )
        , caller='gridContactTest()', verbose='BASIC')

  testCancelled = False
  curGridPoint = 0

  rangeY = range(len(gridY))

  for indexY in rangeY:
    if( indexY % 2 == 0 ):  rangeX = range(len(gridX))
    else:          rangeX = range(len(gridX)-1,-1,-1)

    for indexX in rangeX:
      ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')
      ui.debugLog(  "Testing[%d][%d] Y=%.3f X=%.3f (%d/%d)..."
            %  ( indexY
              , indexX
              , gridY[indexY]
              , gridX[indexX]
              , curGridPoint+1
              , gridLines*gridLines )
            , caller='gridContactTest()', verbose='BASIC')
      ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')

      ui.debugLog("mch.rapidAbsolute(Y=%.3f X=%.3f)..." % (gridY[indexY],gridX[indexX],), caller='gridContactTest()', verbose='DEBUG')
      mch.rapidAbsolute(y=gridY[indexY], x=gridX[indexX], verbose='NONE')

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
    ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')
    ui.debugLog("GRID CONTACT TEST CANCELLED", caller='gridContactTest()', verbose='BASIC')
    ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')
    if(tbl.getZ() < tbl.getSafeHeight()):
      ui.debugLog("Temporarily moving to safe Z...", caller='gridContactTest()', verbose='DETAIL')
      mch.rapidAbsolute(z=tbl.getSafeHeight(), verbose='NONE')
    ui.debugLog("Restoring original XYZ...", caller='gridContactTest()', verbose='DETAIL')
    mch.safeRapidAbsolute(x=savedX, y=savedY, verbose='NONE')
    mch.safeRapidAbsolute(z=savedZ, verbose='NONE')
    return
  else:
    ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')
    ui.debugLog("Test finished.", caller='gridContactTest()', verbose='BASIC')
    ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')

  # Test results - normal
  ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')
  ui.debugLog("Test tesults (normalized) = ", caller='gridContactTest()', verbose='BASIC')

  rangeY = range(len(gridY))
  rangeX = range(len(gridX))

  for indexY in rangeY:
    for indexX in rangeX:
      if(result[indexY][indexX] is None):
        ui.debugLog(  "Y[%02d][%07.3f] X[%02d][%07.3f] Z[ERROR]"
              %  (  indexY
                , 0.0
                , indexX
                , 0.0 )
              , caller='gridContactTest()', verbose='BASIC')
      else:
        ui.debugLog(  "Y[%02d][%07.3f] X[%02d][%07.3f] Z[%07.3f]-dev[%07.3f]"
              % (  indexY
                , result[indexY][indexX]['Y']
                , indexX
                , result[indexY][indexX]['X']
                , (result[indexY][indexX]['Z'] - result[0][0]['Z'])
                , result[indexY][indexX]['Zdev'] )
              , caller='gridContactTest()', verbose='BASIC')


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

  ui.debugLog("", caller='gridContactTest()', verbose='BASIC')
  ui.debugLog("Excel version saved to %s" % fileName, caller='gridContactTest()', verbose='BASIC')
  ui.debugLog("*"*40, caller='gridContactTest()', verbose='BASIC')

  ui.debugLog("Restoring original XYZ...", caller='gridContactTest()', verbose='BASIC')
  mch.safeRapidAbsolute(x=savedX, y=savedY, verbose='NONE')
  mch.safeRapidAbsolute(z=savedZ, verbose='NONE')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
