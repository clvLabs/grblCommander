# Get shared variables for this macro
from .vars import *

macro = {
  'title': 'Macro demo - drill pattern',

  'description': """
  This example drills a series of holes using a macro for making the holes.
  It assumes the material goes from Z0 to Z5 and uses a safe height of Z8.
  """,

  'commands': [
    ['',                   'Prepare machine modal settings'],
    ['G21',                'Programming in millimeters (mm)'],
    ['G90',                'Absolute programming'],
    [],
    ['',                   'Spindle initialization'],
    [SAFE_HEIGHT,          'Rapid to safe height'],
    [RAPID_00,             'Rapid to 0/0'],
    ['PAUSE',              'Please start spindle'],
    [],
    ['',                   'Starting drill pattern'],
    ['G0 X0 Y0',           'Hole 1/9 - rapid'],
    ['demo.2.drill',       'Hole 1/9 - Drill'],
    [],
    ['G0 X50 Y0',          'Hole 2/9 - rapid'],
    ['demo.2.drill',       'Hole 2/9 - Drill'],
    [],
    ['G0 X100 Y0',         'Hole 3/9 - rapid'],
    ['demo.2.drill',       'Hole 3/9 - Drill'],
    [],
    ['G0 X0 Y50',          'Hole 4/9 - rapid'],
    ['demo.2.drill',       'Hole 4/9 - Drill'],
    [],
    ['G0 X50 Y50',         'Hole 5/9 - rapid'],
    ['demo.2.drill',       'Hole 5/9 - Drill'],
    [],
    ['G0 X100 Y50',        'Hole 6/9 - rapid'],
    ['demo.2.drill',       'Hole 6/9 - Drill'],
    [],
    ['G0 X0 Y100',         'Hole 7/9 - rapid'],
    ['demo.2.drill',       'Hole 7/9 - Drill'],
    [],
    ['G0 X50 Y100',        'Hole 8/9 - rapid'],
    ['demo.2.drill',       'Hole 8/9 - Drill'],
    [],
    ['G0 X100 Y100',       'Hole 9/9 - rapid'],
    ['demo.2.drill',       'Hole 9/9 - Drill'],
    [],
    ['',                   'Cleanup - finished'],
    [RAPID_00,             'Rapid to 0/0'],
    ['STARTUP',            'Restore machine modal settings'],
  ],
}
