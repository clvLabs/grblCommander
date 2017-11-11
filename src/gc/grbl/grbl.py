#!/usr/bin/python3
"""
grbl - grbl
===========
Main grbl class
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time

from .. import ui as ui

from . import serialport
from . import dict


# ------------------------------------------------------------------
# Constants
GRBL_SOFT_RESET = 24
GRBL_QUERY_MACHINE_STATUS = '?'

STATUSQUERY_INTERVAL = 5
PROCESS_SLEEP = 0.05
WAITIDLE_SLEEP = 0.15
WAITSTARTUP_TIME = 2


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

    self.dct = dict.Dict()

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
      'settings': {},
      'parserState': {
        'str': '',
      },
      'MPos': {'desc':'machinePos', 'x':0, 'y':0, 'z':0},
      'WPos': {'desc':'workPos', 'x':0, 'y':0, 'z':0},
      'WCO': {'desc':'workCoords', 'x':0, 'y':0, 'z':0},
    }

    self.sp = serialport.SerialPort(cfg)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getConfig(self):
    ''' Get working configuration
    '''
    return self.cfg


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def start(self):
    ''' Start connection with grblShield
    '''
    self.sp.open()

    if self.sp.isOpen():
      ui.log('Serial port open.', color='ui.successMsg')
      ui.log()

      self.waitForStartup()

      self.queryMachineStatus()
      self.viewBuildInfo()
      self.viewGrblConfig()
      self.viewGCodeParserState()
      self.viewGCodeParameters()

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
    startTime = time.time()

    while self.waitingStartup and (time.time() - startTime) < WAITSTARTUP_TIME:
      self.process()

    if not self.waitingStartup:
      ui.log('Startup message received, machine ready', color='ui.successMsg')
      ui.log()
    else:
      self.lastStatusStr = ''
      ui.log('TIMEOUT Waiting for startup', v='WARNING')
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
    self.sp.write('%c' % GRBL_SOFT_RESET)
    self.waitForStartup()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sleep(self, seconds):
    ''' grbl-aware sleep
    '''
    startTime = time.time()

    while (time.time() - startTime) < seconds:
      self.process()

      # Give some time for the processor to do other stuff
      ui.log('SLEEP[1] <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<',v='SUPER')
      time.sleep(PROCESS_SLEEP)


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
      ui.log('Alarm detected, resetting wait flags', c='ui.msg', v='DETAIL')
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


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parse(self, line):
    ''' Parse a text line
    '''
    if line:
      originalLine = line

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
      elif line[:1] == '>' and line[-3:] == ':ok':
        line = line[:-3]
      elif line[:1] == '>' and line[-8:-1] == ':error:':
        line = line[:-8]
      elif line[:1] == '>' and line[-9:-2] == ':error:':
        line = line[:-9]

      # Status
      if line[:1] == '<' and line[-1:] == '>':
        isStatus = True
        showLine = False
        try:
          self.parseMachineStatus(line)
          self.lastStatusStr = line
          # self.lastMachineStatusReceptionTimestamp
          if self.waitingMachineStatus:
            self.waitingMachineStatus = False
            self.statusQuerySent = False
        except:
          ui.log("UNKNOWN machine data [{:}]".format(line), color='ui.errorMsg', v='ERROR')

      # Messages
      elif line[:5] == "[MSG:":
        self.lastMessage = line[5:-1]

      # Version info
      elif line[:5] == "[VER:":
        self.status['version'] = line[5:-1]

      # Build options
      elif line[:5] == "[OPT:":
        self.status['buildOptions'] = line[5:-1]

      # gcode parser state
      elif line[:4] == "[GC:":
        parserState = line[4:-1]
        self.status['parserState']['str'] = parserState
        self.parseParserState(parserState)

      # User-defined startup line
      elif line[:2] == "$N":
        pass

      # Settings
      elif line[:1] == "$":
        components = line[1:].split('=')
        setting = components[0]
        value = components[1]
        self.status['settings'][setting] = {
          'desc': self.dct.settings[setting],
          'val': value,
        }
        showLine = False
        ui.log('<<<<< {:} ({:})'.format(line, self.dct.settings[setting]), color='comms.recv')

      # Display
      if showLine:
        ui.log('<<<<< {:}'.format(originalLine), color='comms.recv')

      if errorCode:
        ui.log('ERROR [{:}]: {:}'.format(errorCode, self.dct.errors[errorCode]), color='ui.errorMsg')

      if isAlarm:
        ui.log('ALARM [{:}]: {:}'.format(self.alarm, self.getAlarmStr()), color='ui.errorMsg')
        if self.waitingResponse:
          self.waitingResponse = False

      if isResponse:
        if self.waitingResponse:
          self.waitingResponse = False
        else:
          ui.log('[WARNING] Unexpected machine response',c='ui.msg',v='DETAIL')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseParserState(self,state):
    ''' TODO: Comment
    '''
    # Split modal commands
    commands = state.split(' ')

    for command in commands:
      modalGroup = self.dct.getModalGroup(command)
      if modalGroup:
        commandName = self.dct.getModalCommandName(command)
        self.status['parserState'][modalGroup] = {}
        self.status['parserState'][modalGroup]['val'] = command
        self.status['parserState'][modalGroup]['desc'] = commandName
      else:
        value=command[1:]
        command=command[:1]
        modalGroup = self.dct.getModalGroup(command)
        if modalGroup:
          commandName = self.dct.getModalCommandName(command)
          self.status['parserState'][modalGroup] = {}
          self.status['parserState'][modalGroup]['val'] = value
          self.status['parserState'][modalGroup]['desc'] = commandName


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

        self.status[paramName]['x'] = x
        self.status[paramName]['y'] = y
        self.status[paramName]['z'] = z

        # From: https://github.com/gnea/grbl/wiki/Grbl-v1.1-Interface
        #  If WPos: is given, use MPos = WPos + WCO.
        #  If MPos: is given, use WPos = MPos - WCO.
        if paramName == 'MPos':
          self.status['WPos']['x'] = x - self.status['WCO']['x']
          self.status['WPos']['y'] = y - self.status['WCO']['y']
          self.status['WPos']['z'] = z - self.status['WCO']['z']
        elif paramName == 'WPos':
          self.status['MPos']['x'] = x + self.status['WCO']['x']
          self.status['MPos']['y'] = y + self.status['WCO']['y']
          self.status['MPos']['z'] = z + self.status['WCO']['z']

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
    self.sp.write(GRBL_QUERY_MACHINE_STATUS)
    self.statusQuerySent = True
    self.waitingMachineStatus = True
    self.lastStatusQuery = time.time()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachineStatus(self):
    ''' TODO: Comment
    '''
    self.queryMachineStatus()
    startTime = time.time()

    while( self.waitingMachineStatus and (time.time() - startTime) < self.spCfg['responseTimeout'] ):
      self.process()

    if not self.waitingMachineStatus:
      ui.log('Successfully received machine status', v='DEBUG')
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

    while self.waitingResponse and (time.time() - startTime) < responseTimeout:
      self.process()

    if not self.waitingResponse:
      ui.log(  'readResponse() - Successfully received {:d} data lines from serial'.format(
        len(self.response)), v='SUPER')
    else:
      ui.log('readResponse() - TIMEOUT Waiting for response from serial', color='ui.errorMsg', v='ERROR')
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
  def getWorkCoordinatesStr(self):
    ''' TODO: comment
    '''
    wco = self.status['WCO'] if 'WCO' in self.status else None

    if not wco:
      return '<NONE>'

    return ui.xyzStr(
      wco['x'],
      wco['y'],
      wco['z'])


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
  def getWorkPos(self):
    ''' TODO: comment
    '''
    return {
      'x': self.status['MPos']['x'] - self.status['WCO']['x'],
      'y': self.status['MPos']['y'] - self.status['WCO']['y'],
      'z': self.status['MPos']['z'] - self.status['WCO']['z']
    }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getWorkPosStr(self):
    ''' TODO: comment
    '''
    wpos = self.getWorkPos()
    return ui.xyzStr(wpos['x'], wpos['y'], wpos['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getLastMessage(self):
    ''' TODO: comment
    '''
    return self.lastMessage


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getAlarmStr(self):
    ''' TODO: comment
    '''
    if self.alarm:
      return self.dct.alarms[self.alarm]
    else:
      return ''


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForMachineIdle(self,verbose='WARNING'):
    ''' TODO: comment
    '''
    ui.log('Waiting for machine operation to finish...', v='SUPER')
    self.getMachineStatus()

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
      self.sleep(WAITIDLE_SLEEP)

    if currPosShown:
      showCurrentPosition()

    ui.log('Machine operation finished', v='SUPER')
    ui.log()


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


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def feedAbsolute(self,x=None, y=None, z=None, speed=None, verbose='WARNING'):
    ''' TODO: comment
    '''
    if speed is None:
      speed = self.mchCfg['feedSpeed']

    cmd = 'G1 '

    if x != None:
      cmd += 'X{:} '.format(ui.coordStr(x))

    if y != None:
      cmd += 'Y{:} '.format(ui.coordStr(y))

    if z != None:
      cmd += 'Z{:} '.format(ui.coordStr(z))

    cmd += 'F{:} '.format(speed)

    cmd = cmd.rstrip()

    ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
    self.sendCommand(cmd, verbose=verbose)
    self.waitForMachineIdle(verbose=verbose)
    return


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_Z(self):
    ''' TODO: comment
    '''
    # '27': "Homing switch pull-off distance, millimeters"
    pullOff = float(self.status['settings']['27']['val'])

    self.rapidAbsolute(z=pullOff*-1, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_XY(self):
    ''' TODO: comment
    '''
    # '27': "Homing switch pull-off distance, millimeters"
    pullOff = float(self.status['settings']['27']['val'])

    self.rapidAbsolute(x=pullOff*-1, y=pullOff*-1, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def translateToMachinePos(self,coordName,val):
    ''' Translate a WCO coordinate into MPos
    '''
    if val is None:
      return None

    return val - ( float(self.status['WCO'][coordName]) )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def rapidAbsolute(self,x=None, y=None, z=None, machineCoords=False, verbose='WARNING'):
    ''' TODO: comment
    '''
    cmd = 'G0 '

    if machineCoords:
      x = self.translateToMachinePos('x', x)
      y = self.translateToMachinePos('y', y)
      z = self.translateToMachinePos('z', z)

    if x != None:
      cmd += 'X{:} '.format(ui.coordStr(x))

    if y != None:
      cmd += 'Y{:} '.format(ui.coordStr(y))

    if z != None:
      cmd += 'Z{:} '.format(ui.coordStr(z))

    cmd = cmd.rstrip()

    ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
    self.sendCommand(cmd, verbose=verbose)
    self.waitForMachineIdle(verbose=verbose)
    return


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def rapidRelative(self,x=None, y=None, z=None, verbose='WARNING'):
    ''' TODO: comment
    '''
    if x is None and y is None and z is None:
      ui.log('No parameters provided, doing nothing', v=verbose)
      return

    wpos = self.getWorkPos()

    cmd = 'G0 '

    minX = 0.0
    minY = 0.0
    minZ = 0.0
    maxX = self.mchCfg['max']['X']
    maxY = self.mchCfg['max']['Y']
    maxZ = self.mchCfg['max']['Z']
    curX = wpos['x']
    curY = wpos['y']
    curZ = wpos['z']

    if x:
      newX = curX + x
      if newX<minX:
        ui.log('Adjusting X to MinX ({:})'.format(minX), v='DETAIL')
        newX=minX
      elif newX>maxX:
        ui.log('Adjusting X to MaxX ({:})'.format(maxX), v='DETAIL')
        newX=maxX

      if newX == curX:
        ui.log('X value unchanged, skipping', v='DETAIL')
      else:
        cmd += 'X{:} '.format(ui.coordStr(newX))

    if y:
      newY = curY + y
      if newY<minY:
        ui.log('Adjusting Y to MinY ({:})'.format(minY), v='DETAIL')
        newY=minY
      elif newY>maxY:
        ui.log('Adjusting Y to MaxY ({:})'.format(maxY), v='DETAIL')
        newY=maxY

      if newY == curY:
        ui.log('Y value unchanged, skipping', v='DETAIL')
      else:
        cmd += 'Y{:} '.format(ui.coordStr(newY))

    if z:
      newZ = curZ + z
      if newZ<minZ:
        ui.log('Adjusting Z to MinZ ({:})'.format(minZ), v='DETAIL')
        newZ=minZ
      elif newZ>maxZ:
        ui.log('Adjusting Z to MaxZ ({:})'.format(maxZ), v='DETAIL')
        newZ=maxZ

      if newZ == curZ:
        ui.log('Z value unchanged, skipping', v='DETAIL')
      else:
        cmd += 'Z{:} '.format(ui.coordStr(newZ))

    cmd = cmd.rstrip()

    ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
    self.sendCommand(cmd, verbose=verbose)
    self.waitForMachineIdle(verbose=verbose)
    return


