#!/usr/bin/python3
"""
grblCommander - utils
=====================
Programming utilities
"""
#print("***[IMPORTING]*** grblCommander - utils")

import sys
from . import ui as ui

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def isWindows():
	return( 'win' in sys.platform )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def genericValueChanger(value, direction, min, max, loop=False, valueName="", valueFormatter=None):
	ui.debugLog("[ Entering genericValueChanger() ]", caller='genericValueChanger()', verbose='DEBUG')

	newValue = 0
	increment = 0

	increment = direction

	if( direction > 0 ):	# Up
		if(	( value < max )
		and	( value + increment > max ) ):
			increment = max - value

	else:					# Down
		if(	( value > min )
		and	( value + increment  < min ) ):
			increment = min - value

	newValue = value + increment

	if(loop):
		if( newValue < min ):	newValue = max
		if( newValue > max ):	newValue = min
	else:
		if( newValue < min ):
			ui.debugLog( "ERROR: %s below %d not allowed!" % (valueName, min), caller='genericValueChanger()', verbose='BASIC')
			return value

		if( newValue > max ):
			ui.debugLog( "ERROR: %s over %d not allowed!" % (valueName, max), caller='genericValueChanger()', verbose='BASIC')
			return value

	if( valueFormatter != None ):
		formattedValue = valueFormatter( newValue )
	else:
		formattedValue = newValue

	ui.debugLog("New %s: %s" % (valueName, formattedValue), caller='genericValueChanger()', verbose='BASIC')
	return newValue


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
