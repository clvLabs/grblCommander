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
from src.gc.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
spCfg = cfg['serial']

# Serial port
gSerial = serial.Serial()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def connect():
  global gSerial

  if ut.isWindows():
    portNumber = spCfg['portWindows'] - 1
  else:
    portNumber = spCfg['portLinux']

  gSerial.baudrate = spCfg['baudRate']
  gSerial.port = portNumber
  gSerial.timeout = spCfg['timeout']

  if gSerial.isOpen():
    if ut.isWindows():
      ui.log('Closing serial port {:s}...'.format(gSerial.makeDeviceName(gSerial.port)))
    else:
      ui.log('Closing serial port {:s}...'.format(gSerial.port))
    gSerial.close()

  if ut.isWindows():
    ui.log('Opening serial port {:s}...'.format(gSerial.makeDeviceName(gSerial.port)))
  else:
    ui.log('Opening serial port {:s}...'.format(gSerial.port))

  try:
    gSerial.open()
  except:
    pass

  if gSerial.isOpen():
    ui.log('Serial port open, waiting for startup message...')
    ui.log()
    response = readResponse()
    if len(response):
      ui.log()
      ui.log('Startup message received, machine ready', color='ui.msg')
      ui.log()
    else:
      ui.log('ERROR: startup message error, exiting program', color='ui.errorMsg', v='ERROR')
      quit()
  else:
    ui.log('ERROR opening serial port, exiting program', color='ui.errorMsg', v='ERROR')
    quit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def close():
  return gSerial.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendCommand(command, responseTimeout=spCfg['responseTimeout'], verbose='BASIC'):
  command = command.rstrip()
  ui.log('>>>>> {:}'.format(command), color='comms.send' ,v=verbose)
  write(command+'\n')

  return readResponse(responseTimeout=responseTimeout,verbose=verbose)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readResponse(responseTimeout=spCfg['responseTimeout'], verbose='BASIC'):
  ui.log('readResponse() - Waiting for response from serial...', v='SUPER')

  startTime = time.time()
  receivedLines = 0
  responseArray=[]

  while (time.time() - startTime) < responseTimeout:
    line = readline()
    if line:
      finished = False

      if line == 'ok':
        finished = True
      else:
        if line[:1] == '>' and line[-3:] == ':ok':
          line = line[:-3]
          finished = True

        receivedLines += 1
        responseArray.append(line)
        ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v=verbose)

      if finished:
        ui.log(  'readResponse() - Successfully received {:d} data lines from serial'.format(
          receivedLines), v='SUPER')
        break
  else:
    ui.log('readResponse() - TIMEOUT Waiting for data from serial', color='ui.errorMsg', v='ERROR')
    return []

  return responseArray

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readline():
  line = gSerial.readline()

  if line:
    line = line.decode('utf-8')
    line = line.strip('\r\n')

    ui.log('Read line: [{:}]'.format(line), v='DEBUG')

  return line

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def write(data):
  return gSerial.write(bytes(data, 'UTF-8'))
