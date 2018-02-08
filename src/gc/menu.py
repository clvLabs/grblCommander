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

  def __init__(self, n=None, k=None, c=None, h=None, ha=None, xha=None, \
              SECTION=None, INFO=None, HIDDEN=None):
    self.n = n        # name
    self.k = k        # key
    self.c = c        # char
    self.h = h        # handler (function)
    self.ha = ha      # handler args (**kwargs)
    self.xha = xha    # EXTRA handler args (**kwargs)

    # Special keywords
    self.SECTION = SECTION
    self.INFO = INFO
    self.HIDDEN = HIDDEN

    self.kd = self.keyDisplay(k)   # key (display version)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def keyDisplay(self, k):
    ''' Format a key name/combination for display '''
    if type(k) is str:
      r = k
    elif type(k) is list:
      r = ' / '.join(k)
    else:
      r = k

    return '{:}'.format(r)

# ------------------------------------------------------------------
# Menu class

class Menu(object):

  def __init__(self, kb, options=None, settings=None):
    ''' Construct a Menu object '''
    self.kb = kb
    self.options = []

    if options:
      self.setOptions(options)

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
    for opt in options:
      self.options.append(Option(**opt))


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

    return self.parseKey(self.kb.getKey())


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def isSection(self, opt):
    return opt.SECTION

  def isInfo(self, opt):
    return opt.INFO

  def isHidden(self, opt):
    return opt.HIDDEN

  def isNormal(self, opt):
    return True \
      and not self.isSection(opt) \
      and not self.isInfo(opt) \
      and not self.isHidden(opt) \


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def parseKey(self, key):
    ''' Parse a key and run the corresponding handler '''
    processed = False
    for opt in self.options:
      if self.isNormal(opt) or self.isHidden(opt):
        if opt.k:
          if key._in(opt.k):
            ui.keyPressMessage('{:} - {:}'.format(opt.kd, opt.n), key.k, key.c)

            if type(opt.h) is Menu:
              opt.h.submenu()        # Run handler as submenu
            else:
              # EXTRA handler arguments
              if opt.xha:
                if not opt.ha:
                  opt.ha = {}
                for k in opt.xha:
                  v = opt.xha[k]
                  if k == 'inChar':
                    opt.ha[v] = key.c

              # Regular handler arguments
              if opt.ha:
                opt.h(**opt.ha)   # Run handler with arguments
              else:
                opt.h()              # Run handler without arguments

            processed = True
            break

    if not processed:
      ui.keyPressMessage('Unknown command {:s} ({:d})'.format(key.c, key.k), key.k, key.c)
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
          ui.color(opt.n, 'ui.menuSection'),
          ui.color(ui.gMSG_SEPARATOR, 'ui.menuSection'),
        )
      elif self.isInfo(opt):
        optName = '{:20s} {:}'.format(opt.kd, opt.n)
        txt += ui.color(optName, 'ui.menuItem') + '\n'
      elif self.isHidden(opt):
        pass
      else:
        optName = '{:20s} {:}'.format(opt.kd, opt.n)

        if type(opt.h) is Menu:
          txt += ui.color(optName, 'ui.menuSubmenu') + '\n'
        else:
          txt += ui.color(optName, 'ui.menuItem') + '\n'

    ui.logBlock(txt)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def submenu(self):
    ''' Run self as a submenu '''
    self.showOptions()
    ui.inputMsg('Select command...')
    return self.parseKey(self.kb.getKey())
