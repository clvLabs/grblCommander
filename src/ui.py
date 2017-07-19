#!/usr/bin/python3
"""
grblCommander - interface
=========================
User interface management
"""
#print("***[IMPORTING]*** grblCommander - interface")

# Verbose level
gVerboseLevels = [ 'NONE', 'BASIC', 'ERROR', 'WARNING', 'DETAIL', 'SUPER', 'DEBUG' ]
gMIN_VERBOSE_LEVEL = gVerboseLevels.index('BASIC')
gMAX_VERBOSE_LEVEL = len(gVerboseLevels) - 1
gVerboseLevel = gVerboseLevels.index('WARNING')

def getVerboseLevel():		return(gVerboseLevel)
def getVerboseLevelStr(level=None):
	if(level is None):
		return(gVerboseLevels[gVerboseLevel])
	else:
		return(gVerboseLevels[level])

def getVerboseLevelIndex(str):
	return gVerboseLevels.index(str)

def setVerboseLevel(level):
	global gVerboseLevel
	gVerboseLevel = level

# Ready message
gREADY_MSG = "\n***[ Ready ]***\n"

# Standard separator
gMSG_SEPARATOR_LEN = 70
gMSG_SEPARATOR_CHAR = "-"
gMSG_SEPARATOR = gMSG_SEPARATOR_CHAR * gMSG_SEPARATOR_LEN

class AnsiColors:
	aaa = '\033[95m'
	bbb = '\033[94m'
	ccc = '\033[92m'
	ddd = '\033[93m'
	eee = '\033[91m'
	_END = '\033[0m'

"""
#define ANSI_COLOR_RED     "\x1b[31m"
#define ANSI_COLOR_GREEN   "\x1b[32m"
#define ANSI_COLOR_YELLOW  "\x1b[33m"
#define ANSI_COLOR_BLUE    "\x1b[34m"
#define ANSI_COLOR_MAGENTA "\x1b[35m"
#define ANSI_COLOR_CYAN    "\x1b[36m"

#define ANSI_COLOR_BRIGHT  "\x1b[1m"
#define ANSI_COLOR_RESET   "\x1b[0m"
"""

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def debugLog(message,*pargs, **kargs):
	if( "verbose" in kargs ):		verboseStr = kargs.pop("verbose")
	else:							verboseStr = 'BASIC'

	if( "caller" in kargs ):		caller = kargs.pop("caller")
	else:							caller = None

	if( "color" in kargs ):			color = kargs.pop("color")
	else:							color = None

	verboseLevel = getVerboseLevelIndex(verboseStr)

	if( verboseLevel > 0 and verboseLevel <= getVerboseLevel()):	# > 0 to avoid NONE

		if(getVerboseLevelStr() == 'DEBUG'):
			print("%d| " % verboseLevel, end="")

		# Only display caller on DEBUG level
		if((caller is not None) and (getVerboseLevelStr() == 'DEBUG')):
			print("%s - " % caller, end="")

#		if( color != None ):
#			print(color + message + AnsiColors._END, *pargs, **kargs)
#		else:
#			print(message, *pargs, **kargs)

		print(message, *pargs, **kargs)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showReadyMsg(caller=None):
	if(caller is None):
		debugLog(gREADY_MSG, caller='showReadyMsg()', verbose='BASIC')
	else:
		debugLog(gREADY_MSG, caller=caller, verbose='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressMessage(msg, key, char):
#	debugLog("[ Entering keyPressMessage() ]", caller='keyPressMessage()', verbose='DEBUG')

	debugLog("", caller='keyPressMessage()', verbose='WARNING')
	debugLog(gMSG_SEPARATOR, caller='keyPressMessage()', verbose='WARNING')
	debugLog(msg, caller='keyPressMessage()', verbose='WARNING')
	debugLog("", caller='keyPressMessage()', verbose='WARNING')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def clearScreen():
	debugLog("\n"*100, caller='processUserInput()', verbose='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


