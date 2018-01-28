# ###################################################
#
# Advanced macro example:
#
# grblCommander just expects to find a 'macro' object
#  in macro files, and this object can be built on
#  the fly. So we can use this to build 'smarter' macros
#


# ###################################################
# Initialize macro
macro = {
  'title': 'Advanced macro example',
  'description': '''
  This example drills a horizontal series of holes with increasing depth.
  Check out the code, most parameters are configurable!
  ''',
  'commands': [],
}


# ###################################################
# Configuration
MATERIAL_WIDTH = 50

BIT_DIAMETER = 5

# Horizontal spacing: Proportion to BIT_DIAMETER
H_SPACING = 1.0
X_INCREMENT = ((H_SPACING * BIT_DIAMETER) + BIT_DIAMETER)

SAFE_HEIGHT = 0.5
INITIAL_DEPTH = 0.5
DEPTH_INCREMENT = 0.1
PLUNGE_FEED = 20


# ###################################################
# Functions
def addMacroCommands(commands):
  global macro
  macro['commands'].extend(commands)

def addSetup():
  addMacroCommands([
    [],
    ['', 'Setup'],
    [],
    ['G0 G90 G94 G21 G17 G54', 'Settings'],
    ['G0Z{:}'.format(SAFE_HEIGHT), 'Safe Z'],
  ])

def addEnd():
  addMacroCommands([
    [],
    ['', 'End'],
    [],
    ['G0Z{:}'.format(SAFE_HEIGHT), 'Safe Z'],
    ['G0X0', 'Back to X0'],
  ])

def addHole(index):
  hole = holeList[index]
  x = hole['x']
  z = hole['z']
  holeNum = index + 1

  addMacroCommands([
    [],
    ['', 'Hole {:}/{:}: x:{:} depth:{:}'.format(holeNum, numHoles, x, z)],
    [],
    ['G0X{:}'.format(x), 'Move to hole X'],
    ['G0Z0', 'Rapid Z to surface'],
    ['G1Z{:}F{:}'.format(z, PLUNGE_FEED), 'Plunge'],
    ['G0Z{:}'.format(SAFE_HEIGHT), 'Safe Z'],
  ])


# ###################################################
# Create and fill hole list
holeList = []
finished = False
x = 0
z = INITIAL_DEPTH * -1

while not finished:
  holeList.append({
      'x': '{0:.3f}'.format(x),
      'z': '{0:.3f}'.format(z),
    })
  x += X_INCREMENT
  z -= DEPTH_INCREMENT
  if x > MATERIAL_WIDTH:
    finished = True

numHoles = len(holeList)


# ###################################################
# Macro build
addSetup()
for index in range(len(holeList)):
  addHole(index)
addEnd()
