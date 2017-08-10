# Get shared variables for this macro
from .vars import *

macro = {
  'title': 'Single drill',

  'description': """
  Drill a single 5mm hole in 1mm steps.
  """,

  'commands': [
    ['',          'Preparing drill'],
    ['G90',       'Absolute programming'],
    ['G0 Z5',     'Rapid to material top'],
    ['G91',       'Relative programming'],
    [],
    ['',          'Drilling: Z (-1/-5)'],
    ['G1 Z-1',    'Feed'],
    ['G0 Z1',     'Rapid back to material top'],
    [],
    ['',          'Drilling: Z (-2/-5)'],
    ['G0 Z-1',    'Rapid to last position'],
    ['G1 Z-1',    'Feed'],
    ['G0 Z2',     'Rapid back to material top'],
    [],
    ['',          'Drilling: Z (-3/-5)'],
    ['G0 Z-2',    'Rapid to last position'],
    ['G1 Z-1',    'Feed'],
    ['G0 Z3',     'Rapid back to material top'],
    [],
    ['',          'Drilling: Z (-4/-5)'],
    ['G0 Z-3',    'Rapid to last position'],
    ['G1 Z-1',    'Feed'],
    ['G0 Z4',     'Rapid back to material top'],
    [],
    ['',          'Drilling: Z (-5/-5)'],
    ['G0 Z-4',    'Rapid to last position'],
    ['G1 Z-1',    'Feed'],
    ['G0 Z5',     'Rapid back to material top'],
    [],
    ['',          'Restoring settings'],
    ['G90',       'Absolute programming'],
    [SAFE_HEIGHT, 'Rapid to safe height'],
  ],
}
