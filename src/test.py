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


testCancelled = False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def automaticContactTest(iterations = 3):
  _k = 'test.automaticContactTest()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  global testCancelled

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
    mch.feedAbsolute(z=nextStartPoint, speed=mch.gDEFAULT_SEEK_SPEED, verbose='NONE')

    # Step down until contact
    exit = False
    testCancelled = False
    z = tbl.getZ()

    ui.log("---[Iteration %d]-----------------------" % (curIteration+1,), k=_k, v='BASIC')
    while(not exit):
      ui.log("Seeking CONTACT point (Z=%.3f)\r" % (z,), end='', k=_k, v='BASIC')

      mch.feedAbsolute(z=z, verbose='NONE')

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

        mch.feedAbsolute(z=z, verbose='NONE')

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
    ui.logBlock("POINT CONTACT TEST CANCELLED", s="*"*40, k=_k, v='BASIC')

  ui.log("Restoring original Z...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=savedZ, verbose='NONE')

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

  global testCancelled

  ui.log("Saving original Z", k=_k, v='DETAIL')
  savedZ = tbl.getZ()
  ui.log("Moving to Z0 to start test...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=0, verbose='NONE')

  ui.log("Starting contact test...", k=_k, v='BASIC')

  # 0.1 step down until contact
  exit = False
  testCancelled = False
  touchZ = 0
  z = tbl.getZ()

  while(not exit):
    z -= 0.1
    ui.log("Seeking CONTACT point (Z=%.3f)\r" % (z,), end='', k=_k, v='BASIC')

    mch.feedAbsolute(z=z, verbose='NONE')

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
      ui.log("Seeking RELEASE point (Z=%.3f)\r" % (z,), end='', k=_k, v='BASIC')

      mch.feedAbsolute(z=z, verbose='NONE')

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
    ui.logBlock("POINT CONTACT TEST CANCELLED", s="*"*40, k=_k, v='BASIC')

  ui.log("Restoring original Z...", k=_k, v='DETAIL')
  mch.safeRapidAbsolute(z=savedZ)

  if(testCancelled):  return False
  else:        return { 'z':touchZ, 'iter':1, 'max':touchZ, 'min':touchZ, 'dev':0 }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def gridContactTest():
  _k = 'test.gridContactTest()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  global testCancelled

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
    mch.rapidAbsolute(z=tbl.getSafeHeight(), verbose='NONE')

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
    ui.logBlock("GRID CONTACT TEST CANCELLED", s="*"*40, k=_k, v='BASIC')
    if(tbl.getZ() < tbl.getSafeHeight()):
      ui.log("Temporarily moving to safe Z...", k=_k, v='DETAIL')
      mch.rapidAbsolute(z=tbl.getSafeHeight(), verbose='NONE')
    ui.log("Restoring original XYZ...", k=_k, v='DETAIL')
    mch.safeRapidAbsolute(x=savedX, y=savedY, verbose='NONE')
    mch.safeRapidAbsolute(z=savedZ, verbose='NONE')
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
  mch.safeRapidAbsolute(x=savedX, y=savedY, verbose='NONE')
  mch.safeRapidAbsolute(z=savedZ, verbose='NONE')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def baseLevelingHoles():
  _k = 'test.baseLevelingHoles()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  global testCancelled

  ui.log("""
  WARNING !!!!!
  =============

  This test understands your 0,0 is set to the upper right corner
  of your machine, so it will send NEGATIVE COORDINATES.

  Please read the code thoroughly before proceeding.

  Are you sure you want to continue?
  (please write IAmSure if you want to go on)
  """ , k=_k, v='BASIC')

  password=input()
  if password != 'IAmSure':
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  # - [X/Y steps]- - - - - - - - - - - - - - - - - -
  XSteps = [0, -30, -60, -80, -100, -120, -140, -150, -170, -200, -220, -240, -260, -280]
  YSteps = [0, -20, -40, -60, -80, -100, -130, -150, -170, -210, -230, -250, -280]

  # - [Internal helpers]- - - - - - - - - - - - - - - - - -
  def sendCmd(cmd):
    global testCancelled

    if testCancelled:
      ui.log("IGNORING command [{0}] (Test CANCELLED)".format(cmd) , k=_k, v='BASIC')
      return

    sp.sendCommand(cmd)
    mch.waitForMachineIdle()

    if(kb.keyPressed()):
      key=kb.readKey()

      if( key == 27 ):  # <ESC>
        testCancelled = True

  def goTo(x, y):
    sendCmd('G0 X{0} Y{1}'.format(x, y))

  def goToSafeZ():
    sendCmd("G0 Z3")

  def drill():
    sendCmd("G0 Z1.5")
    sendCmd("G1 Z0")
    goToSafeZ()

  # - [Main process]- - - - - - - - - - - - - - - - - -
  ui.log("Raising Z to safe height..." , k=_k, v='BASIC')
  goToSafeZ()

  ui.log("Starting drill pattern..." , k=_k, v='BASIC')
  for yIndex, y in enumerate(YSteps):
    xRange = XSteps if (yIndex % 2) == 0 else XSteps[::-1]
    for x in xRange:
      goTo(x, y)
      drill()

  ui.log("" , k=_k, v='BASIC')
  ui.log("**********************" , k=_k, v='BASIC')
  ui.log("DRILL PATTERN FINISHED", k=_k, v='BASIC')
  ui.log("**********************" , k=_k, v='BASIC')
  ui.log("" , k=_k, v='BASIC')

  if testCancelled:
    testCancelled = False   # Make sure we always get back home

  ui.log("Back home..." , k=_k, v='BASIC')
  sendCmd("G0 X0 Y0")
  sendCmd("G0 Z1.5")
  sendCmd("G1 Z0")


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def zigZagPattern():
  _k = 'test.zigZagPattern()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  global testCancelled

  ui.log("""
  WARNING !!!!!
  =============

  This test will start a series of zig-zag patterns
  using incremental feed speeds to determine
  optimal speed-feed for a given material.

  Based on:
  http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm

  Please read the code thoroughly before proceeding.
  """ , k=_k, v='BASIC')

  def showZZParameters(title):
    ui.log("""
    {:s}:
      Run                   {:f}
      Rise                  {:f}
      Plunge                {:f}
      PlungeSpeed           {:f}
      InitialFeed           {:f}
      DeltaFeed             {:d}
      ZigZagPerIteration    {:d}
      Iterations            {:d}
      Spacing               {:f}

      TOTAL
        Width               {:f}
        Height              {:f}
      """.format(
        title,
        zzRun,
        zzRise,
        zzPlunge,
        zzPlungeSpeed,
        zzInitialFeed,
        zzDeltaFeed,
        zzZigZagPerIteration,
        zzIterations,
        zzSpacing,
        zzTotalWidth,
        zzTotalHeight,
        ), k=_k, v='BASIC')

  def checkTestCancelled():
    global testCancelled
    if(kb.keyPressed()):
      key=kb.readKey()

      if( key == 27 ):  # <ESC>
        testCancelled = True

  def feed(x=None, y=None, z=None, speed=None):
    if not testCancelled:
      mch.feedAbsolute(x=x, y=y, z=z, speed=speed)
      checkTestCancelled()

  def rapid(x=None, y=None, z=None):
    if not testCancelled:
      mch.rapidAbsolute(x=x, y=y, z=z)
      checkTestCancelled()

  bitDiameter=ui.getUserInput('bit diameter (mm)', float)
  if bitDiameter == None:
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  bitFlutes=ui.getUserInput('number of flutes', int)
  if bitFlutes == None:
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  bitRPM=ui.getUserInput('spindle RPM', int)
  if bitRPM == None:
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  zSafeHeight=ui.getUserInput('Z safe height (mm)', float)
  if zSafeHeight == None:
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  # zig-zag default parameter calculations
  # NOTE: Using parameters for softwoods!!
  # Check before trying with other materials!!

  zzRun = 25 if bitDiameter < 3.18 else 50
  zzRise = bitDiameter * 2
  zzPlunge = bitDiameter
  zzPlungeSpeed = 100
  zzInitialFeed = 0.02 * bitDiameter * bitFlutes * bitRPM
  zzDeltaFeed = 125 if bitDiameter < 0.8 else 200 if bitDiameter < 3.0 else 250
  zzZigZagPerIteration = 4
  zzIterations = 4
  zzSpacing = bitDiameter * 2
  zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
  zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter

  showZZParameters('Calculated parameters')

  zzTmpRun=ui.getUserInput('Run ({:f})'.format(zzRun), float)
  if zzTmpRun is not None: zzRun = zzTmpRun

  zzTmpRise=ui.getUserInput('Rise ({:f})'.format(zzRise), float)
  if zzTmpRise is not None: zzRise = zzTmpRise

  zzTmpPlunge=ui.getUserInput('Plunge ({:f})'.format(zzPlunge), float)
  if zzTmpPlunge is not None: zzPlunge = zzTmpPlunge

  zzTmpPlungeSpeed=ui.getUserInput('PlungeSpeed ({:f})'.format(zzPlungeSpeed), float)
  if zzTmpPlungeSpeed is not None: zzPlungeSpeed = zzTmpPlungeSpeed

  zzTmpInitialFeed=ui.getUserInput('InitialFeed ({:f})'.format(zzInitialFeed), float)
  if zzTmpInitialFeed is not None: zzInitialFeed = zzTmpInitialFeed

  zzTmpDeltaFeed=ui.getUserInput('DeltaFeed ({:d})'.format(zzDeltaFeed), int)
  if zzTmpDeltaFeed is not None: zzDeltaFeed = zzTmpDeltaFeed

  zzTmpZigZagPerIteration=ui.getUserInput('ZigZagPerIteration ({:d})'.format(zzZigZagPerIteration), int)
  if zzTmpZigZagPerIteration is not None: zzZigZagPerIteration = zzTmpZigZagPerIteration

  zzTmpIterations=ui.getUserInput('Iterations ({:d})'.format(zzIterations), int)
  if zzTmpIterations is not None: zzIterations = zzTmpIterations

  zzTmpSpacing=ui.getUserInput('Spacing ({:f})'.format(zzSpacing), float)
  if zzTmpSpacing is not None: zzSpacing = zzTmpSpacing

  zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
  zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter

  showZZParameters('FINAL parameters')

  ui.log("""
  Are you sure you want to start?
  (please write IAmSure if you want to go on)
  """ , k=_k, v='BASIC')

  password=input()
  if password != 'IAmSure':
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  rapid(z=zSafeHeight)

  currX = 0
  currY = 0
  currSpeed = zzInitialFeed

  for currIteration in range(zzIterations):
    currIterX = currX
    currIterY = currY

    # "Draw" the zig-zag pattern
    feed(z=zzPlunge*-1, speed=zzPlungeSpeed)

    for zigZag in range(zzZigZagPerIteration):
      # Up right
      currY += zzRise
      currX += zzRun
      feed(x=currX, y=currY, speed=currSpeed)

      # If run==0, we'll switch the zig-zag pattern for a straight line
      if zzRun:
        # Up left
        currY += zzRise
        currX -= zzRun
        feed(x=currX, y=currY, speed=currSpeed)

    # Raise the spindle
    rapid(z=zSafeHeight)

    # Move to the next start point
    if currIteration < (zzIterations-1):
      currX = currIterX + zzRun + zzSpacing
      currY = currIterY
      rapid(x=currX, y=currY)

    # Increase feed speed
    currSpeed += zzDeltaFeed

  ui.log("" , k=_k, v='BASIC')
  ui.log("************************" , k=_k, v='BASIC')
  ui.log("ZIG-ZAG PATTERN FINISHED", k=_k, v='BASIC')
  ui.log("************************" , k=_k, v='BASIC')
  ui.log("" , k=_k, v='BASIC')

  if testCancelled:
    testCancelled = False   # Make sure we always get back home

  # Raise the spindle
  rapid(z=zSafeHeight)

  ui.log("Back home..." , k=_k, v='BASIC')
  rapid(x=0, y=0)
  rapid(z=0)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def dummy():
  _k = 'test.dummy()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  global testCancelled

  ui.log("""
  WARNING !!!!!
  =============

  This is a DUMMY test, it can contain ANYTHING.
  Please read the code thoroughly before proceeding.

  Currently this test will:

  - Mill a configurable horizontal pocket (designed for making my holding clamps)
  - Add a tab in the center of each horizontal cut
  """ , k=_k, v='BASIC')

  def showParams(title):
    ui.log("""
    {:s}:
      MaterialZ             {:d}
      PocketWidth           {:f}
      PocketHeight          {:f}
      TabWidth              {:f}
      TabHeight             {:f}
      TargetZ               {:f}
      SafeHeight            {:d}
      Plunge                {:f}
      PlungeSpeed           {:d}
      Feed                  {:d}
      """.format(
        title,
        materialZ,
        pocketWidth,
        pocketHeight,
        tabWidth,
        tabHeight,
        targetZ,
        safeHeight,
        plunge,
        plungeSpeed,
        feed,
        ), k=_k, v='BASIC')

  def checkTestCancelled():
    global testCancelled
    if(kb.keyPressed()):
      key=kb.readKey()

      if( key == 27 ):  # <ESC>
        testCancelled = True

  def mchFeed(x=None, y=None, z=None, speed=None):
    if not testCancelled:
      mch.feedAbsolute(x=x, y=y, z=z, speed=speed)
      checkTestCancelled()

  def mchRapid(x=None, y=None, z=None):
    if not testCancelled:
      mch.rapidAbsolute(x=x, y=y, z=z)
      checkTestCancelled()

  # Check before trying with other materials!!

  materialZ = 10.5
  pocketWidth = 50.0
  pocketHeight = 6.5
  tabWidth = 6.0
  tabHeight = 0.5
  targetZ = 7.0
  safeHeight = materialZ + 5
  plunge = 1.0
  plungeSpeed = 100
  feed = 500

  showParams('Default parameters')

  tmpMaterialZ=ui.getUserInput('MaterialZ ({:d})'.format(materialZ), int)
  if tmpMaterialZ is not None: materialZ = tmpMaterialZ

  tmpPocketWidth=ui.getUserInput('PocketWidth ({:f})'.format(pocketWidth), float)
  if tmpPocketWidth is not None: pocketWidth = tmpPocketWidth

  tmpPocketHeight=ui.getUserInput('PocketHeight ({:f})'.format(pocketHeight), float)
  if tmpPocketHeight is not None: pocketHeight = tmpPocketHeight

  tmpTabWidth=ui.getUserInput('TabWidth ({:f})'.format(tabWidth), float)
  if tmpTabWidth is not None: tabWidth = tmpTabWidth

  tmpTabHeight=ui.getUserInput('TabHeight ({:f})'.format(tabHeight), float)
  if tmpTabHeight is not None: tabHeight = tmpTabHeight

  tmpTargetZ=ui.getUserInput('TargetZ ({:f})'.format(targetZ), float)
  if tmpTargetZ is not None: targetZ = tmpTargetZ

  safeHeight = materialZ + 5
  tmpSafeHeight=ui.getUserInput('SafeHeight ({:d})'.format(safeHeight), int)
  if tmpSafeHeight is not None: safeHeight = tmpSafeHeight

  tmpPlunge=ui.getUserInput('Plunge ({:f})'.format(plunge), float)
  if tmpPlunge is not None: plunge = tmpPlunge

  tmpPlungeSpeed=ui.getUserInput('PlungeSpeed ({:d})'.format(plungeSpeed), int)
  if tmpPlungeSpeed is not None: plungeSpeed = tmpPlungeSpeed

  tmpFeed=ui.getUserInput('Feed ({:d})'.format(feed), int)
  if tmpFeed is not None: feed = tmpFeed

  showParams('FINAL parameters')

  ui.log("""
  Are you sure you want to start?
  (please write IAmSure if you want to go on)
  """ , k=_k, v='BASIC')

  password=input()
  if password != 'IAmSure':
    ui.log("Test CANCELLED", k=_k, v='BASIC')
    return

  ui.log('---------------------------------[Safe initial position]', k=_k, v='BASIC')
  mchRapid(z=safeHeight)
  mchRapid(x=0, y=0)

  ui.log('', k=_k, v='BASIC')
  ui.log('Please start spindle and press <ENTER>...', k=_k, v='BASIC')
  input()

  currX = 0
  currY = 0
  currZ = materialZ - plunge
  if (currZ - plunge) < targetZ:
    currZ = targetZ

  tabStartX = (pocketWidth / 2) - (tabWidth / 2)
  tabEndX = tabStartX + tabWidth
  tabZ = targetZ + tabHeight

  finished = False
  while not finished:
    # Plunge
    ui.log('---------------------------------[Plunge][z={0}]'.format(currZ), k=_k, v='BASIC')
    mchFeed(z=currZ, speed=plungeSpeed)

    # Horizontal line DL-DR
    ui.log('---------------------------------[Horizontal line DL-DR][z={0}]'.format(currZ), k=_k, v='BASIC')
    if currZ == targetZ:
      mchFeed(x=tabStartX, speed=feed)
      ui.log('------------------------------------[tab:start]', k=_k, v='BASIC')
      mchFeed(z=tabZ, speed=plungeSpeed)
      mchFeed(x=tabEndX, speed=feed)
      mchFeed(z=currZ, speed=plungeSpeed)
      ui.log('------------------------------------[tab:end]', k=_k, v='BASIC')
      mchFeed(x=pocketWidth, speed=feed)
    else:
      mchFeed(x=pocketWidth, speed=feed)

    # Vertical line DR-UR
    ui.log('---------------------------------[Vertical line DR-UR][z={0}]'.format(currZ), k=_k, v='BASIC')
    mchFeed(y=pocketHeight, speed=feed)

    # Horizontal line UR-UL
    ui.log('---------------------------------[Horizontal line UR-UL][z={0}]'.format(currZ), k=_k, v='BASIC')
    if currZ == targetZ:
      mchFeed(x=tabEndX, speed=feed)
      ui.log('------------------------------------[tab:start]', k=_k, v='BASIC')
      mchFeed(z=tabZ, speed=plungeSpeed)
      mchFeed(x=tabStartX, speed=feed)
      mchFeed(z=currZ, speed=plungeSpeed)
      ui.log('------------------------------------[tab:end]', k=_k, v='BASIC')
      mchFeed(x=0, speed=feed)
    else:
      mchFeed(x=0, speed=feed)

    # Vertical line UL-DL
    ui.log('---------------------------------[Vertical line UL-DL][z={0}]'.format(currZ), k=_k, v='BASIC')
    mchFeed(y=0, speed=feed)

    # Next plunge calculation/check
    if currZ == targetZ:
      finished = True
    else:
      if (currZ - plunge) < targetZ:
        currZ = targetZ
      else:
        currZ -= plunge

  ui.log("" , k=_k, v='BASIC')
  ui.log("************************" , k=_k, v='BASIC')
  ui.log("DUMMY TEST FINISHED", k=_k, v='BASIC')
  ui.log("************************" , k=_k, v='BASIC')
  ui.log("" , k=_k, v='BASIC')

  if testCancelled:
    testCancelled = False   # Make sure we always get back home

  ui.log('---------------------------------[Back home]', k=_k, v='BASIC')

  # Raise the spindle
  mchRapid(z=safeHeight)

  mchRapid(x=0, y=0)
  # mchRapid(z=0)

