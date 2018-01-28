#!/usr/bin/python3
'''
grblCommander - utils
=====================
Programming utilities
'''

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import sys
from . import ui as ui

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def genericValueChanger(value, direction, min, max, loop=False, valueName='', valueFormatter=None):
  newValue = 0
  increment = 0

  increment = direction

  if( direction > 0 ):  # Up
    if(  ( value < max )
    and  ( value + increment > max ) ):
      increment = max - value

  else:          # Down
    if(  ( value > min )
    and  ( value + increment  < min ) ):
      increment = min - value

  newValue = value + increment

  if(loop):
    if( newValue < min ):  newValue = max
    if( newValue > max ):  newValue = min
  else:
    if( newValue < min ):
      ui.log('ERROR: {:s} below {:d} not allowed!'.format(valueName, min), c='ui.errorMsg', v='ERROR')
      return value

    if( newValue > max ):
      ui.log('ERROR: {:s} over {:d} not allowed!'.format(valueName, max), c='ui.errorMsg', v='ERROR')
      return value

  if( valueFormatter != None ):
    formattedValue = valueFormatter( newValue )
  else:
    formattedValue = newValue

  ui.log('New {:s}: {:}'.format(valueName, formattedValue))
  return newValue
