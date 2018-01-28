# Get shared variables for this macro
from . import vars

macro = {
  'title': 'Macro demo - sample 1mm feeds XYZ',

  'description': '''
  This is an example on using grblCommanders' macros:
  - Each line can contain a command and/or a comment
  - Empty lines are allowed as display spacers
  - Macros can be called from macros
  - Special keywords are allowed:
    - 'PAUSE' command can be used to pause execution
    - 'STARTUP' command can be used to recall startup sequence
  - Any settings or commands can be stored in an external .py file
      to share amongst macros in the same folder
  ''',

  'commands': [
    ['',                   'Prepare machine modal settings'],
    vars.mmRelative,
    vars.feed,
    [],
    ['PAUSE',              'Pause before X axis'],
    ['G1 X+1',             'X - Right'],
    ['G1 X-2',             'X - Left'],
    ['G1 X+1',             'X - Center'],
    [],
    ['PAUSE',              'Pause before Y axis'],
    ['G1 Y+1',             'Y - Right'],
    ['G1 Y-2',             'Y - Left'],
    ['G1 Y+1',             'Y - Center'],
    [],
    ['PAUSE',              'Pause before Z axis'],
    ['G1 Z+1',             'Z - Right'],
    ['G1 Z-2',             'Z - Left'],
    ['G1 Z+1',             'Z - Center'],
    [],
    ['',                   'Finish demo'],
    vars.go000,
    vars.restoreSettings,
  ],
}
