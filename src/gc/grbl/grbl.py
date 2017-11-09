#!/usr/bin/python3
"""
grbl - grbl
===========
Main grbl class
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time

from .. import utils as ut
from .. import ui as ui
from .. import keyboard as kb
from .. import table as tbl

from . import serialport

# ------------------------------------------------------------------
# Grbl class

class Grbl:

  def __init__(self, cfg):
    ''' Construct a Grbl object.
    '''
    self.cfg = cfg
    self.spCfg = cfg['serial']
    self.mchCfg = cfg['machine']
    self.mcrCfg = cfg['macro']

    self.waitingStartup = True
    self.waitingResponse = False
    self.response = []
    self.waitingMachineStatus = False
    self.lastStatusStr = ''
    self.status = {}
    self.lastMessage = ''

    self.sp = serialport.SerialPort(cfg)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def start(self):
    ''' Start connection with grblShield
    '''
    self.sp.open()

    if self.sp.isOpen():
      ui.log('Serial port open, waiting for startup message...')
      ui.log()

      self.waitingStartup = True
      while self.waitingStartup:
        self.process()

      ui.log()
      ui.log('Startup message received, machine ready', color='ui.msg')
      ui.log()

      # Give some time for informational messages
      self.sleep(0.5)

      # else:
      #   ui.log('ERROR: startup message error, exiting program', color='ui.errorMsg', v='ERROR')
      #   quit()
    else:
      ui.log('ERROR opening serial port, exiting program', color='ui.errorMsg', v='ERROR')
      quit()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stop(self):
    ''' Stop connection with grblShield
    '''
    self.sp.close()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetConnection(self):
    ''' Reset connection with grblShield
    '''
    self.start()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sleep(self, seconds):
    ''' grbl-aware sleep
    '''
    startTime = time.time()

    while (time.time() - startTime) < seconds:
      self.process()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def process(self):
    ''' Call this method frequently to give Grbl some processing time
    '''
    line = self.sp.readline()
    self.parse(line)
    time.sleep(0.1)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parse(self, line):
    ''' Parse a text line
    '''
    if line:

      if self.waitingResponse:
        self.response.append(line)

      isResponse = False

      if self.waitingStartup:
        if line[:5] == 'Grbl ' and line[-15:] == " ['$' for help]":
          self.waitingStartup = False

      if line == 'ok':
        ui.log('<<<<< {:}'.format(line), color='comms.recv')
        isResponse = True
      elif line[:6] == "error:":
        ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v='ERROR')
        isResponse = True
      elif line[:1] == '>' and line[-3:] == ':ok':
        ui.log('<<<<< {:}'.format(line), color='comms.recv')
        line = line[:-3]
        isResponse = True
      elif line[:1] == '>' and line[-8:-1] == ':error:':
        ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v='ERROR')
        line = line[:-8]
        isResponse = True
      elif line[:1] == '>' and line[-9:-2] == ':error:':
        ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v='ERROR')
        line = line[:-9]
        isResponse = True
      else:
        ui.log('<<<<< {:}'.format(line), color='comms.recv')

      if isResponse:
        if self.waitingResponse:
          self.waitingResponse = False
        else:
          ui.log('UNEXPECTED MACHINE RESPONSE',c='red+',v='WARNING')

      # Status
      if line[:1] == '<' and line[-1:] == '>':
        self.lastStatusStr = line
        try:
          self.parseMachineStatus(self.lastStatusStr)
          # self.lastMachineStatusReceptionTimestamp
          if self.waitingMachineStatus:
            self.waitingMachineStatus = False
        except:
          ui.log("UNKNOWN machine data [{:}]".format(self.lastStatusStr), color='ui.errorMsg', v='ERROR')

      # Messages
      elif line[:5] == "[MSG:":
        self.lastMessage = line[5:-1]


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseMachineStatus(self,status):
    ''' TODO: Comment
    '''
    # Remove chevrons
    status = status[1:-1]

    # Split parameter groups
    params = status.split('|')

    # Status is always the first field
    self.status['machineState'] = params.pop(0)

    # Get the rest of fields
    while len(params):
      param = params.pop(0).split(':')
      paramName = param[0]
      paramValue = param[1]

      if paramName == 'MPos' or paramName == 'WPos' or paramName == 'WCO':
        coords = paramValue.split(',')
        x = float(coords[0])
        y = float(coords[1])
        z = float(coords[2])

        self.status[paramName] = {
          'x':x,
          'y':y,
          'z':z
        }

        if paramName == 'MPos':
          self.status[paramName]['desc'] = 'machinePos'
        elif paramName == 'WPos':
          self.status[paramName]['desc'] = 'workPos'
        elif paramName == 'WCO':
          self.status[paramName]['desc'] = 'workCoordinates'

      elif paramName == 'Bf':
        blocks = paramValue.split(',')
        planeBufferBlocks = int(blocks[0])
        serialRXBufferBlocks = int(blocks[1])
        self.status[paramName] = {
          'desc': 'buffer',
          'planeBufferBlocks': planeBufferBlocks,
          'serialRXBufferBlocks': serialRXBufferBlocks
        }

      elif paramName == 'Ln':
        self.status[paramName] = {
          'desc': 'lineNumber',
          'value': paramValue
        }

      elif paramName == 'F':
        self.status[paramName] = {
          'desc': 'feed',
          'value': int(paramValue)
        }

      elif paramName == 'FS':
        values = paramValue.split(',')
        feed = int(values[0])
        speed = int(values[1])

        self.status['F'] = {
          'desc': 'feed',
          'value': int(feed)
        }

        self.status['S'] = {
          'desc': 'speed',
          'value': int(speed)
        }

      elif paramName == 'Pn':
        self.status[paramName] = {
          'desc': 'inputPinState',
          'value': paramValue
        }

      elif paramName == 'Ov':
        values = paramValue.split(',')
        feed = values[0]
        rapid = values[1]
        speed = values[2]
        self.status[paramName] = {
          'desc': 'override',
          'feed': int(feed),
          'rapid': int(rapid),
          'speed': int(speed)
        }

      elif paramName == 'A':
        self.status[paramName] = {
          'desc': 'accesoryState',
          'value': paramValue
        }

      else:
        self.status[paramName] = {
          'desc': 'UNKNOWN',
          'value': paramValue
        }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachineStatus(self):
    ''' TODO: Comment
    '''
    ui.log('Querying machine status...', v='DEBUG')
    self.sp.write('?')
    self.waitingMachineStatus = True
    startTime = time.time()

    while( (time.time() - startTime) < self.spCfg['responseTimeout'] ):
      self.process()
      if not self.waitingMachineStatus:
        ui.log('Successfully received machine status', v='DEBUG')
        break
    else:
      self.lastStatusStr = ''
      ui.log('TIMEOUT Waiting for machine status', v='WARNING')

    return self.status


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sendCommand(self, command):
    ''' Send a command
    '''
    return self.sp.sendCommand(command)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSimpleMachineStatusStr(self):
    ''' TODO: comment
    '''
    return '[{:}] - MPos {:}'.format(
      self.getColoredMachineStateStr(),
      self.getMachinePosStr()
    )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getColoredMachineStateStr(self):
    ''' TODO: comment
    '''
    machineStateStr = self.status['machineState']
    return ui.setStrColor(machineStateStr, 'machineState.{:}'.format(machineStateStr))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachinePosStr(self):
    ''' TODO: comment
    '''
    mPos = self.status['MPos'] if 'MPos' in self.status else None

    if not mPos:
      return '<NONE>'

    return ui.xyzStr(
      mPos['x'],
      mPos['y'],
      mPos['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getWorkPosStr(self):
    ''' TODO: comment
    '''
    wPos = self.status['WPos'] if 'WPos' in self.status else None
    return ui.xyzStr(wPos['x'], wPos['y'], wPos['z']) if wPos else '<NONE>'


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSoftwarePosStr(self):
    ''' TODO: comment
    '''
    return ui.xyzStr(
      tbl.getX(),
      tbl.getY(),
      tbl.getZ())


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def refreshSoftwarePos(self):
    ''' TODO: comment
    '''
    tbl.setX(self.status['MPos']['x'])
    tbl.setY(self.status['MPos']['y'])
    tbl.setZ(self.status['MPos']['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForMachineIdle(self,verbose='WARNING'):
    ''' TODO: comment
    '''
    ui.log('Waiting for machine operation to finish...', v='SUPER')
    self.process()

    showStatus = ((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose)))

    # Valid states types: Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
    while self.status['machineState'] != 'Idle' and self.status['machineState'] != 'Check':
      if showStatus:
        ui.clearLine()
        coloredMachineStatusStr = ui.setStrColor(self.lastStatusStr, 'ui.onlineMachineStatus')
        ui.log('\r[{:}] {:}'.format(self.getColoredMachineStateStr(), coloredMachineStatusStr), end='')
      self.process()

    if showStatus:
      ui.clearLine()
      coloredMachineStatusStr = ui.setStrColor(self.lastStatusStr, 'ui.onlineMachineStatus')
      ui.log('\r[{:}] {:}'.format(self.getColoredMachineStateStr(), coloredMachineStatusStr), end='')

    ui.log(' - ', end='')
    # ui.log(getSoftwarePosStr(), v=verbose)

    ui.log('Machine operation finished', v='SUPER')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewBuildInfo(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting build info')
    ui.log('Sending command [$I]...', v='DETAIL')
    self.sendCommand('$I')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGCodeParserState(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting GCode parser state')
    ui.log('Sending command [$G]...', v='DETAIL')
    self.sendCommand('$G')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGCodeParameters(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting GCode parameters')
    ui.log('Sending command [$#]...', v='DETAIL')
    self.sendCommand('$#')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGrblConfig(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting grbl config')
    ui.log('Sending command [$$]...', v='DETAIL')
    self.sendCommand('$$')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewStartupBlocks(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting startup blocks')
    ui.log('Sending command [$N]...', v='DETAIL')
    self.sendCommand('$N')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def enableSleepMode(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting sleep mode enable')
    ui.log('Sending command [$SLP]...', v='DETAIL')
    self.sendCommand('$SLP')
    ui.log()
