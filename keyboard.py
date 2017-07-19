#!/usr/bin/python3
"""
grblCommander - keyboard
========================
Keyboard management
"""
#print("***[IMPORTING]*** grblCommander - keyboard")

import time
import kbhit

import utils as ut

if(ut.isWindows()):		import msvcrt
if(not ut.isWindows()):	import getch

# Keyboard manager
gKey = kbhit.KBHit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def keyPressed():
	return gKey.kbhit()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def _internal_readKey():
	if(ut.isWindows()):
		return ord(msvcrt.getch())
	else:
		return ord(getch.getch())

def readKey():
	return _internal_readKey()

def test_readKey():
	key=_int_readKey()
	time.sleep(0.1)
	if(not gKey.kbhit()):
		return key

	keylist=[key]
	while(True):
		key=_int_readKey()
		keylist.append(key)
		time.sleep(0.1)
		if(not gKey.kbhit()):
			return keylist

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if __name__ == '__main__':
	try:

		print("TESTING keyboard.py")
		print("-------------------")
		print("")

		x=input("Normal input test...\n")
		print("Entered text is [%s]" % repr(x))

		key=''

		print("kbhit() test")
		print("------------")
		while(key != 27):
			if(gKey.kbhit()):
				print("Key pressed:",end='')
				key=readKey()
				print(key)

		print("readKey() test")
		print("--------------")
		while True:
			key=readKey()
			if(isinstance(key,int)):
				print("Key is %d [%s]" % (key,chr(key)))
			else:
				print("KeyList is [%s]" % (key,))
	finally:
		pass
#		debugLog("Press any key to exit...", caller='main()', verbose='BASIC')
#		readKey()



# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
def _find_getch():
	try:
		import termios
	except ImportError:
		# Non-POSIX. Return msvcrt's (Windows') getch.
		import msvcrt
		return msvcrt.getch

	# POSIX system. Create and return a getch that manipulates the tty.
	import sys, tty
	def _getch():
		fd = sys.stdin.fileno()
		old_settings = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			ch = sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
		return ch

	return _getch

#int_readKey = _find_getch()
int_readKey = gKey.getch

def readKey():
	if(ut.isWindows()):
		return int_readKey()[0]
		#return ord(gKey.getch())
	else:
		return ord(int_readKey())
"""
