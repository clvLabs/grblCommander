#!/usr/bin/python3
"""
grblCommander - joystick
=======================
joystick management class
"""

if __name__ == '__main__':
  print('This file is a module, it should not be executed directly')

import pygame
from os import environ
from pygame.locals import QUIT, JOYBUTTONUP, JOYBUTTONDOWN, \
    JOYAXISMOTION, JOYHATMOTION

from . import ui as ui

# ------------------------------------------------------------------
# Joystick class

class Joystick:

  def __init__(self, cfg):
    ''' Construct a Joystick object
    '''
    self.cfg = cfg
    self.joyCfg = cfg['joystick']
    self._joystick = None
    self.connected = False
    self.enabled = False
    self.status = {}
    self.resetStatus()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def resetStatus(self):
    ''' Reset joystick status
    '''
    self.status = {
      'x+': False,
      'x-': False,
      'y+': False,
      'y-': False,
      'z+': False,
      'z-': False,
      'extraD': False,
      'extraU': False,
    }


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def start(self):
    ''' Start joystick connection
    '''

    ui.log('Starting pygame...')
    # Don't use drivers we don't need
    environ["SDL_VIDEODRIVER"] = "dummy"
    environ["SDL_AUDIODRIVER"] = "dummy"
    pygame.init()

    self.searchJoystick()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def restart(self):
    ''' Restart joystick connection
    '''
    self.searchJoystick()


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def searchJoystick(self):
    ''' Search for the configured joystick in the system list
    '''

    self._joystick = None
    self.resetStatus()

    ui.log('Restarting joystick driver...')
    if pygame.joystick.get_init():
      pygame.joystick.quit()

    pygame.joystick.init()

    ui.log('Searching for joystick [{:s}]...'.format(self.joyCfg['name']))
    try:
      for i in range(0, pygame.joystick.get_count()):
          foundJoy = pygame.joystick.Joystick(i)
          # print("Detected joystick '%s'" % foundJoy.get_name())

          if foundJoy.get_name() == self.joyCfg['name']:
            ui.log('Joystick found!!.', c='ui.successMsg')
            self._joystick = foundJoy
            self._joystick.init()
    except:
      pass

    # Ignore initialization messages
    if self._joystick:
      self.connected = True
      self.flushQueue()
    else:
      self.connected = False
      ui.log('Joystick not found', c='ui.errorMsg', v='ERROR')


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def process(self):
    ''' Call this method frequently to give Joystick some processing time
    '''
    if not self._joystick:
      self.flushQueue()
      return

    for event in pygame.event.get():
        if self.enabled:
          self.joystickEventListener(event)


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def flushQueue(self):
    ''' Clear the event queue
    '''
    for event in pygame.event.get():
        pass


  # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  def joystickEventListener(self, event):
    ''' Joystick event handler
    '''

    # Ignore events from other joysticks
    if not self._joystick or event.joy != self._joystick.get_id():
      # print("IGNORING event from joystick {:d}".format(event.joy))
      return

    if event.type == JOYAXISMOTION:
      # print("Joystick axis {:d} value {:0.3f}".format(event.axis,event.value))
      if event.axis in self.joyCfg['axes']:
        axisCfg = self.joyCfg['axes'][event.axis]
        axis = axisCfg['axis']
        invert = axisCfg['invert']

        self.status[axis + '+'] = False
        self.status[axis + '-'] = False

        if event.value:
          if event.value < 0:
            if invert:
              move ='+'
            else:
              move ='-'
          elif event.value > 0:
            if invert:
              move ='-'
            else:
              move ='+'

          self.status[axis + move] = True

    elif event.type == JOYBUTTONDOWN:
      # print("Joystick button {:d} down.".format(event.button))
      if event.button in self.joyCfg['buttons']:
        buttonFunction = self.joyCfg['buttons'][event.button]
        self.status[buttonFunction] = True

    elif event.type == JOYBUTTONUP:
      if event.button in self.joyCfg['buttons']:
        buttonFunction = self.joyCfg['buttons'][event.button]
        self.status[buttonFunction] = False

          # print("Joystick button {:d} up.".format(event.button))
    # elif event.type == JOYHATMOTION:
    #     print("Joystick hat motion.")

