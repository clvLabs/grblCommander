macro = {
  'title': 'Macro demo - sample 1mm feeds XYZ',

  'description': """
  This is an example on using grblCommanders' macros:
  - Each line can contain a command and/or a comment
  - Empty lines are allowed as display spacers
  - Macros can be called from macros
  - 'PAUSE' command can be used to pause execution
  - 'STARTUP' command can be used to recall startup sequence
  """,

  'commands': [
    ['',              'Prepare machine modal settings'],
    ['G21',           'Programming in millimeters (mm)'],
    ['G91',           'Relative programming'],
    [],
    ['PAUSE',         'Pause before X axis'],
    [],
    ['',              'X axis travel'],
    ['G1 X+1 F100',   'X - Right'],
    ['G1 X-2 F100',   'X - Left'],
    ['G1 X+1 F100',   'X - Center'],
    [],
    ['PAUSE',         'Pause before Y axis'],
    [],
    ['',              'Y axis travel'],
    ['G1 Y+1 F100',   'Y - Right'],
    ['G1 Y-2 F100',   'Y - Left'],
    ['G1 Y+1 F100',   'Y - Center'],
    [],
    ['PAUSE',         'Pause before Z axis'],
    [],
    ['',              'Z axis travel'],
    ['G1 Z+1 F100',   'Z - Right'],
    ['G1 Z-2 F100',   'Z - Left'],
    ['G1 Z+1 F100',   'Z - Center'],
    [],
    ['demo.goto0',    'Restore position to 0/0/0'],
    ['STARTUP',       'Restore machine modal settings'],
  ],
}
