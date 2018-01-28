# Get shared variables for this macro
from . import vars

macro = {
  'title': 'Macro demo - drill pattern',

  'description': '''
  This example drills a series of holes using a macro for making the holes.
  It assumes the material goes from Z0 to Z5 and uses a safe height of Z8.
  ''',

  'commands': [
    ['',                   'Prepare machine modal settings'],
    vars.mmAbsolute,
    vars.feed,
    [],
    ['',                   'Spindle initialization'],
    vars.safeHeight,
    vars.rapid00,
    vars.startSpindlePause,
    [],
    ['',                      'Starting drill pattern'],
    ['G0 X0 Y0',              'Hole 1/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X50 Y0',             'Hole 2/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X100 Y0',            'Hole 3/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X0 Y50',             'Hole 4/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X50 Y50',            'Hole 5/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X100 Y50',           'Hole 6/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X0 Y100',            'Hole 7/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X50 Y100',           'Hole 8/9 - rapid'],
    vars.singleHole,
    [],
    ['G0 X100 Y100',          'Hole 9/9 - rapid'],
    vars.singleHole,
    [],
    ['',                      'Cleanup - finished'],
    vars.safeHeight,
    vars.rapid00,
    vars.restoreSettings,
  ],
}
