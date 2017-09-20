#!/usr/bin/python3
"""
grblCommander - macro
========================
grblCommander macro manager
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import importlib
from pathlib import Path, PurePath

from . import ui as ui
from . import keyboard as kb
from . import serialport as sp
from . import machine as mch
from src.gc.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
mcrCfg = cfg['macro']

gMACROS = {}
gSUPPORT_FILES = {}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def load(silent=False):
  global gMACROS, gSUPPORT_FILES
  gMACROS = {}

  # Reload support files before macros
  for index in gSUPPORT_FILES:
    try:
      importlib.reload(gSUPPORT_FILES[index])
    except:
      pass
  gSUPPORT_FILES = {}

  loadFolder('src/macros', silent=silent)

  if not silent:
    ui.log()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def loadFolder(folder='', silent=False):
  global gMACROS

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
      for item in mcrCfg['blackList']:
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
          gSUPPORT_FILES[macroName] = tmpModule
          continue

        if 'title' in tmpMacro and 'commands' in tmpMacro:
          gMACROS[macroShortName] = tmpMacro
          if not silent:
            ui.log('[{:}]'.format(macroShortName), end=' ')
        else:
          if not silent:
            ui.log('[{:}]'.format(macroShortName), color='ui.errorMsg', end=' ')
      except ImportError:
        if not silent:
          ui.log('[{:}]'.format(macroShortName), color='ui.errorMsg', end=' ')

  for item in Path(folder).glob('*'):
    if item.is_dir():
      folderName = PurePath(item).as_posix()
      loadFolder(folderName, silent=silent)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def list():
  if mcrCfg['autoReload']:
    load(silent=True)

  maxNameLen = 0
  for macroName in gMACROS:
    if len(macroName) > maxNameLen:
      maxNameLen = len(macroName)

  block = ''
  block += '  Available macros:\n\n'
  block += '  {:}   {:} {:}\n\n'.format(
    'Name'.ljust(maxNameLen),
    'Lines'.ljust(5),
    'title'
    )

  for macroName in sorted(gMACROS):
    macro = gMACROS[macroName]
    title = macro['title'] if 'title' in macro else ''
    commands = macro['commands']

    block += '  {:}   {:} {:}\n'.format(
      macroName.ljust(maxNameLen),
      str(len(commands)).ljust(5),
      title
      )

  ui.logBlock(block)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def run(name, silent=False, isSubCall=False):
  success = _run(name, silent=silent)

  if not success:
    ui.logTitle('Restoring machine settings after macro cancel')
    _run(mcrCfg['startup'], silent=True)

  return success

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def _run(name, silent=False, isSubCall=False):
  if mcrCfg['autoReload']:
    load(silent=True)

  if not name in gMACROS:
    ui.log('ERROR: Macro [{:}] does not exist, please check config file.'.format(name),
      color='ui.errorMsg')
    return False

  macro = gMACROS[name]
  commands = macro['commands']

  if not silent:
    if isSubCall:
      ui.logTitle('Macro [{:}] subcall START'.format(name), color='macro.subCallStart')
    else:
      show(name, avoidReload=True)

      ui.inputMsg('Press y/Y to execute, any other key to cancel...')
      key=kb.readKey()
      char=chr(key)

      if not char in 'yY':
        ui.logBlock('MACRO [{:}] CANCELLED'.format(name), color='ui.cancelMsg')
        return False

  for command in commands:
    cmdName = command[0] if len(command) > 0 else ''
    cmdComment = command[1] if len(command) > 1 else ''
    isReservedName = cmdName in mcrCfg['reservedNames']
    isMacroCall = cmdName in gMACROS

    if cmdComment:
      # if not silent:
      ui.logTitle(cmdComment, color='macro.macroCall' if isMacroCall else 'macro.comment')

    if cmdName:
      if isReservedName:
        ui.logTitle(cmdName, color='macro.reservedName')
        if cmdName == 'PAUSE':
          ui.inputMsg('Paused, press <ENTER> to continue / <ESC> to exit ...')
          key=0
          while( key != 13 and key != 10 and key != 27 ):
            key=kb.readKey()

          if key == 27:  # <ESC>
            ui.logBlock('MACRO [{:}] CANCELLED'.format(name), color='ui.cancelMsg')
            return False
          elif key == 13 or key == 10:  # <ENTER>
            continue

        elif cmdName == 'STARTUP':
          cmdName = mcrCfg['startup']
          isMacroCall = cmdName in gMACROS

      if isMacroCall:
        if not _run(cmdName, silent=silent, isSubCall=True):
          ui.logBlock('MACRO [{:}] CANCELLED'.format(name), color='ui.cancelMsg')
          return False
      else:
        sp.sendCommand(cmdName)
        if not silent:
          mch.waitForMachineIdle()

    if kb.keyPressed():
      if kb.readKey() == 27:  # <ESC>
        ui.logBlock('MACRO [{:}] CANCELLED'.format(name), color='ui.cancelMsg')
        return False

  if not silent:
    if isSubCall:
      ui.logTitle('Macro [{:}] subCall END'.format(name), color='macro.subCallEnd')
    else:
      ui.logBlock('MACRO [{:}] FINISHED'.format(name), color='ui.finishedMsg')

  if not isSubCall:
    ui.log()

  return True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def show(name, avoidReload=False):
  if mcrCfg['autoReload'] and not avoidReload:
    load(silent=True)

  if not name in gMACROS:
    ui.log('ERROR: Macro [{:}] does not exist, check config file.'.format(name),
      color='ui.errorMsg')
    return

  macro = gMACROS[name]
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
    isMacroCall = cmdName in gMACROS
    isReservedName = cmdName in mcrCfg['reservedNames']
    cmdColor = 'macro.macroCall' if isMacroCall else 'macro.reservedName' if isReservedName else 'macro.command'

    block += '{:}   {:}\n'.format(
      ui.setStrColor(cmdName.ljust(maxCommandLen), cmdColor),
      ui.setStrColor(cmdComment, 'macro.comment') )

  ui.logBlock(block)
