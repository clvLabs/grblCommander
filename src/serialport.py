#!/usr/bin/python3
"""
grblCommander - serialport
==========================
Serial port management
"""
#print("***[IMPORTING]*** grblCommander - serialport")

import time
import serial

from . import utils as ut
from . import ui as ui

# Serial port
gSerial = serial.Serial()

# Serial configuration
gBAUDRATE = 115200
gPORTNUMBER_WINDOWS = 3              # Change THIS to match your Arduino's COM port !!!
gPORTNUMBER_LINUX = '/dev/ttyACM0'   # Change THIS to match your Arduino's COM port !!!
gPORTNUMBER = 0
gTIMEOUT = 0.1

# Serial response timeout (seconds)
gRESPONSE_TIMEOUT = 2


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def connect():
  global gSerial, gPORTNUMBER

  _k = 'sp.connect()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if( ut.isWindows() ):
    gPORTNUMBER = gPORTNUMBER_WINDOWS - 1
  else:
    gPORTNUMBER = gPORTNUMBER_LINUX

  gSerial.baudrate = gBAUDRATE
  gSerial.port = gPORTNUMBER
  gSerial.timeout = gTIMEOUT

  if(gSerial.isOpen()):
    if(ut.isWindows()):
      ui.log("Closing serial port %s: ..." % gSerial.makeDeviceName(gSerial.port), k=_k, v='BASIC')
    else:
      ui.log("Closing serial port %s: ..." % gSerial.port, k=_k, v='BASIC')
    gSerial.close()

  if(ut.isWindows()):
    ui.log("Opening serial port %s: ..." % gSerial.makeDeviceName(gSerial.port), k=_k, v='BASIC')
  else:
    ui.log("Opening serial port %s: ..." % gSerial.port, k=_k, v='BASIC')

  try:
    gSerial.open()
  except:
    pass

  if(gSerial.isOpen()):
    ui.log("Serial port open, waiting for startup message...", k=_k, v='BASIC')
    ui.log("", k=_k, v='BASIC')
    response = readResponse(expectedLines=None)
    if( len(response) >= 2 ):
      ui.log("", k=_k, v='BASIC')
      ui.log("Startup message received, machine ready", k=_k, v='BASIC')
      ui.log("", k=_k, v='BASIC')
    else:
      ui.log("ERROR: startup message error, exiting program", k=_k, v='BASIC')
      quit()
  else:
    ui.log("ERROR opening serial port, exiting program", k=_k, v='BASIC')
    quit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def close():
  return gSerial.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendCommand(command, responseTimeout=gRESPONSE_TIMEOUT, expectedResultLines=1, verbose='BASIC'):
  _k = 'sp.sendCommand()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  command = command.rstrip()
  ui.log(">>>>> [%s]" % repr(command), color=ui.AnsiColors.aaa, k=_k ,v=verbose)
  gSerial.write( bytes(command+"\n", 'UTF-8') )

  return readResponse(expectedLines=expectedResultLines,responseTimeout=responseTimeout,verbose=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readResponse(expectedLines=1, responseTimeout=gRESPONSE_TIMEOUT, verbose='BASIC'):
  _k = 'sp.readResponse()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.log(  "readResponse() - Waiting for %s lines from serial..."
        % (expectedLines if expectedLines != None else 'undefined',)
        , k=_k, v='SUPER')

  startTime = time.time()
  receivedLines = 0
  responseArray=[]

  while( (time.time() - startTime) < responseTimeout ):
    line = gSerial.readline()
    if(line):
      ui.log("<<<<<",line, k=_k, v=verbose)
      receivedLines += 1
      responseArray.append(line)
      if((expectedLines != None) and (receivedLines == expectedLines)):
        ui.log(  "readResponse() - Successfully received %d lines from serial" % expectedLines
              , k=_k, v='SUPER')
        break
  else:
    if(expectedLines != None):
      ui.log("readResponse() - TIMEOUT Waiting for data from serial", k=_k, v='WARNING')
    else:
      ui.log("readResponse() - Finished waiting for undefined lines from serial", k=_k, v='DEBUG')

  return responseArray

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readline():
    line = gSerial.readline()

    if(line):
      line = line.decode('utf-8')
      line = line.strip('\r')
      line = line.strip('\n')

    return line

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def write(data):
  return gSerial.write(bytes(data, 'UTF-8'))
