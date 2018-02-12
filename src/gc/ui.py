#!/usr/bin/python3
'''
grblCommander - ui
==================
User interface management
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')


# ------------------------------------------------------------------
# UI class

class UI:

  def __init__(self, cfg, kb):
    ''' Construct a UI object.
    '''
    self.cfg = cfg
    self.kb = kb
    self.uiCfg = self.cfg['ui']

    # Verbose level
    self.verboseLevels = [ 'NONE', 'BASIC', 'ERROR', 'WARNING', 'DETAIL', 'SUPER', 'DEBUG' ]
    self.MIN_VERBOSE_LEVEL = self.verboseLevels.index('BASIC')
    self.MAX_VERBOSE_LEVEL = len(self.verboseLevels) - 1
    self.verboseLevel = self.verboseLevels.index(self.uiCfg['verboseLevel'])

    # Standard separator
    self.MSG_SEPARATOR = self.charLine(self.uiCfg['msgSeparatorChar'])
    self.MSG_SEPARATOR_HALF = self.charLine(self.uiCfg['msgSeparatorChar'], 0.5)

    self.TITLE_SEPARATOR = self.charLine(self.uiCfg['titleSeparatorChar'], 0.5)
    self.SUBTITLE_SEPARATOR = self.charLine(self.uiCfg['titleSeparatorChar'], 0.5)

    self.BLOCK_SEPARATOR = self.charLine(self.uiCfg['blockSeparatorChar'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getAnsiColorStr(self, string, foreColor, backColor=None):
    ''' Give a string some ANSI color formatting '''

    if backColor is None:
      colors = foreColor.replace(' ', '').split(',')
      if len(colors) > 1:
        foreColor = colors[0]
        backColor = colors[1]
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

    return '\x1b[{:s}m{:s}\x1b[0;0m'.format(';'.join(attr), string)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def color(self, str, colorName):
    ''' Give a string some ANSI color formatting - allows to use config colors
        Color format examples:
          - ui.title
          - comms.send
          - machineState.Run
    '''
    if '.' in colorName:
      parts = colorName.split('.')
      colorSet = parts[0]
      colorName = parts[1]
    else:
      colorSet = 'ui'

    color = colorName

    if 'colors' in self.uiCfg:
      if colorSet in self.uiCfg['colors']:
        if colorName in self.uiCfg['colors'][colorSet]:
          color = self.uiCfg['colors'][colorSet][colorName]

    return self.getAnsiColorStr(str, color)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def fillLogParams(self, kwargs):
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
  def log(self, message='', **kwargs):
    kwargs = self.fillLogParams(kwargs)

    verboseStr = kwargs.pop('verbose')
    verboseLevel = self.getVerboseLevelIndex(verboseStr)
    _color = kwargs.pop('color')

    if( verboseLevel > 0 and verboseLevel <= self.getVerboseLevel()):  # > 0 to avoid NONE

      if(self.getVerboseLevelStr() == 'DEBUG'):
        print('{:d}| '.format(verboseLevel), end='')

      if _color is not None:
        message = self.color(message, _color)

      print(message, **kwargs)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logBlock(self, message, **kwargs):
    separator = self.BLOCK_SEPARATOR

    while 'separator' in kwargs:   separator = kwargs.pop('separator')
    while 's' in kwargs:           separator = kwargs.pop('s')

    message = message.rstrip(' ').strip('\r\n')
    self.log('\n{:}\n{:}\n{:}'.format(separator, message, separator), **kwargs)
    self.log('', **kwargs)  # Additional separator line NOT colored!


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logTitle(self, text, **kwargs):
    if not 'color' in kwargs:    kwargs['color'] = 'ui.title'
    self.log('{:s}[{:s}]'.format(self.TITLE_SEPARATOR, text), **kwargs)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def logSubtitle(self, text, **kwargs):
    if not 'color' in kwargs:    kwargs['color'] = 'ui.subtitle'
    self.log('{:s}[{:s}]'.format(self.SUBTITLE_SEPARATOR, text), **kwargs)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def inputMsg(self, text, **kwargs):
    if not 'color' in kwargs:    kwargs['color'] = 'ui.inputMsg'
    self.log('{:}'.format(text), **kwargs)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def readyMsg(self, extraInfo=None):
    self.log()
    if extraInfo:
      self.log('{:}'.format(extraInfo))
    self.log('{:}'.format(self.color(self.uiCfg['readyMsg'], 'ui.readyMsg')))


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def keyPressMessage(self, message):
    # self.log('\n{:}\n{:}\n'.format(self.MSG_SEPARATOR, message)
    self.log('{:}\n{:}\n'.format(self.MSG_SEPARATOR, message)
      , c='ui.keyPressMsg', v='WARNING')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def clearScreen(self):
    self.log('\n' * self.uiCfg['clearScreenLines'])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def charLine(self, char, widthMultiplier=1):
    return char * int(self.uiCfg['maxLineLen'] * widthMultiplier)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def clearLine(self):
    self.log('\r{:}'.format(self.charLine(' ')), end='')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getUserInput(self, description, dataType='str', default=None):
    titleWidth = self.uiCfg['inputTitleWidth']
    self.inputMsg('Enter {:}:'.format(description)[:titleWidth].ljust(titleWidth), end='')
    userInput = self.kb.input()
    try:
      userInput = dataType(userInput)
      return userInput
    except:
      return default


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def userConfirm(self, message, password):
    ''' TODO: comment
    '''
    while True:
      self.log('''
      {:}
      (please enter '{:}' to continue)
      '''.format(message, password), c='ui.confirmMsg')

      self.inputMsg('Enter confirmation text')
      typedPassword = self.kb.input()

      if typedPassword == '':
        continue
      elif typedPassword == password:
        return True
      else:
        return False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def coordStr(self, c):
    cFmt = self.uiCfg['coordFormat']
    return cFmt.format(c)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def coloredXyzStr(self, x, y, z, xColor='', yColor='', zColor=''):
    xyzFmt = self.uiCfg['xyzFormat']
    return xyzFmt.format(
      self.color(self.coordStr(x), xColor ),
      self.color(self.coordStr(y), yColor ),
      self.color(self.coordStr(z), zColor ),
      )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def xyzStr(self, x, y, z):
    xyzFmt = self.uiCfg['xyzFormat']
    return xyzFmt.format(
      self.coordStr(x),
      self.coordStr(y),
      self.coordStr(z),
      )


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getVerboseLevel(self):
    return(self.verboseLevel)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getVerboseLevelStr(self, level=None):
    if(level is None):
      return(self.verboseLevels[self.verboseLevel])
    else:
      return(self.verboseLevels[level])


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getVerboseLevelIndex(self, str):
    return self.verboseLevels.index(str)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def setVerboseLevel(self, level):
    self.verboseLevel = level
