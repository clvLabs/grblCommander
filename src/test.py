#!/usr/bin/python3
"""
grblCommander - test
=====================
Test code (useful macros)
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import sys
import time
import math

from . import utils as ut
from . import ui as ui
from . import table as tbl
from . import machine as mch
from . import serialport as sp
from . import keyboard as kb
from src.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
mchCfg = cfg['machine']
tstCfg = cfg['test']

if not ut.isWindows():
  from . import rpigpio as gpio
  gpio.setup()

testCancelled = False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logTestHeader(text):
  ui.log("""
  WARNING !!!!!
  =============
  \n{:}

  Please read the code thoroughly before proceeding.
  """.format(text.rstrip(' ').strip('\r\n')), color='ui.msg')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logTestCancelled():
  ui.logBlock('TEST CANCELLED', color='ui.cancelMsg')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logTestFinished():
  ui.logBlock('TEST FINISHED', color='ui.finishedMsg')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def checkTestCancelled():
  global testCancelled
  if kb.keyPressed():
    if kb.readKey() == 27:  # <ESC>
      testCancelled = True
      logTestCancelled()
  return testCancelled

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def userConfirmTest(password=tstCfg['password']):
  while True:
    ui.log("""
    Are you sure you want to continue?
    (please enter '{:}' to confirm)
    """.format(password), color='ui.confirmMsg')

    ui.inputMsg('Enter confirmation text')
    typedPassword=input()

    if typedPassword == '':
      continue
    elif typedPassword == password:
      return True
    else:
      logTestCancelled()
      return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def mchFeed(x=None, y=None, z=None, speed=None):
  if not testCancelled:
    mch.feedAbsolute(x=x, y=y, z=z, speed=speed)
    checkTestCancelled()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def mchRapid(x=None, y=None, z=None):
  if not testCancelled:
    mch.rapidAbsolute(x=x, y=y, z=z)
    checkTestCancelled()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def automaticProbe(iterations = tstCfg['autoProbeIterations']):
  global testCancelled
  testCancelled = False

  ui.log('Saving original Z')
  savedZ = tbl.getZ()

  downStep = 0.1
  upStep = 0.01
  touchZList = []
  nextStartPoint = 0
  touchZ = 0

  ui.log('Starting automatic probe ({:d} iterations)...'.format(iterations))

  for curIteration in range(iterations):

    # Prepare Z position
    ui.log('Moving to Z to last known touch point +1 step to start test...')
    mch.feedAbsolute(z=nextStartPoint, speed=mchCfg['seekSpeed'])

    # Step down until contact
    exit = False
    z = tbl.getZ()

    ui.logTitle('Iteration {:d}'.format(curIteration+1))
    while(not exit and not testCancelled):
      ui.log('Seeking CONTACT point (Z={:})\r'.format(ui.coordStr(z)), end='')

      mch.feedAbsolute(z=z)

      if checkTestCancelled():
        break

      if gpio.isProbeContactActive():
        ui.log()
        exit = True
        touchZ = z
        nextStartPoint = touchZ+downStep
        break

      z -= downStep

    # Step up until contact lost
    if testCancelled:
      break
    else:
      exit = False
      lastZ = z

      while(not exit and not testCancelled):
        z += upStep
        ui.log('Seeking RELEASE point (Z={:})\r'.format(ui.coordStr(z)), end='')

        mch.feedAbsolute(z=z)

        if checkTestCancelled():
          break

        if not gpio.isProbeContactActive():
          ui.log()
          ui.log('TOUCH POINT @Z={:}'.format(ui.coordStr(lastZ)), color='ui.finishedMsg')
          exit = True
          touchZ = lastZ
          break

        lastZ = z

      touchZList.append(touchZ)

    ui.log('---------------------------------------')

  if testCancelled:
    return False

  ui.log('Restoring original Z...')
  mch.safeRapidAbsolute(z=savedZ)

  averageTouchZ = float(sum(touchZList))/len(touchZList) if len(touchZList) > 0 else 0

  minTouchZ = 9999
  for tz in touchZList:
    if tz < minTouchZ: minTouchZ = tz

  maxTouchZ = -9999
  for tz in touchZList:
    if tz > maxTouchZ: maxTouchZ = tz

  maxDevTouchZ = maxTouchZ - minTouchZ

  ui.log('RESULTS:')
  ui.log('--------')
  ui.log('- TOUCH POINTS @Z={:s}'.format(touchZList), color='ui.finishedMsg')
  ui.log('- Average={:} - Min={:} - Max={:} - MaxDev={:}'.format(
            ui.coordStr(averageTouchZ)
          , ui.coordStr(minTouchZ)
          , ui.coordStr(maxTouchZ)
          , ui.coordStr(maxDevTouchZ))
         )

  return {
    'z': averageTouchZ,
    'iter': iterations,
    'max': maxTouchZ,
    'min': minTouchZ,
    'dev': maxDevTouchZ,
  }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def manualProbe():
  global testCancelled
  testCancelled = False

  ui.log('Saving original Z')
  savedZ = tbl.getZ()
  ui.log('Moving to Z0 to start test...')
  mch.safeRapidAbsolute(z=0)

  ui.log('Starting manual probe...')

  # 0.1 step down until contact
  exit = False
  touchZ = 0
  z = tbl.getZ()

  while not exit and not testCancelled:
    z -= 0.1
    ui.log('Seeking CONTACT point (Z={:})\r'.format(ui.coordStr(z)), end='')

    mch.feedAbsolute(z=z)

    ui.inputMsg('<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...')
    key=0
    while( key != 13 and key != 10 and key != 32 and key != 27 ):
      key=kb.readKey()

    if key == 27:  # <ESC>
      testCancelled = True
      logTestCancelled()
      break
    elif key == 13 or key == 10:  # <ENTER>
      ui.log('Stopping at Z={:}'.format(ui.coordStr(z)))
      exit = True
      touchZ = z
      break
    elif key == 32:  # <SPACE>
      pass

    if exit or testCancelled:
      break

  # 0.025 step up until contact lost
  if not testCancelled:
    exit = False
    lastZ = z

    while not exit and not testCancelled:
      z += 0.025
      ui.log('Seeking RELEASE point (Z={:})\r'.format(ui.coordStr(z)), end='')

      mch.feedAbsolute(z=z)

      ui.log('PHASE2 : Seeking RELEASE point')
      ui.inputMsg('<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...')
      key=0
      while( key != 13 and key != 10 and key != 32 and key != 27 ):
        key=kb.readKey()

      if key == 27:  # <ESC>
        testCancelled = True
        logTestCancelled()
        break
      elif key == 13 or key == 10:  # <ENTER>
        ui.log('TOUCH POINT @Z={:}'.format(ui.coordStr(lastZ)), color='ui.finishedMsg')
        exit = True
        touchZ = lastZ
        break
      elif key == 32:  # <SPACE>
        pass

      if exit or testCancelled:
        break

      lastZ = z

  if testCancelled:
    return False

  ui.log('Restoring original Z...')
  mch.safeRapidAbsolute(z=savedZ)

  return {
    'z': touchZ,
    'iter': 1,
    'max': touchZ,
    'min': touchZ,
    'dev': 0,
  }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def pointProbe():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This test will start a probing test to check a measuring attachment
  or verify base level.

  On Linux, it will try to do an automatic probe test (check gpio config)
  On Windows, it will try to do a manual probe test
  """)

  if not ut.isWindows():
    iterations=ui.getUserInput('Number of auto probing iterations ({:})'.format(tstCfg['autoProbeIterations']),
      int, tstCfg['autoProbeIterations'])

  if not userConfirmTest():
    return

  if ut.isWindows():
    manualProbe()
  else:
    automaticProbe(iterations)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def tableProbingScan():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This test will start a series of probing tests
  in a grid pattern to get a grid of level measurements
  and save them on a file for further analysis.
  """)

  userLines=ui.getUserInput('Number of inner lines (0)', int, 0)

  if not userConfirmTest():
    return

  gridLines = int(userLines) + 2

  result = [[None for i in range(gridLines)] for j in range(gridLines)]

  ui.log('Saving original XYZ')
  savedX, savedY, savedZ = tbl.getX(), tbl.getY(), tbl.getZ()

  if tbl.getZ() < tbl.getSafeHeight():
    ui.log('Temporarily moving to safe Z...')
    mch.rapidAbsolute(z=tbl.getSafeHeight())

  gridIncrementX = tbl.getMaxX() / (gridLines-1)
  gridIncrementY = tbl.getMaxY() / (gridLines-1)

  gridX = [gridIncrementX * pos for pos in range(gridLines)]
  gridY = [gridIncrementY * pos for pos in range(gridLines)]

  ui.log('tbl.getMaxX() = [:]'.format(ui.coordStr(tbl.getMaxX())), v='DEBUG')
  ui.log('tbl.getMaxY() = [:]'.format(ui.coordStr(tbl.getMaxY())), v='DEBUG')
  ui.log('gridIncrementX = [:]'.format(ui.coordStr(gridIncrementX)), v='DEBUG')
  ui.log('gridIncrementY = [:]'.format(ui.coordStr(gridIncrementY)), v='DEBUG')
  ui.log('gridX = [:s]'.format(repr(gridX)), v='DEBUG')
  ui.log('gridY = [:s]'.format(repr(gridY)), v='DEBUG')

  ui.log(  'Starting test ({:d}*{:d} lines / {:d} points)...'.format(
            gridLines
          , gridLines
          , gridLines*gridLines )
        )

  curGridPoint = 0

  rangeY = range(len(gridY))

  for indexY in rangeY:
    if indexY % 2 == 0:
      rangeX = range(len(gridX))
    else:
      rangeX = range(len(gridX)-1,-1,-1)

    for indexX in rangeX:
      ui.logTitle('Testing[{:d}][{:d}] Y={:} X={:} ({:d}/{:d})'.format(
        indexY
      , indexX
      , ui.coordStr(gridY[indexY])
      , ui.coordStr(gridX[indexX])
      , curGridPoint+1
      , gridLines*gridLines ) )

      ui.log('mch.rapidAbsolute(Y={:} X={:})...'.format(
          ui.coordStr(gridY[indexY]),
          ui.coordStr(gridX[indexX])
        ), v='DEBUG')
      mch.rapidAbsolute(y=gridY[indexY], x=gridX[indexX])

      if checkTestCancelled():
        break

      curGridPoint+=1

      # Make a probe
      if ut.isWindows():
        testResult = manualProbe()
      else:
        testResult = automaticProbe()

      if testResult is False:
        testCancelled = True
        break

      result[indexY][indexX] = { 'X':gridX[indexX], 'Y':gridY[indexY], 'Z':testResult['z'], 'Zmaz':testResult['max'], 'Zmin':testResult['min'], 'Zdev':testResult['dev'] }

    if testCancelled:
      break

  saveTestResults = not testCancelled

  if testCancelled:
    testCancelled = False
  else:
    logTestFinished()

  ui.logTitle('Back home')
  ui.log('Temporarily moving to safe Z...')
  mch.rapidAbsolute(z=tbl.getSafeHeight())
  ui.log('Restoring original XYZ...')
  mch.safeRapidAbsolute(x=savedX, y=savedY)
  mch.safeRapidAbsolute(z=savedZ)

  if not saveTestResults:
    return

  # Test results - normal
  ui.logBlock('Test tesults (normalized)')

  rangeY = range(len(gridY))
  rangeX = range(len(gridX))

  for indexY in rangeY:
    for indexX in rangeX:
      if result[indexY][indexX] is None:
        ui.log(  'Y[{:02d}][{:07.3f}] X[{:02d}][{:07.3f}] Z[ERROR]'.format(
                  indexY
                , 0.0
                , indexX
                , 0.0 )
              )
      else:
        ui.log(  'Y[{:02d}][{:07.3f}] X[{:02d}][{:07.3f}] Z[{:07.3f}]-dev[{:07.3f}]'.format(
                  indexY
                , result[indexY][indexX]['Y']
                , indexX
                , result[indexY][indexX]['X']
                , (result[indexY][indexX]['Z'] - result[0][0]['Z'])
                , result[indexY][indexX]['Zdev'] )
              )


  # Test results - Excel formatted
  # Create output file
  t=time.localtime()
  fileName =  'logs/TableProbingScan {:d}{:02d}{:02d}{:02d}{:02d}{:02d}.txt'.format(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec)
  outFile = open(fileName, 'w')

  outFile.write(' grblCommander Table Probing Scan \n')
  outFile.write('=================================\n')
  outFile.write('\n')
  outFile.write('TimeStamp: {:d}/{:02d}/{:02d} {:02d}:{:02d}:{:02d}\n'.format(t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec) )
  outFile.write('\n')
  outFile.write(
  """  Software config:
    RapidIncrement_XY = {:.2f}
    RapidIncrement_Z  = {:.2f}
    TableSize%        = {:d}%
  """.format(tbl.getRI_XY(), tbl.getRI_Z(), tbl.getTableSizePercent()) )
  outFile.write('\n')

  outFile.write('Test results (real Z):\n')
  outFile.write('----------------------\n')
  outFile.write('\n')

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = '{:07.3f}\t'.format(result[indexY][0]['Y'])

    for indexX in rangeX:
      if result[indexY][indexX] is None:
        line += 'ERROR\t'
      else:
        line += '{:07.3f}\t'.format(result[indexY][indexX]['Z'])

    outFile.write(line.rstrip('\t')+'\n')

  line = '\t'

  for indexX in rangeX:
    line += '{:07.3f}\t'.format(result[0][indexX]['X'])

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write('\n')


  outFile.write('Test results (normalized Z):\n')
  outFile.write('----------------------------\n')
  outFile.write('\n')

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = '{:07.3f}\t'.format(result[indexY][0]['Y'])

    for indexX in rangeX:
      if result[indexY][indexX] is None:
        line += 'ERROR\t'
      else:
        line += '{:07.3f}\t'.format((result[indexY][indexX]['Z'] - result[0][0]['Z']))

    outFile.write(line.rstrip('\t')+'\n')

  line = '\t'

  for indexX in rangeX:
    line += '{:07.3f}\t'.format(result[0][indexX]['X'])

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write('\n')


  outFile.write('Test results (Z deviations):\n')
  outFile.write('----------------------------\n')
  outFile.write('\n')

  rangeY = range(len(gridY)-1,-1,-1)
  rangeX = range(len(gridX))

  for indexY in rangeY:
    line = '{:07.3f}\t'.format(result[indexY][0]['Y'])

    for indexX in rangeX:
      if result[indexY][indexX] is None:
        line += 'ERROR\t'
      else:
        line += '{:07.3f}\t'.format((result[0][0]['Zdev'],))

    outFile.write(line.rstrip('\t')+'\n')

  line = '\t'

  for indexX in rangeX:
    line += '{:07.3f}\t'.format(result[0][indexX]['X'])

  outFile.write(line.rstrip('\t')+'\n')
  outFile.write('\n')

  outFile.close()

  ui.logBlock('Excel version saved to {:s}'.format(fileName))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def tablePositionScan():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This test will move the spindle around a 3x3 grid representing the coordinates:
  [UL] [UC] [UR]
  [CL] [CC] [CR]
  [DL] [DC] [DR]
  """)

  if not userConfirmTest():
    return

  def tpsSingleStep(stepName, x, y):
    if testCancelled:
      return

    ui.logTitle('Going to [{:}]'.format(stepName))
    mch.safeRapidAbsolute(x=x,y=y)
    checkTestCancelled()

  savedX = tbl.getX()
  savedY = tbl.getY()

  tpsSingleStep('BL', x=0,y=0)
  tpsSingleStep('BC', x=tbl.getMaxX()/2,y=0)
  tpsSingleStep('BR', x=tbl.getMaxX(),y=0)
  tpsSingleStep('CR', x=tbl.getMaxX(),y=tbl.getMaxY()/2)
  tpsSingleStep('CC', x=tbl.getMaxX()/2,y=tbl.getMaxY()/2)
  tpsSingleStep('CL', x=0,y=tbl.getMaxY()/2)
  tpsSingleStep('UL', x=0,y=tbl.getMaxY())
  tpsSingleStep('UC', x=tbl.getMaxX()/2,y=tbl.getMaxY())
  tpsSingleStep('UR', x=tbl.getMaxX(),y=tbl.getMaxY())

  if testCancelled:
    testCancelled = False   # Make sure we always get back home
  else:
    logTestFinished()

  ui.logTitle('Back home')
  mchRapid(x=0, y=0)
  tpsSingleStep('Return', x=savedX,y=savedY)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def baseLevelingHoles():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This test understands your 0,0 is set to the upper right corner
  of your machine, so it will send NEGATIVE COORDINATES.
  """)

  if not userConfirmTest():
    return

  # - [X/Y steps]- - - - - - - - - - - - - - - - - -
  XSteps = [0, -30, -60, -80, -100, -120, -140, -150, -170, -200, -220, -240, -260, -280]
  YSteps = [0, -20, -40, -60, -80, -100, -130, -150, -170, -210, -230, -250, -280]

  # - [Internal helpers]- - - - - - - - - - - - - - - - - -
  def sendCmd(cmd):
    if testCancelled:
      return

    sp.sendCommand(cmd)
    mch.waitForMachineIdle()

    checkTestCancelled()

  def goTo(x, y):
    sendCmd('G0 X{0} Y{1}'.format(x, y))

  def goToSafeZ():
    sendCmd('G0 Z3')

  def drill():
    sendCmd('G0 Z1.5')
    sendCmd('G1 Z0')
    goToSafeZ()

  # - [Main process]- - - - - - - - - - - - - - - - - -
  ui.logTitle('Safe initial position')
  goToSafeZ()
  ui.log()

  ui.logTitle('Spindle start')
  ui.log()
  ui.inputMsg('Please start spindle and press <ENTER>...')
  input()

  ui.logTitle('Starting drill pattern')
  totalDrills = len(YSteps) * len(XSteps)

  for yIndex, y in enumerate(YSteps):
    xRange = XSteps if (yIndex % 2) == 0 else XSteps[::-1]
    for xIndex, x in enumerate(xRange):
      if not testCancelled:
        currDrill = (yIndex * len(YSteps)) + (xIndex+1)
        ui.logTitle('Rapid to next drill')
        goTo(x, y)
        ui.logTitle('Drilling @ X{:} Y{:} ({:}/{:})'.format(
          x, y,
          currDrill, totalDrills)
        )
        drill()

  if testCancelled:
    testCancelled = False   # Make sure we always get back home
  else:
    logTestFinished()

  ui.logTitle('Back home')
  mchRapid(z=1.5)
  mchRapid(x=0, y=0)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def zigZagPattern():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This test will start a series of zig-zag patterns
  using incremental feed speeds to determine
  optimal speed-feed for a given material.

  Based on:
  http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm
  """)

  def showZZParameters(title):
    ui.log("""
    {:s}:
      BitDiameter           {:f}
      BitFlutes             {:d}
      BitRPM                {:d}
      ZSafeHeight           {:f}
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
        bitDiameter,
        bitFlutes,
        bitRPM,
        zSafeHeight,
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
        ))

  # zig-zag default parameter calculations
  # NOTE: Using parameters for softwoods!!
  # Check before trying with other materials!!

  bitDiameter = 3
  bitFlutes = 2
  bitRPM = 12000
  zSafeHeight = 3
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

  bitDiameter=ui.getUserInput('Bit diameter (mm) ({:})'.format(bitDiameter), float, bitDiameter)
  bitFlutes=ui.getUserInput('Number of flutes ({:})'.format(bitFlutes), int, bitFlutes)
  bitRPM=ui.getUserInput('Spindle RPM ({:})'.format(bitRPM), int, bitRPM)
  zSafeHeight=ui.getUserInput('Z safe height (mm) ({:})'.format(zSafeHeight), float, zSafeHeight)
  zzRun=ui.getUserInput('Run ({:f}) (0 for straight line)'.format(zzRun), float, zzRun)
  zzRise=ui.getUserInput('Rise ({:f})'.format(zzRise), float, zzRise)
  zzPlunge=ui.getUserInput('Plunge ({:f})'.format(zzPlunge), float, zzPlunge)
  zzPlungeSpeed=ui.getUserInput('PlungeSpeed ({:f})'.format(zzPlungeSpeed), float, zzPlungeSpeed)
  zzInitialFeed=ui.getUserInput('InitialFeed ({:f})'.format(zzInitialFeed), float, zzInitialFeed)
  zzDeltaFeed=ui.getUserInput('DeltaFeed ({:d})'.format(zzDeltaFeed), int, zzDeltaFeed)
  zzZigZagPerIteration=ui.getUserInput('ZigZagPerIteration ({:d})'.format(zzZigZagPerIteration), int, zzZigZagPerIteration)
  zzIterations=ui.getUserInput('Iterations ({:d})'.format(zzIterations), int, zzIterations)
  zzSpacing=ui.getUserInput('Spacing ({:f})'.format(zzSpacing), float, zzSpacing)

  zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
  zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter

  showZZParameters('FINAL parameters')

  if not userConfirmTest():
    return

  ui.logTitle('Safe initial position')
  mchRapid(z=zSafeHeight)
  mchRapid(x=0, y=0)
  ui.log()

  ui.logTitle('Spindle start')
  ui.log()
  ui.inputMsg('Please start spindle and press <ENTER>...')
  input()

  currX = 0
  currY = 0
  currFeed = zzInitialFeed

  for currIteration in range(zzIterations):
    if not testCancelled:
      ui.logTitle('Iteration {:}/{:} feed: {:}'.format(
        currIteration+1,
        zzIterations,
        currFeed)
      )

      currIterX = currX
      currIterY = currY

      # Plunge
      ui.logTitle('Iteration {:}/{:} Plunge'.format(currIteration+1,zzIterations))
      mchFeed(z=zzPlunge*-1, speed=zzPlungeSpeed)

      # "Draw" the zig-zag patterns
      for zigZag in range(zzZigZagPerIteration):
        if not testCancelled:
          ui.logTitle('Iteration {:}/{:} ZigZag {:}/{:}'.format(
            currIteration+1,
            zzIterations,
            zigZag+1,
            zzZigZagPerIteration)
          )

          # Up right
          if not testCancelled:
            currY += zzRise
            currX += zzRun
            mchFeed(x=currX, y=currY, speed=currFeed)

          # If run==0, we'll switch the zig-zag pattern for a straight line
          if not testCancelled:
            if zzRun:
              # Up left
              currY += zzRise
              currX -= zzRun
              mchFeed(x=currX, y=currY, speed=currFeed)

      # Move to the next start point (if there's a next one)
      if currIteration+1 < zzIterations:
        if not testCancelled:
          ui.logTitle('Rapid to iteration {:}/{:}'.format(currIteration+2,zzIterations))
          mchRapid(z=zSafeHeight)

        if not testCancelled:
          if currIteration < (zzIterations-1):
            currX = currIterX + zzRun + zzSpacing
            currY = currIterY
            mchRapid(x=currX, y=currY)

          # Increase feed speed
          currFeed += zzDeltaFeed

  if testCancelled:
    testCancelled = False   # Make sure we always get back home
  else:
    logTestFinished()

  ui.logTitle('Back home')
  mchRapid(z=zSafeHeight)
  mchRapid(x=0, y=0)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def dummy():
  global testCancelled
  testCancelled = False

  logTestHeader("""
  This is a DUMMY test, it can contain ANYTHING.
  Please read the code thoroughly before proceeding.

  Currently this test will:

  - Mill a configurable horizontal pocket (designed for making my holding clamps)
  - Add a tab in the center of each horizontal cut
  """)

  def showParams(title):
    ui.log("""
    {:s}:
      MaterialZ             {:f}
      PocketWidth           {:f}
      PocketHeight          {:f}
      TabWidth              {:f}
      TabHeight             {:f}
      TargetZ               {:f}
      SafeHeight            {:f}
      Plunge                {:f}
      PlungeSpeed           {:d}
      Feed                  {:d}

      TOTAL
        ZPasses             {:d}
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
        zPasses,
        ))

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

  zPasses = math.ceil((materialZ - targetZ) / plunge)

  showParams('Default parameters')

  materialZ=ui.getUserInput('MaterialZ ({:f})'.format(materialZ), float, materialZ)
  pocketWidth=ui.getUserInput('PocketWidth ({:f})'.format(pocketWidth), float, pocketWidth)
  pocketHeight=ui.getUserInput('PocketHeight ({:f})'.format(pocketHeight), float, pocketHeight)
  tabWidth=ui.getUserInput('TabWidth ({:f})'.format(tabWidth), float, tabWidth)
  tabHeight=ui.getUserInput('TabHeight ({:f})'.format(tabHeight), float, tabHeight)
  targetZ=ui.getUserInput('TargetZ ({:f})'.format(targetZ), float, targetZ)

  safeHeight = materialZ + 5
  safeHeight=ui.getUserInput('SafeHeight ({:f})'.format(safeHeight), float, safeHeight)
  plunge=ui.getUserInput('Plunge ({:f})'.format(plunge), float, plunge)
  plungeSpeed=ui.getUserInput('PlungeSpeed ({:d})'.format(plungeSpeed), int, plungeSpeed)
  feed=ui.getUserInput('Feed ({:d})'.format(feed), int, feed)

  zPasses = math.ceil((materialZ - targetZ) / plunge)

  showParams('FINAL parameters')

  if not userConfirmTest():
    return

  ui.logTitle('Safe initial position')
  mchRapid(z=safeHeight)
  mchRapid(x=0, y=0)
  ui.log()

  ui.logTitle('Spindle start')
  ui.log()
  ui.inputMsg('Please start spindle and press <ENTER>...')
  input()

  currX = 0
  currY = 0
  currZ = materialZ - plunge
  if currZ < targetZ:
    currZ = targetZ

  currZPass = 0

  tabStartX = (pocketWidth / 2) - (tabWidth / 2)
  tabEndX = tabStartX + tabWidth
  tabZ = targetZ + tabHeight

  finished = False
  while not finished and not testCancelled:
    currZPass += 1

    # Plunge
    if not testCancelled:
      ui.logTitle('Plunge Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
      mchFeed(z=currZ, speed=plungeSpeed)

    # Horizontal line DL-DR
    if not testCancelled:
      ui.logTitle('Horizontal line DL-DR Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
      if currZ == targetZ:
        mchFeed(x=tabStartX, speed=feed)
        ui.logTitle('tab:start')
        mchFeed(z=tabZ, speed=plungeSpeed)
        mchFeed(x=tabEndX, speed=feed)
        mchFeed(z=currZ, speed=plungeSpeed)
        ui.logTitle('tab:end')
        mchFeed(x=pocketWidth, speed=feed)
      else:
        mchFeed(x=pocketWidth, speed=feed)

    # Vertical line DR-UR
    if not testCancelled:
      ui.logTitle('Vertical line DR-UR Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
      mchFeed(y=pocketHeight, speed=feed)

    # Horizontal line UR-UL
    if not testCancelled:
      ui.logTitle('Horizontal line UR-UL Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
      if currZ == targetZ:
        mchFeed(x=tabEndX, speed=feed)
        ui.logTitle('tab:start')
        mchFeed(z=tabZ, speed=plungeSpeed)
        mchFeed(x=tabStartX, speed=feed)
        mchFeed(z=currZ, speed=plungeSpeed)
        ui.logTitle('tab:end')
        mchFeed(x=0, speed=feed)
      else:
        mchFeed(x=0, speed=feed)

    # Vertical line UL-DL
    if not testCancelled:
      ui.logTitle('Vertical line UL-DL Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
      mchFeed(y=0, speed=feed)

    # Next plunge calculation/check
    if not testCancelled:
      if currZ == targetZ:
        finished = True
      else:
        if (currZ - plunge) < targetZ:
          currZ = targetZ
        else:
          currZ -= plunge

  if testCancelled:
    testCancelled = False   # Make sure we always get back home
  else:
    logTestFinished()

  ui.logTitle('Back home')
  mchRapid(z=safeHeight)
  mchRapid(x=0, y=0)
