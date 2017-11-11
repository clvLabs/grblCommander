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

from . import ui as ui
from . import keyboard as kb

# ------------------------------------------------------------------
if not 'win' in sys.platform:
  from . import rpigpio as gpio
  gpio.setup()

# ------------------------------------------------------------------
# Test class

class Test:

  def __init__(self, grbl):
    ''' Construct a Test object.
    '''
    self.grbl = grbl
    self.cfg = self.grbl.getConfig()
    self.mchCfg = self.cfg['machine']
    self.tstCfg = self.cfg['test']

    self.testCancelled = False

    # Table limits
    self.maxX = self.mchCfg['max']['X']
    self.maxY = self.mchCfg['max']['Y']
    self.maxZ = self.mchCfg['max']['Z']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getConfig(self):
    ''' Get working configuration
    '''
    return self.cfg


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestHeader(self,text):
    ''' TODO: comment
    '''
    ui.log("""
    WARNING !!!!!
    =============
    \n{:}

    Please read the code thoroughly before proceeding.
    """.format(text.rstrip(' ').strip('\r\n')), color='ui.msg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestCancelled(self):
    ''' TODO: comment
    '''
    ui.logBlock('TEST CANCELLED', color='ui.cancelMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestFinished(self):
    ''' TODO: comment
    '''
    ui.logBlock('TEST FINISHED', color='ui.finishedMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def checkTestCancelled(self):
    ''' TODO: comment
    '''
    if kb.keyPressed():
      if kb.readKey() == 27:  # <ESC>
        self.testCancelled = True
        self.logTestCancelled()
    return self.testCancelled


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def userConfirm(self,password=None):
    ''' TODO: comment
    '''
    if password is None:
      password = self.tstCfg['password']

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
        self.logTestCancelled()
        return False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def mchFeed(self,x=None, y=None, z=None, speed=None):
    ''' TODO: comment
    '''
    if not self.testCancelled:
      self.grbl.feedAbsolute(x=x, y=y, z=z, speed=speed)
      self.checkTestCancelled()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def mchRapid(self,x=None, y=None, z=None):
    ''' TODO: comment
    '''
    if not self.testCancelled:
      self.grbl.rapidAbsolute(x=x, y=y, z=z)
      self.checkTestCancelled()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def automaticProbe(self,iterations=None):
    ''' TODO: comment
    '''
    if iterations is None:
      iterations = tstCfg['autoProbeIterations']

    self.testCancelled = False

    ui.log('Saving original Z')
    savedZ = self.grbl.status['WPos']['z']

    downStep = 0.1
    upStep = 0.01
    touchZList = []
    nextStartPoint = 0
    touchZ = 0

    ui.log('Starting automatic probe ({:d} iterations)...'.format(iterations))

    for curIteration in range(iterations):

      # Prepare Z position
      ui.log('Moving to Z to last known touch point +1 step to start test...')
      self.grbl.feedAbsolute(z=nextStartPoint, speed=self.mchCfg['seekSpeed'])

      # Step down until contact
      exit = False
      z = self.grbl.status['WPos']['z']

      ui.logTitle('Iteration {:d}'.format(curIteration+1))
      while not exit and not self.testCancelled:
        ui.log('Seeking CONTACT point (Z={:})\r'.format(ui.coordStr(z)), end='')

        self.grbl.feedAbsolute(z=z)

        if self.checkTestCancelled():
          break

        if gpio.isProbeContactActive():
          ui.log()
          exit = True
          touchZ = z
          nextStartPoint = touchZ+downStep
          break

        z -= downStep

      # Step up until contact lost
      if self.testCancelled:
        break
      else:
        exit = False
        lastZ = z

        while not exit and not self.testCancelled:
          z += upStep
          ui.log('Seeking RELEASE point (Z={:})\r'.format(ui.coordStr(z)), end='')

          self.grbl.feedAbsolute(z=z)

          if self.checkTestCancelled():
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

    if self.testCancelled:
      return False

    ui.log('Restoring original Z...')
    self.grbl.rapidAbsolute(z=savedZ)

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
    ui.log('- TOUCH POINTS @Z={:}'.format(touchZList), color='ui.finishedMsg')
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
  def manualProbe(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    ui.log('Saving original Z')
    savedZ = self.grbl.status['WPos']['z']
    ui.log('Moving to Z0 to start test...')
    self.grbl.rapidAbsolute(z=0)

    ui.log('Starting manual probe...')

    # 0.1 step down until contact
    exit = False
    touchZ = 0
    z = self.grbl.status['WPos']['z']

    while not exit and not self.testCancelled:
      z -= 0.1
      ui.log('Seeking CONTACT point (Z={:})\r'.format(ui.coordStr(z)), end='')

      self.grbl.feedAbsolute(z=z)

      ui.inputMsg('<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...')
      key=0
      while key != 13 and key != 10 and key != 32 and key != 27:
        key=kb.readKey()

      if key == 27:  # <ESC>
        self.testCancelled = True
        self.logTestCancelled()
        break
      elif key == 13 or key == 10:  # <ENTER>
        ui.log('Stopping at Z={:}'.format(ui.coordStr(z)))
        exit = True
        touchZ = z
        break
      elif key == 32:  # <SPACE>
        pass

      if exit or self.testCancelled:
        break

    # 0.025 step up until contact lost
    if not self.testCancelled:
      exit = False
      lastZ = z

      while not exit and not self.testCancelled:
        z += 0.025
        ui.log('Seeking RELEASE point (Z={:})\r'.format(ui.coordStr(z)), end='')

        self.grbl.feedAbsolute(z=z)

        ui.log('PHASE2 : Seeking RELEASE point')
        ui.inputMsg('<ENTER>:stop / <SPACE>:continue / <ESC>:exit ...')
        key=0
        while key != 13 and key != 10 and key != 32 and key != 27:
          key=kb.readKey()

        if key == 27:  # <ESC>
          self.testCancelled = True
          self.logTestCancelled()
          break
        elif key == 13 or key == 10:  # <ENTER>
          ui.log('TOUCH POINT @Z={:}'.format(ui.coordStr(lastZ)), color='ui.finishedMsg')
          exit = True
          touchZ = lastZ
          break
        elif key == 32:  # <SPACE>
          pass

        if exit or self.testCancelled:
          break

        lastZ = z

    if self.testCancelled:
      return False

    ui.log('Restoring original Z...')
    self.grbl.rapidAbsolute(z=savedZ)

    return {
      'z': touchZ,
      'iter': 1,
      'max': touchZ,
      'min': touchZ,
      'dev': 0,
    }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def pointProbe(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This test will start a probing test to check a measuring attachment
    or verify base level.

    On Linux, it will try to do an automatic probe test (check gpio config)
    On Windows, it will try to do a manual probe test
    """)

    if not 'win' in sys.platform:
      iterations=ui.getUserInput('Number of auto probing iterations ({:})'.format(self.tstCfg['autoProbeIterations']),
        int, self.tstCfg['autoProbeIterations'])

    if not self.userConfirm():
      return

    if 'win' in sys.platform:
      self.manualProbe()
    else:
      self.automaticProbe(iterations)

    if self.testCancelled:
      self.testCancelled = False
    else:
      self.logTestFinished()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def tableProbingScan(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This test will start a series of probing tests
    in a grid pattern to get a grid of level measurements
    and save them on a file for further analysis.
    """)

    userLines=ui.getUserInput('Number of inner lines (0)', int, 0)
    safeHeight=ui.getUserInput('Safe height (0)', float, 0)

    if not self.userConfirm():
      return

    gridLines = int(userLines) + 2

    result = [[None for i in range(gridLines)] for j in range(gridLines)]

    ui.log('Saving original XYZ')
    savedX, savedY, savedZ = self.grbl.status['WPos']['x'], self.grbl.status['WPos']['y'], self.grbl.status['WPos']['z']

    if self.grbl.status['WPos']['z'] < safeHeight:
      ui.log('Temporarily moving to safe Z...')
      self.grbl.rapidAbsolute(z=safeHeight)

    gridIncrementX = self.maxX / (gridLines-1)
    gridIncrementY = self.maxY / (gridLines-1)

    gridX = [gridIncrementX * pos for pos in range(gridLines)]
    gridY = [gridIncrementY * pos for pos in range(gridLines)]

    ui.log('self.maxX = [:]'.format(ui.coordStr(self.maxX)), v='DEBUG')
    ui.log('self.maxY = [:]'.format(ui.coordStr(self.maxY)), v='DEBUG')
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

        ui.log('self.grbl.rapidAbsolute(Y={:} X={:})...'.format(
            ui.coordStr(gridY[indexY]),
            ui.coordStr(gridX[indexX])
          ), v='DEBUG')
        self.grbl.rapidAbsolute(y=gridY[indexY], x=gridX[indexX])

        if self.checkTestCancelled():
          break

        curGridPoint+=1

        # Make a probe
        if 'win' in sys.platform:
          testResult = self.manualProbe()
        else:
          testResult = self.automaticProbe()

        if testResult is False:
          self.testCancelled = True
          break

        result[indexY][indexX] = { 'X':gridX[indexX], 'Y':gridY[indexY], 'Z':testResult['z'], 'Zmaz':testResult['max'], 'Zmin':testResult['min'], 'Zdev':testResult['dev'] }

      if self.testCancelled:
        break

    saveTestResults = not self.testCancelled

    if self.testCancelled:
      self.testCancelled = False
    else:
      self.logTestFinished()

    ui.logTitle('Back home')
    ui.log('Temporarily moving to safe Z...')
    self.grbl.rapidAbsolute(z=safeHeight)
    ui.log('Restoring original XYZ...')
    self.grbl.rapidAbsolute(x=savedX, y=savedY)
    self.grbl.rapidAbsolute(z=savedZ)

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
  def tablePositionScan(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This test will move the spindle around a 3x3 grid representing the coordinates:
    [UL] [UC] [UR]
    [CL] [CC] [CR]
    [DL] [DC] [DR]
    """)

    if not self.userConfirm():
      return

    def tpsSingleStep(stepName, x, y):
      if self.testCancelled:
        return

      ui.logTitle('Going to [{:}]'.format(stepName))
      self.grbl.rapidAbsolute(x=x,y=y)
      self.checkTestCancelled()

    savedX = self.grbl.status['WPos']['x']
    savedY = self.grbl.status['WPos']['y']

    tpsSingleStep('BL', x=0,y=0)
    tpsSingleStep('BC', x=self.maxX/2,y=0)
    tpsSingleStep('BR', x=self.maxX,y=0)
    tpsSingleStep('CR', x=self.maxX,y=self.maxY/2)
    tpsSingleStep('CC', x=self.maxX/2,y=self.maxY/2)
    tpsSingleStep('CL', x=0,y=self.maxY/2)
    tpsSingleStep('UL', x=0,y=self.maxY)
    tpsSingleStep('UC', x=self.maxX/2,y=self.maxY)
    tpsSingleStep('UR', x=self.maxX,y=self.maxY)

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    ui.logTitle('Back home')
    self.mchRapid(x=0, y=0)
    tpsSingleStep('Return', x=savedX,y=savedY)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def baseLevelingHoles(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This test understands your 0,0 is set to the upper right corner
    of your machine, so it will send NEGATIVE COORDINATES.
    """)

    if not self.userConfirm():
      return

    # - [X/Y steps]- - - - - - - - - - - - - - - - - -
    # XSteps = [0, 30, 60, 80, 100, 120, 140, 150, 170, 200, 220, 240, 260, 270]
    # YSteps = [0, 20, 40, 60, 80, 100, 130, 150, 170, 210, 230, 250, 270]
    XSteps = [0, 30, 60]
    YSteps = [0, 20, 40]

    # - [Internal helpers]- - - - - - - - - - - - - - - - - -
    def sendCmd(cmd):
      if self.testCancelled:
        return

      self.grbl.sendCommand(cmd)
      self.grbl.waitForMachineIdle()

      self.checkTestCancelled()

    def goTo(x, y):
      sendCmd('G0 X{:} Y{:}'.format(x, y))

    def goToSafeZ():
      sendCmd('G0 Z3')

    def drill():
      sendCmd('G0 Z1.5')
      sendCmd('G1 Z0 F200')
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
        if not self.testCancelled:
          currDrill = (yIndex * len(YSteps)) + (xIndex+1)
          ui.logTitle('Rapid to next drill')
          goTo(x, y)
          ui.logTitle('Drilling @ X{:} Y{:} ({:}/{:})'.format(
            x, y,
            currDrill, totalDrills)
          )
          drill()

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    ui.logTitle('Back home')
    self.mchRapid(z=1.5)
    self.mchRapid(x=0, y=0)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def zigZagPattern(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This test will start a series of zig-zag patterns
    using incremental feed speeds to determine
    optimal speed-feed for a given material.

    Based on:
    http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm
    """)

    def showZZParameters(title):
      ui.log("""
      {:s}:
        startRow              {:d}
        startCol              {:d}
        startY                {:f}
        startX                {:f}
        materialTop           {:f}
        bitDiameter           {:f}
        bitFlutes             {:d}
        bitRPM                {:d}
        safeTravelZ           {:f}
        safeWorkZ             {:f}
        zzRun                 {:f}
        zzRise                {:f}
        zzPlunge              {:f}
        zzPlungeSpeed         {:f}
        zzInitialFeed         {:f}
        zzDeltaFeed           {:d}
        zzZigZagPerIteration  {:d}
        zzIterations          {:d}
        zzSpacing             {:f}

        TOTAL
          Height              {:f}
          Width               {:f}
          EndY                {:f}
          EndX                {:f}
        """.format(
          title,
          startRow,
          startCol,
          startY,
          startX,
          materialTop,
          bitDiameter,
          bitFlutes,
          bitRPM,
          safeTravelZ,
          safeWorkZ,
          zzRun,
          zzRise,
          zzPlunge,
          zzPlungeSpeed,
          zzInitialFeed,
          zzDeltaFeed,
          zzZigZagPerIteration,
          zzIterations,
          zzSpacing,

          zzTotalHeight,
          zzTotalWidth,
          endY,
          endX,
          ))

    # zig-zag default parameter calculations
    # NOTE: Using parameters for softwoods!!
    # Check before trying with other materials!!

    # DEFINE THESE FOR CURRENT WASTEBOARD ======
    startOffsetY = 0
    startOffsetX = 0
    # ==========================================

    rows = []
    cols = []

    SAMPLE_ITEM_HEIGHT = 20
    SAMPLE_ITEM_WIDTH = 31.35

    for i in range(10):
      rows.append(startOffsetY + (i*SAMPLE_ITEM_HEIGHT))
      cols.append(startOffsetX + (i*SAMPLE_ITEM_WIDTH))

    startRow = 1
    startCol = 1
    startY = rows[startRow-1]
    startX = cols[startCol-1]
    bitDiameter = 3.175
    # materialTop = 10.1
    materialTop = 0
    bitFlutes = 2
    bitRPM = 12000
    safeTravelZ = 30
    safeWorkZ = materialTop + 3
    zzRun = 25 if bitDiameter < 3.18 else 50
    zzRise = bitDiameter * 2
    # zzPlunge = bitDiameter
    zzPlunge = 0.1
    zzPlungeSpeed = 100
    # zzInitialFeed = 0.02 * bitDiameter * bitFlutes * bitRPM
    zzInitialFeed = 100
    # zzDeltaFeed = 125 if bitDiameter < 0.8 else 200 if bitDiameter < 3.0 else 250
    zzDeltaFeed = 50
    zzZigZagPerIteration = 1
    zzIterations = 1
    zzSpacing = bitDiameter * 2

    zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter
    zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
    endY = startY + zzTotalHeight
    endX = startX + zzTotalWidth

    showZZParameters('Calculated parameters')

    startRow=ui.getUserInput('startRow (BASE 1!!!) ({:d})'.format(startRow), int, startRow)
    startCol=ui.getUserInput('startCol (BASE 1!!!) ({:d})'.format(startCol), int, startCol)
    # startY=ui.getUserInput('StartY ({:f})'.format(startY), float, startY)
    # startX=ui.getUserInput('StartX ({:f})'.format(startX), float, startX)
    startY = rows[startRow-1]
    startX = cols[startCol-1]

    materialTop=ui.getUserInput('MaterialTop ({:f})'.format(materialTop), float, materialTop)
    # bitDiameter=ui.getUserInput('Bit diameter (mm) ({:})'.format(bitDiameter), float, bitDiameter)
    # bitFlutes=ui.getUserInput('Number of flutes ({:})'.format(bitFlutes), int, bitFlutes)
    # bitRPM=ui.getUserInput('Spindle RPM ({:})'.format(bitRPM), int, bitRPM)

    safeWorkZ = materialTop + 3
    # safeTravelZ=ui.getUserInput('Z safe TRAVEL height (mm) ({:})'.format(safeTravelZ), float, safeTravelZ)
    # safeWorkZ=ui.getUserInput('Z safe WORK height (mm) ({:})'.format(safeWorkZ), float, safeWorkZ)
    # zzRun=ui.getUserInput('Run ({:f}) (0 for straight line)'.format(zzRun), float, zzRun)
    # zzRise=ui.getUserInput('Rise ({:f})'.format(zzRise), float, zzRise)
    zzPlunge=ui.getUserInput('Plunge ({:f})'.format(zzPlunge), float, zzPlunge)
    # zzPlungeSpeed=ui.getUserInput('PlungeSpeed ({:f})'.format(zzPlungeSpeed), float, zzPlungeSpeed)
    zzInitialFeed=ui.getUserInput('InitialFeed ({:f})'.format(zzInitialFeed), float, zzInitialFeed)
    zzDeltaFeed=ui.getUserInput('DeltaFeed ({:d})'.format(zzDeltaFeed), int, zzDeltaFeed)
    # zzZigZagPerIteration=ui.getUserInput('ZigZagPerIteration ({:d})'.format(zzZigZagPerIteration), int, zzZigZagPerIteration)
    zzIterations=ui.getUserInput('Iterations ({:d})'.format(zzIterations), int, zzIterations)
    # zzSpacing=ui.getUserInput('Spacing ({:f})'.format(zzSpacing), float, zzSpacing)

    zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
    zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter
    endX = startX + zzTotalWidth
    endY = startY + zzTotalHeight

    showZZParameters('FINAL parameters')

    if not self.userConfirm():
      return

    ui.logTitle('Safe initial position')
    self.mchRapid(z=safeTravelZ)
    self.mchRapid(x=0, y=0)
    ui.log()

    ui.logTitle('Spindle start')
    ui.log()
    ui.inputMsg('Please start spindle and press <ENTER>...')
    input()

    ui.logTitle('Rapid to initial position')
    self.mchRapid(x=startX, y=startY)

    currX = startX
    currY = startY
    currFeed = zzInitialFeed

    for currIteration in range(zzIterations):
      if not self.testCancelled:
        ui.logTitle('Iteration {:}/{:} feed: {:}'.format(
          currIteration+1,
          zzIterations,
          currFeed)
        )

        currIterX = currX
        currIterY = currY

        # Plunge
        ui.logTitle('Rapid Z approach to material top')
        self.mchRapid(z=materialTop)

        ui.logTitle('Iteration {:}/{:} Plunge'.format(currIteration+1,zzIterations))
        self.mchFeed(z=(materialTop-zzPlunge), speed=zzPlungeSpeed)

        # "Draw" the zig-zag patterns
        for zigZag in range(zzZigZagPerIteration):
          if not self.testCancelled:
            ui.logTitle('Iteration {:}/{:} ZigZag {:}/{:}'.format(
              currIteration+1,
              zzIterations,
              zigZag+1,
              zzZigZagPerIteration)
            )

            # Up right
            if not self.testCancelled:
              currY += zzRise
              currX += zzRun
              self.mchFeed(x=currX, y=currY, speed=currFeed)

            # If run==0, we'll switch the zig-zag pattern for a straight line
            if not self.testCancelled:
              if zzRun:
                # Up left
                currY += zzRise
                currX -= zzRun
                self.mchFeed(x=currX, y=currY, speed=currFeed)

        # Move to the next start point (if there's a next one)
        if currIteration+1 < zzIterations:
          if not self.testCancelled:
            ui.logTitle('Rapid to iteration {:}/{:}'.format(currIteration+2,zzIterations))
            self.mchRapid(z=safeWorkZ)

          if not self.testCancelled:
            if currIteration < (zzIterations-1):
              currX = currIterX + zzRun + zzSpacing
              currX = currIterX + SAMPLE_ITEM_WIDTH
              currY = currIterY
              self.mchRapid(x=currX, y=currY)

            # Increase feed speed
            currFeed += zzDeltaFeed

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    ui.logTitle('Back home')
    self.mchRapid(z=safeTravelZ)
    self.mchRapid(x=0, y=0)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def dummy(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader("""
    This is a DUMMY test, it can contain ANYTHING.
    Please read the code thoroughly before proceeding.

    Currently this test will:

    - Mill a configurable horizontal pocket (designed for making my holding clamps)
    - Add a tab in the center of each horizontal cut
    """)

    def showParams(title):
      ui.log("""
      {:s}:
        StartX                {:f}
        StartY                {:f}
        MaterialTop           {:f}
        TargetZ               {:f}
        SafeHeight            {:f}
        PocketWidth           {:f}
        PocketHeight          {:f}
        TabWidth              {:f}
        TabHeight             {:f}
        Plunge                {:f}
        PlungeSpeed           {:d}
        Feed                  {:d}

        TOTAL
          ZPasses             {:d}
        """.format(
          title,
          startX,
          startY,
          materialTop,
          targetZ,
          safeHeight,
          pocketWidth,
          pocketHeight,
          tabWidth,
          tabHeight,
          plunge,
          plungeSpeed,
          feed,
          zPasses,
          ))

    # Check before trying with other materials!!
    startX = 0
    startY = 0
    materialTop = 13.4
    targetZ = 0.4
    safeHeight = materialTop + 5
    pocketWidth = 50.0
    pocketHeight = 3.2
    tabWidth = 6.0
    tabHeight = 0.0
    plunge = 1.0
    plungeSpeed = 100
    feed = 400

    if not tabWidth or not tabHeight:
      tabWidth = tabHeight = 0

    zPasses = math.ceil((materialTop - targetZ) / plunge)

    showParams('Default parameters')

    startX=ui.getUserInput('StartX ({:f})'.format(startX), float, startX)
    startY=ui.getUserInput('StartY ({:f})'.format(startY), float, startY)
    materialTop=ui.getUserInput('MaterialTop ({:f})'.format(materialTop), float, materialTop)
    targetZ=ui.getUserInput('TargetZ ({:f})'.format(targetZ), float, targetZ)

    safeHeight = materialTop + 5
    safeHeight=ui.getUserInput('SafeHeight ({:f})'.format(safeHeight), float, safeHeight)
    pocketWidth=ui.getUserInput('PocketWidth ({:f})'.format(pocketWidth), float, pocketWidth)
    pocketHeight=ui.getUserInput('PocketHeight ({:f})'.format(pocketHeight), float, pocketHeight)
    tabWidth=ui.getUserInput('TabWidth ({:f})'.format(tabWidth), float, tabWidth)
    tabHeight=ui.getUserInput('TabHeight ({:f})'.format(tabHeight), float, tabHeight)
    plunge=ui.getUserInput('Plunge ({:f})'.format(plunge), float, plunge)
    plungeSpeed=ui.getUserInput('PlungeSpeed ({:d})'.format(plungeSpeed), int, plungeSpeed)
    feed=ui.getUserInput('Feed ({:d})'.format(feed), int, feed)

    if not tabWidth or not tabHeight:
      tabWidth = tabHeight = 0

    zPasses = math.ceil((materialTop - targetZ) / plunge)

    showParams('FINAL parameters')

    if not self.userConfirm():
      return

    ui.logTitle('Safe initial position')
    self.mchRapid(z=safeHeight)
    self.mchRapid(x=0, y=0)
    ui.log()

    ui.logTitle('Spindle start')
    ui.log()
    ui.inputMsg('Please start spindle and press <ENTER>...')
    input()

    ui.logTitle('Rapid to initial position')
    self.mchRapid(x=startX, y=startY)

    ui.logTitle('Rapid Z approach to material top')
    self.mchRapid(z=materialTop)

    currZ = materialTop - plunge
    if currZ < targetZ:
      currZ = targetZ

    currZPass = 0

    holeStartX = startX
    holeEndX = holeStartX + pocketWidth
    holeStartY = startY
    holeEndY = holeStartY + pocketHeight

    tabStartX = holeStartX + (pocketWidth / 2) - (tabWidth / 2)
    tabEndX = tabStartX + tabWidth
    tabZ = targetZ + tabHeight

    finished = False
    while not finished and not self.testCancelled:
      currZPass += 1

      # Plunge
      if not self.testCancelled:
        ui.logTitle('Plunge Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
        self.mchFeed(z=currZ, speed=plungeSpeed)

      # Horizontal line DL-DR
      if not self.testCancelled:
        ui.logTitle('Horizontal line DL-DR Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
        if currZ < tabZ:
          self.mchFeed(x=tabStartX, speed=feed)
          ui.logTitle('tab:start')
          self.mchFeed(z=tabZ, speed=plungeSpeed)
          self.mchFeed(x=tabEndX, speed=feed)
          self.mchFeed(z=currZ, speed=plungeSpeed)
          ui.logTitle('tab:end')
          self.mchFeed(x=holeEndX, speed=feed)
        else:
          self.mchFeed(x=holeEndX, speed=feed)

      # Vertical line DR-UR
      if not self.testCancelled:
        ui.logTitle('Vertical line DR-UR Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
        self.mchFeed(y=holeEndY, speed=feed)

      # Horizontal line UR-UL
      if not self.testCancelled:
        ui.logTitle('Horizontal line UR-UL Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
        if currZ < tabZ:
          self.mchFeed(x=tabEndX, speed=feed)
          ui.logTitle('tab:start')
          self.mchFeed(z=tabZ, speed=plungeSpeed)
          self.mchFeed(x=tabStartX, speed=feed)
          self.mchFeed(z=currZ, speed=plungeSpeed)
          ui.logTitle('tab:end')
          self.mchFeed(x=holeStartX, speed=feed)
        else:
          self.mchFeed(x=holeStartX, speed=feed)

      # Vertical line UL-DL
      if not self.testCancelled:
        ui.logTitle('Vertical line UL-DL Z{:} ({:}/{:})'.format(ui.coordStr(currZ), currZPass, zPasses))
        self.mchFeed(y=holeStartY, speed=feed)

      # Next plunge calculation/check
      if not self.testCancelled:
        if currZ == targetZ:
          finished = True
        else:
          if (currZ - plunge) < targetZ:
            currZ = targetZ
          else:
            currZ -= plunge

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    ui.logTitle('Back home')
    self.mchRapid(z=safeHeight)
    self.mchRapid(x=0, y=0)

