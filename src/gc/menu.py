#!/usr/bin/python3
'''
grblCommander - menu
========================
grblCommander menu manager
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

from . import ui as ui
from . import keyboard as kb

# ------------------------------------------------------------------
# Menu Option class

class Option:

  def __init__(self, n=None, k=None, c=None, h=None, ha=None):
    self.n = n        # name
    self.k = k        # key
    self.c = c        # char
    self.h = h        # handler (function)
    self.ha = ha      # handler args (**kwargs)


# ------------------------------------------------------------------
# Menu class

class Menu(object):

  def __init__(self, options=None, settings=None):
    ''' Construct a Menu object '''
    self.options = options

    if settings:
      self.settings = settings
    else:
      self.settings = {
        'readyMsg': None
      }

    self._quit = False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def setOptions(self, options):
    ''' Set options after construction '''
    self.options = options


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def setSettings(self, settings):
    ''' Set settings after construction '''
    self.settings = settings


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def quit(self):
    ''' Use this as a handler for your "quit" option '''
    self._quit = True


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def process(self):
    ''' Call this method frequently to give the menu some processing time '''
    if self._quit:
      return False

    if not self.options:
      return True

    if not kb.keyPressed():
      return True

    return self.parseChar(kb.getch())


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseChar(self, char):
    ''' Parse a character and run the corresponding handler '''
    processed = False
    key = kb.ch2key(char)
    for optKey in self.options:
      opt = self.options[optKey]

      if char in optKey:
        ui.keyPressMessage('{:} - {:}'.format(optKey, opt['n']), key, char)

        if type(opt['h']) is Menu:
          opt['h'].submenu()        # Run handler as submenu
        else:
          if 'ha' in opt:
            opt['h'](**opt['ha'])   # Run handler with arguments
          else:
            opt['h']()              # Run handler without arguments

        processed = True
        break

    if not processed:
      ui.keyPressMessage('Unknown command {:s} ({:d})'.format(char, key), key, char)
    else:
      if self.settings['readyMsg']:
        self.settings['readyMsg']()

    return True


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def showOptions(self):
    ''' Show option list '''
    print('-----------------------------------------------')
    for key in self.options:
      opt = self.options[key]
      keyName = '{:}'.format(key)
      print('{:10s} {:}'.format(keyName, opt['n']))
    print('-----------------------------------------------')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def submenu(self):
    ''' Run self as a submenu '''
    self.showOptions()
    ui.inputMsg('Select command...')
    return self.parseChar(kb.getch())
