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
gCaller = ''

def getVerboseLevel():    return(gVerboseLevel)
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

def log(message,*pargs, **kargs):
  verboseStr = 'BASIC'
  caller = None
  color = None

  if( "verbose" in kargs ):   verboseStr = kargs.pop("verbose")
  if( "v" in kargs ):         verboseStr = kargs.pop("v")

  if( "caller" in kargs ):    caller = kargs.pop("caller")
  if( "k" in kargs ):         caller = kargs.pop("k")

  if( "color" in kargs ):     color = kargs.pop("color")
  if( "c" in kargs ):         color = kargs.pop("c")

  verboseLevel = getVerboseLevelIndex(verboseStr)

  if( verboseLevel > 0 and verboseLevel <= getVerboseLevel()):  # > 0 to avoid NONE

    if(getVerboseLevelStr() == 'DEBUG'):
      print("%d| " % verboseLevel, end="")

    # Only display caller on DEBUG level
    if((caller is not None) and (getVerboseLevelStr() == 'DEBUG')):
      print("%s - " % caller, end="")

#    if( color != None ):
#      print(color + message + AnsiColors._END, *pargs, **kargs)
#    else:
#      print(message, *pargs, **kargs)

    print(message, *pargs, **kargs)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logBlock(message,*pargs, **kargs):
  verboseStr = 'BASIC'
  caller = None
  color = None

  if( "verbose" in kargs ):   verboseStr = kargs.pop("verbose")
  if( "v" in kargs ):         verboseStr = kargs.pop("v")

  if( "caller" in kargs ):    caller = kargs.pop("caller")
  if( "k" in kargs ):         caller = kargs.pop("k")

  if( "color" in kargs ):     color = kargs.pop("color")
  if( "c" in kargs ):         color = kargs.pop("c")

  log("", k=caller, v=verboseStr, c=color)
  log(gMSG_SEPARATOR, k=caller, v=verboseStr, c=color)
  log(message, k=caller, v=verboseStr, c=color)
  log(gMSG_SEPARATOR, k=caller, v=verboseStr, c=color)
  log("", k=caller, v=verboseStr, c=color)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def showReadyMsg(caller=None):
  _k = 'ui.showReadyMsg()'
  # log("[ Entering ]", k=_k, v='DEBUG')

  if(caller is None):
    log(gREADY_MSG, k=_k, v='BASIC')
  else:
    log(gREADY_MSG, k=caller, v='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressMessage(msg, key, char):
  _k = 'ui.keyPressMessage()'
  # log("[ Entering ]", k=_k, v='DEBUG')

  log("", k=_k, v='WARNING')
  log(gMSG_SEPARATOR, k=_k, v='WARNING')
  log(msg, k=_k, v='WARNING')
  log("", k=_k, v='WARNING')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def clearScreen():
  _k = 'ui.clearScreen()'
  log("\n"*100, k=_k, v='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


