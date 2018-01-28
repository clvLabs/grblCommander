#!/usr/bin/python3
'''
grbl - probe
============
grbl Probe class
'''

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
        - G38.3 + G38.5 @ 'feedSlow' speed
        - Z pulloff
        - Reset WCO
    '''
    self.mch.getMachineStatus()
    state = self.saveCurrentState()
    log = []

    result = self.probe('Stage 1', 'down', self.prbCfg['feedSlow'])
    if result['success']:
      log.append(result)
      result = self.probe('Stage 1', 'up', self.prbCfg['feedSlow'])
      if result['success']:
        log.append(result)
        self.pullOff(self.prbCfg['pulloff'])
        self.resetWCOZ()

    self.restoreState(state)

    if result['success']:
      self.showLogTitle()
      for item in log:
        self.showLogItem(item)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def twoStage(self):
    ''' Two stage probing cycle:
        - G38.3 + G38.5 @ 'feedMedium' speed
        - First Z pulloff ('interStagePulloff')
        - G38.3 + G38.5 @ 'feedSlow' speed
        - Z pulloff
        - Reset WCO
    '''
    self.mch.getMachineStatus()
    state = self.saveCurrentState()
    log = []

    # Stage 1 start
    result = self.probe('Stage 1', 'down', self.prbCfg['feedMedium'])
    if result['success']:
      log.append(result)
      result = self.probe('Stage 1', 'up', self.prbCfg['feedMedium'])
      if result['success']:
        log.append(result)
        self.pullOff(self.prbCfg['interStagePulloff'])
        # Stage 2 start
        result = self.probe('Stage 2', 'down', self.prbCfg['feedSlow'])
        if result['success']:
          log.append(result)
          result = self.probe('Stage 2', 'up', self.prbCfg['feedSlow'])
          if result['success']:
            log.append(result)
            self.pullOff(self.prbCfg['pulloff'])
            self.resetWCOZ()

    self.restoreState(state)

    if result['success']:
      self.showLogTitle()
      for item in log:
        self.showLogItem(item)



  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def threeStage(self):
    ''' Two stage probing cycle:
        - G38.3 + G38.5 @ 'feedFast' speed
        - First Z pulloff ('interStagePulloff')
        - G38.3 + G38.5 @ 'feedMedium' speed
        - First Z pulloff ('interStagePulloff')
        - G38.3 + G38.5 @ 'feedSlow' speed
        - Z pulloff
        - Reset WCO
    '''
    self.mch.getMachineStatus()
    state = self.saveCurrentState()
    log = []

    # Stage 1 start
    result = self.probe('Stage 1', 'down', self.prbCfg['feedFast'])
    if result['success']:
      log.append(result)
      result = self.probe('Stage 1', 'up', self.prbCfg['feedFast'])
      if result['success']:
        log.append(result)
        self.pullOff(self.prbCfg['interStagePulloff'])

        # Stage 2 start
        result = self.probe('Stage 2', 'down', self.prbCfg['feedMedium'])
        if result['success']:
          log.append(result)
          result = self.probe('Stage 2', 'up', self.prbCfg['feedMedium'])
          if result['success']:
            log.append(result)
            self.pullOff(self.prbCfg['interStagePulloff'])

            # Stage 3 start
            result = self.probe('Stage 3', 'down', self.prbCfg['feedSlow'])
            if result['success']:
              log.append(result)
              result = self.probe('Stage 3', 'up', self.prbCfg['feedSlow'])
              if result['success']:
                log.append(result)
                self.pullOff(self.prbCfg['pulloff'])
                self.resetWCOZ()

    self.restoreState(state)

    if result['success']:
      self.showLogTitle()
      for item in log:
        self.showLogItem(item)


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
  def probe(self, comment, direction, feed):
    ''' Moves the probe up or down to find the contact point
    '''
    result = {}

    if direction not in ['down', 'up']:
      ui.log('ERROR: probe.probe() : invalid direction [{:}]'.format(direction), c='ui.errorMsg')
      result['success'] = False
      return result

    down = True if direction == 'down' else False

    ui.logTitle('{:}: Probing {:} (feed {:})'.format(
      comment,
      direction,
      feed))

    probeContacting = self.mch.getProbeState()
    if (down and probeContacting):
      ui.log('The probe is contacting the plate before probing down. CANCELLING', c='ui.errorMsg')
      result['success'] = False
      return result
    elif (not down and not probeContacting):
      ui.log('The probe is NOT contacting the plate before probing up. CANCELLING', c='ui.errorMsg')
      result['success'] = False
      return result

    if down:
      cmd = 'G38.3Z{:}F{:}'.format(self.mch.getMin('z'), feed)
    else:
      cmd = 'G38.5Z{:}F{:}'.format(self.mch.getMax('z'), feed)

    self.mch.sendWait(cmd, responseTimeout=self.prbCfg['timeout'])

    result['comment'] = comment
    result['direction'] = direction
    result['feed'] = feed
    result['success'] = self.success

    if self.success:
      result['probeZ'] = self.axisPos('z')
      result['currZ'] = self.mch.status['MPos']['z']
      result['overshoot'] = result['probeZ']  - result['currZ']
      self.showLogTitle()
      self.showLogItem(result)

    return result


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def showLogTitle(self):
    ''' TODO: comment
    '''
    ui.log('Name     Dir  Feed   ProbeZ   StopZ  Overshoot', c='ui.successMsg')
    ui.log('-------- ---- ----   ------   ------ ----------', c='ui.successMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def showLogItem(self, item):
    ''' TODO: comment
    '''
    ui.log('{:8s} {:4s} {:4d} {:} {:} {:7.3f} {:}'.format(
      item['comment'],
      item['direction'],
      item['feed'],
      ui.coordStr(item['probeZ']),
      ui.coordStr(item['currZ']),
      item['overshoot'],
      self.mch.status['parserState']['units']['desc']
      ), c='ui.successMsg')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def pullOff(self, distance):
    ''' Pulls Z off by the specified distance
    '''
    if distance:
      ui.logTitle('Pulling off ({:} {:})'.format(distance, self.mch.status['parserState']['units']['desc']))
      self.mch.rapidRelative(z=distance)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetWCOZ(self):
    ''' Resets current WCO's Z to PRB:Z - <touchPlateHeight>
    '''
    ui.logTitle('Resetting WCO Z')
    touchPlateHeight = self.prbCfg['touchPlateHeight']
    probeZ = self.axisPos('z')
    newWCOZ = self.axisPos('z') - touchPlateHeight
    ui.log('Probe Z: {:}'.format(probeZ), c='ui.successMsg')
    ui.log('Touch plate height: {:}'.format(touchPlateHeight), c='ui.successMsg')
    ui.log('New Z0: {:}'.format(newWCOZ), c='ui.finishedMsg')
    self.mch.resetWCOAxis('z', newWCOZ)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def saveCurrentState(self):
    ''' Gets a few parameters to be restored after probing
    '''
    ui.logTitle('Saving current parser state')
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
    ui.logTitle('Restoring previous parser state')
    self.mch.sendWait(state['savedParserMotion'])
    self.mch.sendWait('F{:}'.format(state['savedFeed']))
