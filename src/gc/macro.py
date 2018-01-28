#!/usr/bin/python3
'''
grblCommander - macro
========================
grblCommander macro manager
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import importlib
import time
from pathlib import Path, PurePath

from . import ui as ui
from . import keyboard as kb


# ------------------------------------------------------------------
# Macro class

class Macro:

  def __init__(self, grbl):
    ''' Construct a Macro object.
    '''
    self.grbl = grbl
    self.cfg = grbl.getConfig()
    self.mcrCfg = self.cfg['macro']

    self.macros = {}
    self.supportFiles = {}


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getConfig(self):
    ''' Get working configuration
    '''
    return self.cfg


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def load(self, silent=False):
    ''' TODO: comment
    '''
    self.macros = {}

    # Reload support files before macros
    for index in self.supportFiles:
      try:
        importlib.reload(self.supportFiles[index])
      except:
        pass
    self.supportFiles = {}

    self.loadFolder('src/macros', silent=silent)

    if not silent:
      ui.log()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def loadFolder(self,folder='', silent=False):
    ''' TODO: comment
    '''
    dotBasePath = 'src.macros.'

    if folder[-1] != '/':
      folder += '/'

    dotPath = folder.replace('/','.')

    # Find macros and subfolders
    for item in Path(folder).glob('*.py'):
      if item.is_file():
        fileName = item.name[:-3]

        if fileName == '__init__':    # IGNORE __init__.py !!!
          continue

        macroName = dotPath + fileName
        macroShortName = macroName.replace(dotBasePath,'')

        blackListed = False
        for item in self.mcrCfg['blackList']:
          if macroShortName[:len(item)] == item:
            blackListed = True
            continue

        if blackListed:
          continue

        try:
          tmpModule = __import__(macroName, fromlist=[''])
          importlib.reload(tmpModule)

          try:
            tmpMacro = tmpModule.macro
          except AttributeError:
            self.supportFiles[macroName] = tmpModule
            continue

          if 'title' in tmpMacro and 'commands' in tmpMacro:
            self.macros[macroShortName] = tmpMacro
            if not silent:
              ui.log('[{:}]'.format(macroShortName), end=' ')
          else:
            if not silent:
              ui.log('[{:}]'.format(macroShortName), c='ui.errorMsg', end=' ')
        except:
          if not silent:
            ui.log('[{:}]'.format(macroShortName), c='ui.errorMsg', end=' ')

    for item in Path(folder).glob('*'):
      if item.is_dir():
        folderName = PurePath(item).as_posix()
        self.loadFolder(folderName, silent=silent)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def list(self):
    ''' TODO: comment
    '''
    if self.mcrCfg['autoReload']:
      self.load(silent=True)

    maxNameLen = 0
    for macroName in self.macros:
      if len(macroName) > maxNameLen:
        maxNameLen = len(macroName)

    block = ''
    block += '  Available macros:\n\n'
    block += '  {:}   {:} {:}\n\n'.format(
      'Name'.ljust(maxNameLen),
      'Lines'.ljust(5),
      'title'
      )

    for macroName in sorted(self.macros):
      macro = self.macros[macroName]
      title = macro['title'] if 'title' in macro else ''
      commands = macro['commands']

      block += '  {:}   {:} {:}\n'.format(
        macroName.ljust(maxNameLen),
        str(len(commands)).ljust(5),
        title
        )

    ui.logBlock(block)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def run(self,name, silent=False, isSubCall=False):
    ''' TODO: comment
    '''
    success = self._run(name, silent=silent)

    if not success:
      ui.logTitle('Restoring machine settings after macro cancel')
      self._run(self.mcrCfg['startup'], silent=True)

    return success


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def isMacro(self,name):
    ''' TODO: comment
    '''
    for macroName in self.macros:
      if macroName.lower() == name.lower():
        return True
    return False


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def getMacro(self,name):
    ''' TODO: comment
    '''
    for macroName in self.macros:
      if macroName.lower() == name.lower():
        return self.macros[macroName]
    return None


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def _run(self,name, silent=False, isSubCall=False):
    ''' TODO: comment
    '''
    if self.mcrCfg['autoReload']:
      self.load(silent=True)

    macro = self.getMacro(name)
    if not macro:
      ui.log('ERROR: Macro [{:}] does not exist, please check config file.'.format(name),
        color = 'ui.errorMsg')
      return False

    commands = macro['commands']

    if not silent:
      if isSubCall:
        ui.logTitle('Macro [{:}] subcall START'.format(name), c='macro.subCallStart')
      else:
        self.show(name, avoidReload=True)

        ui.inputMsg('Press y/Y to execute, any other key to cancel...')
        char = kb.getch()

        if not char in 'yY':
          ui.logBlock('MACRO [{:}] CANCELLED'.format(name), c='ui.cancelMsg')
          return False

    for command in commands:
      cmdName = command[0] if len(command) > 0 else ''
      cmdComment = command[1] if len(command) > 1 else ''
      isReservedName = cmdName.lower().split(' ')[0] in self.mcrCfg['reservedNames']
      isMacroCall = self.isMacro(cmdName)

      if cmdComment:
        color = 'macro.comment'
        if not cmdName:
          color = 'macro.headerComment'
        if isMacroCall:
          color = 'macro.macroCall'

        ui.logTitle(cmdComment, c=color)

      if cmdName:
        if isReservedName:
          ui.logTitle(cmdName, c='macro.reservedName')

          if cmdName.lower() == 'pause':
            ui.inputMsg('Paused, press <ENTER> to continue / <ESC> to exit ...')
            key = 0
            while key != kb.CR and key != kb.LF and key != kb.ESC:
              key = kb.getKey()

            if key == kb.ESC:
              ui.logBlock('MACRO [{:}] CANCELLED'.format(name), c='ui.cancelMsg')
              return False
            elif key == kb.CR or key == kb.LF:
              continue

          elif cmdName.lower() == 'startup':
            cmdName = self.mcrCfg['startup']
            isMacroCall = self.isMacro(cmdName)

          elif cmdName[:5].lower() == 'sleep':
            time.sleep(float(cmdName[5:]))
            continue

        if isMacroCall:
          if not self._run(cmdName, silent=silent, isSubCall=True):
            ui.logBlock('MACRO [{:}] CANCELLED'.format(name), c='ui.cancelMsg')
            return False
        else:
          self.grbl.send(cmdName)
          if not silent:
            self.grbl.waitForMachineIdle()

      if kb.keyPressed():
        if kb.getKey() == kb.ESC:
          ui.logBlock('MACRO [{:}] CANCELLED'.format(name), c='ui.cancelMsg')
          return False

    if not silent:
      if isSubCall:
        ui.logTitle('Macro [{:}] subCall END'.format(name), c='macro.subCallEnd')
      else:
        ui.logBlock('MACRO [{:}] FINISHED'.format(name), c='ui.finishedMsg')

    if not isSubCall:
      ui.log()

    return True


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def show(self,name, avoidReload=False):
    ''' TODO: comment
    '''
    if self.mcrCfg['autoReload'] and not avoidReload:
      self.load(silent=True)

    macro = self.getMacro(name)
    if not macro:
      ui.log('ERROR: Macro [{:}] does not exist, check config file.'.format(name),
        c='ui.errorMsg')
      return

    title = macro['title'] if 'title' in macro else ''

    commands = macro['commands']

    block = ui.setStrColor('Macro [{:}] - {:} ({:} lines)\n\n'.format(
      name, title, len(commands)), 'ui.title')

    if 'description' in macro:
      description = macro['description'].rstrip(' ').strip('\r\n')
      block += ui.setStrColor(description, 'ui.msg') + '\n\n'

    maxCommandLen = 0
    for command in commands:
      cmdName = command[0] if len(command) > 0 else ''
      cmdComment = command[1] if len(command) > 1 else ''

      if len(cmdName) > maxCommandLen:
        maxCommandLen = len(cmdName)

    for command in commands:
      cmdName = command[0] if len(command) > 0 else ''
      cmdComment = command[1] if len(command) > 1 else ''
      isMacroCall = self.isMacro(cmdName)
      isReservedName = cmdName.lower() in self.mcrCfg['reservedNames']
      cmdColor = 'macro.macroCall' if isMacroCall else 'macro.reservedName' if isReservedName else 'macro.command'

      commentColor = 'macro.comment'
      if not cmdName:
        commentColor = 'macro.headerComment'

      block += '{:}   {:}\n'.format(
        ui.setStrColor(cmdName.ljust(maxCommandLen), cmdColor),
        ui.setStrColor(cmdComment, commentColor) )

    ui.logBlock(block)
