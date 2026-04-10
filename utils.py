from cambc import Direction, EntityType, Environment
from cambc import GameConstants

All_Dirs = [d for d in Direction]
Dirs = [d for d in Direction if d != Direction.CENTRE]
Diagonal_Dirs = [Dirs[x] for x in range(1, 8, 2)]
Straight_Dirs = [Dirs[x] for x in range(0, 7, 2)]

# ORE
ORE_ENV = [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]
MAX_ORE_IGNORE_TURN = 10

# CORE
MAX_BUILDER_COUNT = GameConstants.MAX_TEAM_UNITS - 5
MAX_BUILDER_OPENING = 4

# CONVEYOR
CONVEY_TYPE = [EntityType.CONVEYOR, EntityType.BRIDGE, EntityType.SPLITTER, EntityType.ARMOURED_CONVEYOR]

# TURRET
TURRET_TYPE = [EntityType.SENTINEL, EntityType.GUNNER, EntityType.BREACH, EntityType.LAUNCHER]

# GUARD
MAX_STEP_FROM_CORE = 30