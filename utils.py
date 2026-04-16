from cambc import Direction, EntityType, Environment
from cambc import GameConstants
from enum import Enum

All_Dirs = [d for d in Direction]
Dirs = [d for d in Direction if d != Direction.CENTRE]
Diagonal_Dirs = [Dirs[x] for x in range(1, 8, 2)]
Straight_Dirs = [Dirs[x] for x in range(0, 7, 2)]

# ORE
ORE_ENV = [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]
MAX_ORE_IGNORE_TURN = 10

# CORE
MAX_BUILDER_COUNT = GameConstants.MAX_TEAM_UNITS - 10
OPENING_COUNT = 4
OPENING = ["ECO", "ECO", "ECO", "ECO"]

# CONVEYOR
CONVEY_TYPE = [EntityType.CONVEYOR, EntityType.BRIDGE, EntityType.SPLITTER, EntityType.ARMOURED_CONVEYOR]

# TURRET
TURRET_TYPE = [EntityType.SENTINEL, EntityType.GUNNER, EntityType.BREACH, EntityType.LAUNCHER]

# GUARD
CHANGE_HOTSPOT_TURN = 100

# RUSH
MAX_ATTACKABLE_IGNORE_TURN = 10
MAX_ATTACK_TURN_COUNT = 40
MAX_ATTACK_TURN_COUNT_CONCENTRATE = 60
class ATTACK_TYPE(Enum):
    NONE = 0 
    NORMAL = 2
    PLACE_TURRET = 3
    DONE = 4