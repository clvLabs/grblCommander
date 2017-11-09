#!/usr/bin/python3
"""
grbl - serialport
=================
Serial port management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import os
import time
import serial

from .. import ui as ui

# ------------------------------------------------------------------
# SerialPort class

class SerialPort:

  def __init__(self, cfg):
    ''' Construct a SerialPort object.
    '''
    self.cfg = cfg
    self.spCfg = cfg['serial']

    self.serial = serial.Serial()
    self.serial.baudrate = self.spCfg['baudRate']
    self.serial.timeout = self.spCfg['timeout']


    # Windows
    if os.name == 'nt':
      self.serial.port = self.spCfg['portWindows'] - 1
      self.portName = self.serial.makeDeviceName(self.serial.port)

    # Posix (Linux, OS X)
    else:
      self.serial.port = self.spCfg['portLinux']
      self.portName = self.serial.port


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def close(self):
    ''' Close the serial port
    '''
    ui.log('Closing serial port {:s}...'.format(self.portName))
    return self.serial.close()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def isOpen(self):
    ''' Is the serial port open?
    '''
    return self.serial.isOpen()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def open(self):
    ''' Open the serial port and wait for startup message
    '''
    if self.serial.isOpen():
      self.close()

    ui.log('Opening serial port {:s}...'.format(self.portName))

    try:
      self.serial.open()
    except e:
      pass


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def sendCommand(self,command, responseTimeout=None, verbose='BASIC'):
    ''' Send a command
    '''
    if responseTimeout is None:
      responseTimeout = self.spCfg['responseTimeout']

    command = command.rstrip()
    ui.log('>>>>> {:}'.format(command), color='comms.send' ,v=verbose)
    self.write(command+'\n')

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
    responseArray=[]

    while (time.time() - startTime) < responseTimeout:
      line = self.readline()
      if line:
        finished = False

        if line == 'ok':
          finished = True
        elif line[:6] == "error:":
          ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v='ERROR')
          finished = True
        elif line == "[MSG:'$H'|'$X' to unlock]":
          ui.log('<<<<< {:}'.format(line), color='comms.recv' ,v='WARNING')
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
  def readline(self):
    ''' Read a text line
    '''
    line = self.serial.readline()

    if line:
      line = line.decode('utf-8')
      line = line.strip('\r\n')

      ui.log('Read line: [{:}]'.format(line), v='DEBUG')

    return line


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def write(self,data):
    ''' Write data
    '''
    return self.serial.write(bytes(data, 'UTF-8'))

