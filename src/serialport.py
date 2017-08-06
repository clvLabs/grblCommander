#!/usr/bin/python3
"""
grblCommander - serialport
==========================
Serial port management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
import serial

from . import utils as ut
from . import ui as ui
from src.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
spCfg = cfg['serial']

# Serial port
gSerial = serial.Serial()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def connect():
  global gSerial

  if( ut.isWindows() ):
    portNumber = spCfg['portWindows'] - 1
  else:
    portNumber = spCfg['portLinux']

  gSerial.baudrate = spCfg['baudRate']
  gSerial.port = portNumber
  gSerial.timeout = spCfg['timeout']

  if(gSerial.isOpen()):
    if(ut.isWindows()):
      ui.log('Closing serial port {:s}...'.format(gSerial.makeDeviceName(gSerial.port)))
    else:
      ui.log('Closing serial port {:s}...'.format(gSerial.port))
    gSerial.close()

  if(ut.isWindows()):
    ui.log('Opening serial port {:s}...'.format(gSerial.makeDeviceName(gSerial.port)))
  else:
    ui.log('Opening serial port {:s}...'.format(gSerial.port))

  try:
    gSerial.open()
  except:
    pass

  if(gSerial.isOpen()):
    ui.log('Serial port open, waiting for startup message...')
    ui.log()
    response = readResponse(expectedLines=None)
    if( len(response) >= 2 ):
      ui.log()
      ui.log('Startup message received, machine ready')
      ui.log()
    else:
      ui.log('ERROR: startup message error, exiting program')
      quit()
  else:
    ui.log('ERROR opening serial port, exiting program')
    quit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def close():
  return gSerial.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendCommand(command, responseTimeout=spCfg['responseTimeout'], expectedResultLines=1, verbose='BASIC'):
  command = command.rstrip()
  ui.log('>>>>> [{0}]'.format(command), color='comms.send' ,v=verbose)
  write(command+'\n')

  return readResponse(expectedLines=expectedResultLines,responseTimeout=responseTimeout,verbose=verbose)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readResponse(expectedLines=1, responseTimeout=spCfg['responseTimeout'], verbose='BASIC'):
  ui.log(  'readResponse() - Waiting for {:} lines from serial...'.format(
        expectedLines if expectedLines != None else 'undefined'), v='SUPER')

  startTime = time.time()
  receivedLines = 0
  responseArray=[]

  while( (time.time() - startTime) < responseTimeout ):
    line = readline()
    if(line):
      ui.log('<<<<< [{0}]'.format(line), color='comms.recv' ,v=verbose)
      receivedLines += 1
      responseArray.append(line)
      if((expectedLines != None) and (receivedLines == expectedLines)):
        ui.log(  'readResponse() - Successfully received {:d} lines from serial'.format(
          expectedLines), v='SUPER')
        break
  else:
    if(expectedLines != None):
      ui.log('readResponse() - TIMEOUT Waiting for data from serial', v='WARNING')
    else:
      ui.log('readResponse() - Finished waiting for undefined lines from serial', v='DEBUG')

  return responseArray

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readline():
  line = gSerial.readline()

  if(line):
    line = line.decode('utf-8')
    line = line.strip('\r\n')

    ui.log('Read line: [{0}]'.format(line), v='DEBUG')

  return line

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def write(data):
  return gSerial.write(bytes(data, 'UTF-8'))
