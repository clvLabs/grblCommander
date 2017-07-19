#!/usr/bin/python3
"""
grblCommander
=============
Allows to control a CNC driven by a grblShield

PENDING
========
- Feed speed configuration ( always send G0 with F )
- Parse machine status response
- Parse general machine responses
"""


import sys
import time

import src.utils as ut
import src.ui as ui
import src.keyboard as kb
import src.serialport as sp
import src.machine as mch
import src.table as tbl
import src.test as test

# Current version
gVERSION = '0.2.0'

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showHelp():
	ui.debugLog("[ Entering showHelp() ]", caller='showHelp()', verbose='DEBUG')

	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR												, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog("Available commands:"											, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog("qQ             - Exit"											, caller='showHelp()', verbose='BASIC')
	ui.debugLog("hH?            - Show this help text"							, caller='showHelp()', verbose='BASIC')
	ui.debugLog("sS             - Show current status"							, caller='showHelp()', verbose='BASIC')
	ui.debugLog("rR             - Reset serial connection"						, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog("gG             - Send raw GCode command"						, caller='showHelp()', verbose='BASIC')
	ui.debugLog("cC             - Clear screen"									, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog("<numpad>       - Safe relative rapid (including diagonals)"	, caller='showHelp()', verbose='BASIC')
	ui.debugLog("<numpad>0      - Safe go to X0Y0Z0"							, caller='showHelp()', verbose='BASIC')
	ui.debugLog("*              - Safe absolute rapid to table corners"			, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog(".              - POINT TEST"									, caller='showHelp()', verbose='BASIC')
	ui.debugLog("tT             - TABLE TEST"									, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog("+/-            - Rapid Increment (XY) +/-"						, caller='showHelp()', verbose='BASIC')
	ui.debugLog("Z/z            - Rapid Increment (Z) +/-"						, caller='showHelp()', verbose='BASIC')
	ui.debugLog("A/a            - Safe Height (Z) +/-"							, caller='showHelp()', verbose='BASIC')
	ui.debugLog("%              - Table size percent (loop)"					, caller='showHelp()', verbose='BASIC')
	ui.debugLog("V/v            - Verbose level +/- (loop)"						, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR												, caller='showHelp()', verbose='BASIC')
	ui.debugLog(""																, caller='showHelp()', verbose='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def processUserInput():
#	ui.debugLog("[ Entering processUserInput() ]", caller='processUserInput()', verbose='DEBUG')

	if not kb.keyPressed():
		return True

	processed = True

	key = kb.readKey()
	char=chr(key)

	if(key == 0):	# Combined code 0+x
		key = kb.readKey()
		char=chr(key)

		if(key == 999999):
			pass

		else:	# Rest of keys
			processed = False
			if(ui.getVerboseLevelStr() == 'DEBUG'):
				ui.keyPressMessage("Pressed unknown COMBINED key 0+%d" % (key,), key, char)
			else:
				pass
				#ui.keyPressMessage("Unknown command", key, char)

	elif(key == 224):	# Combined code 224+x
		key = kb.readKey()
		char=chr(key)

		if(key == 999999):
			pass
		else:	# Rest of keys
			processed = False
			if(ui.getVerboseLevelStr() == 'DEBUG'):
				ui.keyPressMessage("Pressed unknown COMBINED key 224+%d" % (key,), key, char)
			else:
				pass
				#ui.keyPressMessage("Unknown command", key, char)

	else:	# Standard keys


		if(char in 'qQ'):
			ui.keyPressMessage("qQ - Exit", key, char)
			return False

		elif(char in 'hH?'):
			ui.keyPressMessage("hH? - Show help text", key, char)
			showHelp()

		elif(char in 'gG'):
			ui.keyPressMessage("gG - Send raw GCode command", key, char)
			ui.debugLog("Enter command...", caller='processUserInput()', verbose='BASIC')
			userCommand=input()
			sp.sendSerialCommand(userCommand,  expectedResultLines=None, responseTimeout=2)

		elif(char in 'sS'):
			ui.keyPressMessage("sS - Show current status", key, char)
			mch.showStatus()

		elif(char in 'rR'):
			ui.keyPressMessage("rR - Reset serial connection", key, char)
			sp.serialConnect()

		elif(char in 'cC'):
			ui.keyPressMessage("cC - Clear screen", key, char)
			ui.clearScreen()

		elif(char in '.'):
			ui.keyPressMessage(". - POINT TEST", key, char)
			test.automaticContactTest(iterations=1)

		elif(char in 'tT'):
			ui.keyPressMessage("tT - TABLE TEST", key, char)
			test.gridContactTest()

		elif(char == '0'):
			ui.keyPressMessage("<numpad>0 - Safe go to X0Y0Z0", key, char)
			mch.safeRapidAbsolute(x=0,y=0,z=0)

		elif(char == '1'):
			ui.keyPressMessage("<numpad>1 - Safe relative rapid - DL", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY()*-1)

		elif(char == '2'):
			ui.keyPressMessage("<numpad>2 - Safe relative rapid - D", key, char)
			mch.safeRapidRelative(y=tbl.getRI_XY()*-1)

		elif(char == '3'):
			ui.keyPressMessage("<numpad>3 - Safe relative rapid - DR", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY()*-1)

		elif(char == '4'):
			ui.keyPressMessage("<numpad>4 - Safe relative rapid - L", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY()*-1)

		elif(char == '6'):
			ui.keyPressMessage("<numpad>6 - Safe relative rapid - R", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY())

		elif(char == '7'):
			ui.keyPressMessage("<numpad>7 - Safe relative rapid - UL", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY()*-1,y=tbl.getRI_XY())

		elif(char == '8'):
			ui.keyPressMessage("<numpad>8 - Safe relative rapid - U", key, char)
			mch.safeRapidRelative(y=tbl.getRI_XY())

		elif(char == '9'):
			ui.keyPressMessage("<numpad>9 - Safe relative rapid - UR", key, char)
			mch.safeRapidRelative(x=tbl.getRI_XY(),y=tbl.getRI_XY())

		elif(char == '*'):
			ui.keyPressMessage("* - Safe absolute rapid to table corners", key, char)
			ui.debugLog("Use <numpad> to select corner...", caller='processUserInput()', verbose='BASIC')
			key = kb.readKey()
			char=chr(key)

			if(char == '1'):
				ui.keyPressMessage("1 - Safe absolute rapid to table corners - BL", key, char)
				mch.safeRapidAbsolute(x=0,y=0)
			elif(char == '2'):
				ui.keyPressMessage("2 - Safe absolute rapid to table corners - BC", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=0)
			elif(char == '3'):
				ui.keyPressMessage("3 - Safe absolute rapid to table corners - BR", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX(),y=0)
			elif(char == '4'):
				ui.keyPressMessage("4 - Safe absolute rapid to table corners - CL", key, char)
				mch.safeRapidAbsolute(x=0,y=tbl.getMaxY()/2)
			elif(char == '5'):
				ui.keyPressMessage("5 - Safe absolute rapid to table corners - CC", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY()/2)
			elif(char == '6'):
				ui.keyPressMessage("6 - Safe absolute rapid to table corners - CR", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX(),y=tbl.getMaxY()/2)
			elif(char == '7'):
				ui.keyPressMessage("7 - Safe absolute rapid to table corners - UL", key, char)
				mch.safeRapidAbsolute(x=0,y=tbl.getMaxY())
			elif(char == '8'):
				ui.keyPressMessage("8 - Safe absolute rapid to table corners - UC", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX()/2,y=tbl.getMaxY())
			elif(char == '9'):
				ui.keyPressMessage("9 - Safe absolute rapid to table corners - UR", key, char)
				mch.safeRapidAbsolute(x=tbl.getMaxX(),y=tbl.getMaxY())
			else:
				ui.keyPressMessage("Unknown command", key, char)

		elif(char == '+'):
			ui.keyPressMessage("X - Rapid Increment (XY)+", key, char)
			tbl.changeRI_XY(+1)

		elif(char == '-'):
			ui.keyPressMessage("x - Rapid Increment (XY)-", key, char)
			tbl.changeRI_XY(-1)

		elif(char == 'Z'):
			ui.keyPressMessage("Z - Rapid Increment (Z)+", key, char)
			tbl.changeRI_Z(+1)

		elif(char == 'z'):
			ui.keyPressMessage("z - Rapid Increment (Z)-", key, char)
			tbl.changeRI_Z(-1)

		elif(char == '%'):
			ui.keyPressMessage("% - Table size percent (loop)", key, char)
			tmpTableSizePercent = ut.genericValueChanger(	tbl.getTableSizePercent(), +10, tbl.gMIN_TABLE_SIZE_PERCENT, tbl.gMAX_TABLE_SIZE_PERCENT,
															loop=True, valueName="Table size percent")

			tbl.setTableSizePercent(tmpTableSizePercent)

		elif(char == 'V'):
			ui.keyPressMessage("V - Verbose level+", key, char)
			tempVerboseLevel = ut.genericValueChanger(	ui.getVerboseLevel(), +1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
														loop=True, valueName="Verbose level",
														valueFormatter=lambda level : "%d (%s)" % (level,ui.getVerboseLevelStr(level)) )
			ui.setVerboseLevel(tempVerboseLevel)

		elif(char == 'v'):
			ui.keyPressMessage("v - Verbose level-", key, char)
			tempVerboseLevel = ut.genericValueChanger(	ui.getVerboseLevel(), -1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
													loop=True, valueName="Verbose level",
													valueFormatter=lambda level : "%d (%s)" % (level,ui.getVerboseLevelStr(level)) )
			ui.setVerboseLevel(tempVerboseLevel)

		elif(char == 'A'):
			ui.keyPressMessage("A - Safe Height+", key, char)
			tempSafeHeight = ut.genericValueChanger(	tbl.getSafeHeight(), +1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
														loop=True, valueName="Safe Height" )
			tbl.setSafeHeight(tempSafeHeight)

		elif(char == 'a'):
			ui.keyPressMessage("a - Safe Height-", key, char)
			tempSafeHeight = ut.genericValueChanger(	tbl.getSafeHeight(), -1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
														loop=True, valueName="Safe Height" )
			tbl.setSafeHeight(tempSafeHeight)

		else:	# Rest of keys
			processed = False
			if(ui.getVerboseLevelStr() == 'DEBUG'):
				ui.keyPressMessage("Pressed unknown key %d [%s]" % (key,char), key, char)
			else:
				pass
				#ui.keyPressMessage("Unknown command", key, char)

	if(processed):
		ui.showReadyMsg(caller='processUserInput()')

	return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
	ui.debugLog("[ Entering main() ]", caller='main()', verbose='DEBUG')

	ui.clearScreen()

	ui.debugLog("", caller='main()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR, caller='main()', verbose='BASIC')
	ui.debugLog("    grblCommander v{0}".format(gVERSION), caller='main()', verbose='BASIC')
	ui.debugLog(ui.gMSG_SEPARATOR, caller='main()', verbose='BASIC')
	ui.debugLog("", caller='main()', verbose='BASIC')

	sp.serialConnect()

	mch.sendGCodeInitSequence()

	ui.debugLog("", caller='main()', verbose='BASIC')
	ui.debugLog("System ready!", caller='main()', verbose='BASIC')
	ui.debugLog("", caller='main()', verbose='BASIC')

	showHelp()

	mch.showStatus()

	ui.showReadyMsg(caller='main()')

	while(True):

		line = sp.gSerial.readline()
		if(line):
			ui.debugLog("<<<<<",line, caller='main()', verbose='BASIC')

		if not processUserInput():
			break

	ui.debugLog("Closing serial port...", caller='main()', verbose='BASIC')
	sp.gSerial.close()

	ui.debugLog("Closing program...", caller='main()', verbose='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
	try:
		main()
	finally:
		pass
#		ui.debugLog("Press any key to exit...", caller='main()', verbose='BASIC')
#		readKey()
