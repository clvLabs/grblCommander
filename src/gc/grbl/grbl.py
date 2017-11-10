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
from . import dict


# ------------------------------------------------------------------
# Constants
CTRL_X = 24

STATUSQUERY_INTERVAL = 5
PROCESS_SLEEP = 0.2
WAITRESPONSE_SLEEP = 0.2


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
    self.lastStatusQuery = 0
    self.statusQuerySent = False
    self.waitingMachineStatus = False
    self.lastStatusStr = ''
    self.lastMessage = ''
    self.alarm = ''
    self.status = {
      'settings': {}
    }

    self.sp = serialport.SerialPort(cfg)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def start(self):
    ''' Start connection with grblShield
    '''
    self.sp.open()

    if self.sp.isOpen():
      ui.log('Serial port open.', color='ui.successMsg')
      ui.log()

      self.waitForStartup()
      self.viewBuildInfo()
      self.viewGrblConfig()
      self.viewGCodeParserState()

      # else:
      #   ui.log('ERROR: startup message error, exiting program', color='ui.errorMsg', v='ERROR')
      #   quit()
    else:
      ui.log('ERROR opening serial port, exiting program', color='ui.errorMsg', v='ERROR')
      quit()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForStartup(self):
    ''' Wait for grblShield startup
    '''
    ui.log('Waiting for startup message...')
    self.alarm = ''
    self.waitingStartup = True
    while self.waitingStartup:
      self.sleep(WAITRESPONSE_SLEEP)

    ui.log('Startup message received, machine ready', color='ui.successMsg')
    ui.log()


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
  def softReset(self):
    ''' grblShield soft reset
    '''
    self.sp.write('%c' % CTRL_X)
    self.waitForStartup()


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

    # Read all available serial lines
    line = self.sp.readline()
    while line:
      self.parse(line)
      line = self.sp.readline()

    # Manage alarm state
    if self.alarm:
      if self.waitingResponse:
        self.waitingResponse = False
      if self.waitingMachineStatus:
        self.waitingMachineStatus = False

    # Automatic periodic status queries
    sendQuery = False

    if self.waitingMachineStatus and not self.statusQuerySent:
      sendQuery = True

    if (time.time() - self.lastStatusQuery) > STATUSQUERY_INTERVAL:
      sendQuery = True

    if sendQuery:
      self.queryMachineStatus()

    # Give some time for the processor to do other stuff
    time.sleep(PROCESS_SLEEP)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parse(self, line):
    ''' Parse a text line
    '''
    if line:

      if self.waitingResponse:
        self.response.append(line)

      showLine = True
      isResponse = False
      isStatus = False
      isAlarm = False
      errorCode = ''

      if self.waitingStartup:
        if line[:5] == 'Grbl ' and line[-15:] == " ['$' for help]":
          self.waitingStartup = False

      if line == 'ok':
        isResponse = True
      elif line[:6] == "error:":
        errorCode = line[6:]
        isResponse = True
      elif line[:6] == "ALARM:":
        self.alarm = line[6:]
        self.status['machineState'] = 'Alarm'
        isAlarm = True
        isResponse = True
      elif line[:1] == '>' and line[-3:] == ':ok':
        line = line[:-3]
        isResponse = True
      elif line[:1] == '>' and line[-8:-1] == ':error:':
        line = line[:-8]
        isResponse = True
      elif line[:1] == '>' and line[-9:-2] == ':error:':
        line = line[:-9]
        isResponse = True

      if isResponse:
        if self.waitingResponse:
          self.waitingResponse = False
        else:
          ui.log('[WARNING] Unexpected machine response',c='ui.msg',v='DETAIL')

      # Status
      if line[:1] == '<' and line[-1:] == '>':
        self.lastStatusStr = line
        isStatus = True
        showLine = False
        try:
          self.parseMachineStatus(self.lastStatusStr)
          # self.lastMachineStatusReceptionTimestamp
          if self.waitingMachineStatus:
            self.waitingMachineStatus = False
            self.statusQuerySent = False
        except:
          ui.log("UNKNOWN machine data [{:}]".format(self.lastStatusStr), color='ui.errorMsg', v='ERROR')

      # Messages
      elif line[:5] == "[MSG:":
        self.lastMessage = line[5:-1]

      # User-defined startup line
      elif line[:2] == "$N":
        pass

      # Settings
      elif line[:1] == "$":
        components = line[1:].split('=')
        setting = components[0]
        value = components[1]
        self.status['settings'][setting] = {
          'desc': dict.settings[setting],
          'val': value,
        }
        showLine = False
        ui.log('<<<<< {:} ({:})'.format(line, dict.settings[setting]), color='comms.recv')

      # Display
      if showLine:
        ui.log('<<<<< {:}'.format(line), color='comms.recv')

      if errorCode:
        ui.log('ERROR [{:}]: {:}'.format(errorCode, dict.errors[errorCode]), color='ui.errorMsg')

      if isAlarm:
        ui.log('ALARM [{:}]: {:}'.format(self.alarm, self.getAlarm()), color='ui.errorMsg')



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
          'val': paramValue
        }

      elif paramName == 'F':
        self.status[paramName] = {
          'desc': 'feed',
          'val': int(paramValue)
        }

      elif paramName == 'FS':
        values = paramValue.split(',')
        feed = int(values[0])
        speed = int(values[1])

        self.status['F'] = {
          'desc': 'feed',
          'val': int(feed)
        }

        self.status['S'] = {
          'desc': 'speed',
          'val': int(speed)
        }

      elif paramName == 'Pn':
        self.status[paramName] = {
          'desc': 'inputPinState',
          'val': paramValue
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
          'val': paramValue
        }

      else:
        self.status[paramName] = {
          'desc': 'UNKNOWN',
          'val': paramValue
        }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def queryMachineStatus(self):
    ''' TODO: Comment
    '''
    ui.log('Querying machine status...', v='DEBUG')
    self.sp.write('?')
    self.statusQuerySent = True
    self.waitingMachineStatus = True
    self.lastStatusQuery = time.time()

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachineStatus(self):
    ''' TODO: Comment
    '''
    self.queryMachineStatus()
    startTime = time.time()

    while( (time.time() - startTime) < self.spCfg['responseTimeout'] ):
      self.sleep(WAITRESPONSE_SLEEP)
      if not self.waitingMachineStatus:
        ui.log('Successfully received machine status', v='DEBUG')
        break
    else:
      self.lastStatusStr = ''
      ui.log('TIMEOUT Waiting for machine status', v='WARNING')
      self.waitingMachineStatus = False
      self.statusQuerySent = False

    return self.status


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sendCommand(self, command, responseTimeout=None, verbose='BASIC'):
    ''' Send a command
    '''
    self.sp.sendCommand(command)
    return self.readResponse(responseTimeout=responseTimeout,verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def readResponse(self,responseTimeout=None, verbose='BASIC'):
    ''' Read a command's response
    '''
    if responseTimeout is None:
      responseTimeout = self.spCfg['responseTimeout']

    ui.log('readResponse() - Waiting for response from serial...', v='SUPER')

    startTime = time.time()
    receivedLines = 0
    self.response=[]
    self.waitingResponse = True

    while (time.time() - startTime) < responseTimeout:
      self.sleep(WAITRESPONSE_SLEEP)
      if not self.waitingResponse:
        ui.log(  'readResponse() - Successfully received {:d} data lines from serial'.format(
          len(self.response)), v='SUPER')
        break
    else:
      ui.log('TIMEOUT Waiting for machine response', v='WARNING')
      ui.log('readResponse() - TIMEOUT Waiting for data from serial', color='ui.errorMsg', v='ERROR')
      self.response = []
      self.waitingResponse = False

    return self.response


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSimpleMachineStatusStr(self):
    ''' TODO: comment
    '''
    return '[{:}] - WPos[{:}]'.format(
      self.getColoredMachineStateStr(),
      self.getWorkPosStr()
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
    return ui.xyzStr(
      self.status['MPos']['x'] - self.status['WCO']['x'],
      self.status['MPos']['y'] - self.status['WCO']['y'],
      self.status['MPos']['z'] - self.status['WCO']['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMessage(self):
    ''' TODO: comment
    '''
    return self.lastMessage


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getAlarm(self):
    ''' TODO: comment
    '''
    if self.alarm:
      return dict.alarms[self.alarm]
    else:
      return ''


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForMachineIdle(self,verbose='WARNING'):
    ''' TODO: comment
    '''
    ui.log('Waiting for machine operation to finish...', v='SUPER')
    self.queryMachineStatus()
    while self.waitingMachineStatus:
      self.sleep(WAITRESPONSE_SLEEP)

    showStatus = ((verbose != 'NONE') and (ui.getVerboseLevel() >= ui.getVerboseLevelIndex(verbose)))
    currPosShown = False

    def showCurrentPosition():
      ui.clearLine()
      stateStr = self.getColoredMachineStateStr()
      posStr = 'W[{:}] M[{:}] F[{:}]'.format(
        self.getWorkPosStr(),
        self.getMachinePosStr(),
        self.status['F']['val']
        )
      posStr = ui.setStrColor(posStr, 'ui.onlineMachinePos')
      displayStr = '[{:}] {:}'.format(
        stateStr,
        posStr
        )
      ui.log('\r{:}'.format(displayStr), end='')

    # Valid states types: Idle, Run, Hold, Jog, Alarm, Door, Check, Home, Sleep
    while self.status['machineState'] == 'Run':
      self.queryMachineStatus()
      if showStatus:
        showCurrentPosition()
        currPosShown = True
      self.sleep(WAITRESPONSE_SLEEP)

    if currPosShown:
      showCurrentPosition()

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
