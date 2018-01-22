#!/usr/bin/python3
"""
grbl - probe
============
grbl Probe class
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time

from .. import ui as ui
from . import grbl

# ------------------------------------------------------------------
# Constants


# ------------------------------------------------------------------
# Probe class

class Probe:

  def __init__(self, mch):
    ''' Construct a Grbl object.
    '''
    self.mch = mch

    self.cfg = mch.cfg
    self.mchCfg = self.cfg['machine']
    self.uiCfg = self.cfg['ui']
    self.prbCfg = self.mchCfg['probing']

    self.mchSt = self.mch.status
    self.parserSt = self.mchSt['parserState']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def basic(self):
    ''' Basic probing cycle:
        - Send a G38.3 to find the touch plate
        - Retract with a G38.5
        - Z pulloff
        - Reset WCO
    '''
    self.mch.getMachineStatus()
    state = self.saveCurrentState()

    if self.probeDown(self.prbCfg['feed']):
      if self.probeUp(self.prbCfg['feed']):
        self.pullOff(self.prbCfg['pulloff'])
        self.resetWCOZ()

    self.restoreState(state)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def twoStage(self):
    ''' Two stage probing cycle:
        - G38.3 + G38.5 @ 'feed' speed
        - First Z pulloff ('interStagePulloff')
        - G38.3 + G38.5 @ 'feedStage2' speed
        - Z pulloff
        - Reset WCO
    '''
    self.mch.getMachineStatus()
    state = self.saveCurrentState()

    # Stage 1 start
    if self.probeDown(self.prbCfg['feed']):
      if self.probeUp(self.prbCfg['feed']):
        self.pullOff(self.prbCfg['interStagePulloff'])
        # Stage 2 start
        if self.probeDown(self.prbCfg['feedStage2']):
          if self.probeUp(self.prbCfg['feedStage2']):
            self.pullOff(self.prbCfg['pulloff'])
            self.resetWCOZ()

    self.restoreState(state)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def axisPos(self, axis):
    ''' Get probe coordinate
    '''
    return self.mchSt['GCodeParams']['PRB'][axis]


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def success(self, axis):
    ''' Get probe success
    '''
    return self.mchSt['GCodeParams']['PRB']['success']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def probeDown(self, feed):
    ''' Sends a G38.3 to find the touch plate
    '''
    ui.logTitle('Probing toward workpiece')

    if self.mch.getProbeState():
      ui.log('The probe is contacting the plate before probing down. CANCELLING', c='ui.errorMsg')
      return False

    cmd = 'G38.3Z{:}F{:}'.format(self.mch.getMin('z'), feed)
    self.mch.sendWait(cmd, responseTimeout=self.prbCfg['timeout'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def probeUp(self, feed):
    ''' Sends a G38.5 to detect last contact point while retracting
    '''
    ui.logTitle('Probing away from workpiece')

    if not self.mch.getProbeState():
      ui.log('The probe is NOT contacting the plate before probing up. CANCELLING', c='ui.errorMsg')
      return False

    cmd = 'G38.5Z{:}F{:}'.format(self.mch.getMax('z'), feed)
    self.mch.sendWait(cmd, responseTimeout=self.prbCfg['timeout'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def pullOff(self, distance):
    ''' Pulls Z off by the specified distance
    '''
    ui.logTitle('Pulling off ({:})'.format(distance))
    self.mch.rapidRelative(z=distance)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetWCOZ(self):
    ''' Resets current WCO's Z to PRB:Z - <touchPlateHeight>
    '''
    ui.logTitle('Resetting WCO Z')
    touchPlateHeight = self.prbCfg['touchPlateHeight']
    ui.log('- Touch plate height: {:}'.format(touchPlateHeight))
    newWCOZ = self.axisPos('z') - touchPlateHeight
    self.mch.resetWCoord('z', newWCOZ)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def saveCurrentState(self):
    ''' Gets a few parameters to be restored after probing
    '''
    ui.logTitle('Saving current motion mode (G0/G1/...) and feed')
    savedParserMotion = self.parserSt['motion']['val']
    savedFeed = self.parserSt['feed']['val']

    return {
      'savedParserMotion': savedParserMotion,
      'savedFeed': savedFeed,
    }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def restoreState(self, state):
    ''' Restores a few parameters after probing
    '''
    ui.logTitle('Restoring previous motion mode and feed')
    self.mch.sendWait(state['savedParserMotion'])
    self.mch.sendWait('F{:}'.format(state['savedFeed']))
