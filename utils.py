from cambc import Direction, EntityType, Environment

All_Dirs = [d for d in Direction]
Dirs = [d for d in Direction if d != Direction.CENTRE]
Diagonal_Dirs = [Dirs[x] for x in range(1, 8, 2)]
Straight_Dirs = [Dirs[x] for x in range(0, 7, 2)]

# ORE
Ore_Env = [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]
MAX_ORE_IGNORE_TURN = 10
MAX_ATTACKABLE_IGNORE_TURN = 5

# CORE
MAX_BUILDER_OPENING = 4
MAX_BUILDER_COUNT = 47

# TURRET
Turret_Type = [EntityType.SENTINEL, EntityType.GUNNER, EntityType.BREACH, EntityType.LAUNCHER]
