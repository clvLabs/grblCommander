#!/usr/bin/python3
"""
grblCommander - ui
==================
User interface management
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

from enum import Enum
from . import keyboard as kb
from src.gc.config import cfg
# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
uiCfg = cfg['ui']


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Give a string some ANSI color formatting
def colorStr(string, foreColor, backColor=None):

  if backColor is None:
    colors = foreColor.replace(' ', '').split(',')
    if len(colors) > 1:
      foreColor=colors[0]
      backColor=colors[1]
    else:
      backColor = 'black'

  attr = []

  if foreColor.find('+') != -1:
    foreColor = foreColor.replace('+','')
    attr.append('1')  # bright

  if foreColor == 'black':       attr.append('30')
  elif foreColor == 'red':       attr.append('31')
  elif foreColor == 'green':     attr.append('32')
  elif foreColor == 'yellow':    attr.append('33')
  elif foreColor == 'blue':      attr.append('34')
  elif foreColor == 'magenta':   attr.append('35')
  elif foreColor == 'cyan':      attr.append('36')
  elif foreColor == 'white':     attr.append('37')

  if backColor == 'black':  pass
  elif backColor == 'red':       attr.append('41')
  elif backColor == 'green':     attr.append('42')
  elif backColor == 'yellow':    attr.append('43')
  elif backColor == 'blue':      attr.append('44')
  elif backColor == 'magenta':   attr.append('45')
  elif backColor == 'cyan':      attr.append('46')
  elif backColor == 'white':     attr.append('47')

  return '\x1b[{:s}m{:s}\x1b[0m'.format(';'.join(attr), string)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Give a string some ANSI color formatting - allows to use config colors
# Color format examples:
#  - ui.title
#  - comms.send
#  - machineState.Run
#
def setStrColor(str, colorName):
  if '.' in colorName:
    parts = colorName.split('.')
    colorSet = parts[0]
    colorName = parts[1]
  else:
    colorSet = 'ui'

  color = colorName

  if 'colors' in uiCfg:
    if colorSet in uiCfg['colors']:
      if colorName in uiCfg['colors'][colorSet]:
        color = uiCfg['colors'][colorSet][colorName]

  return colorStr(str, color)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def fillLogParams(kwargs):
  verboseStr = 'BASIC'
  color = None

  while 'verbose' in kwargs:   verboseStr = kwargs.pop('verbose')
  while 'v' in kwargs:         verboseStr = kwargs.pop('v')

  while 'color' in kwargs:     color = kwargs.pop('color')
  while 'c' in kwargs:         color = kwargs.pop('c')

  # Write values back
  kwargs['verbose'] = verboseStr
  kwargs['color'] = color

  return kwargs

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def log(message='', **kwargs):
  kwargs = fillLogParams(kwargs)

  verboseStr = kwargs.pop('verbose')
  verboseLevel = getVerboseLevelIndex(verboseStr)
  color = kwargs.pop('color')

  if( verboseLevel > 0 and verboseLevel <= getVerboseLevel()):  # > 0 to avoid NONE

    if(getVerboseLevelStr() == 'DEBUG'):
      print('{:d}| '.format(verboseLevel), end='')

    if color is not None:
      message = setStrColor(message, color)

    print(message, **kwargs)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logBlock(message, **kwargs):
  separator = gBLOCK_SEPARATOR

  while 'separator' in kwargs:   separator = kwargs.pop('separator')
  while 's' in kwargs:           separator = kwargs.pop('s')

  message = message.rstrip(' ').strip('\r\n')
  log('\n{:}\n{:}\n{:}'.format(separator, message, separator), **kwargs)
  log('', **kwargs)  # Additional separator line NOT colored!

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logTitle(text, **kwargs):
  if not 'color' in kwargs:    kwargs['color'] = 'ui.title'
  log('{:s}[{:s}]'.format(gTITLE_SEPARATOR, text), **kwargs)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def logSubtitle(text, **kwargs):
  if not 'color' in kwargs:    kwargs['color'] = 'ui.subtitle'
  log('{:s}[{:s}]'.format(gSUBTITLE_SEPARATOR, text), **kwargs)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def inputMsg(text, **kwargs):
  if not 'color' in kwargs:    kwargs['color'] = 'ui.inputMsg'
  log('{:}'.format(text), **kwargs)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def readyMsg(extraInfo=None):
  log()
  if extraInfo:
    log('{:}'.format(extraInfo))
  log('{:}'.format(setStrColor(uiCfg['readyMsg'], 'ui.readyMsg')))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressMessage(message, key, char):
  # log('\n{:}\n{:}\n'.format(gMSG_SEPARATOR, message)
  log('{:}\n{:}\n'.format(gMSG_SEPARATOR, message)
    , color='ui.keyPressMsg', v='WARNING')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def clearScreen():
  log('\n' * uiCfg['clearScreenLines'])

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def charLine(char, widthMultiplier=1):
  return char * int(uiCfg['maxLineLen'] * widthMultiplier)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def clearLine():
  log('\r{:}'.format(charLine(' ')), end='')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getUserInput(description, dataType='str', default=None):
  titleWidth = uiCfg['inputTitleWidth']
  inputMsg('Enter {:}:'.format(description)[:titleWidth].ljust(titleWidth), end='')
  userInput=input()
  try:
    userInput=dataType(userInput)
    return userInput
  except:
    return default



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def waitForEnterOrEscape(message):
  ''' TODO: comment
  '''
  msg = """{:}
  (press <ENTER> or <ESC>)""".format(message)

  log()
  inputMsg(msg)
  while True:
    while not kb.keyPressed():
      key = kb.readKey()
      if key == kb.ENTER:
        return True
      elif key == kb.ESC:
        return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def userConfirm(message, password):
  ''' TODO: comment
  '''
  while True:
    log("""
    {:}
    (please enter '{:}' to continue)
    """.format(message, password), color='ui.confirmMsg')

    inputMsg('Enter confirmation text')
    typedPassword=input()

    if typedPassword == '':
      continue
    elif typedPassword == password:
      return True
    else:
      return False

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def coordStr(c):
  cFmt = uiCfg['coordFormat']
  return cFmt.format(c)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def ColoredXyzStr(x, y, z, xColor='', yColor='', zColor=''):
  xyzFmt = uiCfg['xyzFormat']
  return xyzFmt.format(
    setStrColor(coordStr(x), xColor ),
    setStrColor(coordStr(y), yColor ),
    setStrColor(coordStr(z), zColor ),
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def xyzStr(x, y, z):
  xyzFmt = uiCfg['xyzFormat']
  return xyzFmt.format(
    coordStr(x),
    coordStr(y),
    coordStr(z),
    )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Verbose level
class v(Enum):
  NONE = 0
  BASIC = 1
  ERROR = 2
  WARNING = 3
  DETAIL = 4
  SUPER = 5
  DEBUG = 6

gVerboseLevels = [ 'NONE', 'BASIC', 'ERROR', 'WARNING', 'DETAIL', 'SUPER', 'DEBUG' ]
gMIN_VERBOSE_LEVEL = gVerboseLevels.index('BASIC')
gMAX_VERBOSE_LEVEL = len(gVerboseLevels) - 1
gVerboseLevel = gVerboseLevels.index(uiCfg['verboseLevel'])

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

# Standard separator
gMSG_SEPARATOR = charLine(uiCfg['msgSeparatorChar'])
gMSG_SEPARATOR_HALF = charLine(uiCfg['msgSeparatorChar'], 0.5)

gTITLE_SEPARATOR = charLine(uiCfg['titleSeparatorChar'], 0.5)
gSUBTITLE_SEPARATOR = charLine(uiCfg['titleSeparatorChar'], 0.5)

gBLOCK_SEPARATOR = charLine(uiCfg['blockSeparatorChar'])
