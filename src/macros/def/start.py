macro = {
  'title': 'grblCommander - Startup sequence - DEFAULT',

  'description': """
  This is the default startup sequence for grblCommander.

  WARNING!! It forces working in millimeters, absolute mode and a few other settings.

  PLEASE DO NOT CHANGE THIS FILE.
  To set a custom startup sequence with your preferred settings, modify [macro][startup]
  on your user config file to point to a custom macro with your settings.
  """,

  'commands': [
    ['G0',      'Rapid positioning'],
    ['G17',     'XY Plane selection'],
    ['G90',     'Absolute programming'],
    ['G21',     'Programming in millimeters (mm)'],
    ['F400',    'Feed rate'],
  ],

}
