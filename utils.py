from cambc import Direction, Environment

All_Dirs = [d for d in Direction]
Dirs = [d for d in Direction if d != Direction.CENTRE]
Diagonal_Dirs = [Dirs[x] for x in range(1, 8, 2)]

Ore_Env = [Environment.ORE_TITANIUM, Environment.ORE_AXIONITE]
# CORE
Max_Builder_Opening = 4
