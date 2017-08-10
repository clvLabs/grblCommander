macro = {
  'title': 'grblCommander - Machine Long Status - DEFAULT',

  'description': """
  This is the default macro used by grblCommander to display extended
  machine settings in the 'Show current status (LONG)' option.

  PLEASE DO NOT CHANGE THIS FILE.
  To set a custom long status text with your preferred info/ordering, modify [macro][machineLongStatus]
  on your user config file to point to a custom macro with your info/ordering.
  """,

  'commands': [
    ['$I',      'Build info'],
    ['$N',      'Startup blocks'],
    ['$G',      'GCode parser state'],
    ['$#',      'GCode parameters'],
    ['$$',      'grbl config'],
  ],

}
