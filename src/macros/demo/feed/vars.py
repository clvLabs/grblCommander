# This file is used to store common commands thru the macro files
# It will not be treated as a macro, as it doesnt' export a 'macro' object
# To use it into your macro files, add 'from . import vars'

# Material/project characteristics (shared)
feed              = ['F400',     'Set feed']

# subMacro calls
go000             = ['demo.feed.go000', 'Restore position to 0/0/0']

# Simple command substitutions
restoreSettings   = ['STARTUP',  'Restore machine modal settings']

mm                = ['G21',      'Settings: [mm]']
inch              = ['G20',      'Settings: [inch]']

absolute          = ['G90',      'Settings: [absolute]']
relative          = ['G91',      'Settings: [relative]']

mmAbsolute        = ['G21 G90',  'Settings: [mm] [absolute]']
mmRelative        = ['G21 G91',  'Settings: [mm] [relative]']
inchAbsolute      = ['G20 G90',  'Settings: [inch] [absolute]']
inchRelative      = ['G20 G91',  'Settings: [inch] [relative]']
