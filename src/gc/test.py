#!/usr/bin/python3
'''
grblCommander - test
=====================
Test code (useful macros)
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import sys
import time
import math

# ------------------------------------------------------------------
# Test class

class Test:

  def __init__(self, cfg, kb, ui, mch):
    ''' Construct a Test object.
    '''
    self.cfg = cfg
    self.kb = kb
    self.ui = ui
    self.mch = mch
    self.mchCfg = self.cfg['machine']
    self.tstCfg = self.cfg['test']
    self.mpos = self.mch.status['MPos']
    self.wpos = self.mch.status['WPos']

    self.testCancelled = False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getConfig(self):
    ''' Get working configuration
    '''
    return self.cfg


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sendCommand(self,cmd):
    ''' Send a move command to the grblShield (wait for machine idle)
    '''
    self.mch.sendWait(cmd)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def mchFeed(self,x=None, y=None, z=None, speed=None):
    ''' TODO: comment
    '''
    if not self.testCancelled:
      self.mch.feedAbsolute(x=x, y=y, z=z, speed=speed)
      self.checkTestCancelled()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def mchRapid(self,x=None, y=None, z=None):
    ''' TODO: comment
    '''
    if not self.testCancelled:
      self.mch.rapidAbsolute(x=x, y=y, z=z)
      self.checkTestCancelled()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestHeader(self,text):
    ''' TODO: comment
    '''
    self.ui.log('''
    WARNING !!!!!
    =============
    \n{:}

    Please read the code thoroughly before proceeding.
    '''.format(text.rstrip(' ').strip('\r\n')), c='ui.msg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestCancelled(self):
    ''' TODO: comment
    '''
    self.ui.logBlock('TEST CANCELLED', c='ui.cancelMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTestFinished(self):
    ''' TODO: comment
    '''
    self.ui.logBlock('TEST FINISHED', c='ui.finishedMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def checkTestCancelled(self):
    ''' TODO: comment
    '''
    if self.kb.keyPressed():
      if self.kb.getKey().n == 'ESC':
        self.testCancelled = True
        self.logTestCancelled()
    return self.testCancelled


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForSpindleStart(self):
    ''' TODO: comment
    '''
    self.ui.logTitle('Spindle start')

    self.ui.log()
    self.ui.inputMsg('''Please start spindle...
    (press <ENTER> or <ESC>)''')
    while True:
      while not self.kb.keyPressed():
        key = self.kb.getKey()
        if key.n == 'ENTER':
          return True
        elif key.n == 'ESC':
          self.testCancelled = True
          self.logTestCancelled()
          return False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def confirmStart(self,password=None):
    ''' TODO: comment
    '''
    if password is None:
      password = self.tstCfg['password']

    if self.ui.userConfirm('Are you sure you want to start?', password):
      return True
    else:
      self.testCancelled = True
      self.logTestCancelled()
      return False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def tablePositionScan(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader('''
    This test will move the spindle around a 3x3 grid representing the coordinates:
    [UL] [UC] [UR]
    [CL] [CC] [CR]
    [DL] [DC] [DR]
    ''')

    if not self.confirmStart():
      return

    def tpsSingleStep(stepName, x, y):
      if self.testCancelled:
        return

      self.ui.logTitle('Going to [{:}]'.format(stepName))
      self.mchRapid(x=x,y=y)

    maxX = self.mch.getMax('x')
    maxY = self.mch.getMax('y')
    savedX = self.wpos['x']
    savedY = self.wpos['y']

    tpsSingleStep('BL', x=0,y=0)
    tpsSingleStep('BC', x=maxX/2,y=0)
    tpsSingleStep('BR', x=maxX,y=0)
    tpsSingleStep('CR', x=maxX,y=maxY/2)
    tpsSingleStep('CC', x=maxX/2,y=maxY/2)
    tpsSingleStep('CL', x=0,y=maxY/2)
    tpsSingleStep('UL', x=0,y=maxY)
    tpsSingleStep('UC', x=maxX/2,y=maxY)
    tpsSingleStep('UR', x=maxX,y=maxY)

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    self.ui.logTitle('Back home')
    self.mchRapid(x=0, y=0)
    tpsSingleStep('Return', x=savedX,y=savedY)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def baseLevelingHoles(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader('''
    This test understands your 0,0 is set to the upper right corner
    of your machine, so it will send NEGATIVE COORDINATES.
    ''')

    if not self.confirmStart():
      return

    # - [X/Y steps]- - - - - - - - - - - - - - - - - -
    # XSteps = [0, 30, 60, 80, 100, 120, 140, 150, 170, 200, 220, 240, 260, 270]
    # YSteps = [0, 20, 40, 60, 80, 100, 130, 150, 170, 210, 230, 250, 270]
    XSteps = [0, 30, 60]
    YSteps = [0, 20, 40]

    # - [Internal helpers]- - - - - - - - - - - - - - - - - -
    def sendCmd(cmd):
      if not self.testCancelled:
        self.sendCommand(cmd)
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
    self.ui.logTitle('Safe initial position')
    goToSafeZ()
    self.ui.log()

    if not self.waitForSpindleStart():
      return

    self.ui.logTitle('Starting drill pattern')
    totalDrills = len(YSteps) * len(XSteps)

    for yIndex, y in enumerate(YSteps):
      xRange = XSteps if (yIndex % 2) == 0 else XSteps[::-1]
      for xIndex, x in enumerate(xRange):
        if not self.testCancelled:
          currDrill = (yIndex * len(YSteps)) + (xIndex+1)
          self.ui.logTitle('Rapid to next drill')
          goTo(x, y)
          self.ui.logTitle('Drilling @ X{:} Y{:} ({:}/{:})'.format(
            x, y,
            currDrill, totalDrills)
          )
          drill()

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    self.ui.logTitle('Back home')
    self.mchRapid(z=1.5)
    self.mchRapid(x=0, y=0)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def zigZagPattern(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader('''
    This test will start a series of zig-zag patterns
    using incremental feed speeds to determine
    optimal speed-feed for a given material.

    Based on:
    http://www.precisebits.com/tutorials/calibrating_feeds_n_speeds.htm
    ''')

    def showZZParameters(title):
      self.ui.log('''
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
        '''.format(
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

    startRow = self.ui.getUserInput('startRow (BASE 1!!!) ({:d})'.format(startRow), int, startRow)
    startCol = self.ui.getUserInput('startCol (BASE 1!!!) ({:d})'.format(startCol), int, startCol)
    # startY = self.ui.getUserInput('StartY ({:f})'.format(startY), float, startY)
    # startX = self.ui.getUserInput('StartX ({:f})'.format(startX), float, startX)
    startY = rows[startRow-1]
    startX = cols[startCol-1]

    materialTop = self.ui.getUserInput('MaterialTop ({:f})'.format(materialTop), float, materialTop)
    # bitDiameter = self.ui.getUserInput('Bit diameter (mm) ({:})'.format(bitDiameter), float, bitDiameter)
    # bitFlutes = self.ui.getUserInput('Number of flutes ({:})'.format(bitFlutes), int, bitFlutes)
    # bitRPM = self.ui.getUserInput('Spindle RPM ({:})'.format(bitRPM), int, bitRPM)

    safeWorkZ = materialTop + 3
    # safeTravelZ = self.ui.getUserInput('Z safe TRAVEL height (mm) ({:})'.format(safeTravelZ), float, safeTravelZ)
    # safeWorkZ = self.ui.getUserInput('Z safe WORK height (mm) ({:})'.format(safeWorkZ), float, safeWorkZ)
    # zzRun = self.ui.getUserInput('Run ({:f}) (0 for straight line)'.format(zzRun), float, zzRun)
    # zzRise = self.ui.getUserInput('Rise ({:f})'.format(zzRise), float, zzRise)
    zzPlunge = self.ui.getUserInput('Plunge ({:f})'.format(zzPlunge), float, zzPlunge)
    # zzPlungeSpeed = self.ui.getUserInput('PlungeSpeed ({:f})'.format(zzPlungeSpeed), float, zzPlungeSpeed)
    zzInitialFeed = self.ui.getUserInput('InitialFeed ({:f})'.format(zzInitialFeed), float, zzInitialFeed)
    zzDeltaFeed = self.ui.getUserInput('DeltaFeed ({:d})'.format(zzDeltaFeed), int, zzDeltaFeed)
    # zzZigZagPerIteration = self.ui.getUserInput('ZigZagPerIteration ({:d})'.format(zzZigZagPerIteration), int, zzZigZagPerIteration)
    zzIterations = self.ui.getUserInput('Iterations ({:d})'.format(zzIterations), int, zzIterations)
    # zzSpacing = self.ui.getUserInput('Spacing ({:f})'.format(zzSpacing), float, zzSpacing)

    zzTotalWidth = ((zzRun + zzSpacing) * zzIterations) - zzSpacing + bitDiameter
    zzTotalHeight = (zzRise * zzZigZagPerIteration * 2) + bitDiameter
    endX = startX + zzTotalWidth
    endY = startY + zzTotalHeight

    showZZParameters('FINAL parameters')

    if not self.confirmStart():
      return

    self.ui.logTitle('Safe initial position')
    self.mchRapid(z=safeTravelZ)
    self.mchRapid(x=0, y=0)
    self.ui.log()

    if not self.waitForSpindleStart():
      return

    self.ui.logTitle('Rapid to initial position')
    self.mchRapid(x=startX, y=startY)

    currX = startX
    currY = startY
    currFeed = zzInitialFeed

    for currIteration in range(zzIterations):
      if not self.testCancelled:
        self.ui.logTitle('Iteration {:}/{:} feed: {:}'.format(
          currIteration+1,
          zzIterations,
          currFeed)
        )

        currIterX = currX
        currIterY = currY

        # Plunge
        self.ui.logTitle('Rapid Z approach to material top')
        self.mchRapid(z=materialTop)

        self.ui.logTitle('Iteration {:}/{:} Plunge'.format(currIteration+1,zzIterations))
        self.mchFeed(z=(materialTop-zzPlunge), speed=zzPlungeSpeed)

        # 'Draw' the zig-zag patterns
        for zigZag in range(zzZigZagPerIteration):
          if not self.testCancelled:
            self.ui.logTitle('Iteration {:}/{:} ZigZag {:}/{:}'.format(
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
            self.ui.logTitle('Rapid to iteration {:}/{:}'.format(currIteration+2,zzIterations))
            self.mchRapid(z=safeWorkZ)

          if not self.testCancelled:
            if currIteration < (zzIterations-1):
              # currX = currIterX + zzRun + zzSpacing
              currX = currIterX + SAMPLE_ITEM_WIDTH
              currY = currIterY
              self.mchRapid(x=currX, y=currY)

            # Increase feed speed
            currFeed += zzDeltaFeed

    if self.testCancelled:
      self.testCancelled = False   # Make sure we always get back home
    else:
      self.logTestFinished()

    self.ui.logTitle('Back home')
    self.mchRapid(z=safeTravelZ)
    self.mchRapid(x=0, y=0)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def dummy(self):
    ''' TODO: comment
    '''
    self.testCancelled = False

    self.logTestHeader('''
    This is a DUMMY test, it can contain ANYTHING.
    Please read the code thoroughly before proceeding.

    Currently this test will:

    - Mill a configurable horizontal pocket (designed for making my holding clamps)
    - Add a tab in the center of each horizontal cut
    ''')

    def showParams(title):
      self.ui.log('''
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
        '''.format(
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

    startX = self.ui.getUserInput('StartX ({:f})'.format(startX), float, startX)
    startY = self.ui.getUserInput('StartY ({:f})'.format(startY), float, startY)
    materialTop = self.ui.getUserInput('MaterialTop ({:f})'.format(materialTop), float, materialTop)
    targetZ = self.ui.getUserInput('TargetZ ({:f})'.format(targetZ), float, targetZ)

    safeHeight = materialTop + 5
    safeHeight = self.ui.getUserInput('SafeHeight ({:f})'.format(safeHeight), float, safeHeight)
    pocketWidth = self.ui.getUserInput('PocketWidth ({:f})'.format(pocketWidth), float, pocketWidth)
    pocketHeight = self.ui.getUserInput('PocketHeight ({:f})'.format(pocketHeight), float, pocketHeight)
    tabWidth = self.ui.getUserInput('TabWidth ({:f})'.format(tabWidth), float, tabWidth)
    tabHeight = self.ui.getUserInput('TabHeight ({:f})'.format(tabHeight), float, tabHeight)
    plunge = self.ui.getUserInput('Plunge ({:f})'.format(plunge), float, plunge)
    plungeSpeed = self.ui.getUserInput('PlungeSpeed ({:d})'.format(plungeSpeed), int, plungeSpeed)
    feed = self.ui.getUserInput('Feed ({:d})'.format(feed), int, feed)

    if not tabWidth or not tabHeight:
      tabWidth = tabHeight = 0

    zPasses = math.ceil((materialTop - targetZ) / plunge)

    showParams('FINAL parameters')

    if not self.confirmStart():
      return

    self.ui.logTitle('Safe initial position')
    self.mchRapid(z=safeHeight)
    self.mchRapid(x=0, y=0)
    self.ui.log()

    if not self.waitForSpindleStart():
      return

    self.ui.logTitle('Rapid to initial position')
    self.mchRapid(x=startX, y=startY)

    self.ui.logTitle('Rapid Z approach to material top')
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
        self.ui.logTitle('Plunge Z{:} ({:}/{:})'.format(self.ui.coordStr(currZ), currZPass, zPasses))
        self.mchFeed(z=currZ, speed=plungeSpeed)

      # Horizontal line DL-DR
      if not self.testCancelled:
        self.ui.logTitle('Horizontal line DL-DR Z{:} ({:}/{:})'.format(self.ui.coordStr(currZ), currZPass, zPasses))
        if currZ < tabZ:
          self.mchFeed(x=tabStartX, speed=feed)
          self.ui.logTitle('tab:start')
          self.mchFeed(z=tabZ, speed=plungeSpeed)
          self.mchFeed(x=tabEndX, speed=feed)
          self.mchFeed(z=currZ, speed=plungeSpeed)
          self.ui.logTitle('tab:end')
          self.mchFeed(x=holeEndX, speed=feed)
        else:
          self.mchFeed(x=holeEndX, speed=feed)

      # Vertical line DR-UR
      if not self.testCancelled:
        self.ui.logTitle('Vertical line DR-UR Z{:} ({:}/{:})'.format(self.ui.coordStr(currZ), currZPass, zPasses))
        self.mchFeed(y=holeEndY, speed=feed)

      # Horizontal line UR-UL
      if not self.testCancelled:
        self.ui.logTitle('Horizontal line UR-UL Z{:} ({:}/{:})'.format(self.ui.coordStr(currZ), currZPass, zPasses))
        if currZ < tabZ:
          self.mchFeed(x=tabEndX, speed=feed)
          self.ui.logTitle('tab:start')
          self.mchFeed(z=tabZ, speed=plungeSpeed)
          self.mchFeed(x=tabStartX, speed=feed)
          self.mchFeed(z=currZ, speed=plungeSpeed)
          self.ui.logTitle('tab:end')
          self.mchFeed(x=holeStartX, speed=feed)
        else:
          self.mchFeed(x=holeStartX, speed=feed)

      # Vertical line UL-DL
      if not self.testCancelled:
        self.ui.logTitle('Vertical line UL-DL Z{:} ({:}/{:})'.format(self.ui.coordStr(currZ), currZPass, zPasses))
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

    self.ui.logTitle('Back home')
    self.mchRapid(z=safeHeight)
    self.mchRapid(x=0, y=0)

