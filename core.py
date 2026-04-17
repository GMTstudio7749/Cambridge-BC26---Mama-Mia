import random
from cambc import Controller, Position
from utils import *

class Core:
    def __init__(self):
        self.setup = False
        self.my_pos = Position(-1, -1)
        self.state = "OPENING"
        self.builder_spawn = 0
        self.Open_Idx = -1
        self.Cur_Round = -1

        # Opening 
        self.Open_Eco_Dir: Direction
        self.Open_Guard_Dir: Direction

        # Expanding
        self.EXPAND_ROUND = 200
        self.Spawn_Dir_Idx = 0

        # RESOURCE
        self.Glob_Tit = -1
        self.Glob_Anx = -1

        # COST
        self.Builder_Cost = -1
        self.Harvest_Cost = -1
        self.Foundry_Cost = -1
        self.Convey_Cost = -1
        self.Bridge_Cost = -1
        self.Gunner_Cost = -1
        self.Launcher_Cost = -1
        self.Road_Cost = -1
        self.Barrier_Cost = -1
        self.Spawn_Limit = -1

    #region ----- Core GENERAL -----
    def CORE_setup(self, ct: Controller):
        """Core setup infos"""
        self.my_pos = ct.get_position()

        map_mid = Position(ct.get_map_width() // 2, ct.get_map_height() // 2)
        tmp_dir = self.my_pos.direction_to(map_mid)
        if tmp_dir in Diagonal_Dirs:
            self.Open_Eco_Dir = tmp_dir
            self.Open_Guard_Dir = tmp_dir.rotate_right().rotate_right().rotate_right()
        else:
            self.Open_Eco_Dir = tmp_dir.rotate_right()
            self.Open_Guard_Dir = tmp_dir.opposite()

    def CORE_update(self, ct: Controller):
        """Core update info about global values"""
        self.Cur_Round = ct.get_current_round()

        self.Glob_Tit, self.Glob_Anx = ct.get_global_resources()

        self.Builder_Cost, tmp = ct.get_builder_bot_cost()
        self.Harvest_Cost, tmp = ct.get_harvester_cost()
        self.Foundry_Cost, tmp = ct.get_foundry_cost()
        self.Convey_Cost, tmp = ct.get_conveyor_cost()
        self.Bridge_Cost, tmp = ct.get_bridge_cost()
        self.Gunner_Cost, tmp = ct.get_gunner_cost()
        self.Launcher_Cost, tmp = ct.get_launcher_cost()
        self.Road_Cost, tmp = ct.get_road_cost()
        self.Barrier_Cost, tmp = ct.get_barrier_cost()

    def CORE_spawn_builder(self, ct: Controller, spawn_dir: Direction):
        """Core spawn builder depends on spawn dir, return bool value"""
        if ct.get_action_cooldown() > 0: return False
        if self.Builder_Cost > self.Glob_Tit: return False
        if ct.get_unit_count() > MAX_BUILDER_COUNT: return False

        spawn_pos = self.my_pos.add(spawn_dir)
        if ct.can_spawn(spawn_pos):
            ct.spawn_builder(spawn_pos)
            self.builder_spawn = self.builder_spawn + 1
            return True
        return False
    
    #endregion

    def DEBUG_core(self):
        """Debug function for every core info"""
        print(f"State: {self.state}\n")
        print(f"ECO dir: {self.Open_Eco_Dir}")
        print(f"GUARD dir: {self.Open_Guard_Dir}")

    def DEBUG_global_cost(self):
        """Print current costs for debug purpose"""
        print("\n== Global Cost ==")
        print("Builder:", self.Builder_Cost)
        print("Harvester:", self.Harvest_Cost)
        print("Conveyor:", self.Convey_Cost)
        print("Bridge:", self.Bridge_Cost)
        print("Foundry:", self.Foundry_Cost)
        print("Gunner:", self.Gunner_Cost)
        print("Launcher:", self.Launcher_Cost)
        print("Road:", self.Road_Cost)
        print("===================\n")

    #region --- Core STATE ---
    def CORE_opening(self, ct: Controller):
        """Core function for opening state, return True if work finished"""
        if self.builder_spawn >= OPENING_COUNT: return True

        self.Open_Idx = (self.Open_Idx + 1) % OPENING_COUNT
        type = OPENING[self.Open_Idx]
        if type == "GUARD":
            if self.CORE_spawn_builder(ct, self.Open_Guard_Dir):
                self.Open_Guard_Dir = self.Open_Guard_Dir.rotate_right().rotate_right()
        
        elif type == "ECO":
            if self.CORE_spawn_builder(ct, self.Open_Eco_Dir):
                self.Open_Eco_Dir = self.Open_Eco_Dir.rotate_right().rotate_right()
        
        elif type == "RUSH":
            self.CORE_spawn_builder(ct, Direction.CENTRE)
        return False
    
    def CORE_expanding(self, ct: Controller):
        """Core function for expanding state, return True if work finished"""
        if self.Cur_Round < self.EXPAND_ROUND: return False
        
        if self.Cur_Round % 50 == 0:
            if self.Glob_Tit > self.Builder_Cost + 300:
                if ct.get_unit_count() < 30 and ct.get_unit_count() % 2 == 0:
                    self.CORE_spawn_builder(ct, Direction.CENTRE)

                else:
                    self.CORE_spawn_builder(ct, Dirs[self.Spawn_Dir_Idx])
                    self.Spawn_Dir_Idx = (self.Spawn_Dir_Idx + 3) % 8
        
        return False

    #endregion

    def CORE_run(self, ct: Controller):
        """Main core runner"""
        # SETUP
        if not self.setup:
            self.CORE_setup(ct)
            self.setup = True
        
        # UPDATE
        self.CORE_update(ct)

        # WORK
        if self.state == "OPENING":
            if self.CORE_opening(ct):
                self.state = "EXPANDING"

        if self.state == "EXPANDING":
            self.CORE_expanding(ct)
            pass

        # DEBUG
        # self.DEBUG_core()
        # self.DEBUG_global_cost()