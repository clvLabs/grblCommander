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
gSERIAL_BAUDRATE = 9600
gSERIAL_PORTNUMBER_WINDOWS = 5				# Change THIS to match your Arduino's COM port !!!
#gSERIAL_PORTNUMBER_LINUX = '/dev/ttyUSB0'	# Change THIS to match your Arduino's COM port !!!
#gSERIAL_PORTNUMBER_LINUX = '/dev/ttyAMA0'	# Change THIS to match your Arduino's COM port !!!
gSERIAL_PORTNUMBER_LINUX = '/dev/ttyACM0'	# Change THIS to match your Arduino's COM port !!!
gSERIAL_PORTNUMBER = gSERIAL_PORTNUMBER_WINDOWS
gSERIAL_TIMEOUT = 0.1

# Serial response timeout (seconds)
gSERIAL_RESPONSE_TIMEOUT = 5


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def serialConnect():
	global gSerial, gSERIAL_PORTNUMBER

	ui.debugLog("[ Entering serialConnect() ]", caller='serialConnect()', verbose='DEBUG')

	if( ut.isWindows() ):
		gSERIAL_PORTNUMBER = gSERIAL_PORTNUMBER_WINDOWS
	else:
		gSERIAL_PORTNUMBER = gSERIAL_PORTNUMBER_LINUX

	gSerial.baudrate = gSERIAL_BAUDRATE
	gSerial.port = gSERIAL_PORTNUMBER
	gSerial.timeout = gSERIAL_TIMEOUT

	if(gSerial.isOpen()):
		if(ut.isWindows()):
			ui.debugLog("Closing serial port %s: ..." % gSerial.makeDeviceName(gSerial.port), caller='serialConnect()', verbose='BASIC')
		else:
			ui.debugLog("Closing serial port %s: ..." % gSerial.port, caller='serialConnect()', verbose='BASIC')
		gSerial.close()

	if(ut.isWindows()):
		ui.debugLog("Opening serial port %s: ..." % gSerial.makeDeviceName(gSerial.port), caller='serialConnect()', verbose='BASIC')
	else:
		ui.debugLog("Opening serial port %s: ..." % gSerial.port, caller='serialConnect()', verbose='BASIC')

	try:
		gSerial.open()
	except:
		pass

	if(gSerial.isOpen()):
		ui.debugLog("Serial port open, waiting for startup message...", caller='serialConnect()', verbose='BASIC')
		ui.debugLog("", caller='serialConnect()', verbose='BASIC')
		response = readSerialResponse(2)
		if( len(response) == 2 ):
			ui.debugLog("", caller='serialConnect()', verbose='BASIC')
			ui.debugLog("Startup message received, machine ready", caller='serialConnect()', verbose='BASIC')
			ui.debugLog("", caller='serialConnect()', verbose='BASIC')
		else:
			ui.debugLog("ERROR: startup message error, exiting program", caller='serialConnect()', verbose='BASIC')
			quit()
	else:
		ui.debugLog("ERROR opening serial port, exiting program", caller='serialConnect()', verbose='BASIC')
		quit()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def sendSerialCommand(command, responseTimeout=gSERIAL_RESPONSE_TIMEOUT, expectedResultLines=1, verbose='BASIC'):
	ui.debugLog("[ Entering sendSerialCommand() ]", caller='sendSerialCommand()', verbose='DEBUG')

	command = command.rstrip()
	ui.debugLog(">>>>> [%s]" % repr(command), color=ui.AnsiColors.aaa, caller='sendSerialCommand()' ,verbose=verbose)
	gSerial.write( bytes(command+"\n", 'UTF-8') )

	return readSerialResponse(expectedLines=expectedResultLines,responseTimeout=responseTimeout,verbose=verbose)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readSerialResponse(expectedLines=1, responseTimeout=gSERIAL_RESPONSE_TIMEOUT, verbose='BASIC'):
	ui.debugLog("[ Entering readSerialResponse() ]", caller='readSerialResponse()', verbose='DEBUG')

	ui.debugLog(	"readSerialResponse() - Waiting for %s lines from serial..."
				% (expectedLines if expectedLines != None else 'undefined',)
				, caller='readSerialResponse()', verbose='SUPER')

	startTime = time.time()
	receivedLines = 0
	responseArray=[]

	while( (time.time() - startTime) < responseTimeout ):
		line = gSerial.readline()
		if(line):
			ui.debugLog("<<<<<",line, caller='readSerialResponse()', verbose=verbose)
			receivedLines += 1
			responseArray.append(line)
			if((expectedLines != None) and (receivedLines == expectedLines)):
				ui.debugLog(	"readSerialResponse() - Successfully received %d lines from serial" % expectedLines
							, caller='readSerialResponse()', verbose='SUPER')
				break
	else:
		if(expectedLines != None):
			ui.debugLog("readSerialResponse() - TIMEOUT Waiting for data from serial", caller='readSerialResponse()', verbose='WARNING')
		else:
			ui.debugLog("readSerialResponse() - Finished waiting for undefined lines from serial", caller='readSerialResponse()', verbose='DEBUG')

	return responseArray
