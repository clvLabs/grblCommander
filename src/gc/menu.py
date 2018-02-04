#!/usr/bin/python3
'''
grblCommander - menu
========================
grblCommander menu manager
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

from . import ui as ui

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

  def __init__(self, kb, options=None, settings=None):
    ''' Construct a Menu object '''
    self.kb = kb
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

    if not self.kb.keyPressed():
      return True

    return self.parseChar(self.kb.getch())


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def isSection(self, opt):
    return 'SECTION' in opt

  def isInfo(self, opt):
    return 'INFO' in opt

  def isHidden(self, opt):
    return 'HIDDEN' in opt

  def isNormal(self, opt):
    return not self.isSection(opt) and not self.isInfo(opt) and not self.isHidden(opt)

  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseChar(self, char):
    ''' Parse a character and run the corresponding handler '''
    processed = False
    key = self.kb.ch2key(char)
    for opt in self.options:
      if self.isNormal(opt) or self.isHidden(opt):
        if 'k' in opt:
          if char in opt['k']:
            ui.keyPressMessage('{:} - {:}'.format(opt['k'], opt['n']), key, char)

            if type(opt['h']) is Menu:
              opt['h'].submenu()        # Run handler as submenu
            else:
              # EXTRA handler arguments
              if 'xha' in opt:
                if not 'ha' in opt:
                  opt['ha'] = {}
                for k in opt['xha']:
                  v = opt['xha'][k]
                  if k == 'inChar':
                    opt['ha'][v] = char

              # Regular handler arguments
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
    txt = ''
    for opt in self.options:
      if self.isSection(opt):
        txt += '\n{:}\n{:}\n'.format(
          ui.color(opt['n'], 'ui.menuSection'),
          ui.color(ui.gMSG_SEPARATOR, 'ui.menuSection'),
        )
      elif self.isInfo(opt):
        keyName = '{:}'.format(opt['k'])
        optName = '{:20s} {:}'.format(keyName, opt['n'])
        txt += optName + '\n'
      elif self.isHidden(opt):
        pass
      else:
        keyName = '{:}'.format(opt['k'])
        optName = '{:20s} {:}'.format(keyName, opt['n'])

        if type(opt['h']) is Menu:
          optName = ui.color(optName, 'ui.menuSubmenu')
        else:
          optName = ui.color(optName, 'ui.menuItem')

        txt += optName + '\n'

    ui.logBlock(txt)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def submenu(self):
    ''' Run self as a submenu '''
    self.showOptions()
    ui.inputMsg('Select command...')
    return self.parseChar(self.kb.getch())
