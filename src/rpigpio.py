#!/usr/bin/python3
"""
grblCommander - rpigpio
=======================
Raspberry Pi GPIO utilities
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import time
import os
import RPi.GPIO as GPIO
from src.config import cfg

# ------------------------------------------------------------------
# Make it easier (shorter) to use cfg object
gpioCfg = cfg['gpio']

#Probe Config
gPROBE_PIN = gpioCfg['probePin']

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def setup():
  GPIO.setmode(GPIO.BOARD)
  GPIO.setup(gPROBE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def isProbeContactActive():
  return(not GPIO.input(gPROBE_PIN))
