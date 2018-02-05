#!/usr/bin/python3
'''
grbl - grbl
===========
Main grbl class
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time

from .. import ui as ui

from . import serialport
from . import dict

# ------------------------------------------------------------------
# Grbl class

class Grbl:

  def __init__(self, cfg):
    ''' Construct a Grbl object. '''
    self.initConstants()

    self.cfg = cfg
    self.spCfg = cfg['serial']
    self.mchCfg = cfg['machine']
    self.mcrCfg = cfg['macro']
    self.uiCfg = cfg['ui']

    self.dct = dict.Dict()

    self.waitingStartup = True
    self.waitingResponse = False
    self.response = []
    self.lastMachineStatusQuery = 0
    self.lastParserStateQuery = 0
    self.lastParserStateStr = ''
    self.onParserStateChanged = []
    self.statusQuerySent = False
    self.waitingMachineStatus = False
    self.showNextMachineStatus = False
    self.showNextParserState = True
    self.ignoreNextLine = False
    self.lastMessage = ''
    self.alarm = ''
    self.status = {
      'str': '',
      'MPos': {'desc':'machinePos', 'x':0.000, 'y':0.000, 'z':0.000},
      'WPos': {'desc':'workPos', 'x':0.000, 'y':0.000, 'z':0.000},
      'WCO': {'desc':'workCoords', 'x':0.000, 'y':0.000, 'z':0.000},
      'settings': {},
      'parserState': {
        'str': '',
      },
      'GCodeParams': {
        'G54': {'x':0.000, 'y':0.000, 'z':0.000},
        'G55': {'x':0.000, 'y':0.000, 'z':0.000},
        'G56': {'x':0.000, 'y':0.000, 'z':0.000},
        'G57': {'x':0.000, 'y':0.000, 'z':0.000},
        'G58': {'x':0.000, 'y':0.000, 'z':0.000},
        'G59': {'x':0.000, 'y':0.000, 'z':0.000},
        'G28': {'x':0.000, 'y':0.000, 'z':0.000},
        'G30': {'x':0.000, 'y':0.000, 'z':0.000},
        'G92': {'x':0.000, 'y':0.000, 'z':0.000},
        'PRB': {'x':0.000, 'y':0.000, 'z':0.000, 'success': False},
        'TLO': 0.000,
      },
      'inputPinState': self.parseInputPinState('')
    }

    self.sp = serialport.SerialPort(cfg)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def initConstants(self):
    ''' Provide constants '''
    self.GRBL_SOFT_RESET = '%c' % 24
    self.GRBL_QUERY_MACHINE_STATUS = '?'
    self.GRBL_QUERY_GCODE_PARSER_STATE = '$G'
    self.GRBL_HOMING_CYCLE = '$H'
    self.GRBL_QUERY_BUILD_INFO = '$I'
    self.GRBL_QUERY_GCODE_PARAMETERS = '$#'
    self.GRBL_QUERY_GRBL_CONFIG = '$$'
    self.GRBL_QUERY_STARTUP_BLOCKS = '$N'
    self.GRBL_ENABLE_SLEEP_MODE = '$SLP'
    self.GCODE_RESET_WCO_PREFIX = 'G10L2P0'

    self.PERIODIC_QUERY_INTERVAL = 0.5
    self.PROCESS_SLEEP = 0.05
    self.WAITIDLE_SLEEP = 0.15
    self.WAITSTARTUP_TIME = 2


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
      ui.log('Serial port open.', c='ui.successMsg')
      ui.log()

      self.waitForStartup()

      self.queryMachineStatus()
      self.viewBuildInfo()
      self.viewGrblConfig()
      self.viewGCodeParserState()
      self.viewGCodeParameters()

    else:
      ui.log('ERROR opening serial port, exiting program', c='ui.errorMsg', v='ERROR')
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
  def softReset(self):
    ''' grblShield soft reset
    '''
    self.sp.write(self.GRBL_SOFT_RESET)
    self.waitForStartup()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sleep(self, seconds):
    ''' grbl-aware sleep
    '''
    startTime = time.time()

    while (time.time() - startTime) < seconds:
      self.process()

      # Give some time for the processor to do other stuff
      time.sleep(self.PROCESS_SLEEP)


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
    if self.alarm and (self.waitingResponse or self.waitingMachineStatus):
      ui.log('Alarm detected, resetting wait flags', c='ui.msg', v='DETAIL')
      self.waitingResponse = False
      self.waitingMachineStatus = False

    # Automatic periodic machine status queries
    sendStatusQuery = False

    if self.waitingMachineStatus and not self.statusQuerySent:
      sendStatusQuery = True

    if (time.time() - self.lastMachineStatusQuery) > self.PERIODIC_QUERY_INTERVAL:
      sendStatusQuery = True

    if sendStatusQuery:
      self.queryMachineStatus()
      self.showNextMachineStatus = False

    # Automatic periodic parser status queries
    sendParserStateQuery = False

    if (time.time() - self.lastParserStateQuery) > self.PERIODIC_QUERY_INTERVAL:
      sendParserStateQuery = True

    if sendParserStateQuery:
      self.queryGCodeParserState()
      self.showNextParserState = False

    # Show 'live' machine status if running
    if self.isRunning():
      ui.clearLine()
      ui.log('\r{:}'.format(self.getSimpleMachineStatusStr()), end='')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def stripCommand(self, command):
    ''' Return a stripped version of the command string '''
    return command.rstrip().rstrip('\n').rstrip('\r')

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sendWait(self, command, responseTimeout=None, verbose='BASIC'):
    ''' Send a command
    '''
    if not command:
      return

    self.send(command=command, responseTimeout=responseTimeout, verbose=verbose)
    self.waitForMachineIdle(verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def send(self, command, responseTimeout=None, verbose='BASIC'):
    ''' Send a command
    '''
    command = command.rstrip().rstrip('\n').rstrip('\r')
    if not command:
      return

    command = self.stripCommand(command)
    upperCommand = command.upper()

    if upperCommand == self.GRBL_QUERY_GCODE_PARSER_STATE:
      self.showNextParserState = True
    elif upperCommand == self.GRBL_QUERY_MACHINE_STATUS:
      self.showNextMachineStatus = True
    elif upperCommand == self.GRBL_HOMING_CYCLE:
      if not responseTimeout:
        responseTimeout = float(self.mchCfg['homingTimeout'])

    ui.log('>>>>> {:}'.format(command), c='comms.send' ,v=verbose)
    self.sp.write(command+'\n')

    return self.readResponse(responseTimeout=responseTimeout,verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def isRunning(self):
    if 'machineState' not in self.status:
      return False

    machineState = self.status['machineState']
    return machineState == 'Run' or machineState == 'Home' or machineState == 'Jog'


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def readResponse(self,responseTimeout=None, verbose='BASIC'):
    ''' Read a command's response
    '''
    if responseTimeout is None:
      responseTimeout = self.spCfg['responseTimeout']

    ui.log('readResponse() - Waiting for response from serial...', v='SUPER')

    startTime = time.time()
    receivedLines = 0
    self.response = []
    self.waitingResponse = True

    while self.waitingResponse and (time.time() - startTime) < responseTimeout:
      self.process()

    if not self.waitingResponse:
      ui.log(  'readResponse() - Successfully received {:d} data lines from serial'.format(
        len(self.response)), v='SUPER')
    else:
      ui.log('readResponse() - TIMEOUT Waiting for response from serial', c='ui.errorMsg', v='ERROR')
      self.response = []
      self.waitingResponse = False

    return self.response


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForStartup(self):
    ''' Wait for grblShield startup
    '''
    ui.log('Waiting for startup message...')
    self.alarm = ''
    self.waitingStartup = True
    startTime = time.time()

    while self.waitingStartup and (time.time() - startTime) < self.WAITSTARTUP_TIME:
      self.process()

    if not self.waitingStartup:
      ui.log('Startup message received, machine ready', c='ui.successMsg')
      ui.log()
    else:
      self.status['str'] = ''
      ui.log('TIMEOUT Waiting for startup', v='WARNING')
      ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parse(self, line):
    ''' Parse a text line
    '''
    if line:
      if self.ignoreNextLine:
        self.ignoreNextLine = False
        return

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
      elif line[:6] == 'error:':
        errorCode = line[6:]
        isResponse = True
      elif line[:6] == 'ALARM:':
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
        if not self.showNextMachineStatus:
          showLine = False
        try:
          self.parseMachineStatus(line)
          self.status['str'] = line
          # self.lastMachineStatusReceptionTimestamp
          self.waitingMachineStatus = False
          self.statusQuerySent = False
        except:
          ui.log('UNKNOWN machine data [{:}]'.format(line), c='ui.errorMsg', v='ERROR')

      # Messages
      elif line[:5] == '[MSG:':
        self.lastMessage = line[5:-1]

      # Version info
      elif line[:5] == '[VER:':
        self.status['version'] = line[5:-1]

      # Build options
      elif line[:5] == '[OPT:':
        self.status['buildOptions'] = line[5:-1]

      # gcode parser state
      elif line[:4] == '[GC:':
        if not self.showNextParserState:
          self.showNextParserState = True
          showLine = False
          self.ignoreNextLine = True
        parserState = line[4:-1]
        self.status['parserState']['str'] = parserState
        self.parseParserState(parserState)
        # Check for changes!
        if self.lastParserStateStr and self.lastParserStateStr != parserState:
          for event in self.onParserStateChanged:
            event()
        self.lastParserStateStr = parserState

      # gcode parameters
      elif line[:1] == '[':
        parserParam = line[1:-1]
        self.parseGCodeParam(parserParam)

      # User-defined startup line
      elif line[:2] == '$N':
        pass

      # Settings
      elif line[:1] == '$':
        settingStr = line[1:]
        self.parseSetting(settingStr)
        showLine = False

      # Display
      if isResponse:
        if self.waitingResponse:
          self.waitingResponse = False
        else:
          ui.log('[WARNING] Unexpected machine response',c='ui.msg',v='DETAIL')

      if showLine:
        if self.isRunning():
          ui.log()
        ui.log('<<<<< {:}'.format(originalLine), c='comms.recv')

      if errorCode:
        ui.log('ERROR [{:}]: {:}'.format(errorCode, self.dct.errors[errorCode]), c='ui.errorMsg')

      if isAlarm:
        ui.log('ALARM [{:}]: {:}'.format(self.alarm, self.getAlarmStr()), c='ui.errorMsg')
        if self.waitingResponse:
          self.waitingResponse = False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseParserState(self,state):
    ''' TODO: Comment
    '''
    # Split modal commands
    commands = state.split(' ')

    for command in commands:
      modalGroup = self.dct.getModalGroup(command)
      if modalGroup:
        original = command
        commandName = self.dct.getModalCommandName(command)
        self.status['parserState'][modalGroup] = {}
        self.status['parserState'][modalGroup]['val'] = command
        self.status['parserState'][modalGroup]['original'] = original
        self.status['parserState'][modalGroup]['desc'] = commandName
      else:
        original = command
        value = command[1:]
        command = command[:1]
        modalGroup = self.dct.getModalGroup(command)
        if modalGroup:
          commandName = self.dct.getModalCommandName(command)
          self.status['parserState'][modalGroup] = {}
          self.status['parserState'][modalGroup]['val'] = value
          self.status['parserState'][modalGroup]['original'] = original
          self.status['parserState'][modalGroup]['desc'] = commandName


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseGCodeParam(self,parserParam):
    ''' Parses a GCode param string and updates self.status
    '''
    # Separate ID and value
    parts = parserParam.split(':')

    # ID/value pair found?
    if len(parts) < 2:
      return

    # Separate parts (possible suffix after value, separated by ':')
    id = parts[0]
    value = parts[1]
    suffix = suffix = parts[2] if len(parts) > 2 else ''

    # Save xyz for common params
    if id in ['G54','G55','G56','G57','G58','G59','G28','G30','G92','PRB']:
      axes = value.split(',')

      if len(axes) < 3:
        return

      self.status['GCodeParams'][id]['x'] = float(axes[0])
      self.status['GCodeParams'][id]['y'] = float(axes[1])
      self.status['GCodeParams'][id]['z'] = float(axes[2])

    # PRB (probe) has an additional parameter
    if id == 'PRB':
      self.status['GCodeParams']['PRB']['success'] = True if int(suffix) else False

    # TLO (tool offset)
    if id == 'TLO':
      self.status['GCodeParams']['TLO'] = float(value)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseInputPinState(self,pinState):
    ''' Parses a pin state string and returns an object
    '''
    state = {}

    for item in dict.inputPinStates:
      state[item] = {
        'desc': dict.inputPinStates[item],
        'val': item in pinState
      }

    return state


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseMachineStatus(self,status):
    ''' TODO: Comment
    '''
    # Remove chevrons
    status = status[1:-1]

    # Split parameter groups
    params = status.split('|')

    # Initialize input pin state variable
    inputPinState = ''

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
        inputPinState = paramValue

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

    # ALWAYS save&parse input pin state (if none comes, it's empty!)
    self.status['Pn'] = {
      'desc': 'inputPinState',
      'val': inputPinState
    }

    self.status['inputPinState'] = self.parseInputPinState(inputPinState)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseSetting(self, settingStr):
    ''' TODO: Comment
    '''
    components = settingStr.split('=')
    setting = int(components[0])
    value = components[1]
    self.status['settings'][setting] = {
      'desc': self.dct.settings[setting],
      'val': value,
    }

    ui.log('<<<<< {:} ({:})'.format(settingStr, self.dct.settings[setting]), c='comms.recv')

    # $2 - Step port invert, mask
    # $3 -  Direction port invert, mask
    # $23 - Homing direction invert, mask
    if setting in [2, 3, 23]:
      mask = int(value)
      self.status['settings'][setting]['parsed'] = {
        'x': (mask & 0x1 == 1),
        'y': (mask & 0x2 == 1),
        'z': (mask & 0x4 == 1),
      }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def queryMachineStatus(self):
    ''' TODO: Comment
    '''
    ui.log('Querying machine status...', v='DEBUG')
    self.sp.write(self.GRBL_QUERY_MACHINE_STATUS)
    self.statusQuerySent = True
    self.waitingMachineStatus = True
    self.lastMachineStatusQuery = time.time()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewMachineStatus(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting machine status')
    ui.log('Sending command [?]...', v='DETAIL')
    self.send(self.GRBL_QUERY_MACHINE_STATUS)
    self.statusQuerySent = True
    self.waitingMachineStatus = True
    self.lastMachineStatusQuery = time.time()
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachineStatus(self):
    ''' TODO: Comment
    '''
    self.queryMachineStatus()
    startTime = time.time()

    while self.waitingMachineStatus and (time.time() - startTime) < self.spCfg['responseTimeout']:
      self.process()

    if not self.waitingMachineStatus:
      ui.log('Successfully received machine status', v='DEBUG')
    else:
      ui.log('TIMEOUT Waiting for machine status', v='WARNING')
      self.waitingMachineStatus = False
      self.statusQuerySent = False

    return self.status


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getCompleteGrblSettings(self):
    ''' TODO: comment
    '''
    result = []

    for key in sorted(self.status['settings']):
      s = self.status['settings'][key]
      id = '${:}'.format(key)
      val = s['val']
      desc = s['desc']
      color = 'ui.successMsg'

      line = '{:6s} {:10s} {:s}'.format(id, val, desc)
      line = ui.color(line, color)

      result.append(line)

    return result


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getCompleteParserState(self):
    ''' TODO: comment
    '''
    result = []

    for modalGroupName in sorted(self.status['parserState']):
      if modalGroupName == 'str':
        continue

      mg = self.status['parserState'][modalGroupName]
      val = mg['val']
      original = mg['original']
      desc = mg['desc']

      if modalGroupName in self.mchCfg['preferredParserState']:
        preferred = self.mchCfg['preferredParserState'][modalGroupName]
      else:
        preferred = val

      color = 'ui.successMsg' if val == preferred else 'ui.errorMsg'

      line = '{:15s} {:6s} {:20s}'.format(modalGroupName, original, desc)
      line = line.rstrip()
      if val != original:
        line += ': {:}'.format(val)
      line = ui.color(line, color)

      if val != preferred:
        line += ui.color(' ({:})'.format(preferred), 'ui.successMsg')

      result.append(line)

    return result


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSimpleParserState(self):
    ''' TODO: comment
    '''
    settingsStr = ''

    # Configured
    for modalGroupName in self.uiCfg['simpleParserState']:
      mg = self.status['parserState'][modalGroupName]
      val = mg['val']
      original = mg['original']
      desc = mg['desc']
      preferred = val
      display = original
      color = 'ui.successMsg'

      if modalGroupName in self.mchCfg['preferredParserState']:
        preferred = self.mchCfg['preferredParserState'][modalGroupName]

      if val != preferred:
        color = 'ui.errorMsg'
        display = '{:}({:})'.format(val, desc)

      settingsStr += '{:} '.format(ui.color(display, color))

    # The rest if != preferred
    for modalGroupName in self.mchCfg['preferredParserState']:
      if not modalGroupName in self.uiCfg['simpleParserState']:
        mg = self.status['parserState'][modalGroupName]
        desc = mg['desc']
        original = mg['original']
        val = mg['val']
        preferred = self.mchCfg['preferredParserState'][modalGroupName]
        if val != preferred:
          color = 'ui.errorMsg'
          display = '{:}({:})'.format(original, desc)
          settingsStr += '{:} '.format(ui.color(display, color))

    return settingsStr.rstrip()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSimpleMachineStatusStr(self):
    ''' TODO: comment
    '''
    machineState = self.status['machineState']
    stateStr = self.getColoredMachineStateStr()

    prefix = '[{:}]'.format(stateStr)
    content = ''
    suffix = ''

    # Content
    if  machineState in ['Idle', 'Alarm', 'Check', 'Sleep', 'Door']:
      content = 'W[{:}] M[{:}] [{:}]'.format(
        self.getWorkPosStr().replace(' ',''),
        self.getMachinePosStr().replace(' ',''),
        self.getSimpleParserState()
        )
    elif  machineState in ['Run', 'Home', 'Hold', 'Jog']:
      content = 'W[{:}] M[{:}] F[{:}]'.format(
        self.getWorkPosStr(),
        self.getMachinePosStr(),
        self.status['F']['val']
        )
      content = ui.color(content, 'ui.onlineMachinePos')

    # Suffix
    if self.getInputPinStateStr():
      suffix = '[{:}]'.format(ui.color(self.getInputPinStateStr(), 'machineState.Alarm'))

    # Build string
    string = prefix
    if content:
      string += ' ' + content
    if suffix:
      string += ' ' + suffix

    return string


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getColoredMachineStateStr(self):
    ''' TODO: comment
    '''
    machineStateStr = self.status['machineState']
    return ui.color(machineStateStr, 'machineState.{:}'.format(machineStateStr))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getWorkCoordinatesStr(self):
    ''' TODO: comment
    '''
    wco = self.status['WCO'] if 'WCO' in self.status else None
    if not wco:
      return '<NONE>'
    return ui.xyzStr(wco['x'],wco['y'],wco['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMachinePosStr(self):
    ''' TODO: comment
    '''
    mPos = self.status['MPos'] if 'MPos' in self.status else None
    if not mPos:
      return '<NONE>'
    return ui.xyzStr(mPos['x'],mPos['y'],mPos['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getWorkPosStr(self):
    ''' TODO: comment
    '''
    wpos = self.status['WPos'] if 'WPos' in self.status else None
    if not wpos:
      return '<NONE>'
    return ui.xyzStr(wpos['x'], wpos['y'], wpos['z'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getProbePosStr(self):
    ''' TODO: comment
    '''
    prb = self.status['GCodeParams']['PRB']
    coords = ui.xyzStr(prb['x'], prb['y'], prb['z'])
    lastRun = ui.color('SUCCESS','ui.successMsg') if prb['success'] else ui.color('FAIL','ui.errorMsg')

    return '[{:}] ({:})'.format(coords, lastRun)


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
  def getInputPinState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getInputPinStateStr(self):
    ''' Helpers to get pin states
    '''
    return self.status['Pn']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getInputPinStateLongStr(self):
    ''' Helpers to get pin states
    '''
    stateStr = ''

    pins = self.status['inputPinState']
    for pin in pins:
      if pins[pin]['val']:
        stateStr += '[{:} ({:})] '.format(ui.color(pin, 'machineState.Alarm'),pins[pin]['desc'])

    return stateStr.rstrip()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getLimitSwitchState(self,axis):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState'][axis]['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getProbeState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']['P']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getDoorState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']['D']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getHoldState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']['H']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getSoftResetState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']['R']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getCycleStartState(self):
    ''' Helpers to get pin states
    '''
    return self.status['inputPinState']['S']['val']


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def waitForMachineIdle(self,verbose='WARNING'):
    ''' TODO: comment
    '''
    ui.log('Waiting for machine operation to finish...', v='SUPER')
    self.getMachineStatus()

    while self.isRunning():
      self.process()
      self.getMachineStatus()

    ui.log('Machine operation finished', v='SUPER')
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewBuildInfo(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting build info')
    self.send(self.GRBL_QUERY_BUILD_INFO)
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def queryGCodeParserState(self):
    ''' TODO: comment
    '''
    ui.log('Querying gcode parser state...', v='DEBUG')
    self.sp.write(self.GRBL_QUERY_GCODE_PARSER_STATE + '\n')
    self.lastParserStateQuery = time.time()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGCodeParserState(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting GCode parser state')
    self.send(self.GRBL_QUERY_GCODE_PARSER_STATE)
    self.lastParserStateQuery = time.time()
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGCodeParameters(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting GCode parameters')
    self.send(self.GRBL_QUERY_GCODE_PARAMETERS)
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewGrblConfig(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting grbl config')
    self.send(self.GRBL_QUERY_GRBL_CONFIG)
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def viewStartupBlocks(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting startup blocks')
    self.send(self.GRBL_QUERY_STARTUP_BLOCKS)
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def enableSleepMode(self):
    ''' TODO: comment
    '''
    ui.logTitle('Requesting sleep mode enable')
    self.send(self.GRBL_ENABLE_SLEEP_MODE)
    ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getResetWCOStr(self, x=None, y=None, z=None):
    ''' Get reset WCO coordinates GCode command string.
        NOTE: Special values for x/y/z
        - 'curr' : Current machine position
        - 'home' : Machine home position
        - 'away' : Opposite point from machine home
        - 'wco'  : Current WCO x/y/z
    '''
    cmd = self.GCODE_RESET_WCO_PREFIX

    for (val, axis) in [(x,'x'),(y,'y'),(z,'z')]:
      if val == 'curr':
        val = self.status['MPos'][axis]
      elif val == 'home':
        val = self.getHomingCorner(axis)
      elif val == 'away':
        val = self.getAwayCorner(axis)
      elif val == 'wco':
        val = self.status['WCO'][axis]

      if val is not None:
        cmd += '{:}{:}'.format(axis,val)

    return cmd


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetWCO(self, x=None, y=None, z=None):
    ''' Reset WCO coordinates.
        NOTE: See 'Special values for x/y/z' @ getResetWCOStr()
    '''
    self.send(self.getResetWCOStr(x,y,z))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetWCOAxis(self,axis,val):
    ''' Reset single WCO axis
        NOTE: Special values for x/y/z
        - 'curr' : Current machine position
        - 'home' : Machine home position
        - 'away' : Opposite point from machine home
    '''
    if val == 'curr':
      val = self.status['MPos'][axis]
    elif val == 'away':
      val = self.getAwayCorner(axis)
    elif val == 'home':
      val = self.getHomingCorner(axis)

    self.send('{:}{:}{:}'.format(self.GCODE_RESET_WCO_PREFIX,axis,val))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def mpos2wpos(self,axis,val):
    ''' Translate a MPos coordinate into WPos
    '''
    if val is None:
      return None

    return val - ( float(self.status['WCO'][axis]) )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def wpos2mpos(self,axis,val):
    ''' Translate a WPos coordinate into MPos
    '''
    if val is None:
      return None

    return val + ( float(self.status['WCO'][axis]) )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getHomingCorner(self, axis):
    ''' TODO: comment
    '''
    # '27': 'Homing switch pull-off distance, millimeters'
    pos = float(self.status['settings'][27]['val'])

    if pos < self.mchCfg['softLimitsMargin']:
      pos = self.mchCfg['softLimitsMargin']

    if self.status['settings'][23]['parsed'][axis]:
      return pos
    else:
      return pos * -1


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getAwayCorner(self, axis):
    ''' TODO: comment
    '''
    pos = self.mchCfg['maxTravel'][axis] - self.mchCfg['softLimitsMargin']

    if self.status['settings'][23]['parsed'][axis]:
      return pos
    else:
      return pos * -1


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMin(self, axis):
    ''' calculate min axis(xyz) coord given current WCO
    '''
    # '23': 'Homing direction invert, mask'
    if self.status['settings'][23]['parsed'][axis]:
      min = self.getHomingCorner(axis)
    else:
      min = self.getAwayCorner(axis)

    return self.mpos2wpos(axis, min)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMax(self, axis):
    ''' calculate max axis(xyz) coord given current WCO
    '''
    # '23': 'Homing direction invert, mask'
    if self.status['settings'][23]['parsed'][axis]:
      max = self.getAwayCorner(axis)
    else:
      max = self.getHomingCorner(axis)

    return self.mpos2wpos(axis, max)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_X(self):
    ''' TODO: comment
    '''
    # '27': 'Homing switch pull-off distance, millimeters'
    xPullOff = float(self.status['settings'][27]['val'])

    # '23': 'Homing direction invert, mask'
    if not self.status['settings'][23]['parsed']['x']:
      xPullOff *= -1

    self.rapidAbsolute(x=xPullOff, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_Y(self):
    ''' TODO: comment
    '''
    # '27': 'Homing switch pull-off distance, millimeters'
    yPullOff = float(self.status['settings'][27]['val'])

    # '23': 'Homing direction invert, mask'
    if not self.status['settings'][23]['parsed']['y']:
      yPullOff *= -1

    self.rapidAbsolute(y=yPullOff, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_XY(self):
    ''' TODO: comment
    '''
    # '27': 'Homing switch pull-off distance, millimeters'
    xPullOff = float(self.status['settings'][27]['val'])
    yPullOff = xPullOff

    # '23': 'Homing direction invert, mask'
    if not self.status['settings'][23]['parsed']['x']:
      xPullOff *= -1

    if not self.status['settings'][23]['parsed']['y']:
      yPullOff *= -1

    self.rapidAbsolute(x=xPullOff, y=yPullOff, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome_Z(self):
    ''' TODO: comment
    '''
    # '27': 'Homing switch pull-off distance, millimeters'
    pullOff = float(self.status['settings'][27]['val'])

    # '23': 'Homing direction invert, mask'
    if not self.status['settings'][23]['parsed']['z']:
      pullOff *= -1

    self.rapidAbsolute(z=pullOff, machineCoords=True)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def goToMachineHome(self):
    ''' TODO: comment
    '''
    self.goToMachineHome_Z()
    self.goToMachineHome_XY()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def rapidRelative(self,x=None, y=None, z=None, verbose='WARNING'):
    cmd = self.getMoveRelativeStr(x=x,y=y,z=z,verbose=verbose)
    if cmd:
      cmd = 'G0 {:}'.format(cmd)
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def feedRelative(self,x=None, y=None, z=None, speed=None, verbose='WARNING'):
    cmd = self.getMoveRelativeStr(x=x,y=y,z=z,speed=speed,verbose=verbose)
    if cmd:
      cmd = 'G1 {:}'.format(cmd)
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def moveRelative(self,x=None, y=None, z=None, speed=None, verbose='WARNING'):
    cmd = self.getMoveRelativeStr(x=x,y=y,z=z,speed=speed,verbose=verbose)
    if cmd:
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMoveRelativeStr(self,x=None, y=None, z=None, speed=None, verbose='WARNING'):
    ''' TODO: comment
    '''
    if x is None and y is None and z is None:
      ui.log('No parameters provided, doing nothing', v=verbose)
      return ''

    axes = ['x','y','z']
    wpos = self.status['WPos']
    target = {
      'x': x,
      'y': y,
      'z': z
    }

    for axis in axes:
      if target[axis] != None:
        target[axis] += wpos[axis]

    return self.getMoveAbsoluteStr(target['x'], target['y'], target['z'], speed=speed, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def rapidAbsolute(self,x=None, y=None, z=None, machineCoords=False, verbose='WARNING'):
    cmd = self.getMoveAbsoluteStr(x=x,y=y,z=z,machineCoords=machineCoords,verbose=verbose)
    if cmd:
      cmd = 'G0 {:}'.format(cmd)
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def feedAbsolute(self,x=None, y=None, z=None, machineCoords=False, speed=None, verbose='WARNING'):
    cmd = self.getMoveAbsoluteStr(x=x,y=y,z=z,machineCoords=machineCoords,speed=speed,verbose=verbose)
    if cmd:
      cmd = 'G1 {:}'.format(cmd)
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def moveAbsolute(self,x=None, y=None, z=None, machineCoords=False, speed=None, verbose='WARNING'):
    cmd = self.getMoveAbsoluteStr(x=x,y=y,z=z,machineCoords=machineCoords,speed=speed,verbose=verbose)
    if cmd:
      ui.log('Sending command [{:s}]...'.format(repr(cmd)), v='DETAIL')
      self.sendWait(cmd, verbose=verbose)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMoveAbsoluteStr(self,x=None, y=None, z=None, machineCoords=False, speed=None, verbose='WARNING'):
    ''' TODO: comment
    '''
    if x is None and y is None and z is None:
      ui.log('No parameters provided, doing nothing', v=verbose)
      return ''

    cmd = ''
    absolute = self.status['parserState']['distanceMode']['val'] == 'G90'
    axes = ['x','y','z']
    target = {'x':x, 'y':y, 'z':z}
    wpos = self.status['WPos']
    min = {
      'x': self.getMin('x'),
      'y': self.getMin('y'),
      'z': self.getMin('z')
    }
    max = {
      'x': self.getMax('x'),
      'y': self.getMax('y'),
      'z': self.getMax('z')
    }

    # ---[ Translate machine coords ]-----------------------------------------
    if machineCoords:
      for axis in axes:
        target[axis] = self.mpos2wpos(axis, target[axis])

    if absolute:
      # ---[ Absolute mode ]-----------------------------------------
      for axis in axes:
        if target[axis] != None:
          if target[axis] < min[axis]:
            ui.log('Adjusting target {:}({:}) to min({:})'.format(axis.upper(), target[axis], min[axis]), v='DETAIL')
            target[axis] = min[axis]
          elif target[axis] > max[axis]:
            ui.log('Adjusting target {:}({:}) to max({:})'.format(axis.upper(), target[axis], max[axis]), v='DETAIL')
            target[axis] = max[axis]

          if target[axis] == wpos[axis]:
            target[axis] = None

    else:
      # ---[ Relative mode ]-----------------------------------------
      for axis in axes:
        if target[axis] != None:
          if target[axis] < min[axis]:
            ui.log('Adjusting target {:}({:}) to min({:})'.format(axis.upper(), target[axis] - wpos[axis], min[axis] - wpos[axis]), v='DETAIL')
            target[axis] = min[axis] - wpos[axis]
          elif target[axis] > max[axis]:
            ui.log('Adjusting target {:}({:}) to max({:})'.format(axis.upper(), target[axis] - wpos[axis], max[axis] - wpos[axis]), v='DETAIL')
            target[axis] = max[axis] - wpos[axis]
          else:
            target[axis] -= wpos[axis]

          if target[axis] == 0:
            target[axis] = None

    # ---[ Generate gcode ]-----------------------------------------
    for axis in axes:
      if target[axis] != None and target[axis] != wpos[axis]:
        cmd += '{:}{:} '.format(axis.upper(), ui.coordStr(target[axis]).strip())

    cmd = cmd.rstrip()

    if cmd and speed:
      cmd += ' F{:}'.format(speed)

    return cmd
