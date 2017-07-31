#!/usr/bin/python3
"""
grblCommander
=============
Allows to control a CNC driven by a grblShield
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
  _k = 'main.showHelp()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.logBlock(
  """
  Available commands:

  qQ             - Exit
  hH?            - Show this help text
  sS             - Show current status
  rR             - Reset serial connection

  gG             - Send raw GCode command
  cC             - Clear screen

  /*             - Relative rapid (Z) +/-
  <numpad>0      - Safe go to X0Y0Z0
  <numpad>       - Safe relative rapid (XY) (including diagonals)
  .              - Safe absolute rapid (XY) to table corners:
                   - <numpad>1..9   - Absolute table positions
                   - sS             - Table position scan
                   - .              - One axis only:
                     - <numpad>2468   - Absolute table positions

  tT             - Tests:
                   - pP             - Point test
                   - tT             - Table test
                   - lL             - Base levelling holes
                   - zZ             - Zig-zag pattern

  +-             - Set rapid increment (XY) +/-
  Zz             - Set rapid increment (Z) +/-
  Aa             - Set safe height (Z) +/-
  %              - Set table size percent (loop)
  Vv             - Set verbose level +/- (loop)
  """
    , k=_k, v='BASIC')

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def tpsSingleStep(stepName, x, y):
  _k = 'main.tpsSingleStep()'
  ui.log("----------------------- Scan point: [{0}]".format(stepName), k=_k, v='WARNING')

  mch.safeRapidAbsolute(x=x,y=y)

  if kb.keyPressed() and (kb.readKey() == 27):  # <ESC>
    ui.logBlock("TABLE POSITION SCAN CANCELLED", s="*"*40, k=_k, v='BASIC')
    return True

  return False


def tablePositionScan():
  _k = 'main.tablePositionScan()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  savedX = tbl.getX()
  savedY = tbl.getY()
  cancelled = False

  if not cancelled: cancelled = tpsSingleStep('BL', x=0,y=0)
  if not cancelled: cancelled = tpsSingleStep('BC', x=tbl.getMaxX()/2,y=0)
  if not cancelled: cancelled = tpsSingleStep('BR', x=tbl.getMaxX(),y=0)
  if not cancelled: cancelled = tpsSingleStep('CR', x=tbl.getMaxX(),y=tbl.getMaxY()/2)
  if not cancelled: cancelled = tpsSingleStep('CC', x=tbl.getMaxX()/2,y=tbl.getMaxY()/2)
  if not cancelled: cancelled = tpsSingleStep('CL', x=0,y=tbl.getMaxY()/2)
  if not cancelled: cancelled = tpsSingleStep('UL', x=0,y=tbl.getMaxY())
  if not cancelled: cancelled = tpsSingleStep('UC', x=tbl.getMaxX()/2,y=tbl.getMaxY())
  if not cancelled: cancelled = tpsSingleStep('UR', x=tbl.getMaxX(),y=tbl.getMaxY())

  tpsSingleStep('Return', x=savedX,y=savedY)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def processUserInput():
  _k = 'main.processUserInput()'
#  ui.log("[ Entering ]", k=_k, v='DEBUG')

  if not kb.keyPressed():
    return True

  processed = True

  key = kb.readKey()
  char=chr(key)

  if(key == 0):  # Combined code 0+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage("Pressed unknown COMBINED key 0+%d" % (key,), key, char)
      else:
        pass
        #ui.keyPressMessage("Unknown command", key, char)

  elif(key == 224):  # Combined code 224+x
    key = kb.readKey()
    char=chr(key)

    if(key == 999999):
      pass
    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage("Pressed unknown COMBINED key 224+%d" % (key,), key, char)
      else:
        pass
        #ui.keyPressMessage("Unknown command", key, char)

  else:  # Standard keys

    if(char in 'qQ'):
      ui.keyPressMessage("qQ - Exit", key, char)
      return False

    elif(char in 'hH?'):
      ui.keyPressMessage("hH? - Show help text", key, char)
      showHelp()

    elif(char in 'gG'):
      ui.keyPressMessage("gG - Send raw GCode command", key, char)
      ui.log("Enter command...", k=_k, v='BASIC')
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

    elif(char in 'tT'):
      ui.keyPressMessage("tT - Tests", key, char)
      ui.log("Select test to run...", k=_k, v='BASIC')
      key = kb.readKey()
      char=chr(key)

      if(char in 'pP'):
        ui.keyPressMessage("pP - Point test", key, char)
        test.automaticContactTest(iterations=1)

      elif(char in 'tT'):
        ui.keyPressMessage("tT - Table test", key, char)
        test.gridContactTest()

      elif(char in 'lL'):
        ui.keyPressMessage("lL - Base levelling holes", key, char)
        test.baseLevelingHoles()

    elif(char == '/'):
      ui.keyPressMessage("/ - Relative rapid (Z)+", key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z())

    elif(char == '*'):
      ui.keyPressMessage("* - Relative rapid (Z)-", key, char)
      mch.safeRapidRelative(x=0,y=0,z=tbl.getRI_Z()*-1)

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

    elif(char == '.'):
      ui.keyPressMessage("* - Safe absolute rapid to table corners", key, char)
      ui.log("Use <numpad> to select corner...", k=_k, v='BASIC')
      key = kb.readKey()
      char=chr(key)

      if(char == '.'):
        ui.keyPressMessage("* - ONE AXIS ONLY", key, char)
        ui.log("Use <numpad> to select corner...", k=_k, v='BASIC')
        key = kb.readKey()
        char=chr(key)

        if(char == '2'):
          ui.keyPressMessage("2 - ONE AXIS ONLY - Safe absolute rapid to table corners - BC", key, char)
          mch.safeRapidAbsolute(y=0)
        elif(char == '4'):
          ui.keyPressMessage("4 - ONE AXIS ONLY - Safe absolute rapid to table corners - CL", key, char)
          mch.safeRapidAbsolute(x=0)
        elif(char == '6'):
          ui.keyPressMessage("6 - ONE AXIS ONLY - Safe absolute rapid to table corners - CR", key, char)
          mch.safeRapidAbsolute(x=tbl.getMaxX())
        elif(char == '8'):
          ui.keyPressMessage("8 - ONE AXIS ONLY - Safe absolute rapid to table corners - UC", key, char)
          mch.safeRapidAbsolute(y=tbl.getMaxY())


      elif(char == '1'):
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
      elif(char in 'sS'):
        ui.keyPressMessage("sS - Safe absolute rapid to table corners - Table position scan", key, char)
        tablePositionScan()
      else:
        ui.keyPressMessage("Unknown command", key, char)

    elif(char == '+'):
      ui.keyPressMessage("+ - Set rapid increment (XY)+", key, char)
      tbl.changeRI_XY(+1)

    elif(char == '-'):
      ui.keyPressMessage("- - Set rapid increment (XY)-", key, char)
      tbl.changeRI_XY(-1)

    elif(char == 'Z'):
      ui.keyPressMessage("Z - Set rapid increment (Z)+", key, char)
      tbl.changeRI_Z(+1)

    elif(char == 'z'):
      ui.keyPressMessage("z - Set rapid increment (Z)-", key, char)
      tbl.changeRI_Z(-1)

    elif(char == '%'):
      ui.keyPressMessage("% - Set table size percent (loop)", key, char)
      tmpTableSizePercent = ut.genericValueChanger(  tbl.getTableSizePercent(), +10, tbl.gMIN_TABLE_SIZE_PERCENT, tbl.gMAX_TABLE_SIZE_PERCENT,
                              loop=True, valueName="Table size percent")

      tbl.setTableSizePercent(tmpTableSizePercent)

    elif(char == 'V'):
      ui.keyPressMessage("V - Set verbose level+", key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), +1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                            loop=True, valueName="Verbose level",
                            valueFormatter=lambda level : "%d (%s)" % (level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    elif(char == 'v'):
      ui.keyPressMessage("v - Set verbose level-", key, char)
      tempVerboseLevel = ut.genericValueChanger(  ui.getVerboseLevel(), -1, ui.gMIN_VERBOSE_LEVEL, ui.gMAX_VERBOSE_LEVEL,
                          loop=True, valueName="Verbose level",
                          valueFormatter=lambda level : "%d (%s)" % (level,ui.getVerboseLevelStr(level)) )
      ui.setVerboseLevel(tempVerboseLevel)

    elif(char == 'A'):
      ui.keyPressMessage("A - Set safe height+", key, char)
      tempSafeHeight = ut.genericValueChanger(  tbl.getSafeHeight(), +1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
                            loop=False, valueName="Safe Height" )
      tbl.setSafeHeight(tempSafeHeight)

    elif(char == 'a'):
      ui.keyPressMessage("a - Set safe height-", key, char)
      tempSafeHeight = ut.genericValueChanger(  tbl.getSafeHeight(), -1, tbl.gMIN_SAFE_HEIGHT, tbl.gMAX_SAFE_HEIGHT,
                            loop=False, valueName="Safe Height" )
      tbl.setSafeHeight(tempSafeHeight)

    else:  # Rest of keys
      processed = False
      if(ui.getVerboseLevelStr() == 'DEBUG'):
        ui.keyPressMessage("Pressed unknown key %d [%s]" % (key,char), key, char)
      else:
        pass
        #ui.keyPressMessage("Unknown command", key, char)

  if(processed):
    ui.showReadyMsg(caller='main.processUserInput()')

  return True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def main():
  _k = 'main()'
  ui.log("[ Entering ]", k=_k, v='DEBUG')

  ui.clearScreen()

  ui.logBlock("    grblCommander v{0}".format(gVERSION), k=_k, v='BASIC')

  sp.serialConnect()

  mch.sendGCodeInitSequence()

  ui.log("", k=_k, v='BASIC')
  ui.log("System ready!", k=_k, v='BASIC')
  ui.log("", k=_k, v='BASIC')

  showHelp()

  mch.showStatus()

  ui.showReadyMsg(caller='main()')

  while(True):

    line = sp.gSerial.readline()
    if(line):
      ui.log("<<<<<",line, k=_k, v='BASIC')

    if not processUserInput():
      break

  ui.log("Closing serial port...", k=_k, v='BASIC')
  sp.gSerial.close()

  ui.log("Closing program...", k=_k, v='BASIC')


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
  _k = '__main__'
  try:
    main()
  finally:
    pass
#    ui.log("Press any key to exit...", k=_k, v='BASIC')
#    readKey()
